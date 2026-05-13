/**
 * Grok Looper Content Script
 * State Machine based automation for grok.com/imagine
 */

let queue = [];
let currentIndex = 0;
let isRunning = false;
let retryCount = 0;
const MAX_RETRY = 1;
const INTERACTION_TIMEOUT = 10000; // 10 seconds for DOM interaction

// --- UTILS ---

const wait = (ms) => new Promise(resolve => setTimeout(resolve, ms));

async function waitElement(selector, timeout = INTERACTION_TIMEOUT, text = null) {
    const start = Date.now();
    while (Date.now() - start < timeout) {
        let elements = document.querySelectorAll(selector);
        if (text) {
            elements = Array.from(elements).filter(el => el.textContent.includes(text));
        }
        if (elements.length > 0) return elements[0];
        await wait(500);
    }
    return null;
}

async function clickByText(text, tagName = 'button') {
    const btn = await waitElement(tagName, INTERACTION_TIMEOUT, text);
    if (btn) {
        btn.click();
        console.log(`Clicked: ${text}`);
        return true;
    }
    console.warn(`Button not found: ${text}`);
    return false;
}

function updateStatus(status, log = null, type = 'info') {
    chrome.runtime.sendMessage({
        action: 'STATUS_UPDATE',
        current: currentIndex,
        total: queue.length,
        status: status,
        log: log,
        type: type
    });
}

// --- CORE LOGIC ---

async function processNext() {
    if (!isRunning || currentIndex >= queue.length) {
        isRunning = false;
        updateStatus('완료', '모든 작업이 종료되었습니다.', 'success');
        return;
    }

    const file = queue[currentIndex];
    updateStatus(`진행 중 (${currentIndex + 1}/${queue.length})`, `[${file.name}] 처리 시작...`);

    try {
        await executeWorkflow(file);
        currentIndex++;
        retryCount = 0;
        updateStatus(`진행 중 (${currentIndex}/${queue.length})`, `[${file.name}] 성공!`, 'success');
        await wait(2000); // 다음 작업 전 여유
        processNext();
    } catch (error) {
        console.error('Workflow error:', error);
        if (retryCount < MAX_RETRY) {
            retryCount++;
            updateStatus('재시도 중', `[${file.name}] 실패, 재시도 (${retryCount}/${MAX_RETRY})...`, 'retry');
            await wait(3000);
            processNext();
        } else {
            currentIndex++;
            retryCount = 0;
            updateStatus('스킵', `[${file.name}] 10초 이상 응답 없어 스킵합니다.`, 'error');
            await wait(2000);
            processNext();
        }
    }
}

async function executeWorkflow(file) {
    // 1. 이미지 업로드
    updateStatus('업로드 중', '이미지를 업로드하고 있습니다...');
    const uploadInput = await findUploadInput();
    if (!uploadInput) throw new Error('Upload input not found');

    const blob = await (await fetch(file.data)).blob();
    const dataFile = new File([blob], file.name, { type: file.type });
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(dataFile);
    uploadInput.files = dataTransfer.files;
    uploadInput.dispatchEvent(new Event('change', { bubbles: true }));
    
    await wait(2000); // 업로드 반영 대기

    // 2. 비디오 옵션 설정
    updateStatus('옵션 설정 중', '비디오 설정을 구성하고 있습니다...');
    
    // "비디오" 선택
    await clickByText('비디오');
    await wait(500);

    // "720p" 선택
    await clickByText('720p');
    await wait(500);

    // "6s" 선택
    await clickByText('6s');
    await wait(500);

    // "종횡비" 클릭 후 "16:9" 선택
    const aspectBtn = document.querySelector('button[aria-label="종횡비"]') || 
                      Array.from(document.querySelectorAll('button')).find(el => el.textContent.includes('종횡비'));
    if (aspectBtn) {
        aspectBtn.click();
        await wait(500);
        await clickByText('16:9', 'div'); 
    }

    // 3. 프롬프트 입력
    updateStatus('프롬프트 입력 중', '프롬프트를 입력하고 있습니다...');
    const promptArea = document.querySelector('div.tiptap.ProseMirror');
    if (promptArea) {
        promptArea.innerHTML = '<p>루프영상 만들어줘</p>';
        promptArea.dispatchEvent(new Event('input', { bubbles: true }));
    }

    // 4. 생성 버튼 클릭
    updateStatus('생성 중', '영상 생성을 시작합니다...');
    const generateBtn = document.querySelector('button[aria-label="생성"]') || 
                        document.querySelector('button:has(svg)'); // 보통 입력창 옆 아이콘 버튼
    if (generateBtn) {
        generateBtn.click();
    } else {
        throw new Error('Generate button not found');
    }

    // 5. 완료 대기
    updateStatus('대기 중', '영상이 완료될 때까지 기다리는 중...');
    await waitForCompletion();
}

async function findUploadInput() {
    // Grok은 종종 숨겨진 input[type="file"]을 사용함
    let input = document.querySelector('input[type="file"]');
    if (!input) {
        const uploadBtn = document.querySelector('button[aria-label="업로드"]');
        if (uploadBtn) {
            uploadBtn.click();
            await wait(500);
            input = document.querySelector('input[type="file"]');
        }
    }
    return input;
}

async function waitForCompletion() {
    const startWait = Date.now();
    const MAX_WAIT = 300000; // 최대 5분 대기 (영상 생성 시간 고려)

    while (Date.now() - startWait < MAX_WAIT) {
        // 1. video 태그 등장 확인
        if (document.querySelector('video')) return true;
        
        // 2. 다운로드 버튼 확인
        if (document.querySelector('button[aria-label="다운로드"]')) return true;

        // 3. 로딩 스피너 사라짐 확인 (이건 보조적으로만)
        const spinner = document.querySelector('.lucide-loader-2'); // 일반적인 로딩 아이콘
        if (!spinner && (Date.now() - startWait > 10000)) {
            // 처음 10초 이후에 스피너가 없으면 완료된 것으로 간주할 수도 있음 (주의 필요)
        }

        await wait(2000);
    }
    throw new Error('Generation timeout');
}

// --- MESSAGE HANDLERS ---

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'START_QUEUE') {
        queue = message.files;
        currentIndex = 0;
        isRunning = true;
        retryCount = 0;
        processNext();
    } else if (message.action === 'STOP_QUEUE') {
        isRunning = false;
    }
});
