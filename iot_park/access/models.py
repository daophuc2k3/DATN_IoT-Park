from django.db import models
from django.contrib.auth.models import User
import uuid

class AccessHistory(models.Model):
    uid = models.CharField(max_length=16, unique=True, editable=False, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    license_plate = models.CharField(max_length=20, blank=True, null=True)
    rfid_code = models.CharField(max_length=64, blank=True, null=True)

    check_in = models.DateTimeField()
    check_out = models.DateTimeField(blank=True, null=True)
    fee = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-check_in']
        verbose_name = "Lịch sử ra vào"
        verbose_name_plural = "Lịch sử ra vào"

    def __str__(self):
        return f"{self.get_license_plate_display()} | {self.check_in.strftime('%H:%M %d/%m')}"

    def get_license_plate_display(self):
        if self.user and hasattr(self.user, 'profile'):
            return self.user.profile.license_plate or 'Không rõ'
        return self.license_plate or 'Chưa có biển số'

    def duration_minutes(self):
        if self.check_out and self.check_in:
            delta = self.check_out - self.check_in
            return int(delta.total_seconds() // 60)
        return None

    def save(self, *args, **kwargs):
        if not self.uid:
            self.uid = uuid.uuid4().hex[:12].upper()  # Ví dụ: '9F1D2C3A4B5E'
        super().save(*args, **kwargs)
