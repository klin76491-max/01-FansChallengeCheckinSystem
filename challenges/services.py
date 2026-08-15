"""
粉絲挑戰打卡系統 - 核心業務邏輯層
根據 SD 文件 Section 4 服務層設計

職責：
- 封裝打卡防呆、Streak 判定、分數累計邏輯
- 所有資料變更使用 transaction.atomic() 確保一致性
- 自訂業務異常類別提供明確錯誤回饋
"""

import requests
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from .models import Challenge, Participant, CheckIn


# ===== 自訂業務異常 =====

class CheckInError(Exception):
    """打卡相關基礎錯誤"""
    pass


class DuplicateCheckInError(CheckInError):
    """重複打卡錯誤"""
    pass


class ChallengeInactiveError(CheckInError):
    """挑戰非活動狀態錯誤"""
    pass


class GoogleAuthError(Exception):
    """Google OAuth 認證錯誤"""
    pass



# ===== 核心服務 =====

class CheckInService:
    """打卡核心業務服務"""

    @staticmethod
    def get_today_date():
        """獲取伺服器時區 (Asia/Taipei) 之今日日期"""
        return timezone.localdate()

    @classmethod
    def join_challenge(cls, user, challenge_id):
        """
        使用者加入挑戰

        Args:
            user: 當前登入使用者
            challenge_id: 挑戰 ID

        Returns:
            tuple: (participant, created) - 參與者實例與是否新建

        Raises:
            CheckInError: 挑戰不存在
            ChallengeInactiveError: 挑戰非進行中或已過期
        """
        try:
            challenge = Challenge.objects.get(id=challenge_id)
        except Challenge.DoesNotExist:
            raise CheckInError("挑戰不存在。")

        if not challenge.is_currently_running():
            raise ChallengeInactiveError("挑戰活動非進行中或已過期。")

        participant, created = Participant.objects.get_or_create(
            user=user,
            challenge=challenge,
            defaults={'current_streak': 0, 'total_points': 0, 'status': 'active'}
        )
        return participant, created

    @classmethod
    def perform_checkin(cls, user, challenge_id):
        """
        執行每日打卡核心邏輯 (具原子交易保護)

        流程 (根據 SA Section 4.2)：
        1. 驗證挑戰有效性
        2. 獲取參與者紀錄 (加鎖避免並發競爭)
        3. 防呆檢查：今日是否已打卡
        4. 計算連續天數 (Streak)
        5. 計算獲得分數
        6. 寫入打卡明細並更新參與者總體進度

        Args:
            user: 當前登入使用者
            challenge_id: 挑戰 ID

        Returns:
            dict: 包含 success, score_earned, new_streak, total_points, message

        Raises:
            CheckInError: 挑戰不存在或未加入
            ChallengeInactiveError: 不在開放打卡時間
            DuplicateCheckInError: 今日已打卡
        """
        today = cls.get_today_date()
        yesterday = today - timedelta(days=1)

        with transaction.atomic():
            # 1. 驗證挑戰有效性
            try:
                challenge = Challenge.objects.select_for_update().get(id=challenge_id)
            except Challenge.DoesNotExist:
                raise CheckInError("挑戰活動不存在。")

            if not challenge.is_currently_running():
                raise ChallengeInactiveError("該挑戰不在開放打卡的時間範圍內。")

            # 2. 獲取參與者紀錄 (加鎖避免並發競爭)
            try:
                participant = Participant.objects.select_for_update().get(
                    user=user, challenge=challenge
                )
            except Participant.DoesNotExist:
                raise CheckInError("請先加入挑戰後再進行打卡！")

            # 3. 防呆檢查：今日是否已打卡
            if CheckIn.objects.filter(
                user=user, challenge=challenge, check_in_date=today
            ).exists():
                raise DuplicateCheckInError("今日已經完成打卡囉，請勿重複提交！")

            # 4. 計算連續天數 (Streak)
            had_checkin_yesterday = CheckIn.objects.filter(
                user=user, challenge=challenge, check_in_date=yesterday
            ).exists()

            if had_checkin_yesterday:
                new_streak = participant.current_streak + 1
            else:
                new_streak = 1  # 斷更或首次打卡重置為 1

            # 5. 計算獲得分數
            earned_points = challenge.points_per_checkin
            if new_streak > 1:
                earned_points += challenge.bonus_for_streak

            # 6. 寫入打卡明細並更新參與者總體進度
            CheckIn.objects.create(
                user=user,
                challenge=challenge,
                check_in_date=today,
                score_earned=earned_points
            )

            participant.current_streak = new_streak
            participant.total_points += earned_points
            participant.save(update_fields=['current_streak', 'total_points', 'updated_at'])

            return {
                'success': True,
                'score_earned': earned_points,
                'new_streak': new_streak,
                'total_points': participant.total_points,
                'message': f"打卡成功！獲得 {earned_points} 積分，連續打卡 {new_streak} 天！"
            }


