import requests
from bs4 import BeautifulSoup

BASE_URL = "https://finance.naver.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
}


def fetch_main_news(limit: int = 10):
    """네이버 금융 메인 페이지에서 주요뉴스 제목과 링크를 가져옵니다."""
    response = requests.get(BASE_URL, headers=HEADERS, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    section = soup.select_one("div.news_area div.section_strategy")
    if not section:
        raise ValueError("네이버 금융 주요뉴스 섹션을 찾을 수 없습니다.")

    news_items = []
    for anchor in section.select("ul li span a")[:limit]:
        title = anchor.get_text(strip=True)
        href = anchor.get("href")
        if not href:
            continue
        if href.startswith("/"):
            href = BASE_URL + href

        news_items.append({
            "title": title,
            "link": href,
        })

    return news_items


if __name__ == "__main__":
    try:
        news_list = fetch_main_news(limit=10)
        print("네이버 금융 주요뉴스\n")
        for idx, item in enumerate(news_list, start=1):
            print(f"{idx}. {item['title']}")
            print(item["link"])
            print()
    except Exception as exc:
        print("뉴스를 가져오는 중 오류가 발생했습니다:", exc)
