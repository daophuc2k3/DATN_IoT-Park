import socket
import threading

# Danh sách client toàn cục
clients = []

def broadcast(message, current_client):
    """Gửi tin nhắn đến tất cả client trừ người gửi"""
    print(f"[BROADCAST] Gui: '{message}' toi tat ca client ngoai tru: {current_client}")
    for client in clients[:]:
        if client != current_client:
            try:
                print(f"  -> Gui toi client {client}")
                client.send(message.encode('utf-8'))
            except Exception as e:
                print(f"  [LỖI] Không gửi được tới client {client}: {e}")
                clients.remove(client)

def handle_client(client_socket, addr):
    print(f"[KẾT NỐI] {addr} đã kết nối.")
    clients.append(client_socket)

    try:
        while True:
            data = client_socket.recv(1024).decode('utf-8').strip()
            if not data:
                continue

            print(f"[{addr}] {data}")

            # Xử lý ping
            if data.lower() == "ping":
                response = "pong"
                print(f"[SERVER -> {addr}] {response}")
                client_socket.send((response + '\n').encode('utf-8'))

            # Lệnh từ backend để broadcast
            elif data.lower().startswith("server_broadcast:"):
                message = data[len("server_broadcast:"):].strip()
                print(f"[SERVER-BROADCAST] Phat tan: {message}")
                broadcast(message, current_client=None)

                # Nếu là lệnh liên quan thanh toán RFID thành công → mở cổng
                if message.lower().startswith("topup") or "rfid" in message.lower():
                    print("[TCP] Phat hien thong bao thanh toan RFID -> mo cong OUT")
                    send_open_gate_command("out")

            else:
                print(f"[BROADCAST] {addr} gui tin: {data}")
                broadcast(f"[{addr}] {data}", client_socket)

    except Exception as e:
        print(f"[LỖI] Kết nối với {addr} gặp lỗi: {e}")
    finally:
        print(f"[NGẮT] {addr} đã ngắt kết nối.")
        if client_socket in clients:
            clients.remove(client_socket)
        client_socket.close()

def start_tcp_server(host='0.0.0.0', port=12345):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(5)
    print(f"[SERVER] Đang chạy tại {host}:{port}")

    while True:
        client_socket, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True)
        thread.start()

def send_open_gate_command(gate_type):
    message = f"open_{gate_type}\n"
    print(f"[DEBUG] Gửi lệnh: {message.strip()} tới {len(clients)} client(s)")
    for client in clients[:]:
        try:
            print(f"  -> Gui lenh '{message.strip()}' toi client {client}")
            client.send("open_out\n".encode('utf-8'))
        except Exception as e:
            print(f"  [⚠] Lỗi gửi tới client {client}: {e}")
            clients.remove(client)
