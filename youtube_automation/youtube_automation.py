"""
유튜브 영상 자동 편집 스크립트
- SRT 자막 파일과 JSON 파일을 읽어서
- 각 image_number에 해당하는 영상을 자막 구간 길이에 맞게 반복/편집
- 자막 텍스트를 영상에 오버레이
- 음성 파일을 합쳐서 최종 MP4 저장
"""

import json
import re
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips

# =============================================
# 설정 (경로를 본인 환경에 맞게 수정하세요)
# =============================================
BASE_DIR = r"C:\Users\210830\Documents\coding\youtube_automation"
SRT_FILE = os.path.join(BASE_DIR, "20260531_강아지가_떠난_날_.srt")
JSON_FILE = os.path.join(BASE_DIR, "gemini-code-1780191119015.json")
AUDIO_FILE = os.path.join(BASE_DIR, "20260531_강아지가_떠난_날_.mp3")
VIDEOS_DIR = BASE_DIR
OUTPUT_FILE = os.path.join(BASE_DIR, "output_final.mp4")

FONT_PATH = "C:/Windows/Fonts/malgunbd.ttf"  # 한국어 폰트 (맑은 고딕 Bold)
FONT_SIZE = 28                                # 자막 글씨 크기
FONT_COLOR = (255, 255, 255, 255)             # 자막 글씨 색상 (흰색)
BG_COLOR = (0, 0, 0, 180)                     # 자막 배경 색상 (반투명 검정)
SUBTITLE_PADDING_X = 16                       # 배경 좌우 여백 (픽셀)
SUBTITLE_PADDING_Y = 10                       # 배경 상하 여백 (픽셀)
SUBTITLE_BOTTOM_MARGIN = 5                    # 하단 여백 (픽셀) - 줄일수록 아래로
# =============================================


def parse_srt(srt_path):
    """SRT 파일을 읽어서 자막 리스트로 반환"""
    with open(srt_path, "r", encoding="utf-8-sig") as f:
        content = f.read()

    pattern = r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.+?)(?=\n\n|\Z)"
    matches = re.findall(pattern, content.strip(), re.DOTALL)

    subtitles = []
    for match in matches:
        number, start_str, end_str, text = match
        subtitles.append({
            "number": int(number),
            "start": srt_time_to_seconds(start_str),
            "end": srt_time_to_seconds(end_str),
            "text": text.strip()
        })
    return subtitles


def srt_time_to_seconds(time_str):
    """00:00:13,600 형식을 초(float)로 변환"""
    time_str = time_str.replace(",", ".")
    h, m, s = time_str.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def match_json_to_srt(json_data, subtitles):
    """
    JSON의 script_text와 SRT 자막을 매칭해서
    각 image_number의 시작/끝 시간을 계산
    """
    result = []
    srt_index = 0

    for item in json_data:
        image_number = item["image_number"]
        script_text = item["script_text"]

        script_tokens = re.sub(r'[^\w\s]', '', script_text).split()

        start_time = subtitles[srt_index]["start"] if srt_index < len(subtitles) else 0
        end_time = start_time
        matched_text = ""

        while srt_index < len(subtitles):
            srt_text = re.sub(r'[^\w\s]', '', subtitles[srt_index]["text"])
            matched_text += " " + srt_text
            matched_text = matched_text.strip()
            end_time = subtitles[srt_index]["end"]
            srt_index += 1

            coverage = sum(1 for t in script_tokens if t in matched_text) / len(script_tokens)
            if coverage >= 0.80:
                break

        result.append({
            "image_number": image_number,
            "start": start_time,
            "end": end_time,
            "duration": end_time - start_time,
            "script_text": script_text
        })

        print(f"[매칭] image {image_number}: {start_time:.2f}초 ~ {end_time:.2f}초 ({end_time - start_time:.2f}초)")

    return result


