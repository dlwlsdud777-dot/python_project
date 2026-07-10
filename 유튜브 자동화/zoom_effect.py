import cv2
import numpy as np
import os
import subprocess
 
 
def imread_unicode(path):
    """Windows에서 cv2.imread가 한글(유니코드) 경로를 못 읽는 문제를 우회."""
    try:
        data = np.fromfile(path, dtype=np.uint8)
        return cv2.imdecode(data, cv2.IMREAD_COLOR)
    except Exception:
        return None
 
 
def imwrite_unicode(path, img):
    """Windows에서 cv2.imwrite가 한글(유니코드) 경로에 저장 못하는 문제를 우회."""
    ext = os.path.splitext(path)[1]
    result, encoded_img = cv2.imencode(ext, img)
    if result:
        encoded_img.tofile(path)
    return result
 
 
def ease_in_out(t):
    """
    선형 시간(t: 0.0~1.0)을 시작과 끝이 부드러운 S자 곡선으로 변환.
    선형 확대 배율 증가는 픽셀 단위 이동 속도가 시간에 따라 미묘하게
    달라져 '튕기는' 느낌을 주는데, 이 곡선을 거치면 훨씬 자연스러워진다.
    """
    return t * t * (3.0 - 2.0 * t)  # smoothstep
 
 
def create_target_zoom_video_cpu():
    # 1. 고정 경로 및 설정 변수 지정
    working_dir = r"C:\Users\210830\Documents\coding\유튜브 자동화\작업중"
    duration = 5      # 영상 길이 (초)
    fps = 30           # 초당 프레임 수
    zoom_rate = 0.08   # 5초 동안 총 8% 확대 (느리고 자연스러운 줌 효과)
 
    # 2. '19'로 시작하는 이미지 파일 찾기
    valid_extensions = ('.png', '.jpg', '.jpeg', '.webp')
    target_file = None
    for file in os.listdir(working_dir):
        if file.lower().startswith('19') and file.lower().endswith(valid_extensions):
            target_file = file
            break
 
    if not target_file:
        print(f"오류: '{working_dir}' 폴더에서 '19'로 시작하는 이미지 파일을 찾을 수 없습니다.")
        return
 
    image_path = os.path.join(working_dir, target_file)
    output_mp4_path = os.path.join(working_dir, "19_zoom_output.mp4")
 
    # 3. 이미지 로드 및 프레임 생성 준비
    img = imread_unicode(image_path)
    if img is None:
        print(f"이미지를 불러올 수 없습니다: {image_path}")
        return
 
    h, w, c = img.shape
    total_frames = duration * fps
 
    # 작업 중 폴더 내에 임시 프레임 저장용 폴더 생성
    temp_dir = os.path.join(working_dir, "temp_frames_19")
    os.makedirs(temp_dir, exist_ok=True)
 
    print(f"대상 파일 찾음: {target_file}")
    print(f"프레임 생성 중 (총 {total_frames}프레임)...")
 
    center_x, center_y = w / 2.0, h / 2.0
 
    # 4. warpAffine 기반 소수점 정밀 줌 (정수 절삭 없음 -> 떨림/왜곡 방지)
    for i in range(total_frames):
        # 5초 동안 부드럽게 증가하는 줌 배율 계산 (ease-in-out 적용, 절삭 없음)
        t = i / total_frames
        eased_t = ease_in_out(t)
        current_zoom = 1.0 + (zoom_rate * eased_t)
 
        # 중심 고정, scale만 적용하는 회전행렬(회전각 0)을 이용해
        # 원본 이미지를 소수점 정밀도로 확대하며 동일 캔버스 크기로 워프
        M = cv2.getRotationMatrix2D((center_x, center_y), angle=0, scale=current_zoom)
        zoomed = cv2.warpAffine(
            img, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE  # 확대 과정에서 가장자리 여백 방지
        )
 
        # 임시 이미지 저장
        imwrite_unicode(os.path.join(temp_dir, f"frame_{i:04d}.png"), zoomed)
 
    # 5. FFmpeg 범용 CPU 인코더(libx264)를 이용한 영상 생성
    print("FFmpeg를 이용해 고화질 비디오 인코딩 중 (CPU 사용)...")
    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-r', str(fps),
        '-i', os.path.join(temp_dir, 'frame_%04d.png'),
        '-c:v', 'libx264',       # 범용 CPU H.264 코덱 (그래픽카드 상관없이 작동)
        '-pix_fmt', 'yuv420p',
        '-crf', '20',             # 화질 설정 (18~23이 고화질·저용량 균형점, 낮을수록 고화질)
        '-preset', 'medium',      # 인코딩 속도/압축률 밸런스 설정
        output_mp4_path
    ]
 
    # FFmpeg 실행 (백그라운드에서 실행)
    subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
 
    # 6. 임시 파일 및 폴더 삭제
    print("임시 파일 정리 중...")
    for i in range(total_frames):
        try:
            os.remove(os.path.join(temp_dir, f"frame_{i:04d}.png"))
        except Exception:
            pass
    os.rmdir(temp_dir)
 
    print(f"✨ 영상 생성 완료!")
    print(f"생성된 파일 경로: {output_mp4_path}")
 
 
if __name__ == "__main__":
    create_target_zoom_video_cpu()