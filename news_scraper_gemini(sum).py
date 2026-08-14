import requests
from bs4 import BeautifulSoup
import time
import os                    # [신규 추가] 환경변수에서 API 키 읽기 위해 필요
import logging               # [신규 추가] SDK가 출력하는 AFC 안내 경고를 숨기기 위해 필요
from google import genai     # [수정] google-generativeai(구 SDK, 폐지됨) -> google-genai(신규 SDK)로 변경

# [신규 추가] google_genai 로거의 레벨을 ERROR로 올려서
#            "Direct use of automatic function calling..." 같은 안내성 경고를 숨김
logging.getLogger("google_genai").setLevel(logging.ERROR)

# ============================================================
# [신규 추가] Gemini API 설정
# - 발급: https://aistudio.google.com/apikey
# - 환경변수 GEMINI_API_KEY 로 등록해두는 것을 권장
# [수정] 구 SDK는 genai.configure() + GenerativeModel() 방식이었지만,
#        신규 SDK는 genai.Client() 하나로 클라이언트를 만들고 이걸로 호출합니다.
# ============================================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)  # [수정] genai.configure() 대신 Client 객체 생성
GEMINI_MODEL_NAMES = [
    "gemini-3.7-flash",        # 최신 Flash, 한국어 문맥/요약/추론 성능 우수
    "gemini-3.5-flash-lite",   # 가볍고 빠름, 단순 요약에 적합
    "gemini-3.6-flash",        # 보조 폴백
]

# ============================================================
# [신규 추가] 기사 본문 크롤링 함수
# 각 언론사 기사 링크(link)에 접속해서 본문 텍스트를 추출한다.
# ============================================================
def fetch_article_text(url: str) -> str:
    res = requests.get(url, headers=headers, timeout=10)
    res.raise_for_status()
    res.encoding = res.apparent_encoding

    article_soup = BeautifulSoup(res.text, 'html.parser')

    # 네이버 뉴스 본문 태그 후보 (버전에 따라 다를 수 있어 순서대로 시도)
    body = article_soup.find(id='dic_area') or article_soup.find(id='newsct_article')

    if body is None:
        # 본문 태그를 못 찾으면 <p> 태그를 모두 이어붙임 (정확도는 다소 떨어질 수 있음)
        paragraphs = article_soup.find_all('p')
        text = "\n".join(p.get_text(strip=True) for p in paragraphs)
    else:
        text = body.get_text(separator="\n", strip=True)

    return text.strip()


# ============================================================
# [신규 추가] Gemini 요약 함수
# ============================================================
def summarize_with_gemini(text: str) -> str:
    if not text:
        return "(본문을 가져오지 못해 요약할 수 없습니다.)"

    prompt = f"""다음 뉴스 기사를 한국어로 핵심만 3줄 이내로 요약해줘.
불필요한 수식어는 빼고, 사실 위주로 간결하게 정리해줘.

기사 본문:
{text}
"""
    # [수정] 모델 1개로 재시도만 반복하던 방식 -> 여러 모델을 순서대로 갈아타는 방식으로 변경
    for model_name in GEMINI_MODEL_NAMES:
        max_retries = 2  # 503(일시적 과부하)에 한해서만 재시도
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
                    # 503(일시적 서버 과부하) -> 같은 모델로 잠깐 기다렸다 재시도
                    wait_seconds = 5 * attempt
                    print(f"  ({model_name}, {attempt}/{max_retries}차 시도 실패, 서버 과부하. {wait_seconds}초 후 재시도)")
                    time.sleep(wait_seconds)
                    continue
 
                if "429" in error_text:
                    # [신규 추가] 429(할당량 초과) -> 재시도 소용없음, 바로 다음 모델로 전환
                    print(f"  ({model_name} 할당량 초과 -> 다음 모델로 즉시 전환)")
                    break
 
                # 그 외 에러(503 마지막 시도 포함) -> 다음 모델로 전환
                print(f"  ({model_name} 실패: {e} -> 다음 모델로 전환)")
                break
 
    # [신규 추가] 모든 모델을 다 시도했는데도 실패한 경우
    return "(요약 실패: 모든 모델에서 응답을 받지 못했습니다)"


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

            # ============================================================
            # [신규 추가] 기사 본문을 가져와 Gemini로 요약 후 출력
            # ============================================================
            try:
                article_text = fetch_article_text(link)
                summary = summarize_with_gemini(article_text)
                print(f"[요약] {summary}")
            except Exception as e:
                print(f"[요약 실패] {e}")

            print("-" * 100)

        time.sleep(0.5)

    except Exception as e:
        print(f"{press_name} 수집 중 오류 발생: {e}")

print("\n모든 뉴스 수집이 완료되었습니다.")