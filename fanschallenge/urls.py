"""
URL configuration for fanschallenge project.
"""

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('challenges.auth_urls')),
    path('challenges/', include('challenges.urls')),
    path('my-challenges/', include('challenges.my_urls')),
    path('api/', include('challenges.api_urls')),
    path('', lambda request: redirect('challenge-list')),
]
