from django.contrib import admin
from .models import Profile, TopUpHistory


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'phone', 'balance')
    search_fields = ('user__username', 'full_name', 'phone')


@admin.register(TopUpHistory)
class TopUpHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'timestamp', 'status')
    list_filter = ('status', 'timestamp')
    search_fields = ('user__username', 'user__profile__full_name')
    ordering = ('-timestamp',)

    # ✅ Cộng tiền vào tài khoản nếu nạp thành công
    def save_model(self, request, obj, form, change):
        is_new = not change
        if is_new and obj.status == 'success':
            profile = obj.user.profile
            profile.balance += obj.amount
            profile.save()
        super().save_model(request, obj, form, change)
