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
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from .models import Challenge, Participant, CheckIn
from .forms import ChallengeCreateForm
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
    """挑戰詳情頁 - 顯示挑戰內容、使用者進度、14 天打卡格子與打卡按鈕"""
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
        context['checkin_count'] = 0

        # 14 天打卡格子預設狀態
        grid_days = []
        for d in range(1, 15):
            grid_days.append({
                'day': d,
                'is_completed': False,
                'is_current': False,
                'is_locked': True,
            })

        if user.is_authenticated:
            try:
                participant = Participant.objects.get(
                    user=user, challenge=challenge
                )
                context['has_joined'] = True
                context['participant'] = participant

                # 檢查今日是否已打卡 (以伺服器時區 Asia/Taipei 為準)
                today = timezone.localdate()
                has_checked_in_today = CheckIn.objects.filter(
                    user=user,
                    challenge=challenge,
                    check_in_date=today,
                ).exists()
                context['has_checked_in_today'] = has_checked_in_today

                # 計算累積打卡次數
                checkin_count = CheckIn.objects.filter(
                    user=user, challenge=challenge
                ).count()
                context['checkin_count'] = checkin_count

                # 計算 14 天格子的動態狀態
                grid_days = []
                for d in range(1, 15):
                    is_completed = d <= checkin_count
                    is_current = (d == checkin_count + 1) and not has_checked_in_today
                    is_locked = not is_completed and not is_current
                    grid_days.append({
                        'day': d,
                        'is_completed': is_completed,
                        'is_current': is_current,
                        'is_locked': is_locked,
                    })

            except Participant.DoesNotExist:
                pass

            # 取得該使用者在本挑戰的打卡歷史
            context['checkin_history'] = CheckIn.objects.filter(
                user=user, challenge=challenge
            ).order_by('-check_in_date')[:10]

        context['grid_days'] = grid_days
        context['grid_total_days'] = 14
        context['progress_percent'] = min(100, int((context['checkin_count'] / 14) * 100))

        # 取得 Top 5 排行榜預覽 (使用 select_related 避免 N+1)
        context['top_participants'] = Participant.objects.filter(
            challenge=challenge
        ).select_related('user').order_by(
            '-total_points', '-current_streak'
        )[:5]

        return context


class ChallengeCreateView(LoginRequiredMixin, CreateView):
    """建立自訂打卡項目頁面"""
    model = Challenge
    form_class = ChallengeCreateForm
    template_name = 'challenges/challenge_create.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        # 自動為建立者加入此挑戰
        try:
            CheckInService.join_challenge(self.request.user, self.object.id)
        except Exception:
            pass
        messages.success(self.request, f"🎉 挑戰「{self.object.title}」建立成功！已自動為您加入該挑戰。")
        return response

    def get_success_url(self):
        return reverse('challenges:detail', kwargs={'pk': self.object.pk})



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