def make_subtitle_image(text, video_w):
    """
    PIL로 자막 이미지를 직접 그려서 반환
    - 텍스트에 맞는 배경 크기 자동 계산
    - 텍스트를 배경 안에서 정확히 세로 중앙 정렬
    """
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    # 텍스트 크기 측정
    dummy_img = Image.new("RGBA", (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_img)
    bbox = dummy_draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # 배경 크기 = 텍스트 + 패딩
    bg_w = text_w + SUBTITLE_PADDING_X * 2
    bg_h = text_h + SUBTITLE_PADDING_Y * 2

    # 배경 이미지 생성 (투명 배경)
    img = Image.new("RGBA", (bg_w, bg_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 반투명 배경 직사각형 그리기
    draw.rectangle([(0, 0), (bg_w - 1, bg_h - 1)], fill=BG_COLOR)

    # 텍스트를 배경 안에서 정확히 중앙 정렬
    text_x = SUBTITLE_PADDING_X - bbox[0]
    text_y = SUBTITLE_PADDING_Y - bbox[1]
    draw.text((text_x, text_y), text, font=font, fill=FONT_COLOR)

    return np.array(img)


def make_segment(video_path, target_duration, subtitles_in_range, video_size):
    """
    5초 영상을 target_duration에 맞게 반복/자르기
    PIL로 그린 자막 이미지를 오버레이
    """
    clip = VideoFileClip(video_path)
    clip_duration = clip.duration

    # 목표 길이만큼 반복해서 이어붙이기
    loops_needed = int(target_duration / clip_duration) + 1
    repeated_clips = [clip] * loops_needed
    looped = concatenate_videoclips(repeated_clips)
    looped = looped.subclipped(0, target_duration)

    video_w, video_h = video_size

    # 자막 오버레이
    text_clips = []
    for sub in subtitles_in_range:
        relative_start = sub["start"] - subtitles_in_range[0]["start"]
        relative_end = sub["end"] - subtitles_in_range[0]["start"]
        sub_duration = relative_end - relative_start

        try:
            # PIL로 자막 이미지 생성
            subtitle_img = make_subtitle_image(sub["text"], video_w)
            img_h, img_w = subtitle_img.shape[:2]

            # 위치: 하단 중앙
            txt_x = (video_w - img_w) // 2
            txt_y = video_h - img_h - SUBTITLE_BOTTOM_MARGIN

            txt_clip = (ImageClip(subtitle_img)
                        .with_position((txt_x, txt_y))
                        .with_start(relative_start)
                        .with_duration(sub_duration))
            text_clips.append(txt_clip)

        except Exception as e:
            print(f"  ⚠️  자막 생성 실패 ({sub['text'][:10]}...): {e}")

    if text_clips:
        segment = CompositeVideoClip([looped] + text_clips, size=video_size)
    else:
        segment = looped

    return segment


def main():
    print("=" * 50)
    print("유튜브 영상 자동 편집 시작")
    print("=" * 50)

    # 1. SRT 파싱
    print("\n[1단계] SRT 파일 읽는 중...")
    subtitles = parse_srt(SRT_FILE)
    print(f"  → 자막 {len(subtitles)}개 읽음")

    # 2. JSON 파싱
    print("\n[2단계] JSON 파일 읽는 중...")
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    print(f"  → 이미지 {len(json_data)}개 읽음")

    # 3. JSON과 SRT 매칭
    print("\n[3단계] 자막 구간 매칭 중...")
    segments_info = match_json_to_srt(json_data, subtitles)

    # 4. 각 세그먼트 영상 생성
    print("\n[4단계] 세그먼트 영상 생성 중...")
    segment_clips = []

    first_video = VideoFileClip(os.path.join(VIDEOS_DIR, "1.mp4"))
    video_size = first_video.size
    first_video.close()
    print(f"  → 영상 크기: {video_size[0]}x{video_size[1]}")

    for seg in segments_info:
        image_num = seg["image_number"]
        video_path = os.path.join(VIDEOS_DIR, f"{image_num}.mp4")

        if not os.path.exists(video_path):
            print(f"  ⚠️  {image_num}.mp4 파일 없음, 건너뜀")
            continue

        print(f"  → {image_num}.mp4 처리 중... ({seg['duration']:.2f}초)")

        subs_in_range = [
            s for s in subtitles
            if s["start"] >= seg["start"] - 0.1 and s["end"] <= seg["end"] + 0.1
        ]

        clip = make_segment(video_path, seg["duration"], subs_in_range, video_size)
        segment_clips.append(clip)

    # 5. 전체 이어붙이기
    print("\n[5단계] 전체 영상 이어붙이는 중...")
    final_video = concatenate_videoclips(segment_clips)

    # 6. 음성 파일 합치기
    print("\n[6단계] 음성 파일 합치는 중...")
    if os.path.exists(AUDIO_FILE):
        audio = AudioFileClip(AUDIO_FILE)
        audio = audio.subclipped(0, min(audio.duration, final_video.duration))
        final_video = final_video.with_audio(audio)
        print(f"  → 음성 파일 적용 완료 ({audio.duration:.2f}초)")
    else:
        print(f"  ⚠️  음성 파일 없음: {AUDIO_FILE}")

    # 7. 최종 저장
    print(f"\n[7단계] 최종 영상 저장 중...")
    print(f"  → 저장 경로: {OUTPUT_FILE}")
    final_video.write_videofile(
        OUTPUT_FILE,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        threads=4
    )

    print("\n" + "=" * 50)
    print("✅ 완료! output_final.mp4 확인하세요")
    print("=" * 50)


if __name__ == "__main__":
    main()