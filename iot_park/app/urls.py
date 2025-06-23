# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.urls import path, re_path
from app import views
from app.views import AccessHistoryListView, AccessIncome, UserManagement
urlpatterns = [

    # The home page
    path('', views.home, name='home'),
    path('home/', views.home, name='home'),

    path('ho-so/', views.profile_update, name='profile_update'),
    path('lich-su-ra-vao/', AccessHistoryListView.as_view(), name='access_history'),
    path('doanh-thu/', AccessIncome.as_view(), name='income_management'),
    path('quan-ly-nguoi-dung/', UserManagement.as_view(), name='user_management'),

    path("api/recognize-plate/", views.recognize_plate_api, name="recognize_plate_api"),
    path("api/create-topup-qr/", views.create_topup_qr, name="create_topup_qr"),
    path("api/gate/event/", views.gate_event_api, name="gate_event_api"),
    path("api/gate/action/", views.gate_action_api, name="gate_action_api"),
    
    # Matches any html file

]
