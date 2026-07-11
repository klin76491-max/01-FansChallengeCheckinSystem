"""
粉絲挑戰打卡系統 - 挑戰頁面路由
"""

from django.urls import path
from .views import ChallengeListView, ChallengeDetailView, LeaderboardView

urlpatterns = [
    path('', ChallengeListView.as_view(), name='challenge-list'),
    path('<int:pk>/', ChallengeDetailView.as_view(), name='challenge-detail'),
    path('<int:pk>/leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
]
