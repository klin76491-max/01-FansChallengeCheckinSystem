"""
粉絲挑戰打卡系統 - 認證相關路由 (登入/登出/註冊)
"""

from django.urls import path
from django.contrib.auth import views as auth_views
from .auth_views import SignUpView, GoogleLoginView, GoogleCallbackView, DevLoginView

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        redirect_authenticated_user=True,
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', SignUpView.as_view(), name='signup'),
    
    # Google OAuth 2.0 路由
    path('google/login/', GoogleLoginView.as_view(), name='google_login'),
    path('google/callback/', GoogleCallbackView.as_view(), name='google_callback'),
    path('dev-login/', DevLoginView.as_view(), name='dev_login'),
]


