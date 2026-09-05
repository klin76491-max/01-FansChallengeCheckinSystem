"""
粉絲挑戰打卡系統 - 視圖與 API 端點測試
"""

import json
from unittest.mock import patch
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from challenges.models import Challenge, Participant, CheckIn



class PageViewTestCase(TestCase):
    """頁面視圖存取測試"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')
        now = timezone.now()
        self.challenge = Challenge.objects.create(
            title='測試挑戰',
            description='測試用挑戰描述',
            start_at=now - timedelta(days=1),
            end_at=now + timedelta(days=7),
            is_active=True,
        )

    def test_challenge_list_public(self):
        """測試挑戰列表頁公開存取"""
        response = self.client.get(reverse('challenges:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '測試挑戰')

    def test_challenge_detail_public(self):
        """測試挑戰詳情頁公開存取"""
        response = self.client.get(
            reverse('challenges:detail', kwargs={'pk': self.challenge.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '測試挑戰')

    def test_leaderboard_public(self):
        """測試排行榜頁公開存取"""
        response = self.client.get(
            reverse('challenges:leaderboard', kwargs={'pk': self.challenge.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_my_challenges_requires_login(self):
        """測試我的挑戰頁需要登入"""
        response = self.client.get(reverse('challenges:my_challenges'))
        self.assertEqual(response.status_code, 302)  # 重定向至登入頁

    def test_my_challenges_authenticated(self):
        """測試已登入使用者存取我的挑戰頁"""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('challenges:my_challenges'))
        self.assertEqual(response.status_code, 200)


class CheckInAPITestCase(TestCase):
    """打卡 API 端點測試"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')
        now = timezone.now()
        self.challenge = Challenge.objects.create(
            title='測試每日挑戰',
            description='這是一個測試用的挑戰',
            challenge_type='daily',
            start_at=now - timedelta(days=1),
            end_at=now + timedelta(days=7),
            is_active=True,
            points_per_checkin=10,
            bonus_for_streak=5,
        )
        self.participant = Participant.objects.create(
            user=self.user, challenge=self.challenge
        )
        self.checkin_url = reverse(
            'challenges:api_checkin',
            kwargs={'challenge_id': self.challenge.id}
        )
        self.join_url = reverse(
            'challenges:api_join',
            kwargs={'challenge_id': self.challenge.id}
        )

    def test_checkin_success(self):
        """測試正常打卡 API"""
        self.client.login(username='testuser', password='password123')
        response = self.client.post(self.checkin_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['score_earned'], 10)
        self.assertEqual(data['new_streak'], 1)
        self.assertEqual(data['total_points'], 10)

    def test_checkin_duplicate_prevention(self):
        """測試重複打卡 API 防呆"""
        self.client.login(username='testuser', password='password123')
        self.client.post(self.checkin_url)

        response = self.client.post(self.checkin_url)
        self.assertEqual(response.status_code, 400)

        data = json.loads(response.content)
        self.assertFalse(data['success'])

    def test_checkin_consecutive_bonus(self):
        """測試連續打卡 API 加分"""
        yesterday = timezone.localdate() - timedelta(days=1)
        CheckIn.objects.create(
            user=self.user, challenge=self.challenge,
            check_in_date=yesterday, score_earned=10
        )
        self.participant.current_streak = 1
        self.participant.total_points = 10
        self.participant.save()

        self.client.login(username='testuser', password='password123')
        response = self.client.post(self.checkin_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['score_earned'], 15)
        self.assertEqual(data['new_streak'], 2)
        self.assertEqual(data['total_points'], 25)

    def test_checkin_inactive_challenge(self):
        """測試非活動挑戰 API 打卡"""
        self.challenge.is_active = False
        self.challenge.save()

        self.client.login(username='testuser', password='password123')
        response = self.client.post(self.checkin_url)
        self.assertEqual(response.status_code, 400)

    def test_checkin_requires_login(self):
        """測試未登入打卡被拒"""
        response = self.client.post(self.checkin_url)
        self.assertEqual(response.status_code, 302)  # 重定向至登入


