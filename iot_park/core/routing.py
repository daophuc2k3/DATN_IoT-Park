# core/routing.py (hoặc trong app chính)
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/topup/(?P<topup_id>\d+)/$', consumers.TopupConsumer.as_asgi()),
    re_path(r'^ws/access-events/$', consumers.AccessEventConsumer.as_asgi()),

]
