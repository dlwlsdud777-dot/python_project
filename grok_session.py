from playwright.sync_api import sync_playwright

def accept_cookie_popup(page):
    try:
        cookie_btn = page.locator("#onetrust-accept-btn-handler")
        if cookie_btn.is_visible(timeout=5000):
            cookie_btn.click()
            print("쿠키 동의 완료!")
            page.wait_for_timeout(1000)
    except:
        pass

def save_session():
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=r"C:\Users\210830\AppData\Local\Playwright\grok_profile",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page.goto("https://grok.com/")
        accept_cookie_popup(page)
        
        print("브라우저에서 직접 로그인해주세요.")
        print("로그인 완료되면 자동 감지합니다...")

        page.wait_for_selector(
            "div[contenteditable='true'], [data-testid='chat-input']",
            timeout=120000
        )
        page.wait_for_timeout(2000)
        print("✅ 로그인 완료! 이제 본 스크립트를 실행하세요!")
        context.close()

save_session()