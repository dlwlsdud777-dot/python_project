import random
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

IMAGE_DIR = Path(r"C:\Users\210830\Documents\coding\유튜브 작업중")
VIDEO_DIR = IMAGE_DIR / "영상제작"
DEBUG_DIR = IMAGE_DIR / "debug"
VIDEO_DIR.mkdir(exist_ok=True)
DEBUG_DIR.mkdir(exist_ok=True)

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

def run_grok_video():
    image_paths = sorted(
        [p for p in IMAGE_DIR.iterdir()
         if p.suffix.lower() in (".png", ".jpg", ".jpeg") and p.stem.isdigit()],
        key=lambda p: int(p.stem)
    )
    total = len(image_paths)
    print(f"총 {total}개 이미지 처리 시작!")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=r"C:\Users\210830\AppData\Local\Playwright\grok_profile",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        page.goto("https://grok.com/", timeout=60000, wait_until="domcontentloaded")
        accept_cookie_popup(page)
        human_delay(page, 2000, 3000)

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

        # ✅ 1번 이미지만 테스트
        image_path = image_paths[0]
        image_number = int(image_path.stem)
        print(f"\n[테스트] {image_path.name} 시작!")

        copy_image_to_clipboard(image_path)
        human_delay(page, 500, 1000)

        # 입력창 붙여넣기
        page.get_by_role("paragraph").click()
        human_delay(page, 500, 1000)
        page.keyboard.press("Control+v")
        human_delay(page, 2000, 3000)

        # ✅ 붙여넣기 직후 스크린샷
        page.screenshot(path=str(DEBUG_DIR / "01_after_paste.png"))
        print("스크린샷 저장: 01_after_paste.png")

        page.get_by_role("textbox", name="Ask Grok anything").fill("루프영상만들어줘")
        human_delay(page, 500, 1000)

        # ✅ 제출 직전 스크린샷
        page.screenshot(path=str(DEBUG_DIR / "02_before_submit.png"))
        print("스크린샷 저장: 02_before_submit.png")

        page.get_by_role("button", name="제출").click()
        print("제출 완료! 30초 후 스크린샷 찍습니다...")

        # ✅ 30초 후 상태 확인
        page.wait_for_timeout(30000)
        page.screenshot(path=str(DEBUG_DIR / "03_after_30s.png"))
        print("스크린샷 저장: 03_after_30s.png")

        print("\n✅ 디버그 완료! debug 폴더의 스크린샷 3장을 확인해주세요.")
        input("확인 후 Enter 누르면 종료...")
        context.close()

run_grok_video()