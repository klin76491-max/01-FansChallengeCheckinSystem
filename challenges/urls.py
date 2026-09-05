"""
粉絲挑戰打卡系統 - 挑戰相關路由與 API 端點
根據 SD 文件 Section 3.2 路由配置
"""

from django.urls import path
from . import views

app_name = 'challenges'

urlpatterns = [
    # 頁面視圖
    path('', views.ChallengeListView.as_view(), name='list'),
    path('create/', views.ChallengeCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ChallengeDetailView.as_view(), name='detail'),
    path('my-challenges/', views.MyChallengeListView.as_view(), name='my_challenges'),
    path('<int:pk>/leaderboard/', views.LeaderboardView.as_view(), name='leaderboard'),

    # AJAX API 端點
    path('api/<int:challenge_id>/join/', views.JoinChallengeAPIView.as_view(), name='api_join'),
    path('api/<int:challenge_id>/checkin/', views.CheckInAPIView.as_view(), name='api_checkin'),
]
