import socket
import threading

class TPC_SERVER:
    # Danh sách client toàn cục
    def __init__(self):
        self.clients = []

    def broadcast(self,message, current_client):
        """Gửi tin nhắn đến tất cả client trừ người gửi"""
        print(f"[BROADCAST] Gui: '{message}' toi tat ca client ngoai tru: {current_client}")
        for client in self.clients[:]:
            if client != current_client:
                try:
                    print(f"  -> Gui toi client {client}")
                    client.send(message.encode('utf-8'))
                except Exception as e:
                    print(f"  [LỖI] Không gửi được tới client {client}: {e}")
                    self.clients.remove(client)

    def handle_client(self, client_socket, addr):
        print(f"[KẾT NỐI] {addr} đã kết nối.")
        self.clients.append(client_socket)
        print(len(self.clients))

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
                    self.broadcast(message, current_client=None)

                    # Nếu là lệnh liên quan thanh toán RFID thành công → mở cổng
                    if message.lower().startswith("topup") or "rfid" in message.lower():
                        print("[TCP] Phat hien thong bao thanh toan RFID -> mo cong OUT")
                        self.send_gate_command(4)

                else:
                    print(f"[BROADCAST] {addr} gui tin: {data}")
                    self.broadcast(f"[{addr}] {data}", client_socket)

        except Exception as e:
            print(f"[LỖI] Kết nối với {addr} gặp lỗi: {e}")
        finally:
            print(f"[NGẮT] {addr} đã ngắt kết nối.")
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            client_socket.close()

    def start_tcp_server(self, host='0.0.0.0', port=12345):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen(5)
        print(f"[SERVER] Đang chạy tại {host}:{port}")

        while True:
            client_socket, addr = server.accept()
            thread = threading.Thread(target=self.handle_client, args=(client_socket, addr), daemon=True)
            thread.start()

    def send_gate_command(self, status):
        if status == 1:
            message = "open_in_manual\n".encode('utf-8')
        elif status == -1:
            message = "close_in_manual\n".encode('utf-8')
        elif status == 2:
            message= "open_out_manual\n".encode('utf-8')
        elif status == -2:
            message = "close_out_manual\n".encode('utf-8')
        elif status == 3:
            message= "open_in\n".encode('utf-8')
        elif status == 4:
            message= "open_out\n".encode('utf-8')
            
        print(f"[DEBUG] Gửi lệnh: {message.strip()} tới {len(self.clients)} client(s)")
        for client in self.clients[:]:
            try:
                print(f"  -> Gui lenh '{message.strip()}' toi client {client}") 
                client.send(message)
            except Exception as e:
                print(f"  [⚠] Lỗi gửi tới client {client}: {e}")
                self.clients.remove(client)
                

tcp_server = TPC_SERVER()