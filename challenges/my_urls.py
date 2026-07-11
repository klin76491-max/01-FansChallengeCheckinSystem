"""
粉絲挑戰打卡系統 - 我的挑戰路由
"""

from django.urls import path
from .views import MyChallengeListView

urlpatterns = [
    path('', MyChallengeListView.as_view(), name='my-challenges'),
]
