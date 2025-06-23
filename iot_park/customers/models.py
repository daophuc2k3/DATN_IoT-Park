from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=32, blank=True, null=True, unique=True)
    license_plate = models.CharField(max_length=15, blank=True, null=True, unique=True)  # 🚗 Biển số xe
    balance = models.DecimalField(default=0, max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        if self.license_plate:
            self.license_plate = self.license_plate.upper()  # Tự động viết hoa
        super().save(*args, **kwargs)
class TopUpHistory(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Đang xử lý'),
        ('success', 'Hoàn thành'),
        ('failed', 'Thất bại'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='topups')
    amount = models.DecimalField(max_digits=12, decimal_places=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.user.username} - {self.amount}đ - {self.get_status_display()}"