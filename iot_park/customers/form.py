from django import forms
from django.core.exceptions import ValidationError
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

    # def check_license_plate(self):
    #     license_plate = self.cleaned_data.get('license_plate')
    #     if Profile.objects.exclude(pk=self.instance.pk).filter(license_plate=license_plate).exists():
    #         return False
    #     return True
    
    # def check_phone(self):
    #     phone = self.cleaned_data.get('phone')
    #     if Profile.objects.exclude(pk=self.instance.pk).filter(phone=phone).exists():
    #         return False
    #     return True