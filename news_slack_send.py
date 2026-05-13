import requests
from bs4 import BeautifulSoup
import time
import os

WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')

def send_slack(message):
    data = {"text": message}
    try:
        response = requests.post(WEBHOOK_URL, json=data, timeout=5)
        if response.status_code != 200:
            print("슬랙 전송 실패:", response.text)
    except Exception as e:
        print("슬랙 오류:", e)

press_dict = {
    "009": "매일경제",
    "138": "디지털데일리",
    "092": "지디넷코리아"
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36'
}

for press_code, press_name in press_dict.items():
    url = f"https://media.naver.com/press/{press_code}"
    print(f"\n=== [{press_name}] 뉴스 수집 시작 ===")

    try:

        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = soup.select('.press_news_item')

        message = f"📢 [{press_name}] 주요 뉴스\n\n"

        for item in news_items[:2]:
            title = item.select_one('.press_news_text').text.strip()
            link = item.a.get('href')

            message += f"• {title}\n{link}\n\n"

        send_slack(message)
        time.sleep(0.5)

    except Exception as e:
        print(f"{press_name} 수집 중 오류 발생: {e}")

print("\n모든 뉴스 수집 완료 & 슬랙 전송 완료")




