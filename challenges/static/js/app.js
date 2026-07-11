/**
 * 粉絲挑戰打卡系統 - 前端互動邏輯
 * 根據 SD 文件 Section 5 定義
 */

// ===== CSRF Token 取得 =====
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// ===== Toast 通知 =====
function showToast(message, type = 'success') {
  // 移除已存在的 toast
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);

  // 觸發動畫
  requestAnimationFrame(() => {
    toast.classList.add('show');
  });

  // 3 秒後自動消失
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ===== 加入挑戰 =====
async function joinChallenge(challengeId, buttonEl) {
  buttonEl.disabled = true;
  buttonEl.textContent = '加入中...';

  try {
    const response = await fetch(`/api/challenges/${challengeId}/join/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrftoken,
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json();

    if (data.success) {
      showToast(data.message, 'success');
      buttonEl.textContent = '✓ 已加入';
      buttonEl.className = 'btn btn-joined';
      buttonEl.disabled = true;

      // 如果在詳細頁，重新整理以顯示打卡區塊
      if (document.querySelector('.checkin-section')) {
        setTimeout(() => location.reload(), 800);
      }
    } else {
      showToast(data.message, 'error');
      buttonEl.disabled = false;
      buttonEl.textContent = '加入挑戰';
    }
  } catch (error) {
    showToast('網路錯誤，請稍後再試', 'error');
    buttonEl.disabled = false;
    buttonEl.textContent = '加入挑戰';
  }
}

// ===== 打卡 =====
async function checkIn(challengeId, buttonEl) {
  buttonEl.disabled = true;
  buttonEl.textContent = '打卡中...';

  try {
    const response = await fetch(`/api/challenges/${challengeId}/checkin/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrftoken,
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json();

    if (data.success) {
      showToast(data.message, 'success');

      // 更新按鈕狀態
      buttonEl.textContent = '✓ 今日已打卡';
      buttonEl.className = 'btn btn-joined btn-lg checkin-btn';
      buttonEl.disabled = true;

      // 更新頁面上的統計數字 (帶動畫)
      const streakEl = document.getElementById('streak-value');
      const totalEl = document.getElementById('total-points');
      const scoreEl = document.getElementById('last-score');

      if (streakEl) {
        streakEl.textContent = data.new_streak;
        streakEl.classList.add('animate-score');
      }
      if (totalEl) {
        totalEl.textContent = data.new_total;
        totalEl.classList.add('animate-score');
      }
      if (scoreEl) {
        scoreEl.textContent = `+${data.score_earned}`;
        scoreEl.classList.add('animate-score');
        scoreEl.style.display = 'block';
      }
    } else {
      showToast(data.message, 'error');
      buttonEl.disabled = false;
      buttonEl.textContent = '🔥 立即打卡';
    }
  } catch (error) {
    showToast('網路錯誤，請稍後再試', 'error');
    buttonEl.disabled = false;
    buttonEl.textContent = '🔥 立即打卡';
  }
}

// ===== 分享功能 =====
async function shareResult(challengeName, streak, points, url) {
  const shareText = `我正在參與【${challengeName}】！目前已連續打卡 ${streak} 天，獲得 ${points} 分！快來一起挑戰吧！`;

  // 優先使用 Web Share API
  if (navigator.share) {
    try {
      await navigator.share({
        title: `粉絲挑戰 - ${challengeName}`,
        text: shareText,
        url: url,
      });
      showToast('分享成功！', 'success');
    } catch (err) {
      if (err.name !== 'AbortError') {
        // 使用者取消不算錯誤
        fallbackCopy(shareText + '\n' + url);
      }
    }
  } else {
    // Fallback: 複製至剪貼簿
    fallbackCopy(shareText + '\n' + url);
  }
}

async function fallbackCopy(text) {
  try {
    await navigator.clipboard.writeText(text);
    showToast('已複製分享文案至剪貼簿！', 'success');
  } catch (err) {
    // 最後手段：建立臨時輸入框
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    showToast('已複製分享文案至剪貼簿！', 'success');
  }
}

// ===== 頁面載入動畫 =====
document.addEventListener('DOMContentLoaded', () => {
  // 為卡片加入漸入動畫
  const cards = document.querySelectorAll('.card');
  cards.forEach((card, index) => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
    setTimeout(() => {
      card.style.transition = 'all 0.5s ease';
      card.style.opacity = '1';
      card.style.transform = 'translateY(0)';
    }, index * 80);
  });
});
