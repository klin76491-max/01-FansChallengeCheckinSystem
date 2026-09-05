"""
粉絲挑戰打卡系統 - 資料模型
根據 SD 文件 Section 1 (ERD) 與 Section 2 (資料庫模式) 定義

模型清單：
- Challenge: 挑戰活動
- Participant: 參與者紀錄 (使用者 × 挑戰的多對多關聯)
- CheckIn: 打卡明細紀錄
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Challenge(models.Model):
    """挑戰活動模型"""

    TYPE_CHOICES = [
        ('daily', '每日挑戰'),
        ('weekly', '每週挑戰'),
    ]

    title = models.CharField('挑戰標題', max_length=100, db_index=True)
    description = models.TextField('挑戰說明')
    challenge_type = models.CharField(
        '挑戰類型', max_length=20, choices=TYPE_CHOICES, default='daily'
    )
    start_at = models.DateTimeField('開始時間')
    end_at = models.DateTimeField('結束時間')
    is_active = models.BooleanField('是否進行中', default=True, db_index=True)
    share_enabled = models.BooleanField('啟用分享', default=True)
    points_per_checkin = models.PositiveIntegerField('每次打卡基礎分數', default=10)
    bonus_for_streak = models.PositiveIntegerField('連續打卡額外加分', default=5)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_challenges', verbose_name='建立者'
    )
    created_at = models.DateTimeField('建立時間', auto_now_add=True)
    updated_at = models.DateTimeField('更新時間', auto_now=True)

    class Meta:
        verbose_name = '挑戰活動'
        verbose_name_plural = '挑戰活動清單'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def is_currently_running(self):
        """判斷挑戰是否正在進行中 (啟用且在時間範圍內)"""
        now = timezone.now()
        return self.is_active and (self.start_at <= now <= self.end_at)

    @property
    def is_upcoming(self):
        """判斷挑戰是否即將開始"""
        now = timezone.now()
        return self.is_active and now < self.start_at

    @property
    def is_ended(self):
        """判斷挑戰是否已結束"""
        return timezone.now() > self.end_at


class Participant(models.Model):
    """參與者紀錄模型 - 記錄使用者在特定挑戰中的總體進度"""

    STATUS_CHOICES = [
        ('active', '進行中'),
        ('completed', '已完成'),
        ('left', '已退出'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='challenge_participations', verbose_name='使用者'
    )
    challenge = models.ForeignKey(
        Challenge, on_delete=models.CASCADE,
        related_name='participants', verbose_name='挑戰活動'
    )
    current_streak = models.PositiveIntegerField('當前連續打卡天數', default=0)
    total_points = models.PositiveIntegerField('總累積積分', default=0, db_index=True)
    status = models.CharField(
        '狀態', max_length=20, choices=STATUS_CHOICES, default='active'
    )
    joined_at = models.DateTimeField('加入時間', auto_now_add=True)
    updated_at = models.DateTimeField('更新時間', auto_now=True)

    class Meta:
        verbose_name = '參與紀錄'
        verbose_name_plural = '參與紀錄名冊'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'challenge'],
                name='unique_user_challenge_participant'
            )
        ]
        ordering = ['-total_points', '-current_streak']

    def __str__(self):
        return f"{self.user.username} - {self.challenge.title}"


class CheckIn(models.Model):
    """打卡紀錄模型 - 記錄使用者每日打卡的明細"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='checkins', verbose_name='使用者'
    )
    challenge = models.ForeignKey(
        Challenge, on_delete=models.CASCADE,
        related_name='checkins', verbose_name='挑戰活動'
    )
    check_in_date = models.DateField('打卡所屬日期', db_index=True)
    score_earned = models.PositiveIntegerField('本次獲得積分', default=0)
    created_at = models.DateTimeField('打卡時間', auto_now_add=True)

    class Meta:
        verbose_name = '打卡紀錄'
        verbose_name_plural = '打卡紀錄明細'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'challenge', 'check_in_date'],
                name='unique_daily_user_challenge_checkin'
            )
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} @ {self.challenge.title} ({self.check_in_date})"
