import requests
from bs4 import BeautifulSoup

# 1. 대상 URL 설정 (네이버 금융 주요뉴스)
url = "https://news.naver.com/"

# 2. 서버에 데이터 요청
# 'headers'는 내가 봇(Bot)이 아니라 사람임을 알려주는 최소한의 예의입니다.
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36'
}

try:
    response = requests.get(url, headers=headers)
    print(f"1. 접속 상태: {response.status_code}") # 200이 나와야 함
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 클래스 이름으로 찾기 시도
    news_items = soup.select('.cc_text_item')
    print(f"2. 찾은 뉴스 개수: {len(news_items)}개")
    
    all_lis = soup.find_all('li')
    print(f"3. 전체 li 태그 개수: {len(all_lis)}개")
    
    if len(news_items) == 0:
        print("⚠️ 클래스 이름을 못 찾았습니다. HTML 구조를 다시 확인해야 합니다.")
        # 디버깅용: HTML 내용 일부 출력
        # print(soup.prettify()[:500]) 
    
    for item in news_items:
        title_tag = item.select_one('.cc_text_a')
        if title_tag:
            print(f"뉴스 제목: {title_tag.text.strip()}")

except Exception as e:
    print(f"에러 발생: {e}")