class JoinChallengeAPITestCase(TestCase):
    """加入挑戰 API 端點測試"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')
        now = timezone.now()
        self.challenge = Challenge.objects.create(
            title='測試挑戰',
            description='描述',
            start_at=now - timedelta(days=1),
            end_at=now + timedelta(days=7),
            is_active=True,
        )
        self.join_url = reverse(
            'challenges:api_join',
            kwargs={'challenge_id': self.challenge.id}
        )

    def test_join_success(self):
        """測試成功加入挑戰"""
        self.client.login(username='testuser', password='password123')
        response = self.client.post(self.join_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertTrue(Participant.objects.filter(
            user=self.user, challenge=self.challenge
        ).exists())

    def test_join_duplicate(self):
        """測試重複加入挑戰"""
        Participant.objects.create(user=self.user, challenge=self.challenge)
        self.client.login(username='testuser', password='password123')
        response = self.client.post(self.join_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data['success'])  # 不報錯，回覆已是參與者

    def test_join_requires_login(self):
        """測試未登入加入被拒"""
        response = self.client.post(self.join_url)
        self.assertEqual(response.status_code, 302)


@override_settings(
    GOOGLE_OAUTH_CLIENT_ID='test-client-id.apps.googleusercontent.com',
    GOOGLE_OAUTH_CLIENT_SECRET='test-client-secret',
    GOOGLE_REDIRECT_URI='http://127.0.0.1:8000/accounts/google/callback/'
)
class GoogleOAuthViewsTestCase(TestCase):
    """Google OAuth 視圖測試"""

    def setUp(self):
        self.client = Client()

    def test_google_login_redirect(self):
        """測試點擊 Google 登入重導向至 Google 授權頁面"""
        response = self.client.get(reverse('google_login'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('https://accounts.google.com/o/oauth2/v2/auth', response.url)

    @override_settings(GOOGLE_OAUTH_CLIENT_ID='')
    def test_google_login_unconfigured(self):
        """測試未設定 Client ID 時優雅導回登入頁並提示訊息"""
        response = self.client.get(reverse('google_login'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Google 登入暫時不可用')

    def test_google_callback_with_error(self):
        """測試 Google 回傳 error 參數時導回登入頁"""
        response = self.client.get(reverse('google_callback') + '?error=access_denied', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Google 授權失敗')

    def test_google_callback_without_code(self):
        """測試未帶 code 訪問 callback 導回登入頁"""
        response = self.client.get(reverse('google_callback'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '未收到 Google 授權碼')

    @patch('challenges.services.GoogleAuthService.exchange_code_for_token')
    @patch('challenges.services.GoogleAuthService.get_user_profile')
    def test_google_callback_success(self, mock_profile, mock_token):
        """測試 Google OAuth 回傳正常 code 成功登入"""
        mock_token.return_value = {'access_token': 'test-access-token'}
        mock_profile.return_value = {
            'email': 'oauthuser@example.com',
            'name': 'OAuth Student',
            'given_name': 'OAuth',
            'family_name': 'Student'
        }

        response = self.client.get(reverse('google_callback') + '?code=valid-code', follow=True)
        self.assertEqual(response.status_code, 200)

        # 驗證使用者已在資料庫中建立
        self.assertTrue(User.objects.filter(email='oauthuser@example.com').exists())

        # 驗證使用者已處於登入狀態
        self.assertIn('_auth_user_id', self.client.session)


class ChallengeCreateAndGridTestCase(TestCase):
    """自訂挑戰建立與 14 天格子功能測試"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='creator', password='password123')
        self.now = timezone.now()

    def test_challenge_create_requires_login(self):
        """測試未登入建立挑戰重導向至登入頁"""
        response = self.client.get(reverse('challenges:create'))
        self.assertEqual(response.status_code, 302)

    def test_challenge_create_get_authenticated(self):
        """測試登入使用者存取建立挑戰頁面"""
        self.client.login(username='creator', password='password123')
        response = self.client.get(reverse('challenges:create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '建立專屬打卡挑戰')

    def test_challenge_create_post_success(self):
        """測試登入使用者成功發起挑戰，且自動加入該挑戰"""
        self.client.login(username='creator', password='password123')
        post_data = {
            'title': '14天英語新聞閱讀挑戰',
            'description': '每天閱讀一篇 BBC 英文新聞並打卡',
            'challenge_type': 'daily',
            'start_at': (self.now - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M'),
            'end_at': (self.now + timedelta(days=14)).strftime('%Y-%m-%dT%H:%M'),
            'points_per_checkin': 15,
            'bonus_for_streak': 8,
            'share_enabled': True,
        }
        response = self.client.post(reverse('challenges:create'), data=post_data, follow=True)
        self.assertEqual(response.status_code, 200)

        # 驗證挑戰已建立且 created_by 正確
        challenge = Challenge.objects.get(title='14天英語新聞閱讀挑戰')
        self.assertEqual(challenge.created_by, self.user)
        self.assertEqual(challenge.points_per_checkin, 15)

        # 驗證建立者自動被加入為參與者
        participant = Participant.objects.get(user=self.user, challenge=challenge)
        self.assertEqual(participant.current_streak, 0)

    def test_challenge_detail_14day_grid_rendering(self):
        """測試 14 天打卡格子 context 正確渲染與狀態標記"""
        challenge = Challenge.objects.create(
            title='14天閱讀挑戰',
            description='說明',
            start_at=self.now - timedelta(days=5),
            end_at=self.now + timedelta(days=9),
            is_active=True,
        )
        self.client.login(username='creator', password='password123')
        participant = Participant.objects.create(
            user=self.user,
            challenge=challenge,
            current_streak=2,
            total_points=20,
        )
        # 建立 2 筆過往打卡紀錄
        CheckIn.objects.create(
            user=self.user,
            challenge=challenge,
            check_in_date=timezone.localdate() - timedelta(days=2),
            score_earned=10
        )
        CheckIn.objects.create(
            user=self.user,
            challenge=challenge,
            check_in_date=timezone.localdate() - timedelta(days=1),
            score_earned=10
        )

        response = self.client.get(reverse('challenges:detail', kwargs={'pk': challenge.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['checkin_count'], 2)
        self.assertEqual(len(response.context['grid_days']), 14)
        # Day 1 & Day 2 completed
        self.assertTrue(response.context['grid_days'][0]['is_completed'])
        self.assertTrue(response.context['grid_days'][1]['is_completed'])
        # Day 3 is current (today's target)
        self.assertTrue(response.context['grid_days'][2]['is_current'])
        # Day 4 is locked
        self.assertTrue(response.context['grid_days'][3]['is_locked'])

    def test_checkin_api_returns_total_checkins(self):
        """測試打卡 API 回傳累計打卡總天數 total_checkins"""
        challenge = Challenge.objects.create(
            title='即時打卡挑戰',
            description='說明',
            start_at=self.now - timedelta(days=1),
            end_at=self.now + timedelta(days=13),
            is_active=True,
        )
        self.client.login(username='creator', password='password123')
        Participant.objects.create(user=self.user, challenge=challenge)

        response = self.client.post(reverse('challenges:api_checkin', kwargs={'challenge_id': challenge.id}))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['total_checkins'], 1)


