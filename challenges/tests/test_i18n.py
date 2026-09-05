"""
Tests for Bilingual (i18n) Support:
- Browser language auto-detection via Accept-Language header
- Manual language switching via /i18n/setlang/
- Language cookie persistence
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from challenges.models import Challenge


class I18nTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.now = timezone.now()
        self.challenge = Challenge.objects.create(
            title="14天英語自然發音挑戰",
            description="每天 5 分鐘聽讀練習",
            challenge_type="daily",
            start_at=self.now - timedelta(days=1),
            end_at=self.now + timedelta(days=13),
            points_per_checkin=10,
            bonus_for_streak=5,
            is_active=True,
        )

    def test_default_or_chinese_browser_language(self):
        """測試預設或瀏覽器 Accept-Language 為 zh-TW 時顯示中文"""
        response = self.client.get(
            reverse('challenges:list'),
            HTTP_ACCEPT_LANGUAGE='zh-TW,zh;q=0.9,en;q=0.8'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '探索正在進行中的熱門挑戰')
        self.assertContains(response, '挑戰列表')
        self.assertContains(response, '登入')

    def test_english_browser_language_auto_detection(self):
        """測試瀏覽器 Accept-Language 為 en 時自動顯示英文"""
        response = self.client.get(
            reverse('challenges:list'),
            HTTP_ACCEPT_LANGUAGE='en-US,en;q=0.9'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Explore Popular Ongoing Challenges')
        self.assertContains(response, 'Challenges')
        self.assertContains(response, 'Log in')

    def test_manual_language_switch_to_english(self):
        """測試使用者手動切換至英文"""
        # POST /i18n/setlang/ with language=en
        response = self.client.post(
            reverse('set_language'),
            {'language': 'en', 'next': reverse('challenges:list')},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Explore Popular Ongoing Challenges')
        self.assertContains(response, 'Ongoing Challenges')
        # Check cookie
        self.assertEqual(self.client.cookies.get('django_language').value, 'en')

    def test_manual_language_switch_to_chinese(self):
        """測試使用者手動切換回中文"""
        # Set to English first
        self.client.post(
            reverse('set_language'),
            {'language': 'en', 'next': reverse('challenges:list')},
            follow=True
        )
        # Then switch to zh-hant
        response = self.client.post(
            reverse('set_language'),
            {'language': 'zh-hant', 'next': reverse('challenges:list')},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '探索正在進行中的熱門挑戰')
        self.assertEqual(self.client.cookies.get('django_language').value, 'zh-hant')

    def test_detail_page_in_english(self):
        """測試挑戰詳情頁手動切換至英文後的呈現"""
        self.client.post(
            reverse('set_language'),
            {'language': 'en', 'next': reverse('challenges:detail', args=[self.challenge.pk])}
        )
        response = self.client.get(reverse('challenges:detail', args=[self.challenge.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Challenge Details')
        self.assertContains(response, 'Back to Challenges')
        self.assertContains(response, 'Leaderboard TOP 5')
