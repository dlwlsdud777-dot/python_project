from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled"]
    )
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        storage_state="session.json"
    )
    page = context.new_page()
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    page.goto("https://labs.google/fx/ko/tools/flow")
    
    # 동의함 버튼 자동 클릭
    page.get_by_role("button", name="동의함").click()
    print("동의함 클릭 완료!")

    page.get_by_role("button", name="Create with Google Flow").click()
    print("Create with Google Flow 클릭 완료!")

    page.get_by_role("button", name="새 프로젝트").click()
    print("새 프로젝트 클릭 완료!")

    page.get_by_role("textbox").filter(has_text="무엇을 만들고 싶으신가요?").click()
    page.get_by_role("textbox").filter(has_text="무엇을 만들고 싶으신가요?").fill("a cute cat sitting on a cloud, dreamy atmosphere")
    print("프롬프트 입력 완료!")
    input("완료 후 Enter...")

    browser.close()