FROM python:3.10-slim

# Node.js 설치 (프론트엔드 빌드용)
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# 프론트엔드 빌드
RUN cd frontend && npm install && npm run build

# 파이썬 의존성 설치
RUN pip install --no-cache-dir -r backend/requirements.txt

WORKDIR /app/backend

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
