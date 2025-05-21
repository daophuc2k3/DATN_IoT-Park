from django.contrib import admin
from .models import AccessHistory


@admin.register(AccessHistory)
class AccessHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'get_user_display',
        'get_license_plate_display',
        'rfid_code',
        'check_in',
        'check_out',
        'duration_display',
        'fee'
    )
    list_filter = ('check_in', 'check_out')
    search_fields = ('user__username', 'license_plate', 'rfid_code')
    ordering = ('-check_in',)

    def get_user_display(self, obj):
        return obj.user.username if obj.user else "Khách"
    get_user_display.short_description = 'Người dùng'

    def get_license_plate_display(self, obj):
        return obj.get_license_plate_display()
    get_license_plate_display.short_description = 'Biển số'

    def duration_display(self, obj):
        minutes = obj.duration_minutes()
        return f"{minutes} phút" if minutes is not None else "—"
    duration_display.short_description = 'Thời gian đỗ'
