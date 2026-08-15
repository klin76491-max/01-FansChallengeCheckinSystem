"""
粉絲挑戰打卡系統 - 後台管理介面
根據 SD 文件 Section 7 定義
"""

from django.contrib import admin
from .models import Challenge, Participant, CheckIn


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'challenge_type', 'start_at', 'end_at',
        'points_per_checkin', 'bonus_for_streak', 'is_active'
    )
    list_filter = ('challenge_type', 'is_active')
    search_fields = ('title', 'description')
    list_editable = ('is_active',)
    ordering = ('-start_at',)


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'challenge', 'current_streak', 'total_points',
        'status', 'joined_at'
    )
    list_filter = ('status', 'challenge')
    search_fields = ('user__username', 'user__email', 'challenge__title')
    readonly_fields = ('current_streak', 'total_points', 'joined_at', 'updated_at')


@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    list_display = ('user', 'challenge', 'check_in_date', 'score_earned', 'created_at')
    list_filter = ('challenge', 'check_in_date')
    search_fields = ('user__username', 'challenge__title')
    readonly_fields = ('user', 'challenge', 'check_in_date', 'score_earned', 'created_at')
