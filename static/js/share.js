/**
 * 粉絲挑戰打卡系統 - Web Share / 複製連結處理
 * 根據 SD 文件 Section 6.2 設計
 *
 * 策略：
 * 1. 優先使用 Web Share API (行動裝置原生分享)
 * 2. 降級至 Clipboard API (複製至剪貼簿)
 * 3. 最終降級至隱藏 textarea + execCommand
 */

function handleShare(challengeTitle, streak, points) {
  const shareData = {
    title: `我正在參加【${challengeTitle}】`,
    text: `我已經連續打卡 ${streak} 天，累積獲得 ${points} 分！快來跟我一起挑戰吧！`,
    url: window.location.href
  };

  if (navigator.share) {
    navigator.share(shareData).catch((err) => {
      if (err.name !== 'AbortError') {
        fallbackCopy(`${shareData.text} ${shareData.url}`);
      }
    });
  } else {
    // 降級處理：複製到剪貼簿
    const copyText = `${shareData.text} ${shareData.url}`;
    fallbackCopy(copyText);
  }
}

async function fallbackCopy(text) {
  try {
    await navigator.clipboard.writeText(text);
    showToast('分享文案與連結已複製到剪貼簿！', 'info');
  } catch (err) {
    // 最後手段：建立臨時輸入框
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    textarea.style.left = '-9999px';
    document.body.appendChild(textarea);
    textarea.select();
    try {
      document.execCommand('copy');
      showToast('分享文案已複製到剪貼簿！', 'info');
    } catch (e) {
      showToast('複製失敗，請手動複製網址。', 'warning');
    }
    document.body.removeChild(textarea);
  }
}

// ===== 頁面載入：綁定分享按鈕 =====
document.addEventListener('DOMContentLoaded', () => {
  const shareBtn = document.getElementById('share-btn');
  if (shareBtn) {
    shareBtn.addEventListener('click', () => {
      const title = shareBtn.dataset.challengeTitle;
      const streak = shareBtn.dataset.streak;
      const points = shareBtn.dataset.points;
      handleShare(title, streak, points);
    });
  }
});
