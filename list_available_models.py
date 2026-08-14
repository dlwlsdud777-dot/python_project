"""
현재 GEMINI_API_KEY로 실제 사용 가능한 모델 목록을 확인하는 스크립트.
(추측으로 모델명을 넣지 않고, API에 직접 물어봐서 정확한 목록을 얻기 위함)
"""

import os
from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

print("=== 이 API 키로 사용 가능한 모델 목록 ===\n")

for model in client.models.list():
    # generateContent(텍스트 생성)를 지원하는 모델만 필터링
    if "generateContent" in getattr(model, "supported_actions", []):
        print(f"- {model.name}")
