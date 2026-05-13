document.addEventListener('DOMContentLoaded', () => {
    const imageInput = document.getElementById('imageInput');
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const fileCount = document.getElementById('fileCount');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const currentStatus = document.getElementById('currentStatus');
    const logContent = document.getElementById('logContent');

    let selectedFiles = [];

    // 파일 선택 시
    imageInput.addEventListener('change', (e) => {
        selectedFiles = Array.from(e.target.files);
        fileCount.textContent = `선택된 파일: ${selectedFiles.length}개`;
        addLog(`파일 ${selectedFiles.length}개가 선택되었습니다.`, 'info');
        updateProgress(0, selectedFiles.length);
    });

    // 시작 버튼 클릭
    startBtn.addEventListener('click', async () => {
        if (selectedFiles.length === 0) {
            addLog('업로드할 이미지를 먼저 선택해주세요.', 'error');
            return;
        }

        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tab.url.includes('grok.com/imagine')) {
            addLog('Grok Imagine 페이지에서만 동작합니다.', 'error');
            return;
        }

        startBtn.disabled = true;
        stopBtn.disabled = false;
        addLog('큐 처리를 시작합니다...', 'info');

        // 파일들을 Base64로 변환하여 전송 (대용량의 경우 주의 필요하지만 V3 메시지 제한 내 처리 시도)
        const fileDatas = await Promise.all(selectedFiles.map(file => fileToBase64(file)));
        
        chrome.tabs.sendMessage(tab.id, {
            action: 'START_QUEUE',
            files: fileDatas.map((data, index) => ({
                id: index,
                name: selectedFiles[index].name,
                data: data,
                type: selectedFiles[index].type
            }))
        });
    });

    // 중지 버튼 클릭
    stopBtn.addEventListener('click', async () => {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        chrome.tabs.sendMessage(tab.id, { action: 'STOP_QUEUE' });
        
        startBtn.disabled = false;
        stopBtn.disabled = true;
        addLog('사용자에 의해 중지되었습니다.', 'warning');
    });

    // 컨텐츠 스크립트로부터 상태 업데이트 수신
    chrome.runtime.onMessage.addListener((message) => {
        if (message.action === 'STATUS_UPDATE') {
            const { current, total, status, log, type } = message;
            updateProgress(current, total);
            currentStatus.textContent = status;
            if (log) addLog(log, type || 'info');

            if (current === total && total > 0) {
                startBtn.disabled = false;
                stopBtn.disabled = true;
                addLog('모든 작업이 완료되었습니다!', 'success');
            }
        }
    });

    // 유틸리티: 파일을 Base64로 변환
    function fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }

    // 유틸리티: 프로그레스 바 업데이트
    function updateProgress(current, total) {
        const percentage = total > 0 ? (current / total) * 100 : 0;
        progressBar.style.width = `${percentage}%`;
        progressText.textContent = `${current} / ${total}`;
    }

    // 유틸리티: 로그 추가
    function addLog(message, type = 'info') {
        const div = document.createElement('div');
        div.className = `log-item ${type}`;
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        div.textContent = `[${time}] ${message}`;
        logContent.prepend(div);
    }
});
