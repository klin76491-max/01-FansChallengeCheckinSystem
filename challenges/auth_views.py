"""
粉絲挑戰打卡系統 - 認證視圖
"""

from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import SignUpForm


class SignUpView(CreateView):
    """註冊頁面"""
    form_class = SignUpForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')
