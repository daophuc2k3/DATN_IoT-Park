# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import socket
import uuid
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.template import loader
from django.http import HttpResponse
from django import template
from django.contrib.auth.decorators import user_passes_test
import requests
import os
from access.models import AccessHistory
from app.plate_utils import run_plate_recognition
from camera.models import Camera
from core import settings
from customers.form import ProfileUpdateForm
from customers.models import Profile,TopUpHistory
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from access.models import AccessHistory
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from camera.models import Camera
from tcp_server.tcp_server import send_open_gate_command
from .plate_utils import process_frame
from ultralytics import YOLO
import cv2, json, traceback
from decimal import Decimal
from django.utils import timezone
from PIL import Image
from io import BytesIO
from urllib.parse import quote_plus

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

# Load model YOLO chỉ 1 lần khi server chạy
plate_detector = YOLO("model/LP_detector.pt")
char_detector = YOLO("model/LP_ocr.pt")

@login_required(login_url="/login/")
def index(request):
    context = {'segment': 'index'}

    html_template = loader.get_template('index.html')
    return HttpResponse(html_template.render(context, request))

@user_passes_test(lambda u: u.is_staff, login_url="/ho-so/")
def home(request):
    # Lấy 1 camera cổng vào và 1 camera cổng ra, nếu có
    camera_entry = Camera.objects.filter(camera_type='entry', is_active=True).first()
    camera_exit = Camera.objects.filter(camera_type='exit', is_active=True).first()
    histories = AccessHistory.objects.select_related('user').order_by('-check_in')[:5]

    context = {
        'segment': 'home',
        'camera_entry': camera_entry,
        'camera_exit': camera_exit,
        'histories': histories,
    }

    template = loader.get_template('home.html')
    return HttpResponse(template.render(context, request))


@login_required
def profile_update(request):
    profile = request.user.profile

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile_update')
    else:
        form = ProfileUpdateForm(instance=profile)

    # ✅ Lấy lịch sử nạp tiền mới nhất
    topups = TopUpHistory.objects.filter(user=request.user).order_by('-timestamp')[:10]

    return render(request, 'profile.html', {
        'form': form,
        'profile': profile,
        'topups': topups,  # ✅ Truyền vào template
    })

class AccessHistoryListView(LoginRequiredMixin, ListView):
    model = AccessHistory
    template_name = 'history.html'
    context_object_name = 'histories'
    paginate_by = 5
    login_url = '/login/'

    def get_queryset(self):
        if self.request.user.is_staff:
            return AccessHistory.objects.select_related('user').order_by('-check_in')
        else:
            return AccessHistory.objects.filter(user=self.request.user).order_by('-check_in')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = self.request.user.is_staff
        context['segment'] = 'access_history'
        return context
    
@user_passes_test(lambda u: u.is_staff, login_url="/ho-so/")
def user_management(request):
    profiles = Profile.objects.select_related('user').all()
    return render(request, 'user_management.html', {
        'profiles': profiles,
        'segment': 'user_management',
    })


@csrf_exempt
@login_required
def create_topup_qr(request):
    if request.method != "POST":
        return JsonResponse({"error": "Chỉ hỗ trợ POST"}, status=405)

    data = json.loads(request.body)
    amount = Decimal(data.get("amount"))

    if amount < 5000:
        return JsonResponse({"error": "Số tiền tối thiểu là 5.000₫"}, status=400)

    user = request.user

    # Tạo bản ghi trong CSDL
    topup = TopUpHistory.objects.create(
        user=user,
        amount=amount,
        status="pending"
    )

    # Tạo link QR động
    account_number = "04792848901"
    account_name = "DO DAO PHUC"
    bank_id = "TPBank"  # thông tin mô tả thêm

    # Giả sử dùng tool tự gen VietQR (hoặc redirect từ Seopay)
    # Bạn có thể tuỳ chỉnh format dưới đây nếu Seopay yêu cầu khác
    qr_url = f"https://qr.sepay.vn/img?bank=TPBank&acc={account_number}&amount={int(amount)}&des=TOPUP_{topup.id}_{user.username}"
    print((timezone.now() + timezone.timedelta(minutes=5)).strftime("%H:%M:%S"))
    return JsonResponse({
        "qr_url": qr_url,
        "topup_id": topup.id,
        "expired_at": (timezone.now() + timezone.timedelta(minutes=5)).strftime("%H:%M:%S")
    })