class GoogleAuthService:
    """Google OAuth 2.0 認證與使用者同步服務"""

    @staticmethod
    def get_auth_url(state: str = None) -> str:
        """產生 Google OAuth 登入重導向 URL"""
        client_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', '')
        redirect_uri = getattr(settings, 'GOOGLE_REDIRECT_URI', '')
        auth_url = getattr(settings, 'GOOGLE_AUTH_URL', 'https://accounts.google.com/o/oauth2/v2/auth')

        if not client_id:
            raise GoogleAuthError("未設定 GOOGLE_OAUTH_CLIENT_ID，請在環境變數或後台配置。")

        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'access_type': 'online',
            'prompt': 'select_account',
        }
        if state:
            params['state'] = state

        from urllib.parse import urlencode
        return f"{auth_url}?{urlencode(params)}"

    @staticmethod
    def exchange_code_for_token(code: str) -> dict:
        """向 Google 伺服器使用 Authorization Code 交換 Access Token"""
        client_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', '')
        client_secret = getattr(settings, 'GOOGLE_OAUTH_CLIENT_SECRET', '')
        redirect_uri = getattr(settings, 'GOOGLE_REDIRECT_URI', '')
        token_url = getattr(settings, 'GOOGLE_TOKEN_URL', 'https://oauth2.googleapis.com/token')

        if not client_id or not client_secret:
            raise GoogleAuthError("Google OAuth Client ID 或 Secret 尚未設定。")

        try:
            resp = requests.post(
                token_url,
                data={
                    'code': code,
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'redirect_uri': redirect_uri,
                    'grant_type': 'authorization_code',
                },
                timeout=10
            )
            if resp.status_code != 200:
                raise GoogleAuthError(f"Google Token 交換失敗: {resp.text}")
            return resp.json()
        except requests.RequestException as e:
            raise GoogleAuthError(f"連線至 Google 認證伺服器失敗: {str(e)}")

    @staticmethod
    def get_user_profile(access_token: str) -> dict:
        """使用 Access Token 獲取 Google 使用者個人資訊 (Email, Name)"""
        userinfo_url = getattr(settings, 'GOOGLE_USERINFO_URL', 'https://www.googleapis.com/oauth2/v2/userinfo')
        try:
            resp = requests.get(
                userinfo_url,
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=10
            )
            if resp.status_code != 200:
                raise GoogleAuthError(f"取得 Google 使用者資訊失敗: {resp.text}")
            return resp.json()
        except requests.RequestException as e:
            raise GoogleAuthError(f"連線至 Google 使用者資訊 API 失敗: {str(e)}")

    @classmethod
    def get_or_create_google_user(cls, profile: dict) -> User:
        """
        根據 Google 回傳資訊建立或登入 User
        - 以 Email 為核心識別依據
        - 自動同步 Google 姓名與 Email
        """
        email = profile.get('email')
        if not email:
            raise GoogleAuthError("Google 帳號未提供電子郵件地址。")

        full_name = profile.get('name', '')
        given_name = profile.get('given_name', '')
        family_name = profile.get('family_name', '')

        with transaction.atomic():
            user = User.objects.filter(email=email).first()
            if not user:
                # 建立新使用者，若 username 衝突自動遞增
                base_username = email.split('@')[0]
                username = base_username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}_{counter}"
                    counter += 1

                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=given_name or full_name,
                    last_name=family_name
                )
                user.set_unusable_password()
                user.save()
            else:
                # 已存在使用者，更新姓名
                if full_name:
                    user.first_name = given_name or full_name
                    user.last_name = family_name
                    user.save(update_fields=['first_name', 'last_name'])

            return user

