"""
01-FansChallengeCheckinSystem: SSO Gateway Middleware
接收來自 Nginx 統一認證網關的 Header，實現自動免登入
"""

import urllib.parse
from django.contrib.auth import login
from django.contrib.auth.models import User


class SSOGatewayMiddleware:
    """
    自動接收來自 Nginx Gateway 注入之認證身分（SSO）：
    - HTTP_X_USER_EMAIL 或 HTTP_REMOTE_USER / REMOTE_USER
    - HTTP_X_USER_NAME (URL-encoded)
    若偵測到 Header，自動在子系統同步建檔並登入，達成全自動免登入。
    若未帶 Header（直接訪問子系統），不干擾子系統內部既有之獨立登入流程。
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        email = (
            request.META.get('HTTP_X_USER_EMAIL')
            or request.META.get('HTTP_REMOTE_USER')
            or request.META.get('REMOTE_USER')
        )
        if email:
            email = email.strip()

        if email:
            current_user = getattr(request, 'user', None)
            if not current_user or not current_user.is_authenticated or current_user.email != email:
                raw_name = request.META.get('HTTP_X_USER_NAME', '')
                name = urllib.parse.unquote(raw_name) if raw_name else ''

                user = User.objects.filter(email=email).first()
                if not user:
                    base_username = email.split('@')[0]
                    username = base_username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}_{counter}"
                        counter += 1

                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        first_name=name or username
                    )
                    user.set_unusable_password()
                    user.save()
                elif name and not user.first_name:
                    user.first_name = name
                    user.save(update_fields=['first_name'])

                login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        return self.get_response(request)