@csrf_exempt
def recognize_plate_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Chỉ hỗ trợ phương thức POST."}, status=405)

    try:
        print("hihi")
        with socket.create_connection(("127.0.0.1", 12345), timeout=3) as sock:
            sock.sendall(f"server_broadcast:TOPUP_THANH_CONG\n".encode("utf-8"))
        print("[TCP] Đã gửi thông báo TOPUP tới TCP server")
        data = json.loads(request.body)
        cam_type = data.get("cam")

        if cam_type not in ["entry", "exit"]:
            return JsonResponse({"error": "Giá trị 'cam' phải là 'entry' hoặc 'exit'"}, status=400)

        # Lấy camera đang hoạt động
        camera = Camera.objects.filter(camera_type=cam_type, is_active=True).first()
        if not camera:
            return JsonResponse({"error": f"Không tìm thấy camera '{cam_type}' đang hoạt động"}, status=404)

        # Mở stream MJPEG bằng OpenCV
        cap = cv2.VideoCapture(camera.stream_url)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            return JsonResponse({"error": "Không thể lấy ảnh từ camera."}, status=500)

        # Nhận diện biển số
        result = process_frame(frame, plate_detector, char_detector)
        plate_text = result[0] if isinstance(result, tuple) else result

        if not plate_text:
            return JsonResponse({"error": "Không nhận diện được biển số"}, status=400)

        profile = Profile.objects.get(license_plate__iexact=plate_text.strip().upper())

        return JsonResponse({
            "plate": plate_text or ""
        })

    except Exception as e:
        print("❌ Lỗi xử lý API nhận diện biển số:")
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

# Đây là phiên bản đã cập nhật đầy đủ các trạng thái WebSocket cho hàm gate_event_api

