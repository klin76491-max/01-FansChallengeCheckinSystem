"""
粉絲挑戰打卡系統 - 表單定義
根據 SD 文件 Section 0.2 表單驗證範例
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Challenge


class CustomUserCreationForm(UserCreationForm):
    """自訂註冊表單，增加 email 欄位並驗證唯一性"""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': '請輸入電子郵件',
            'autocomplete': 'email',
        })
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 為所有欄位統一套用樣式
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-input'})
        self.fields['username'].widget.attrs['placeholder'] = '使用者名稱'
        self.fields['username'].widget.attrs['autocomplete'] = 'username'
        self.fields['password1'].widget.attrs['placeholder'] = '密碼'
        self.fields['password1'].widget.attrs['autocomplete'] = 'new-password'
        self.fields['password2'].widget.attrs['placeholder'] = '確認密碼'
        self.fields['password2'].widget.attrs['autocomplete'] = 'new-password'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('此電子郵件已被註冊。')
        return email


class ChallengeCreateForm(forms.ModelForm):
    """使用者自行建立挑戰表單"""

    class Meta:
        model = Challenge
        fields = [
            'title', 'description', 'challenge_type',
            'start_at', 'end_at', 'points_per_checkin',
            'bonus_for_streak', 'share_enabled'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '例如：14 天英語口說打卡挑戰',
                'required': True,
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 4,
                'placeholder': '請輸入挑戰規則、每日打卡目標與獎勵說明...',
                'required': True,
            }),
            'challenge_type': forms.Select(attrs={
                'class': 'form-input',
            }),
            'start_at': forms.DateTimeInput(attrs={
                'class': 'form-input',
                'type': 'datetime-local',
                'required': True,
            }),
            'end_at': forms.DateTimeInput(attrs={
                'class': 'form-input',
                'type': 'datetime-local',
                'required': True,
            }),
            'points_per_checkin': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 1,
                'max': 1000,
            }),
            'bonus_for_streak': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 0,
                'max': 500,
            }),
            'share_enabled': forms.CheckboxInput(attrs={
                'class': 'form-checkbox',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get('points_per_checkin'):
            self.initial['points_per_checkin'] = 10
        if not self.initial.get('bonus_for_streak'):
            self.initial['bonus_for_streak'] = 5
        if 'share_enabled' not in self.initial:
            self.initial['share_enabled'] = True

    def clean(self):
        cleaned_data = super().clean()
        start_at = cleaned_data.get('start_at')
        end_at = cleaned_data.get('end_at')

        if start_at and end_at:
            if start_at >= end_at:
                raise ValidationError('結束時間必須晚於開始時間。')

        return cleaned_data

