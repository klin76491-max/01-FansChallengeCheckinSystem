"""
粉絲挑戰打卡系統 - 服務層測試 (CheckInService)
根據 SD 文件 Section 9 測試規範

測試案例：
1. test_join_challenge_success - 初次加入挑戰
2. test_perform_first_checkin - 首次打卡
3. test_prevent_duplicate_checkin_same_day - 重複打卡防呆
4. test_streak_increment_consecutive_day - 連續打卡 Streak 累加
5. test_streak_reset_after_missed_day - 斷更後 Streak 重置
6. test_checkin_inactive_challenge_fails - 非活動時間打卡阻擋
"""

from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from challenges.models import Challenge, Participant, CheckIn
from challenges.services import (
    CheckInService, CheckInError, DuplicateCheckInError, ChallengeInactiveError,
    GoogleAuthService, GoogleAuthError
)



class CheckInServiceTestCase(TestCase):
    """CheckInService 核心業務邏輯測試"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='password123'
        )
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

    def test_join_challenge_success(self):
        """測試使用者初次加入挑戰"""
        participant, created = CheckInService.join_challenge(
            self.user, self.challenge.id
        )
        self.assertTrue(created)
        self.assertEqual(participant.current_streak, 0)
        self.assertEqual(participant.total_points, 0)
        self.assertEqual(participant.status, 'active')

    def test_join_challenge_duplicate(self):
        """測試重複加入挑戰不會拋出錯誤"""
        CheckInService.join_challenge(self.user, self.challenge.id)
        participant, created = CheckInService.join_challenge(
            self.user, self.challenge.id
        )
        self.assertFalse(created)

    def test_join_challenge_inactive(self):
        """測試加入非活動挑戰拋出 ChallengeInactiveError"""
        self.challenge.is_active = False
        self.challenge.save()
        with self.assertRaises(ChallengeInactiveError):
            CheckInService.join_challenge(self.user, self.challenge.id)

    def test_join_challenge_not_found(self):
        """測試加入不存在的挑戰拋出 CheckInError"""
        with self.assertRaises(CheckInError):
            CheckInService.join_challenge(self.user, 99999)

    def test_perform_first_checkin(self):
        """測試首次打卡：獲得基本分 10，streak 變為 1"""
        Participant.objects.create(user=self.user, challenge=self.challenge)

        result = CheckInService.perform_checkin(self.user, self.challenge.id)

        self.assertTrue(result['success'])
        self.assertEqual(result['score_earned'], 10)  # 基本分
        self.assertEqual(result['new_streak'], 1)      # 首次打卡 streak=1
        self.assertEqual(result['total_points'], 10)

        # 驗證資料庫
        participant = Participant.objects.get(user=self.user, challenge=self.challenge)
        self.assertEqual(participant.current_streak, 1)
        self.assertEqual(participant.total_points, 10)
        self.assertTrue(CheckIn.objects.filter(
            user=self.user, challenge=self.challenge
        ).exists())

    def test_prevent_duplicate_checkin_same_day(self):
        """測試同日第二次打卡拋出 DuplicateCheckInError"""
        Participant.objects.create(user=self.user, challenge=self.challenge)

        # 第一次打卡
        CheckInService.perform_checkin(self.user, self.challenge.id)

        # 第二次打卡應被阻擋
        with self.assertRaises(DuplicateCheckInError):
            CheckInService.perform_checkin(self.user, self.challenge.id)

        # 確認分數未重複累加
        participant = Participant.objects.get(user=self.user, challenge=self.challenge)
        self.assertEqual(participant.total_points, 10)
        self.assertEqual(
            CheckIn.objects.filter(user=self.user, challenge=self.challenge).count(), 1
        )

    def test_streak_increment_consecutive_day(self):
        """測試連續打卡：昨日有打卡，今日 streak 累加且獲得連擊加分"""
        participant = Participant.objects.create(
            user=self.user, challenge=self.challenge,
            current_streak=1, total_points=10
        )

        # 手動建立昨日打卡紀錄
        yesterday = timezone.localdate() - timedelta(days=1)
        CheckIn.objects.create(
            user=self.user, challenge=self.challenge,
            check_in_date=yesterday, score_earned=10
        )

        # 今日打卡
        result = CheckInService.perform_checkin(self.user, self.challenge.id)

        self.assertTrue(result['success'])
        self.assertEqual(result['score_earned'], 15)   # 基本 10 + 連擊 5
        self.assertEqual(result['new_streak'], 2)       # streak 1 → 2
        self.assertEqual(result['total_points'], 25)    # 原有 10 + 本次 15

        # 驗證資料庫
        participant.refresh_from_db()
        self.assertEqual(participant.current_streak, 2)
        self.assertEqual(participant.total_points, 25)

    def test_streak_reset_after_missed_day(self):
        """測試斷更：前天打卡但昨日未打卡，streak 重置為 1"""
        participant = Participant.objects.create(
            user=self.user, challenge=self.challenge,
            current_streak=5, total_points=75
        )

        # 手動建立「前天」的打卡紀錄 (但昨日沒有)
        day_before_yesterday = timezone.localdate() - timedelta(days=2)
        CheckIn.objects.create(
            user=self.user, challenge=self.challenge,
            check_in_date=day_before_yesterday, score_earned=15
        )

        # 今日打卡
        result = CheckInService.perform_checkin(self.user, self.challenge.id)

        self.assertTrue(result['success'])
        self.assertEqual(result['score_earned'], 10)   # 僅基本分 (無連擊)
        self.assertEqual(result['new_streak'], 1)       # streak 重置為 1
        self.assertEqual(result['total_points'], 85)    # 原有 75 + 本次 10

        participant.refresh_from_db()
        self.assertEqual(participant.current_streak, 1)

    def test_checkin_inactive_challenge_fails(self):
        """測試非活動時間打卡拋出 ChallengeInactiveError"""
        self.challenge.is_active = False
        self.challenge.save()
        Participant.objects.create(user=self.user, challenge=self.challenge)

        with self.assertRaises(ChallengeInactiveError):
            CheckInService.perform_checkin(self.user, self.challenge.id)

    def test_checkin_without_joining(self):
        """測試未加入挑戰就打卡拋出 CheckInError"""
        with self.assertRaises(CheckInError):
            CheckInService.perform_checkin(self.user, self.challenge.id)

    def test_checkin_nonexistent_challenge(self):
        """測試打卡不存在的挑戰拋出 CheckInError"""
        with self.assertRaises(CheckInError):
            CheckInService.perform_checkin(self.user, 99999)


@override_settings(
    GOOGLE_OAUTH_CLIENT_ID='test-client-id.apps.googleusercontent.com',
    GOOGLE_OAUTH_CLIENT_SECRET='test-client-secret',
    GOOGLE_REDIRECT_URI='http://127.0.0.1:8000/accounts/google/callback/'
)
class GoogleAuthServiceTestCase(TestCase):
    """GoogleAuthService 服務層測試"""

    def test_get_auth_url_success(self):
        """測試產生正確的 Google OAuth 授權網址"""
        url = GoogleAuthService.get_auth_url(state='test-state')
        self.assertIn('https://accounts.google.com/o/oauth2/v2/auth', url)
        self.assertIn('client_id=test-client-id.apps.googleusercontent.com', url)
        self.assertIn('state=test-state', url)
        self.assertIn('scope=openid+email+profile', url)

    @override_settings(GOOGLE_OAUTH_CLIENT_ID='')
    def test_get_auth_url_missing_client_id(self):
        """測試未設定 Client ID 拋出 GoogleAuthError"""
        with self.assertRaises(GoogleAuthError):
            GoogleAuthService.get_auth_url()

    @patch('challenges.services.requests.post')
    def test_exchange_code_for_token_success(self, mock_post):
        """測試成功使用授權碼交換 Token"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'access_token': 'mock-access-token-123'}
        mock_post.return_value = mock_resp

        result = GoogleAuthService.exchange_code_for_token('test-auth-code')
        self.assertEqual(result['access_token'], 'mock-access-token-123')

    @patch('challenges.services.requests.get')
    def test_get_user_profile_success(self, mock_get):
        """測試成功取得 Google 使用者個人資料"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'email': 'googleuser@example.com',
            'name': 'Google User',
            'given_name': 'Google',
            'family_name': 'User'
        }
        mock_get.return_value = mock_resp

        profile = GoogleAuthService.get_user_profile('mock-access-token')
        self.assertEqual(profile['email'], 'googleuser@example.com')
        self.assertEqual(profile['name'], 'Google User')

    def test_get_or_create_google_user_new(self):
        """測試透過 Google Profile 建立新使用者"""
        profile = {
            'email': 'newgoogle@example.com',
            'name': 'New Student',
            'given_name': 'New',
            'family_name': 'Student'
        }
        user = GoogleAuthService.get_or_create_google_user(profile)
        self.assertEqual(user.email, 'newgoogle@example.com')
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.last_name, 'Student')
        self.assertFalse(user.has_usable_password())

    def test_get_or_create_google_user_existing(self):
        """測試透過 Google Profile 同步既有使用者"""
        existing_user = User.objects.create_user(
            username='existing', email='existing@example.com', first_name='OldName'
        )
        profile = {
            'email': 'existing@example.com',
            'name': 'Updated Name',
            'given_name': 'Updated',
            'family_name': 'Name'
        }
        user = GoogleAuthService.get_or_create_google_user(profile)
        self.assertEqual(user.id, existing_user.id)
        self.assertEqual(user.first_name, 'Updated')

