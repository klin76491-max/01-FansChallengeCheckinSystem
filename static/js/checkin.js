/**
 * 粉絲挑戰打卡系統 - 打卡 AJAX、Web Audio 和弦音階與 Canvas 微粒浮光
 * 依據 IT/roles/designer.md 故事沉浸式微互動規範打造
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

function isEnglish() {
  const lang = (document.documentElement.lang || '').toLowerCase();
  return lang.startsWith('en');
}

// ===== Toast 通知 =====
function showToast(message, type = 'success') {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);

  requestAnimationFrame(() => {
    toast.classList.add('show');
  });

  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}

// ===== 瀏覽器原生 Web Audio API：柔和木質溫暖鐘聲 =====
class CheckinAudioSynthesizer {
  constructor() {
    this.ctx = null;
  }

  init() {
    if (!this.ctx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (AudioContext) {
        this.ctx = new AudioContext();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  playChime(dayIndex = 1) {
    try {
      this.init();
      if (!this.ctx) return;

      const now = this.ctx.currentTime;
      // 依天數階梯爬升的五聲音階基頻 (C4~C6 溫暖音域)
      const pentatonic = [261.63, 293.66, 329.63, 392.00, 440.00, 523.25, 587.33, 659.25, 783.99, 880.00, 1046.50, 1174.66, 1318.51, 1567.98];
      const baseFreq = pentatonic[Math.min(Math.max(dayIndex - 1, 0), pentatonic.length - 1)];

      // 主音
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(baseFreq, now);

      gain.gain.setValueAtTime(0.24, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 1.2);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(now);
      osc.stop(now + 1.2);

      // 伴隨木質敲擊泛音
      const harm = this.ctx.createOscillator();
      const harmGain = this.ctx.createGain();
      harm.type = 'triangle';
      harm.frequency.setValueAtTime(baseFreq * 1.5, now);

      harmGain.gain.setValueAtTime(0.08, now);
      harmGain.gain.exponentialRampToValueAtTime(0.001, now + 0.6);

      harm.connect(harmGain);
      harmGain.connect(this.ctx.destination);

      harm.start(now);
      harm.stop(now + 0.6);

      // 若為第 14 天完結里程碑，彈奏圓滿和弦
      if (dayIndex >= 14) {
        setTimeout(() => {
          this.playResolutionChord();
        }, 300);
      }
    } catch (e) {
      console.warn('Audio feedback failed gracefully:', e);
    }
  }

  playResolutionChord() {
    if (!this.ctx) return;
    const now = this.ctx.currentTime;
    const chord = [523.25, 659.25, 783.99, 1046.50]; // C 大調圓融和弦

    chord.forEach((freq, idx) => {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, now + idx * 0.08);

      gain.gain.setValueAtTime(0.12, now + idx * 0.08);
      gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.08 + 2.0);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(now + idx * 0.08);
      osc.stop(now + idx * 0.08 + 2.0);
    });
  }
}

const checkinAudio = new CheckinAudioSynthesizer();

// ===== 瀏覽器原生 Canvas API：暖陽微光火花粒子 (Ember Sparkles) =====
function spawnEmberSparkles(targetEl) {
  let canvas = document.getElementById('sparkle-canvas');
  if (!canvas) {
    canvas = document.createElement('canvas');
    canvas.id = 'sparkle-canvas';
    document.body.appendChild(canvas);
  }

  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const rect = targetEl.getBoundingClientRect();
  const originX = rect.left + rect.width / 2;
  const originY = rect.top + rect.height / 2;

  const colors = ['#E07A5F', '#F4A261', '#D4A574', '#FAF5F0', '#A0BDC9'];
  const particles = [];

  for (let i = 0; i < 40; i++) {
    const angle = Math.random() * Math.PI * 2;
    const speed = 2 + Math.random() * 5;
    particles.push({
      x: originX,
      y: originY,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed - 2.5, // 向上微飄
      size: 2.5 + Math.random() * 3.5,
      color: colors[Math.floor(Math.random() * colors.length)],
      alpha: 1,
      decay: 0.015 + Math.random() * 0.02,
    });
  }

  function render() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    let alive = false;

    for (const p of particles) {
      if (p.alpha > 0) {
        alive = true;
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.04; // 微重力
        p.alpha -= p.decay;

        ctx.save();
        ctx.globalAlpha = Math.max(0, p.alpha);
        ctx.fillStyle = p.color;
        ctx.shadowColor = p.color;
        ctx.shadowBlur = 8;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }
    }

    if (alive) {
      requestAnimationFrame(render);
    } else {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  }

  requestAnimationFrame(render);
}

// ===== 加入挑戰 =====
async function joinChallenge(challengeId, buttonEl) {
  const isEn = isEnglish();
  buttonEl.disabled = true;
  const originalText = buttonEl.textContent;
  buttonEl.textContent = isEn ? 'Joining...' : '約定建立中...';

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
      checkinAudio.playChime(1);
      spawnEmberSparkles(buttonEl);
      showToast(data.message, 'success');
      buttonEl.textContent = isEn ? '✓ Joined' : '✓ 已定下約定';
      buttonEl.className = 'btn btn-success';
      buttonEl.disabled = true;

      setTimeout(() => location.reload(), 700);
    } else {
      showToast(data.error || data.message || (isEn ? 'Failed to join' : '約定建立失敗'), 'danger');
      buttonEl.disabled = false;
      buttonEl.textContent = originalText;
    }
  } catch (error) {
    showToast(isEn ? 'Network error, please try again later' : '網路連線異常，請稍後再試', 'danger');
    buttonEl.disabled = false;
    buttonEl.textContent = originalText;
  }
}

// ===== 第 14 天達成故事彈窗 =====
function showFourteenDaysModal() {
  const isEn = isEnglish();
  const modalHtml = `
    <div class="modal-overlay active" id="storyModalOverlay" onclick="closeStoryModal(event)">
      <div class="modal-content-story" onclick="event.stopPropagation()">
        <div style="font-size: 2.2rem; margin-bottom: 0.5rem;">🌟</div>
        <h3 class="page-title" style="font-size: 1.5rem; margin-bottom: 0.5rem;">
          ${isEn ? 'Fourteen Days Reached' : '十四天的約定，已全部點亮'}
        </h3>
        <p class="font-serif" style="color: var(--text-secondary); line-height: 1.9; margin-bottom: 1.5rem; font-size: 0.95rem;">
          ${isEn 
            ? '“Fourteen days have ended. I did not know whether what truly began was those fourteen days, or all the days that followed.” — The gap between wanting and doing has just been closed.' 
            : '「直到第十四天，最後一格亮起來。我沒有什麼驕傲。我只是覺得，原來有些事，做完了，會讓人有一點不一樣。想做與做之間，其實可以被拉近一些。」'}
        </p>
        <button type="button" class="btn btn-accent" onclick="closeStoryModal()" style="padding: 0.65rem 1.8rem;">
          ${isEn ? 'Keep Going' : '收下這份痕跡，繼續前行'}
        </button>
      </div>
    </div>
  `;
  document.body.insertAdjacentHTML('beforeend', modalHtml);
}

function closeStoryModal() {
  const modal = document.getElementById('storyModalOverlay');
  if (modal) {
    modal.classList.remove('active');
    setTimeout(() => modal.remove(), 280);
  }
}

// ===== 打卡主要流程 =====
async function checkIn(challengeId, buttonEl) {
  const isEn = isEnglish();
  buttonEl.disabled = true;
  buttonEl.innerHTML = `<span class="spinner"></span> ${isEn ? 'Lighting up today...' : '點亮今日約定中...'}`;
  buttonEl.style.background = 'var(--color-primary)';

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
      const checkinCount = data.total_checkins || 1;
      
      // 觸發音效與 Canvas 微光
      checkinAudio.playChime(checkinCount);
      spawnEmberSparkles(buttonEl);

      showToast(data.message, 'success');

      // 切換按鈕狀態
      buttonEl.textContent = isEn ? '✨ Checked in for today!' : '✨ 今日已點亮完成！';
      buttonEl.className = 'btn btn-checked btn-lg btn-block checkin-btn';
      buttonEl.style.background = '';
      buttonEl.disabled = true;

      // 更新統計數字
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
        scoreEl.style.display = 'inline-block';
      }

      // 動態即時點亮 14 天格子
      const targetBox = document.getElementById(`grid-day-${checkinCount}`);
      if (targetBox) {
        targetBox.classList.remove('is-current', 'is-locked');
        targetBox.classList.add('is-completed', 'animate-lit');
        const iconEl = targetBox.querySelector('.grid-day-icon');
        if (iconEl) iconEl.innerHTML = '<span class="icon-check">✓</span>';
        const statusEl = targetBox.querySelector('.grid-day-status');
        if (statusEl) statusEl.textContent = isEn ? 'Lit Up' : '已點亮';

        // 格子本身也噴發微光
        setTimeout(() => spawnEmberSparkles(targetBox), 150);
      }

      // 更新進度條
      const progressCountEl = document.getElementById('grid-progress-count');
      const progressRateEl = document.getElementById('grid-progress-rate');
      const progressFillEl = document.getElementById('grid-progress-fill');
      const pct = Math.min(100, Math.round((checkinCount / 14) * 100));

      if (progressCountEl) progressCountEl.textContent = checkinCount;
      if (progressRateEl) progressRateEl.textContent = `(${pct}%)`;
      if (progressFillEl) progressFillEl.style.width = `${pct}%`;

      // 若達成 14 天
      if (checkinCount >= 14) {
        setTimeout(() => {
          showFourteenDaysModal();
        }, 1200);
      }

    } else {
      showToast(data.error || (isEn ? 'Check-in failed, please retry.' : '打卡失敗，請稍後重試。'), 'danger');
      buttonEl.disabled = false;
      buttonEl.innerHTML = isEn ? '✨ Check in Now' : '✨ 點亮今日約定';
      buttonEl.style.background = '';
    }
  } catch (err) {
    showToast(isEn ? 'Network connection error, please check connection.' : '網路連線異常，請檢查網路。', 'danger');
    buttonEl.disabled = false;
    buttonEl.innerHTML = isEn ? '✨ Check in Now' : '✨ 點亮今日約定';
    buttonEl.style.background = '';
  }
}

// ===== 頁面載入：事件綁定與微動畫 =====
document.addEventListener('DOMContentLoaded', () => {
  // 首次使用者點擊觸發 AudioContext 初始化
  document.addEventListener('click', () => {
    checkinAudio.init();
  }, { once: true });

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

  // 綁定加入挑戰按鈕
  document.querySelectorAll('[id^="join-btn-"]').forEach(btn => {
    btn.addEventListener('click', () => {
      const challengeId = btn.dataset.challengeId;
      if (challengeId) {
        joinChallenge(challengeId, btn);
      }
    });
  });

  // 為卡片加入溫和漸入動畫
  const cards = document.querySelectorAll('.card, .story-epigraph-card');
  cards.forEach((card, index) => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(14px)';
    setTimeout(() => {
      card.style.transition = 'opacity 0.45s ease, transform 0.45s cubic-bezier(0.16, 1, 0.3, 1)';
      card.style.opacity = '1';
      card.style.transform = 'translateY(0)';
    }, index * 70);
  });
});
