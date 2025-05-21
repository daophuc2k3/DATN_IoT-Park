from django.contrib import admin
from .models import Camera

@admin.register(Camera)
class CameraAdmin(admin.ModelAdmin):
    list_display = ('camera_name', 'camera_type', 'stream_url', 'is_active', 'created_at')
    list_filter = ('camera_type', 'is_active')
    search_fields = ('camera_name', 'stream_url')
    ordering = ('-created_at',)
    list_per_page = 20

    fieldsets = (
        (None, {
            'fields': ('camera_name', 'stream_url', 'camera_type', 'is_active')
        }),
        ('Thông tin hệ thống', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
