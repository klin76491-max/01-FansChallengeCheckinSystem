"""
粉絲挑戰打卡系統 - 表單定義
"""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class SignUpForm(UserCreationForm):
    """自訂註冊表單，增加 email 欄位"""

    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': '電子信箱',
            'autocomplete': 'email',
        }),
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': '使用者名稱',
            'autocomplete': 'username',
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': '密碼',
            'autocomplete': 'new-password',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': '確認密碼',
            'autocomplete': 'new-password',
        })
