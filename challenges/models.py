"""
粉絲挑戰打卡系統 - 資料模型
根據 SD 文件 Section 2 定義
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Challenge(models.Model):
    """挑戰 (Challenge) 模型"""

    CHALLENGE_TYPE_CHOICES = [
        ('daily', '每日挑戰'),
        ('weekly', '每週挑戰'),
    ]

    title = models.CharField('挑戰名稱', max_length=100)
    description = models.TextField('挑戰描述')
    challenge_type = models.CharField(
        '挑戰類型',
        max_length=10,
        choices=CHALLENGE_TYPE_CHOICES,
        default='daily',
    )
    start_at = models.DateTimeField('開始時間')
    end_at = models.DateTimeField('結束時間')
    is_active = models.BooleanField('是否啟用', default=True)
    share_enabled = models.BooleanField('允許分享', default=True)
    points_per_checkin = models.IntegerField('每次打卡基本分數', default=10)
    bonus_for_streak = models.IntegerField('連續打卡額外紅利', default=5)

    class Meta:
        verbose_name = '挑戰'
        verbose_name_plural = '挑戰列表'
        ordering = ['-start_at']

    def __str__(self):
        return self.title

    @property
    def is_ongoing(self):
        """判斷挑戰是否正在進行中"""
        now = timezone.now()
        return self.is_active and self.start_at <= now <= self.end_at

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
    """參與者紀錄 (Participant) 模型 - 記錄使用者在特定挑戰中的總體進度"""

    STATUS_CHOICES = [
        ('active', '進行中'),
        ('completed', '已完成'),
        ('dropped', '已退出'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='participations',
        verbose_name='使用者',
    )
    challenge = models.ForeignKey(
        Challenge,
        on_delete=models.CASCADE,
        related_name='participants',
        verbose_name='挑戰',
    )
    joined_at = models.DateTimeField('加入時間', auto_now_add=True)
    current_streak = models.IntegerField('目前連續打卡天數', default=0)
    total_points = models.IntegerField('總分', default=0)
    status = models.CharField(
        '狀態',
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
    )

    class Meta:
        verbose_name = '挑戰參與紀錄'
        verbose_name_plural = '挑戰參與紀錄'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'challenge'],
                name='unique_participant',
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.challenge.title}'


class CheckIn(models.Model):
    """打卡紀錄 (CheckIn) 模型 - 記錄使用者每日打卡的明細"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='checkins',
        verbose_name='使用者',
    )
    challenge = models.ForeignKey(
        Challenge,
        on_delete=models.CASCADE,
        related_name='checkins',
        verbose_name='挑戰',
    )
    check_in_date = models.DateField('打卡日期')
    created_at = models.DateTimeField('實際寫入時間', auto_now_add=True)
    score_earned = models.IntegerField('本次獲得分數', default=0)

    class Meta:
        verbose_name = '打卡紀錄'
        verbose_name_plural = '打卡紀錄'
        ordering = ['-check_in_date']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'challenge', 'check_in_date'],
                name='unique_daily_checkin',
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.challenge.title} ({self.check_in_date})'
