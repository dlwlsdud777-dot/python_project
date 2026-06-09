import os
from moviepy import VideoFileClip

BASE_DIR = r"C:\Users\210830\Documents\coding\youtube_automation"

for i in range(1, 31):  # 1~30
    video_path = os.path.join(BASE_DIR, f"{i}.mp4")
    if os.path.exists(video_path):
        v = VideoFileClip(video_path)
        print(f"{i}.mp4: {v.size}  ({v.duration:.2f}초)")
        v.close()
    else:
        print(f"{i}.mp4: 없음")