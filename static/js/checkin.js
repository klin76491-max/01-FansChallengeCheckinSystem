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

// ===== 加入挑戰 =====
async function joinChallenge(challengeId, buttonEl) {
  buttonEl.disabled = true;
  const originalText = buttonEl.textContent;
  buttonEl.textContent = '加入中...';

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
      buttonEl.textContent = '✓ 已加入';
      buttonEl.className = 'btn btn-success';
      buttonEl.disabled = true;

      // 重新整理頁面以顯示打卡區塊
      setTimeout(() => location.reload(), 800);
    } else {
      showToast(data.error || data.message || '加入失敗', 'error');
      buttonEl.disabled = false;
      buttonEl.textContent = originalText;
    }
  } catch (error) {
    showToast('網路錯誤，請稍後再試', 'error');
    buttonEl.disabled = false;
    buttonEl.textContent = originalText;
  }
}

// ===== 打卡 =====
async function checkIn(challengeId, buttonEl) {
  buttonEl.disabled = true;
  buttonEl.innerHTML = '<span class="spinner"></span> 打卡處理中...';
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
      buttonEl.textContent = '🎉 今日已打卡完成！';
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
        scoreEl.textContent = `+${data.score_earned} 積分！`;
        scoreEl.classList.add('animate-score');
        scoreEl.style.display = 'block';
      }
    } else {
      showToast(data.error || '打卡失敗，請稍後重試。', 'danger');
      buttonEl.disabled = false;
      buttonEl.innerHTML = '⚡ 立即打卡';
      buttonEl.style.background = '';
    }
  } catch (err) {
    showToast('網路連線異常，請檢查網路。', 'danger');
    buttonEl.disabled = false;
    buttonEl.innerHTML = '⚡ 立即打卡';
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
