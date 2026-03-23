import requests
from bs4 import BeautifulSoup

# 1. 대상 URL 설정 (네이버 금융 주요뉴스)
url = "https://media.naver.com/press/092"

# 2. 서버에 데이터 요청
# 'headers'는 내가 봇(Bot)이 아니라 사람임을 알려주는 최소한의 예의입니다.
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36'
}

response = requests.get(url, headers=headers)

soup = BeautifulSoup(response.text, 'html.parser')

# 클래스 이름으로 찾기 시도
news_items = soup.select('.press_news_item')

for item in news_items[:2]:
    title = item.select_one('.press_news_text').text.strip()
    link = item.a.get('href')

    print(f"제목: {title}")
    print(f"({link})")
    print("-" * 100)
