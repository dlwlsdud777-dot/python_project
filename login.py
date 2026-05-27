import subprocess
import re
from playwright.sync_api import sync_playwright

def refresh_session():
    print("세션 만료! 재로그인 필요...")
    subprocess.run(["python", "session.py"])
    print("세션 갱신 완료! 다시 실행해주세요.")

def run_flow():
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

        page.get_by_role("button", name="동의함").click()
        print("동의함 클릭 완료!")

        page.get_by_role("button", name="Create with Google Flow").click()
        print("Create with Google Flow 클릭 완료!")

        # 세션 만료 감지
        page.wait_for_timeout(3000)
        if "accounts.google.com" in page.url:
            browser.close()
            refresh_session()
            return

        page.get_by_role("button", name="새 프로젝트").click()
        print("새 프로젝트 클릭 완료!")

        page.wait_for_timeout(3000)

        # 에셋 추가
        page.get_by_role("button", name="add_2 만들기").click()
        # 드롭다운에서 첫 번째 항목 선택 (날짜/시간 무관)
        page.get_by_role("button", name=re.compile(r"arrow_drop_down")).first.click()
        page.get_by_role("menuitem", name="샘플이미지").click()
        page.get_by_test_id("virtuoso-item-list").get_by_role("img", name="적용1.png").click()
        print("에셋 추가 완료!")

        # 프롬프트 입력
        page.get_by_role("textbox").filter(has_text="무엇을 만들고 싶으신가요?").click()
        page.get_by_role("textbox").filter(has_text="무엇을 만들고 싶으신가요?").fill("a cute cat sitting on a cloud, dreamy atmosphere")
        print("프롬프트 입력 완료!")

        # 이미지 갯수 1 클릭
        page.get_by_role("button", name="🍌 Nano Banana 2 crop_16_9 x2").click()
        page.get_by_role("tab", name="1x").click()
        page.get_by_role("tab", name="1x").press("Escape")

        # 버튼 클릭
        page.get_by_role("button", name="arrow_forward 만들기").click()

        input("완료 후 Enter...")
        browser.close()

run_flow()