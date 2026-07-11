"""
粉絲挑戰打卡系統 - JSON API 路由
"""

from django.urls import path
from .api_views import join_challenge_api, checkin_api

urlpatterns = [
    path('challenges/<int:challenge_id>/join/', join_challenge_api, name='api-join'),
    path('challenges/<int:challenge_id>/checkin/', checkin_api, name='api-checkin'),
]
