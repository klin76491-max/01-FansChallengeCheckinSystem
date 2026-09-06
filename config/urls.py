"""
URL configuration for 粉絲挑戰打卡系統 (Fans Challenge Check-in System).

根據 SA 文件 Section 5.1 頁面路由與 Controller 對應
"""

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('challenges/i18n/', include('django.conf.urls.i18n')),
    path('accounts/', include('challenges.auth_urls')),
    path('challenges/accounts/', include('challenges.auth_urls')),
    path('challenges/', include('challenges.urls')),
    path('', lambda request: redirect('challenges:list')),
]