@csrf_exempt
def gate_event_api(request):
    if request.method != "POST":
        return JsonResponse({"trang_thai": "that_bai", "thong_diep": "chi_ho_tro_post"}, status=405)

    try:
        data = json.loads(request.body)
        mode = data.get("mode")
        position = data.get("position")
        rfid_id = data.get("rfid_id")

        if not mode or not position:
            return JsonResponse({"trang_thai": "that_bai", "thong_diep": "thieu_du_lieu_mode_hoac_position"}, status=400)

        if mode not in ["sensor", "rfid"] or position not in ["entry", "exit"]:
            return JsonResponse({"trang_thai": "that_bai", "thong_diep": "tham_so_khong_hop_le"}, status=400)

        camera = Camera.objects.filter(camera_type=position, is_active=True).first()
        if not camera:
            return JsonResponse({"trang_thai": "that_bai", "thong_diep": "khong_tim_thay_camera"}, status=404)

        cap = cv2.VideoCapture(camera.stream_url)
        ret, frame = cap.read()
        cap.release()
        if not ret or frame is None:
            return JsonResponse({"trang_thai": "that_bai", "thong_diep": "khong_doc_duoc_anh"}, status=500)

        now = timezone.now()
        filename = f"capture_{uuid.uuid4().hex[:8]}.jpg"
        folder_path = os.path.join(settings.MEDIA_ROOT, "captured")
        os.makedirs(folder_path, exist_ok=True)
        filepath = os.path.join(folder_path, filename)
        cv2.imwrite(filepath, frame)
        image_url = f"/media/captured/{filename}"

        plate_text = process_frame(frame, plate_detector, char_detector).strip().upper() or "KHONG_XAC_DINH"

        if mode == "sensor":
            try:
                profile = Profile.objects.get(license_plate__iexact=plate_text)
            except Profile.DoesNotExist:
                if position == "exit":
                    guest_log = AccessHistory.objects.filter(
                        license_plate__iexact=plate_text,
                        check_out__isnull=True
                    ).first()
                broadcast_access_event({"status": "chua_co_thong_tin", "position": position, "license_plate": plate_text, "rfid": rfid_id, "check_in": now.isoformat(), "check_out": None, "image_url": image_url})
                return JsonResponse({"trang_thai": "that_bai", "thong_diep": "khong_tim_thay_nguoi_dung", "bien_so": plate_text, "image_url": image_url}, status=404)

            user = profile.user
            active_log = AccessHistory.objects.filter(user=user, check_out__isnull=True).first()

            if position == "entry":
                if active_log:
                    broadcast_access_event({"status": "xe_da_trong_bai", "position": position, "license_plate": plate_text, "rfid": rfid_id, "check_in": active_log.check_in.isoformat(), "check_out": None, "image_url": image_url})
                    return JsonResponse({"trang_thai": "that_bai", "thong_diep": "xe_da_trong_bai", "bien_so": plate_text, "image_url": image_url}, status=400)
                AccessHistory.objects.create(user=user, license_plate=plate_text, rfid_code=rfid_id, check_in=now)
                broadcast_access_event({"status": "checkin_thanh_cong", "position": position, "license_plate": plate_text, "rfid": rfid_id, "check_in": now.isoformat(), "check_out": None, "image_url": image_url})
                return JsonResponse({"trang_thai": "thanh_cong", "thong_diep": "checkin_thanh_cong", "bien_so": plate_text, "image_url": image_url})

            elif position == "exit":
                if not active_log:
                    broadcast_access_event({"status": "xe_chua_vao", "position": position, "license_plate": plate_text, "rfid": rfid_id, "image_url": image_url})
                    return JsonResponse({"trang_thai": "that_bai", "thong_diep": "xe_chua_vao", "bien_so": plate_text, "image_url": image_url}, status=400)

                minutes = int((now - active_log.check_in).total_seconds() // 60)
                total_fee = minutes * getattr(settings, "COST", 1000)

                if profile.balance < total_fee:
                    broadcast_access_event({"status": "so_du_khong_du", "position": position, "license_plate": plate_text, "rfid": rfid_id, "check_in": active_log.check_in.isoformat(), "check_out": now.isoformat(), "image_url": image_url})
                    return JsonResponse({"trang_thai": "that_bai", "thong_diep": "so_du_khong_du", "bien_so": plate_text, "so_du": float(profile.balance), "so_tien_can": total_fee, "image_url": image_url}, status=400)

                profile.balance -= total_fee
                profile.save()
                active_log.check_out = now
                active_log.fee = total_fee
                active_log.save()

                broadcast_access_event({"status": "checkout_thanh_cong", "position": position, "license_plate": plate_text, "rfid": rfid_id, "check_in": active_log.check_in.isoformat(), "check_out": now.isoformat(), "image_url": image_url})
                return JsonResponse({"trang_thai": "thanh_cong", "thong_diep": "checkout_thanh_cong", "bien_so": plate_text, "so_phut": minutes, "so_tien": total_fee, "so_du_con_lai": float(profile.balance), "check_in": active_log.check_in.isoformat(), "check_out": now.isoformat(), "image_url": image_url})

        elif mode == "rfid":
            if not rfid_id:
                return JsonResponse({"trang_thai": "that_bai", "thong_diep": "rfid_khong_duoc_bo_trong"}, status=400)

            if Profile.objects.filter(license_plate__iexact=plate_text).exists():
                broadcast_access_event({"status": "bien_so_da_duoc_dang_ky", "position": position, "license_plate": plate_text, "rfid": rfid_id, "image_url": image_url})
                return JsonResponse({"trang_thai": "that_bai", "thong_diep": "bien_so_da_duoc_dang_ky", "bien_so": plate_text, "image_url": image_url}, status=400)

            if position == "entry":
                if AccessHistory.objects.filter(rfid_code=rfid_id, check_out__isnull=True).exists():
                    broadcast_access_event({"status": "rfid_dang_duoc_su_dung", "position": position, "license_plate": plate_text, "rfid": rfid_id, "image_url": image_url})
                    return JsonResponse({"trang_thai": "that_bai", "thong_diep": "rfid_dang_duoc_su_dung", "rfid_id": rfid_id, "image_url": image_url}, status=400)

                AccessHistory.objects.create(user=None, license_plate=plate_text, rfid_code=rfid_id, check_in=now)
                broadcast_access_event({"status": "checkin_khach_thanh_cong", "position": position, "license_plate": plate_text, "rfid": rfid_id, "check_in": now.isoformat(), "check_out": None, "image_url": image_url})
                return JsonResponse({"trang_thai": "thanh_cong", "thong_diep": "checkin_khach_thanh_cong", "bien_so": plate_text, "rfid_id": rfid_id, "check_in": now.isoformat(), "image_url": image_url})

            elif position == "exit":
                last_log = AccessHistory.objects.filter(license_plate=plate_text, rfid_code=rfid_id, check_out__isnull=True).order_by('-check_in').first()

                if not last_log:
                    broadcast_access_event({"status": "khong_tim_thay_log_checkin", "position": position, "license_plate": plate_text, "rfid": rfid_id, "image_url": image_url})
                    return JsonResponse({"trang_thai": "that_bai", "thong_diep": "khong_tim_thay_log_checkin", "rfid_id": rfid_id, "bien_so": plate_text, "image_url": image_url}, status=400)

                minutes = int((now - last_log.check_in).total_seconds() // 60)
                total_fee = minutes * getattr(settings, "COST", 1000)

                try:
                    desc = f"UID {last_log.uid}"
                    qr_url = f"https://qr.sepay.vn/img?acc=04792848901&bank=TPBank&amount={total_fee}&des={quote_plus(desc)}&template=compact&download=false"
                    response = requests.get(qr_url)
                    response.raise_for_status()
                    img = Image.open(BytesIO(response.content)).convert("1").resize((300, 300), Image.Resampling.NEAREST)
                    qr_folder = os.path.join(settings.MEDIA_ROOT, "qr")
                    os.makedirs(qr_folder, exist_ok=True)
                    filename = f"sepay_qr_{last_log.uid}.bmp"
                    img.save(os.path.join(qr_folder, filename), format="BMP")
                    file_url = f"/media/qr/{filename}"
                except Exception as e:
                    print("❌ Lỗi tạo QR:", e)
                    file_url = None

                broadcast_access_event({"status": "cho_thanh_toan", "position": position, "license_plate": plate_text, "rfid": rfid_id, "check_in": last_log.check_in.isoformat(), "check_out": now.isoformat(), "image_url": image_url})
                return JsonResponse({"trang_thai": "cho_thanh_toan", "thong_diep": "vui_long_quet_ma_qr_de_thanh_toan", "bien_so": plate_text, "rfid_id": rfid_id, "uid": last_log.uid, "so_phut": minutes, "so_tien": total_fee, "file_qr": file_url, "check_in": last_log.check_in.isoformat(), "check_out": now.isoformat(), "image_url": image_url})

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"trang_thai": "that_bai", "thong_diep": str(e)}, status=500)
