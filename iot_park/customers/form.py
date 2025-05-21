from django import forms
from .models import Profile

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['full_name', 'phone', 'license_plate', 'balance']
        labels = {
            'full_name': 'Họ và tên',
            'phone': 'Số điện thoại',
            'license_plate': 'Biển số xe',
            'balance': 'Số dư (VNĐ)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['balance'].disabled = True  # không cho chỉnh sửa số dư
