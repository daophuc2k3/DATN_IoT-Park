from django.core.management.base import BaseCommand
from tcp_server.tcp_server import start_tcp_server

class Command(BaseCommand):
    help = 'Khởi động TCP server'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Khởi động TCP server...'))
        start_tcp_server(port=12345)
        self.stdout.write(self.style.SUCCESS('TCP server đang lắng nghe...'))

        # Giữ cho server không bị thoát
        import time
        while True:
            time.sleep(1)
