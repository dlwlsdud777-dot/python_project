// Grok Looper Background Service Worker

chrome.runtime.onInstalled.addListener(() => {
  console.log('Grok Looper Extension Installed');
});

// 향후 상태 영속성이나 알림 기능이 필요할 경우 여기에 추가
