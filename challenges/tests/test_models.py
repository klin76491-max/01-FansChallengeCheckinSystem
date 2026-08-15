"""
粉絲挑戰打卡系統 - 資料模型測試
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from challenges.models import Challenge, Participant, CheckIn


class ChallengeModelTestCase(TestCase):
    """Challenge 模型測試"""

    def setUp(self):
        now = timezone.now()
        self.active_challenge = Challenge.objects.create(
            title='測試進行中挑戰',
            description='這是一個測試用挑戰',
            challenge_type='daily',
            start_at=now - timedelta(days=1),
            end_at=now + timedelta(days=7),
            is_active=True,
            points_per_checkin=10,
            bonus_for_streak=5,
        )
        self.ended_challenge = Challenge.objects.create(
            title='測試已結束挑戰',
            description='這是一個已結束的挑戰',
            challenge_type='daily',
            start_at=now - timedelta(days=14),
            end_at=now - timedelta(days=1),
            is_active=True,
            points_per_checkin=10,
            bonus_for_streak=5,
        )
        self.upcoming_challenge = Challenge.objects.create(
            title='測試即將開始挑戰',
            description='這是一個即將開始的挑戰',
            challenge_type='weekly',
            start_at=now + timedelta(days=1),
            end_at=now + timedelta(days=14),
            is_active=True,
            points_per_checkin=10,
            bonus_for_streak=5,
        )

    def test_is_currently_running_active(self):
        """測試進行中的挑戰回傳 True"""
        self.assertTrue(self.active_challenge.is_currently_running())

    def test_is_currently_running_ended(self):
        """測試已結束的挑戰回傳 False"""
        self.assertFalse(self.ended_challenge.is_currently_running())

    def test_is_currently_running_inactive(self):
        """測試停用的挑戰回傳 False"""
        self.active_challenge.is_active = False
        self.active_challenge.save()
        self.assertFalse(self.active_challenge.is_currently_running())

    def test_is_upcoming(self):
        """測試即將開始的挑戰"""
        self.assertTrue(self.upcoming_challenge.is_upcoming)
        self.assertFalse(self.active_challenge.is_upcoming)

    def test_is_ended(self):
        """測試已結束的挑戰"""
        self.assertTrue(self.ended_challenge.is_ended)
        self.assertFalse(self.active_challenge.is_ended)

    def test_str_representation(self):
        """測試模型字串表示"""
        self.assertEqual(str(self.active_challenge), '測試進行中挑戰')


class ParticipantModelTestCase(TestCase):
    """Participant 模型測試"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        now = timezone.now()
        self.challenge = Challenge.objects.create(
            title='測試挑戰',
            description='描述',
            start_at=now - timedelta(days=1),
            end_at=now + timedelta(days=7),
        )

    def test_create_participant(self):
        """測試建立參與者"""
        p = Participant.objects.create(user=self.user, challenge=self.challenge)
        self.assertEqual(p.current_streak, 0)
        self.assertEqual(p.total_points, 0)
        self.assertEqual(p.status, 'active')

    def test_unique_constraint(self):
        """測試同一使用者不能重複加入同一挑戰"""
        from django.db import IntegrityError
        Participant.objects.create(user=self.user, challenge=self.challenge)
        with self.assertRaises(IntegrityError):
            Participant.objects.create(user=self.user, challenge=self.challenge)

    def test_str_representation(self):
        """測試模型字串表示"""
        p = Participant.objects.create(user=self.user, challenge=self.challenge)
        self.assertEqual(str(p), 'testuser - 測試挑戰')


class CheckInModelTestCase(TestCase):
    """CheckIn 模型測試"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        now = timezone.now()
        self.challenge = Challenge.objects.create(
            title='測試挑戰',
            description='描述',
            start_at=now - timedelta(days=1),
            end_at=now + timedelta(days=7),
        )

    def test_create_checkin(self):
        """測試建立打卡紀錄"""
        today = timezone.localdate()
        ci = CheckIn.objects.create(
            user=self.user,
            challenge=self.challenge,
            check_in_date=today,
            score_earned=15,
        )
        self.assertEqual(ci.score_earned, 15)
        self.assertEqual(ci.check_in_date, today)

    def test_unique_daily_constraint(self):
        """測試同日同挑戰不能重複打卡 (DB 層)"""
        from django.db import IntegrityError
        today = timezone.localdate()
        CheckIn.objects.create(user=self.user, challenge=self.challenge, check_in_date=today)
        with self.assertRaises(IntegrityError):
            CheckIn.objects.create(user=self.user, challenge=self.challenge, check_in_date=today)
