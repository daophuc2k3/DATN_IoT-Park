import paho.mqtt.client as mqtt
import threading
import queue
import json
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.conf import settings  # ✅ import settings Django
from access.models import AccessHistory
from customers.models import TopUpHistory, Profile
from django.utils import timezone
import re
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

def broadcast_access_event(payload):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "access_event",  # group name chung cho tất cả client
        {
            "type": "access_event",  # gọi method access_event() bên consumer
            **payload
        }
    )


# Hàng đợi xử lý tin nhắn MQTT
mqtt_message_queue = queue.Queue()



# Callback khi kết nối thành công
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[MQTT] Connected successfully.")
        client.subscribe(settings.MQTT_TOPIC)
    else:
        print(f"[MQTT] Connection failed with code {rc}")

# Callback khi nhận được tin nhắn MQTT
def on_message(client, userdata, msg):
    try:
        mqtt_message_queue.put(msg)
        print(f"[MQTT] Message received from topic: {msg.topic}")
    except Exception as e:
        print(f"[ERROR] Failed to enqueue MQTT message: {e}")


import socket

def process_mqtt_queue(client):
    while True:
        try:
            msg = mqtt_message_queue.get()
            topic = msg.topic
            payload_raw = msg.payload.decode("utf-8")
            print(topic)
            print("START SEOPAY")
            if topic == "IOT/seopay/transaction":
                try:
                    data = json.loads(payload_raw)
                    amount = int(data.get("amount"))
                    content = data.get("content", "")
                    timestamp = data.get("timestamp")

                    print(f"💰 Giao dich moi: {amount} VND | Noi dung: {content} | Thoi gian: {timestamp}")

                    # Trường hợp 1: xử lý top-up
                    match = re.search(r"TOPUP(\d+)", content)
                    if match:
                        topup_id = int(match.group(1))
                        print(f"🔍 Tach duoc TopUp ID: {topup_id}")
                        topup = TopUpHistory.objects.filter(id=topup_id, status='pending').first()
                        print(f"🔍 Tim thay TopUp ID={topup} trong DB.")

                        if topup:
                            if topup.amount == amount:
                                topup.status = 'success'
                                topup.timestamp = timezone.now()
                                topup.save()

                                profile = Profile.objects.get(user=topup.user)
                                profile.balance += amount
                                profile.save()

                                print(f"✅ Nap thanh cong cho user {topup.user.username}, +{amount}d")

                                channel_layer = get_channel_layer()
                                async_to_sync(channel_layer.group_send)(
                                    f"topup_{topup_id}",
                                    {
                                        "type": "topup_success",
                                        "new_balance": float(profile.balance),
                                    }
                                )
                            else:
                                print(f"[❌] So tien khong khop. DB: {topup.amount} - MQTT: {amount}")
                        else:
                            print(f"[❌] Khong tim thay TopUpHistory ID={topup_id} dang cho xu ly.")
                        mqtt_message_queue.task_done()
                        continue

                    # Trường hợp 2: xử lý thanh toán lối ra dựa trên UID
                    match_uid = re.search(r"UID\s*([A-Za-z0-9]{6,16})", content)
                    if match_uid:
                        uid = match_uid.group(1)
                        print(f"🔍 Tach duoc UID: {uid}")
                        log = AccessHistory.objects.filter(uid=uid, check_out__isnull=True).first()

                        if log:
                            now = timezone.now()
                            log.check_out = now
                            log.fee = amount  # Lưu lại số tiền thanh toán thực tế
                            log.save()
                            print(f"✅ Checkout thanh cong UID={uid}, {amount} VND")

                            # Phát lại WebSocket để cập nhật trạng thái ra
                            broadcast_access_event({
                                "status": "checkout_thanh_cong",
                                "position": "exit",
                                "license_plate": log.license_plate,
                                "rfid": log.rfid_code,
                                "check_in": log.check_in.isoformat(),
                                "check_out": now.isoformat(),
                                "image_url": f"/media/captured/{log.license_plate}.jpg"
                            })

                            # Gửi lệnh mở cổng qua TCP nếu cần
                            try:
                                with socket.create_connection(("127.0.0.1", 12345), timeout=3) as sock:
                                    sock.sendall(b"server_broadcast:open_out\n")
                                    print("[TCP] Đã gửi lệnh open_out tới TCP server")
                            except Exception as e:
                                print(f"[TCP-ERROR] Không gửi được lệnh mở cổng: {e}")
                        else:
                            print(f"[❌] Khong tim thay log checkin tuong ung UID={uid} dang hoat dong")
                        mqtt_message_queue.task_done()
                        continue

                    print(f"[❌] Khong xac dinh duoc loai giao dich voi noi dung: {content}")

                except Exception as e:
                    print(f"[ERROR] Loi xu ly du lieu JSON hoac DB: {e}")

            mqtt_message_queue.task_done()

        except Exception as e:
            print(f"[ERROR] Loi khi xu ly MQTT message: {e}")
# Khởi động client MQTT và thread hàng đợi
def start_mqtt_listener():
    client = mqtt.Client()
    client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, 60)
        client.loop_start()

        # Khởi động thread xử lý hàng đợi
        processing_thread = threading.Thread(target=process_mqtt_queue, args=(client,))

        processing_thread.daemon = True
        processing_thread.start()

        print("[MQTT] Listener and queue processor started.")
    except Exception as e:
        print(f"[ERROR] Failed to start MQTT client: {e}")


        