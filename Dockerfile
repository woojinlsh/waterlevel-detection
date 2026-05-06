FROM python:3.9-slim

# FFmpeg 설치
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# 파이썬 로그가 즉시 출력되도록 -u 옵션 사용
CMD ["python", "-u", "main.py"]
