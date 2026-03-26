import requests
from bs4 import BeautifulSoup
import time

# 1. 대상 언론사 설정 (언론사 코드: 이름)
press_dict = {
    "009": "매일경제",
    "138": "디지털데일리",
    "092": "지디넷코리아"
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36'
}

# 2. 반복문을 통해 각 언론사 순회
for press_code, press_name in press_dict.items():
    url = f"https://media.naver.com/press/{press_code}"
    print(f"\n=== [{press_name}] 뉴스 수집 시작 ===")

    try:

        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = soup.select('.press_news_item')

        for item in news_items[:2]:
            title = item.select_one('.press_news_text').text.strip()
            link = item.a.get('href')

            print(f"제목: {title}")
            print(f"({link})")
            print("-" * 100)

        time.sleep(0.5)

    except Exception as e:
        print(f"{press_name} 수집 중 오류 발생: {e}")

print("\n모든 뉴스 수집이 완료되었습니다.")
