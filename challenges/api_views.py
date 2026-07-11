"""
粉絲挑戰打卡系統 - JSON API 端點 (供 Frontend Fetch 使用)
根據 SD 文件 Section 3.2 與 Section 4 定義
"""

import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db import transaction, IntegrityError
from django.utils import timezone
from .models import Challenge, Participant, CheckIn


@login_required
@require_POST
def join_challenge_api(request, challenge_id):
    """
    加入挑戰 API
    POST /api/challenges/<challenge_id>/join/
    回傳: { "success": true/false, "message": "..." }
    """
    try:
        challenge = Challenge.objects.get(pk=challenge_id)
    except Challenge.DoesNotExist:
        return JsonResponse({'success': False, 'message': '挑戰不存在'}, status=404)

    if not challenge.is_active:
        return JsonResponse({'success': False, 'message': '此挑戰已停用'}, status=400)

    if challenge.is_ended:
        return JsonResponse({'success': False, 'message': '此挑戰已結束'}, status=400)

    try:
        Participant.objects.create(user=request.user, challenge=challenge)
        return JsonResponse({'success': True, 'message': '成功加入挑戰！'})
    except IntegrityError:
        return JsonResponse({'success': False, 'message': '您已加入此挑戰'}, status=400)


@login_required
@require_POST
def checkin_api(request, challenge_id):
    """
    打卡 API
    POST /api/challenges/<challenge_id>/checkin/
    回傳: { "success": true/false, "score_earned": ..., "new_total": ..., "new_streak": ... }

    商業邏輯 (SD Section 4.1):
    1. 驗證資格
    2. 防呆檢查 (今日是否已打卡)
    3. 計算連續天數 (Streak)
    4. 計算分數
    5. 資料庫更新 (Atomic Transaction)
    """
    try:
        challenge = Challenge.objects.get(pk=challenge_id)
    except Challenge.DoesNotExist:
        return JsonResponse({'success': False, 'message': '挑戰不存在'}, status=404)

    # Step 1: 驗證資格
    if not challenge.is_ongoing:
        return JsonResponse({'success': False, 'message': '此挑戰不在活動期間'}, status=400)

    try:
        participant = Participant.objects.get(user=request.user, challenge=challenge)
    except Participant.DoesNotExist:
        return JsonResponse({'success': False, 'message': '您尚未加入此挑戰'}, status=400)

    # Step 2: 防呆檢查 - 以系統時區 (Asia/Taipei) 的今日日期為準
    today = timezone.localdate()
    if CheckIn.objects.filter(
        user=request.user, challenge=challenge, check_in_date=today
    ).exists():
        return JsonResponse({'success': False, 'message': '今日已打卡，明天再來吧！'}, status=400)

    # Step 3: 計算連續天數 (Streak)
    yesterday = today - timezone.timedelta(days=1)
    had_yesterday = CheckIn.objects.filter(
        user=request.user, challenge=challenge, check_in_date=yesterday
    ).exists()

    if had_yesterday:
        new_streak = participant.current_streak + 1
    else:
        new_streak = 1

    # Step 4: 計算分數
    score = challenge.points_per_checkin
    if new_streak > 1:
        score += challenge.bonus_for_streak

    # Step 5: 資料庫更新 (Atomic Transaction)
    with transaction.atomic():
        CheckIn.objects.create(
            user=request.user,
            challenge=challenge,
            check_in_date=today,
            score_earned=score,
        )
        participant.current_streak = new_streak
        participant.total_points += score
        participant.save(update_fields=['current_streak', 'total_points'])

    return JsonResponse({
        'success': True,
        'message': f'打卡成功！獲得 {score} 分！',
        'score_earned': score,
        'new_total': participant.total_points,
        'new_streak': new_streak,
    })
