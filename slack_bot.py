import requests
import os

WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')

def send_slack(message):
    if not WEBHOOK_URL:
        print("SLACK_WEBHOOK_URL 환경 변수가 설정되지 않았습니다.")
        return
    
    data = {
        "text": message
    }

    response = requests.post(WEBHOOK_URL, json=data)

    if response.status_code == 200:
        print("전송 성공 👍")
    else:
        print("전송 실패", response.text)

# 테스트
send_slack("메시지 전달")