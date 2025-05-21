from django.db import models

class Camera(models.Model):
    CAMERA_TYPE_CHOICES = [
        ('entry', 'Cổng vào'),
        ('exit', 'Cổng ra'),
    ]

    camera_name = models.CharField(
        max_length=100,
        verbose_name="Tên camera"
    )
    stream_url = models.URLField(
        verbose_name="URL stream",
        help_text="Nhập URL (ví dụ: rtsp://..., http://...)"
    )
    camera_type = models.CharField(
        max_length=5,
        choices=CAMERA_TYPE_CHOICES,
        verbose_name="Chức năng",
        help_text="Chọn cổng vào hoặc cổng ra"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Đang hoạt động"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Thời điểm thêm"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Cập nhật lần cuối"
    )

    def __str__(self):
        return f"{self.camera_name} ({self.get_camera_type_display()})"
