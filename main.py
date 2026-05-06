import time
import requests
import re
import subprocess
import threading

# 대상 CCTV URL 목록
URLS = {
    "118084": "https://hrfco.go.kr/sumun/cctvPopup.do?Obscd=118084",
    "116010": "https://hrfco.go.kr/sumun/cctvPopup.do?Obscd=116010"
}

def get_m3u8_url(page_url):
    """웹페이지 HTML에서 m3u8(HLS) 스트리밍 주소를 추출합니다."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36"
        }
        response = requests.get(page_url, headers=headers, timeout=10)
        
        # HTML 소스 내에서 m3u8 링크를 정규식으로 찾습니다.
        # (주의: 사이트 구조가 복잡하거나 API로 토큰을 받아오는 방식이라면, 크롬 개발자 도구(F12)의 Network 탭을 확인해 정규식을 수정해야 할 수 있습니다.)
        match = re.search(r'(https?://[^\s"\'<>]+m3u8[^\s"\']*)', response.text)
        if match:
            return match.group(1)
            
        print(f"[{page_url}]에서 m3u8 URL을 찾을 수 없습니다. 페이지 소스를 확인하세요.")
    except Exception as e:
        print(f"[{page_url}] 요청 중 에러 발생: {e}")
    return None

def stream_worker(obscd, page_url):
    # MediaMTX 컨테이너로 푸시할 RTSP 주소
    rtsp_url = f"rtsp://mediamtx:8554/cctv/{obscd}"
    
    while True:
        m3u8_url = get_m3u8_url(page_url)
        if not m3u8_url:
            print(f"[{obscd}] 스트림 URL을 찾지 못했습니다. 30초 후 재시도...")
            time.sleep(30)
            continue
            
        print(f"[{obscd}] FFmpeg 스트리밍 시작: {m3u8_url} -> {rtsp_url}")
        
        # FFmpeg를 사용하여 HLS를 RTSP로 변환 (-c:v copy로 재인코딩 없이 전달하여 CPU 최적화)
        cmd = [
            "ffmpeg",
            "-y",
            "-re",
            "-i", m3u8_url,
            "-c:v", "copy",
            "-c:a", "copy",
            "-f", "rtsp",
            "-rtsp_transport", "tcp",
            rtsp_url
        ]
        
        process = subprocess.Popen(cmd)
        process.wait() # 스트림이 끊기거나 종료될 때까지 대기
        
        print(f"[{obscd}] FFmpeg 프로세스가 종료되었습니다. 스트림 복구를 위해 10초 후 재시작합니다...")
        time.sleep(10)

if __name__ == "__main__":
    print("RTSP 변환 워커 시작...")
    threads = []
    # 각 CCTV 별로 독립적인 스레드를 실행
    for obscd, url in URLS.items():
        t = threading.Thread(target=stream_worker, args=(obscd, url))
        t.daemon = True
        t.start()
        threads.append(t)
        
    for t in threads:
        t.join()
