from playwright.sync_api import sync_playwright

# ===================== 경로 설정 (여기만 수정!) =====================
BASE_DIR = r"C:\Users\210830\Documents\coding\유튜브 자동화"
# ==================================================================

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled"]
    )
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
    )
    page = context.new_page()
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    page.goto("https://accounts.google.com")
    
    print("Google 로그인 완료 후 Enter 누르세요...")
    input()
    
    context.storage_state(path=rf"{BASE_DIR}\flow_session.json")
    print("세션 저장 완료!")
    browser.close()