# import time
# from django.core.management.base import BaseCommand
# from mqttcall.mqtt_listener import start_mqtt_listener

# class Command(BaseCommand):
#     help = 'Start MQTT listener for sensor data'

#     def handle(self, *args, **options):
#         self.stdout.write(self.style.SUCCESS('🚀 Starting MQTT listener...'))

#         start_mqtt_listener()  # Gọi hàm MQTT đã viết

#         # Giữ tiến trình chạy mãi để tiếp tục lắng nghe MQTT
#         try:
#             while True:
#                 time.sleep(1)
#         except KeyboardInterrupt:
#             self.stdout.write(self.style.WARNING('🛑 MQTT listener stopped by user.'))