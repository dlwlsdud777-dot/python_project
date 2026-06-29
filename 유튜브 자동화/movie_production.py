import random
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

# IMAGE_DIR = Path(r"C:\Users\balle\Documents\coding\python_project\유튜브 자동화\작업중")
IMAGE_DIR = Path(r"C:\Users\210830\Documents\coding\유튜브 자동화\작업중")
VIDEO_DIR = IMAGE_DIR / "영상제작"
VIDEO_DIR.mkdir(exist_ok=True)

def human_delay(page, min_ms=500, max_ms=2000):
    page.wait_for_timeout(random.randint(min_ms, max_ms))

def accept_cookie_popup(page):
    try:
        cookie_btn = page.locator("#onetrust-accept-btn-handler")
        if cookie_btn.is_visible(timeout=5000):
            cookie_btn.click()
            print("쿠키 동의 완료!")
            page.wait_for_timeout(1000)
    except:
        pass

def copy_image_to_clipboard(image_path: Path):
    ps_script = f"""
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    $img = [System.Drawing.Image]::FromFile('{str(image_path)}')
    [System.Windows.Forms.Clipboard]::SetImage($img)
    $img.Dispose()
    """
    subprocess.run(["powershell", "-Command", ps_script], check=True)
    print(f"클립보드 복사 완료: {image_path.name}")

def skip_feedback_popup(page):
    """피드백 팝업 건너뛰기"""
    try:
        skip_btn = page.get_by_role("button", name="건너뛰기")
        if skip_btn.is_visible(timeout=3000):
            skip_btn.click()
            print("피드백 팝업 건너뛰기!")
            page.wait_for_timeout(1000)
    except:
        pass

def run_grok_video():
    # ✅ 이미지 목록 확인 (숫자 파일명 + png/jpg 모두 포함)
    image_paths = sorted(
        [p for p in IMAGE_DIR.iterdir() 
         if p.suffix.lower() in (".png", ".jpg", ".jpeg") and p.stem.isdigit()],
        key=lambda p: int(p.stem)
    )
    
    total = len(image_paths)

    # ✅ 이미 영상이 있는 번호는 건너뜀
    image_paths = [
        p for p in image_paths
        if not (VIDEO_DIR / f"{int(p.stem):02d}.mp4").exists()
    ]
    
    
    print(f"총 {total}개 이미지 처리 시작!")
    for p in image_paths:
        print(f"  - {p.name}")  # 어떤 파일 잡혔는지 확인용

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=r"C:\Users\210830\AppData\Local\Playwright\grok_profile",
            # user_data_dir=r"C:\Users\balle\AppData\Local\Playwright\grok_profile",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # ✅ 타임아웃 늘리고 domcontentloaded로 완화
        page.goto("https://grok.com/", timeout=60000, wait_until="domcontentloaded")
        accept_cookie_popup(page)
        human_delay(page, 2000, 3000)

        # Imagine 탭 → 비디오 설정 (최초 1회)
        page.get_by_role("listitem").filter(has_text="Imagine").get_by_role("link").click()
        human_delay(page, 1000, 2000)

        page.get_by_role("radio", name="비디오").click()
        human_delay(page, 500, 1000)

        page.get_by_role("radio", name="480p").click()
        human_delay(page, 300, 700)

        page.get_by_role("radio", name="6s").click()
        human_delay(page, 300, 700)

        page.get_by_role("button", name="종횡비").click()
        human_delay(page, 300, 700)
        page.get_by_text(":9와이드스크린").click()
        human_delay(page, 500, 1000)

        print("초기 설정 완료!")

        for idx, image_path in enumerate(image_paths):
            image_number = int(image_path.stem)
            print(f"\n[{image_number}/{total}] 영상 제작 시작!")

            copy_image_to_clipboard(image_path)
            human_delay(page, 500, 1000)

            input_area = page.get_by_role("paragraph")
            input_area.click()
            human_delay(page, 300, 600)
            page.keyboard.press("Control+v")
            human_delay(page, 1000, 2000)

            page.get_by_role("textbox", name="Ask Grok anything").fill("루프영상만들어줘")
            human_delay(page, 500, 1000)

            page.get_by_role("button", name="제출").click()
            print(f"[{image_number}/{total}] 생성 요청 완료! 대기 중...")

            # ✅ 피드백 팝업이 뜰 수 있으므로 주기적으로 체크하며 대기, 재생 중 영상만 확인
            for _ in range(120):  # 최대 10분 (5초 * 120)
                skip_feedback_popup(page)  # 팝업 체크
                try:
                    # ✅ video 태그가 실제 재생 중인지 확인
                    is_playing = page.evaluate("""
                        () => {
                            const video = document.querySelector('video');
                            return video && !video.paused && video.currentTime > 0;
                        }
                    """)
                    if is_playing:
                        print(f"[{image_number}/{total}] 영상 생성 완료!")
                        break
                except:
                    pass
                page.wait_for_timeout(5000)
            else:
                print(f"[{image_number}/{total}] ❌ 타임아웃 - 다음으로 넘어갑니다")
                page.go_back()
                page.wait_for_timeout(5000)
                continue

            human_delay(page, 1000, 2000)

            # 다운로드
            save_path = VIDEO_DIR / f"{image_number:02d}.mp4"
            # with page.expect_download() as download_info:
            #     page.locator(
            #         "[aria-label='다운로드']:not([disabled]), [aria-label='Download']:not([disabled])"
            #     ).first.click()
            with page.expect_download() as download_info:
                page.get_by_role("button", name="다운로드").click()
            download = download_info.value
            download.save_as(save_path)
            print(f"[{image_number}/{total}] 저장 완료! → {save_path}")

            # 뒤로가기
            human_delay(page, 1500, 2500)
            page.go_back()
            page.wait_for_timeout(5000)

            # ✅ 입력창이 완전히 활성화될 때까지 대기
            page.wait_for_selector(
                "p[data-placeholder]:not([disabled])",
                state="visible",
                timeout=30000
            )
            human_delay(page, 2000, 3000)  # 추가 안정화 대기

            if idx > 0 and idx % 5 == 0:
                rest = random.randint(60, 180)
                print(f"휴식 중... ({rest}초)")
                page.wait_for_timeout(rest * 1000)
            else:
                human_delay(page, 2000, 5000)

        print("\n✅ 전체 완료!")
        context.close()

run_grok_video()