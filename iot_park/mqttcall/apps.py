from django.apps import AppConfig
from django.core.management.base import BaseCommand
import threading
import os

class MqttcallConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mqttcall'

    def ready(self):
        # Chỉ chạy khi process chính đang chạy (tránh reload 2 lần trong DEBUG)
        if os.environ.get('RUN_MAIN') != 'true':
            return

        from mqttcall.mqtt_listener import start_mqtt_listener

        def run_server():
            BaseCommand().stdout.write(BaseCommand().style.SUCCESS('🚀 Starting MQTT listener...'))
            start_mqtt_listener()

        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()