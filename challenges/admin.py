"""
粉絲挑戰打卡系統 - 後台管理介面
根據 SD 文件 Section 7 定義
"""

from django.contrib import admin
from .models import Challenge, Participant, CheckIn


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ('title', 'challenge_type', 'start_at', 'end_at', 'is_active', 'points_per_checkin')
    list_filter = ('challenge_type', 'is_active')
    search_fields = ('title',)
    list_editable = ('is_active',)
    ordering = ('-start_at',)


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('user', 'challenge', 'joined_at', 'current_streak', 'total_points', 'status')
    list_filter = ('status', 'challenge')
    search_fields = ('user__username', 'challenge__title')
    readonly_fields = ('user', 'challenge', 'joined_at', 'current_streak', 'total_points')


@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    list_display = ('user', 'challenge', 'check_in_date', 'score_earned', 'created_at')
    list_filter = ('challenge', 'check_in_date')
    search_fields = ('user__username', 'challenge__title')
    readonly_fields = ('user', 'challenge', 'check_in_date', 'score_earned', 'created_at')
