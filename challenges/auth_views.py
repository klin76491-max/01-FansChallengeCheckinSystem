"""
粉絲挑戰打卡系統 - 認證視圖
包含一般帳號註冊與 Google OAuth 2.0 授權登入流程
"""

from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView
from django.contrib import messages
from django.contrib.auth import login
from django.conf import settings
from .services import GoogleAuthService, GoogleAuthError


class SignUpView(TemplateView):
    """Google 快速註冊導向頁"""
    template_name = 'accounts/signup.html'



class GoogleLoginView(View):
    """導向 Google OAuth 2.0 登入授權頁面"""

    def get(self, request):
        try:
            auth_url = GoogleAuthService.get_auth_url()
            return redirect(auth_url)
        except GoogleAuthError as e:
            messages.error(request, f"Google 登入暫時不可用：{str(e)}")
            return redirect('login')


class GoogleCallbackView(View):
    """接收 Google OAuth 2.0 回傳的 Authorization Code 並進行登入"""

    def get(self, request):
        code = request.GET.get('code')
        error = request.GET.get('error')

        if error:
            messages.error(request, f"Google 授權失敗：{error}")
            return redirect('login')

        if not code:
            messages.error(request, "未收到 Google 授權碼，登入失敗。")
            return redirect('login')

        try:
            # 1. 交換 Token
            token_data = GoogleAuthService.exchange_code_for_token(code)
            access_token = token_data.get('access_token')

            if not access_token:
                messages.error(request, "無法取得 Google 授權憑證。")
                return redirect('login')

            # 2. 獲取使用者個人資料
            profile = GoogleAuthService.get_user_profile(access_token)

            # 3. 建立或同步使用者帳號
            user = GoogleAuthService.get_or_create_google_user(profile)

            # 4. 登入 Django Session
            login(request, user)
            messages.success(request, f"歡迎回來，{user.first_name or user.username}！已成功使用 Google 帳號登入。")

            redirect_url = getattr(settings, 'LOGIN_REDIRECT_URL', '/challenges/')
            return redirect(redirect_url)

        except GoogleAuthError as e:
            messages.error(request, f"Google 登入失敗：{str(e)}")
            return redirect('login')
        except Exception as e:
            messages.error(request, "登入處理發生未預期錯誤，請稍後再試。")
            return redirect('login')

