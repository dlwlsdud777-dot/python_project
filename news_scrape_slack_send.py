import requests
from bs4 import BeautifulSoup
import time
import os
import logging
from google import genai

logging.getLogger("google_genai").setLevel(logging.ERROR)

# ============================================================
# Gemini API 설정
# ============================================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)
GEMINI_MODEL_NAMES = [
    "gemini-3.7-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
]

WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36'
}

# 대상 언론사 (언론사 코드: 이름)
PRESS_DICT = {
    "009": "매일경제",
    "138": "디지털데일리",
    "092": "지디넷코리아",
}

ARTICLES_PER_PRESS = 2  # 언론사별로 가져올 기사 수


# ============================================================
# 기사 본문 크롤링
# ============================================================
def fetch_article_text(url: str) -> str:
    res = requests.get(url, headers=HEADERS, timeout=10)
    res.raise_for_status()
    res.encoding = res.apparent_encoding

    article_soup = BeautifulSoup(res.text, 'html.parser')
    body = article_soup.find(id='dic_area') or article_soup.find(id='newsct_article')

    if body is None:
        paragraphs = article_soup.find_all('p')
        text = "\n".join(p.get_text(strip=True) for p in paragraphs)
    else:
        text = body.get_text(separator="\n", strip=True)

    return text.strip()


# ============================================================
# Gemini 요약
# ============================================================
def summarize_with_gemini(text: str) -> str:
    if not text:
        return "(본문을 가져오지 못해 요약할 수 없습니다.)"

    prompt = f"""다음 뉴스 기사를 한국어로 핵심만 3줄 이내로 요약해줘.
불필요한 수식어는 빼고, 사실 위주로 간결하게 정리해줘.

기사 본문:
{text}
"""
    for model_name in GEMINI_MODEL_NAMES:
        max_retries = 2
        for attempt in range(1, max_retries + 1):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                return response.text.strip()
            except Exception as e:
                error_text = str(e)
                is_last_attempt = (attempt == max_retries)

                if "503" in error_text and not is_last_attempt:
                    wait_seconds = 5 * attempt
                    print(f"  ({model_name}, {attempt}/{max_retries}차 시도 실패, 서버 과부하. {wait_seconds}초 후 재시도)")
                    time.sleep(wait_seconds)
                    continue

                if "429" in error_text:
                    print(f"  ({model_name} 할당량 초과 -> 다음 모델로 즉시 전환)")
                    break

                print(f"  ({model_name} 실패: {e} -> 다음 모델로 전환)")
                break

    return "(요약 실패: 모든 모델에서 응답을 받지 못했습니다)"


# ============================================================
# [핵심 리팩토링] 언론사 하나를 크롤링 + 요약까지 처리하는 함수
# 반환값: [{"title":..., "link":..., "summary":...}, ...]
# ============================================================
def fetch_press_news(press_code: str, press_name: str, limit: int = ARTICLES_PER_PRESS) -> list[dict]:
    url = f"https://media.naver.com/press/{press_code}"
    print(f"\n=== [{press_name}] 뉴스 수집 시작 ===")

    articles = []
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = soup.select('.press_news_item')

        for item in news_items[:limit]:
            title = item.select_one('.press_news_text').text.strip()
            link = item.a.get('href')

            try:
                article_text = fetch_article_text(link)
                summary = summarize_with_gemini(article_text)
            except Exception as e:
                print(f"[요약 실패] {e}")
                summary = "(요약 실패)"

            articles.append({"title": title, "link": link, "summary": summary})

    except Exception as e:
        print(f"{press_name} 수집 중 오류 발생: {e}")

    return articles


# ============================================================
# 슬랙 전송 - Block Kit 사용
# 언론사별로 헤더 + 구분선 + 기사 목록을 하나의 메시지에 담음
# ============================================================
def build_blocks(press_name: str, articles: list[dict]) -> list[dict]:
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"📢 {press_name} 주요 뉴스"}
        },
        {"type": "divider"},
    ]

    for article in articles:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*<{article['link']}|{article['title']}>*\n{article['summary']}"
            }
        })
        blocks.append({"type": "divider"})

    return blocks


def send_slack_blocks(press_name: str, articles: list[dict]):
    if not articles:
        return

    blocks = build_blocks(press_name, articles)
    data = {"blocks": blocks}

    try:
        response = requests.post(WEBHOOK_URL, json=data, timeout=5)
        if response.status_code != 200:
            print("슬랙 전송 실패:", response.text)
    except Exception as e:
        print("슬랙 오류:", e)


# ============================================================
# 메인 로직 - 이제 흐름이 한눈에 보임
# ============================================================
def main():
    for press_code, press_name in PRESS_DICT.items():
        articles = fetch_press_news(press_code, press_name)
        send_slack_blocks(press_name, articles)
        time.sleep(0.5)

    print("\n모든 뉴스 수집 & 슬랙 전송 완료")


if __name__ == "__main__":
    main()