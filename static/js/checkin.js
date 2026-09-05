/**
 * 粉絲挑戰打卡系統 - 打卡 AJAX 與動畫處理
 * 根據 SD 文件 Section 6.1 設計
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

function isEnglish() {
  const lang = (document.documentElement.lang || '').toLowerCase();
  return lang.startsWith('en');
}

// ===== 加入挑戰 =====
async function joinChallenge(challengeId, buttonEl) {
  const isEn = isEnglish();
  buttonEl.disabled = true;
  const originalText = buttonEl.textContent;
  buttonEl.textContent = isEn ? 'Joining...' : '加入中...';

  try {
    const response = await fetch(`/challenges/api/${challengeId}/join/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrftoken,
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json();

    if (data.success) {
      showToast(data.message, 'success');
      buttonEl.textContent = isEn ? '✓ Joined' : '✓ 已加入';
      buttonEl.className = 'btn btn-success';
      buttonEl.disabled = true;

      // 重新整理頁面以顯示打卡區塊
      setTimeout(() => location.reload(), 800);
    } else {
      showToast(data.error || data.message || (isEn ? 'Failed to join' : '加入失敗'), 'error');
      buttonEl.disabled = false;
      buttonEl.textContent = originalText;
    }
  } catch (error) {
    showToast(isEn ? 'Network error, please try again later' : '網路錯誤，請稍後再試', 'error');
    buttonEl.disabled = false;
    buttonEl.textContent = originalText;
  }
}

// ===== 打卡 =====
async function checkIn(challengeId, buttonEl) {
  const isEn = isEnglish();
  buttonEl.disabled = true;
  buttonEl.innerHTML = `<span class="spinner"></span> ${isEn ? 'Checking in...' : '打卡處理中...'}`;
  buttonEl.style.background = '#2d7a8a'; // Accent Teal 處理中狀態

  try {
    const response = await fetch(`/challenges/api/${challengeId}/checkin/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrftoken,
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json();

    if (response.ok && data.success) {
      showToast(data.message, 'success');

      // 切換按鈕狀態為已完成 (Success Green)
      buttonEl.textContent = isEn ? '🎉 Checked in for today!' : '🎉 今日已打卡完成！';
      buttonEl.className = 'btn btn-checked btn-lg btn-block checkin-btn';
      buttonEl.style.background = '';
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
        totalEl.textContent = data.total_points;
        totalEl.classList.add('animate-score');
      }
      if (scoreEl) {
        scoreEl.textContent = isEn ? `+${data.score_earned} Points!` : `+${data.score_earned} 積分！`;
        scoreEl.classList.add('animate-score');
        scoreEl.style.display = 'block';
      }

      // 動態即時點亮 14 天格子
      if (data.total_checkins) {
        const checkinCount = data.total_checkins;
        const targetBox = document.getElementById(`grid-day-${checkinCount}`);
        if (targetBox) {
          targetBox.classList.remove('is-current', 'is-locked');
          targetBox.classList.add('is-completed', 'animate-lit');
          const iconEl = targetBox.querySelector('.grid-day-icon');
          if (iconEl) iconEl.innerHTML = '<span class="icon-check">✓</span>';
          const statusEl = targetBox.querySelector('.grid-day-status');
          if (statusEl) statusEl.textContent = isEn ? 'Lit Up' : '已點亮';
        }

        // 更新計數與進度條
        const progressCountEl = document.getElementById('grid-progress-count');
        const progressRateEl = document.getElementById('grid-progress-rate');
        const progressFillEl = document.getElementById('grid-progress-fill');
        const pct = Math.min(100, Math.round((checkinCount / 14) * 100));

        if (progressCountEl) progressCountEl.textContent = checkinCount;
        if (progressRateEl) progressRateEl.textContent = `(${pct}%)`;
        if (progressFillEl) progressFillEl.style.width = `${pct}%`;
      }
    } else {
      showToast(data.error || (isEn ? 'Check-in failed, please retry.' : '打卡失敗，請稍後重試。'), 'danger');
      buttonEl.disabled = false;
      buttonEl.innerHTML = isEn ? '⚡ Check in Now' : '⚡ 立即打卡';
      buttonEl.style.background = '';
    }
  } catch (err) {
    showToast(isEn ? 'Network connection error, please check connection.' : '網路連線異常，請檢查網路。', 'danger');
    buttonEl.disabled = false;
    buttonEl.innerHTML = isEn ? '⚡ Check in Now' : '⚡ 立即打卡';
    buttonEl.style.background = '';
  }
}

// ===== 頁面載入：事件綁定與動畫 =====
document.addEventListener('DOMContentLoaded', () => {
  // 綁定打卡按鈕
  const checkinBtn = document.getElementById('checkin-btn');
  if (checkinBtn && !checkinBtn.disabled) {
    checkinBtn.addEventListener('click', () => {
      const challengeId = checkinBtn.dataset.challengeId;
      if (challengeId) {
        checkIn(challengeId, checkinBtn);
      }
    });
  }

  // 綁定加入挑戰按鈕 (列表頁與詳情頁)
  document.querySelectorAll('[id^="join-btn-"]').forEach(btn => {
    btn.addEventListener('click', () => {
      const challengeId = btn.dataset.challengeId;
      if (challengeId) {
        joinChallenge(challengeId, btn);
      }
    });
  });

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
