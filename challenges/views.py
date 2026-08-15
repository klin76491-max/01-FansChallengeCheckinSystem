"""
粉絲挑戰打卡系統 - 頁面視圖 (CBV) 與 API 端點
根據 SD 文件 Section 3.1 (頁面 CBV) 與 Section 5 (API 控制器) 定義

頁面視圖：
- ChallengeListView: 挑戰列表頁
- ChallengeDetailView: 挑戰詳情與打卡主畫面
- MyChallengeListView: 我的挑戰歷史
- LeaderboardView: 排行榜頁

API 端點：
- JoinChallengeAPIView: 加入挑戰 API
- CheckInAPIView: 打卡 API
"""

from django.http import JsonResponse
from django.views import View
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from .models import Challenge, Participant, CheckIn
from .services import (
    CheckInService, CheckInError, DuplicateCheckInError, ChallengeInactiveError
)


# ===== 頁面視圖 (Page CBV) =====

class ChallengeListView(ListView):
    """挑戰列表頁 - 顯示所有可參加的挑戰"""
    model = Challenge
    template_name = 'challenges/challenge_list.html'
    context_object_name = 'challenges'

    def get_queryset(self):
        now = timezone.now()
        return Challenge.objects.filter(
            is_active=True,
            end_at__gte=now,
        ).order_by('-start_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()

        # 分類：進行中 vs 即將開始
        ongoing = []
        upcoming = []
        for challenge in context['challenges']:
            if challenge.start_at <= now:
                ongoing.append(challenge)
            else:
                upcoming.append(challenge)

        context['ongoing_challenges'] = ongoing
        context['upcoming_challenges'] = upcoming

        # 如果使用者已登入，附上已加入的挑戰 ID
        if self.request.user.is_authenticated:
            joined_ids = set(
                Participant.objects.filter(
                    user=self.request.user
                ).values_list('challenge_id', flat=True)
            )
            context['joined_challenge_ids'] = joined_ids

        return context


class ChallengeDetailView(DetailView):
    """挑戰詳情頁 - 顯示挑戰內容、使用者進度與打卡按鈕"""
    model = Challenge
    template_name = 'challenges/challenge_detail.html'
    context_object_name = 'challenge'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        challenge = self.object
        user = self.request.user

        context['has_joined'] = False
        context['has_checked_in_today'] = False
        context['participant'] = None
        context['is_running'] = challenge.is_currently_running()

        if user.is_authenticated:
            try:
                participant = Participant.objects.get(
                    user=user, challenge=challenge
                )
                context['has_joined'] = True
                context['participant'] = participant

                # 檢查今日是否已打卡 (以伺服器時區 Asia/Taipei 為準)
                today = timezone.localdate()
                context['has_checked_in_today'] = CheckIn.objects.filter(
                    user=user,
                    challenge=challenge,
                    check_in_date=today,
                ).exists()

            except Participant.DoesNotExist:
                pass

            # 取得該使用者在本挑戰的打卡歷史
            context['checkin_history'] = CheckIn.objects.filter(
                user=user, challenge=challenge
            ).order_by('-check_in_date')[:10]

        # 取得 Top 5 排行榜預覽 (使用 select_related 避免 N+1)
        context['top_participants'] = Participant.objects.filter(
            challenge=challenge
        ).select_related('user').order_by(
            '-total_points', '-current_streak'
        )[:5]

        return context


class MyChallengeListView(LoginRequiredMixin, ListView):
    """我的挑戰頁 - 顯示使用者已加入的挑戰與進度"""
    model = Participant
    template_name = 'challenges/my_challenges.html'
    context_object_name = 'participations'

    def get_queryset(self):
        return Participant.objects.filter(
            user=self.request.user
        ).select_related('challenge').order_by('-joined_at')


class LeaderboardView(DetailView):
    """排行榜頁 - 依照 SD 排序：total_points DESC, current_streak DESC, joined_at ASC"""
    model = Challenge
    template_name = 'challenges/leaderboard.html'
    context_object_name = 'challenge'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        challenge = self.object

        # 依照 SA Section 4.3 排序邏輯
        leaderboard = Participant.objects.filter(
            challenge=challenge
        ).select_related('user').order_by(
            '-total_points', '-current_streak', 'joined_at'
        )[:50]

        # 加上排名序號
        ranked = []
        for idx, p in enumerate(leaderboard, start=1):
            ranked.append({
                'rank': idx,
                'username': p.user.first_name or p.user.username,
                'total_points': p.total_points,
                'current_streak': p.current_streak,
                'user_id': p.user.id,
            })
        context['leaderboard'] = ranked

        # 如果使用者已登入，找出使用者自己的排名
        if self.request.user.is_authenticated:
            try:
                my_participant = Participant.objects.get(
                    user=self.request.user, challenge=challenge
                )
                # 計算排名：有多少人分數比我高
                my_rank = Participant.objects.filter(
                    challenge=challenge,
                    total_points__gt=my_participant.total_points,
                ).count() + 1
                context['my_rank'] = my_rank
                context['my_participant'] = my_participant
            except Participant.DoesNotExist:
                pass

        return context


# ===== API 端點 (AJAX Endpoints) =====

class JoinChallengeAPIView(LoginRequiredMixin, View):
    """加入挑戰 API - POST /challenges/api/<challenge_id>/join/"""

    def post(self, request, challenge_id):
        try:
            participant, created = CheckInService.join_challenge(
                request.user, challenge_id
            )
            msg = "成功加入挑戰！" if created else "您已經是本挑戰的參與者了。"
            return JsonResponse({'success': True, 'message': msg})
        except ChallengeInactiveError as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
        except CheckInError as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
        except Exception:
            return JsonResponse(
                {'success': False, 'error': "加入失敗，請稍後再試。"}, status=500
            )


class CheckInAPIView(LoginRequiredMixin, View):
    """打卡 API - POST /challenges/api/<challenge_id>/checkin/"""

    def post(self, request, challenge_id):
        try:
            result = CheckInService.perform_checkin(request.user, challenge_id)
            return JsonResponse(result)
        except DuplicateCheckInError as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
        except (ChallengeInactiveError, CheckInError) as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
        except Exception:
            return JsonResponse(
                {'success': False, 'error': "系統繁忙，請稍後再試。"}, status=500
            )
