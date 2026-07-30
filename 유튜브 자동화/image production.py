# from operator import index
import random
import subprocess
import re
import json
from playwright.sync_api import sync_playwright
from pathlib import Path

# ===================== 경로 설정 (여기만 수정!) =====================
BASE_DIR = r"C:\Users\210830\Documents\coding\유튜브 자동화"
SAVE_DIR = rf"{BASE_DIR}\작업중"
# ==================================================================

def load_prompts(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def refresh_session():
    print("세션 만료! 재로그인 필요...")
    subprocess.run(["python", rf"{BASE_DIR}\flow_session.py"])
    print("세션 갱신 완료! 다시 실행해주세요.")

def human_delay(page, min_ms=500, max_ms=2000):
    page.wait_for_timeout(random.randint(min_ms, max_ms))

def run_flow(prompts, total):
    # total = len(prompts) 코드정상 작동되면 삭제
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            storage_state=rf"{BASE_DIR}\flow_session.json"
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page.goto("https://labs.google/fx/ko/tools/flow")

        page.get_by_role("button", name="동의함").click()
        print("동의함 클릭 완료!")

        page.get_by_role("button", name="Create with Google Flow").click()
        print("Create with Google Flow 클릭 완료!")

        page.wait_for_timeout(3000)
        if "accounts.google.com" in page.url:
            browser.close()
            refresh_session()
            return

        for index, item in enumerate(prompts):
            image_number = item["image_number"]
            prompt_text = item["prompt"]
            print(f"\n[{image_number}/{total}] 시작!")

            # 첫 번째만 새 프로젝트 생성
            if index % 10 == 0:
                if index > 0:  # 첫 번째는 이미 새 프로젝트 상태
                    page.go_back()  # 뒤로가기
                    page.wait_for_timeout(2000)
                page.get_by_role("button", name="add_2 새 프로젝트").click()
                print(f"새 프로젝트 클릭 완료! ({index+1}번째)")
                page.wait_for_timeout(3000)

            # 에셋 추가
            human_delay(page, 800, 2000)
            page.get_by_role("button", name="add_2 만들기").click()
            human_delay(page, 500, 1500)
            page.get_by_role("button", name=re.compile(r"arrow_drop_down")).first.click()
            human_delay(page, 300, 1000)
            page.get_by_role("menuitem", name="샘플이미지").click()
            human_delay(page, 300, 1000)
            page.get_by_test_id("virtuoso-item-list").get_by_role("img", name="적용1.png").click()

            print("에셋 추가 완료!")

            # 프롬프트 입력
            page.get_by_role("textbox").filter(has_text="무엇을 만들고 싶으신가요?").click()
            page.get_by_role("textbox").filter(has_text="무엇을 만들고 싶으신가요?").fill(prompt_text)
            print("프롬프트 입력 완료!")

            # 이미지 갯수 1 클릭
            if index % 10 == 0:
                page.wait_for_timeout(2000)
                button = page.get_by_role("button", name="🍌 Nano Banana 2 crop_16_9 x2")
                if button.is_visible():
                    button.click()
                    page.wait_for_timeout(1000)
                    page.get_by_role("tab", name="1x").click()
                    page.get_by_role("tab", name="1x").press("Escape")

                # 에이전트 버튼 활성화 여부 확인 후 비활성화
                agent_button = page.get_by_role("button", name="에이전트")
                if agent_button.is_visible():
                    class_attr = agent_button.get_attribute("class") or ""
                    aria_pressed = agent_button.get_attribute("aria-pressed") or ""
                    aria_selected = agent_button.get_attribute("aria-selected") or ""

                    if "true" in aria_pressed or "true" in aria_selected or "active" in class_attr or "selected" in class_attr:
                        agent_button.click()
                        print("에이전트 비활성화 완료!")
                        page.wait_for_timeout(500)
                    else:
                        print("에이전트 이미 비활성화 상태")

            # 만들기 버튼 클릭
            human_delay(page, 1000, 3000)
            page.get_by_role("button", name="arrow_forward 만들기").click()

            # 5번마다 휴식
            if index > 0 and index % 5 == 0:
                rest = random.randint(60000, 180000)
                print(f"잠시 휴식 중... ({rest//1000}초)")
                page.wait_for_timeout(rest)

            # 현재 이미지 개수 기억
            expected_count = (index % 10) + 1

            # 새 이미지 생성 완료 대기
            # page.wait_for_function(
            #     f"document.querySelectorAll('img[alt=\"생성된 이미지\"]').length >= {expected_count}",
            #     timeout=600000
            # )
            # print(f"[{image_number}/{total}] 이미지 생성 완료!")
            # human_delay(page, 2000, 4000)

             # 새 이미지 생성 완료 대기 (참조이미지 적용1.png는 카운트에서 제외)
            page.wait_for_function(
                f"""
                () => {{
                    const imgs = document.querySelectorAll('img[alt="생성된 이미지"]');
                    let cnt = 0;
                    imgs.forEach(img => {{
                        const tile = img.closest('div[data-tile-id]');
                        if (tile && !tile.textContent.includes('적용1.png')) cnt++;
                    }});
                    return cnt >= {expected_count};
                }}
                """,
                timeout=600000
            )
            print(f"[{image_number}/{total}] 이미지 생성 완료!")           

            # 우클릭 → 다운로드, 가장 최근 이미지 = nth(0)
            # image = page.locator("img[alt='생성된 이미지']").nth(0)
            # image.click(button="right")
            # page.wait_for_timeout(1500)

            # download_menu = page.get_by_role("menuitem", name="다운로드")
            # download_menu.hover()
            # page.wait_for_timeout(1500)

            # submenu = page.get_by_role("menuitem", name="1K 원본 크기")
            # submenu.wait_for(state="visible", timeout=10000)  # ✅ 보일 때까지 대기
            # with page.expect_download() as download_info:
            #     submenu.click()
            # download = download_info.value

            # 우클릭 → 다운로드, 참조이미지(적용1.png) 제외하고 선택
            all_images = page.locator("img[alt='생성된 이미지']")
            count = all_images.count()

            image = None
            for i in range(count):
                img = all_images.nth(i)
                tile = img.locator("xpath=ancestor::div[@data-tile-id][1]")
                tile_text = tile.evaluate("el => el.textContent")

                if "적용1.png" not in tile_text:
                    image = img
                    break

            if image is None:
                raise Exception(f"[{image_number}/{total}] 생성된 이미지를 찾지 못했습니다 (참조 이미지만 감지됨)")

            image.click(button="right")
            page.wait_for_timeout(1500)

            download_menu = page.get_by_role("menuitem", name="다운로드")
            download_menu.hover()
            page.wait_for_timeout(1500)

            submenu = page.get_by_role("menuitem", name="1K 원본 크기")
            submenu.wait_for(state="visible", timeout=10000)
            with page.expect_download() as download_info:
                submenu.click()
            download = download_info.value

            # 파일 저장
            save_path = rf"{SAVE_DIR}\{image_number:02d}.png"
            download.save_as(save_path)
            print(f"[{image_number}/{total}] 저장 완료! → {save_path}")

        print("\n전체 완료!")
        browser.close()

all_prompts = load_prompts(rf"{SAVE_DIR}\prompts.json")
total = len(all_prompts)  # ✅ 전체 개수 먼저 저장

# prompts = [
#     item for item in all_prompts
#     if not Path(rf"{SAVE_DIR}\{item['image_number']:02d}.png").exists()
# ]

def image_exists(image_number):
    for ext in ["png", "jpg", "jpeg"]:
        if Path(rf"{SAVE_DIR}\{image_number:02d}.{ext}").exists():
            return True
    return False

prompts = [
    item for item in all_prompts
    if not image_exists(item['image_number'])
]

print(f"남은 작업: {len(prompts)}개 / 전체: {total}개")
run_flow(prompts, total)  # ✅ total 같이 넘겨줌