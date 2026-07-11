"""
粉絲挑戰打卡系統 - 核心邏輯測試 (Unit Tests)
根據 SD 文件 Section 10 定義
"""

import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Challenge, Participant, CheckIn


class CheckInAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')
        
        # 建立一個正在進行中的挑戰
        now = timezone.now()
        self.challenge = Challenge.objects.create(
            title='測試每日挑戰',
            description='這是一個測試用的挑戰',
            challenge_type='daily',
            start_at=now - timezone.timedelta(days=1),
            end_at=now + timezone.timedelta(days=7),
            is_active=True,
            points_per_checkin=10,
            bonus_for_streak=5,
        )
        
        # 使用者加入挑戰
        self.participant = Participant.objects.create(
            user=self.user,
            challenge=self.challenge
        )
        
        self.checkin_url = reverse('api-checkin', kwargs={'challenge_id': self.challenge.id})

    def test_normal_checkin(self):
        """測試：正常打卡"""
        self.client.login(username='testuser', password='password123')
        response = self.client.post(self.checkin_url)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['score_earned'], 10)  # 基本分 10
        self.assertEqual(data['new_streak'], 1)     # 第一天打卡，連續天數為 1
        self.assertEqual(data['new_total'], 10)     # 總分為 10
        
        # 驗證資料庫是否正確寫入
        self.assertTrue(CheckIn.objects.filter(user=self.user, challenge=self.challenge).exists())
        
        # 驗證 Participant 是否更新
        self.participant.refresh_from_db()
        self.assertEqual(self.participant.current_streak, 1)
        self.assertEqual(self.participant.total_points, 10)

    def test_duplicate_checkin_prevention(self):
        """測試：重複打卡防呆"""
        # 第一天打卡
        self.client.login(username='testuser', password='password123')
        self.client.post(self.checkin_url)
        
        # 重複打卡
        response = self.client.post(self.checkin_url)
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], '今日已打卡，明天再來吧！')
        
        # 驗證資料庫中是否只有一筆紀錄
        self.assertEqual(CheckIn.objects.filter(user=self.user, challenge=self.challenge).count(), 1)

    def test_consecutive_checkin_bonus(self):
        """測試：跨日連續打卡加分是否正確"""
        # 手動建立「昨日」的打卡紀錄
        yesterday = timezone.localdate() - timezone.timedelta(days=1)
        CheckIn.objects.create(
            user=self.user,
            challenge=self.challenge,
            check_in_date=yesterday,
            score_earned=10
        )
        # 更新 participant 狀態
        self.participant.current_streak = 1
        self.participant.total_points = 10
        self.participant.save()
        
        # 「今日」打卡
        self.client.login(username='testuser', password='password123')
        response = self.client.post(self.checkin_url)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['score_earned'], 15)  # 基本分 10 + 紅利 5
        self.assertEqual(data['new_streak'], 2)     # 連續天數 2
        self.assertEqual(data['new_total'], 25)     # 原有 10 + 本次 15 = 25
        
        # 驗證 Participant 更新
        self.participant.refresh_from_db()
        self.assertEqual(self.participant.current_streak, 2)
        self.assertEqual(self.participant.total_points, 25)

    def test_inactive_challenge_prevention(self):
        """測試：非活動期間打卡是否被阻擋"""
        # 暫時關閉挑戰
        self.challenge.is_active = False
        self.challenge.save()
        
        self.client.login(username='testuser', password='password123')
        response = self.client.post(self.checkin_url)
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], '此挑戰不在活動期間')
