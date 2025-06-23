from django.apps import AppConfig
from django.core.management.base import BaseCommand
import threading
import os

class TcpServerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tcp_server'

    def ready(self):
        # Chỉ chạy khi process chính đang chạy (tránh reload 2 lần trong DEBUG)
        if os.environ.get('RUN_MAIN') != 'true':
            return

        from tcp_server.tcp_server import tcp_server

        def run_server():
            BaseCommand().stdout.write(BaseCommand().style.SUCCESS('Khởi động TCP server...'))
            tcp_server.start_tcp_server(host='0.0.0.0', port=12345)
            BaseCommand().stdout.write(BaseCommand().style.SUCCESS('TCP server đang lắng nghe...'))

        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()