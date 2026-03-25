import requests

TOKEN = "8644879486:AAGdBLYfeFtbcNJjMOQYMTVUhhWJciVHD-M"
CHAT_ID = "8785799433"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    requests.post(url, data=data)

# 테스트
send_telegram("테스트 메시지입니다 🚀")