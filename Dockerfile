# ── 1단계: 프론트엔드 빌드 ──────────────────────────────
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ── 2단계: 백엔드 런타임 ─────────────────────────────────
FROM python:3.10-slim
WORKDIR /app/backend

# CPU 전용 PyTorch 먼저 설치 (CUDA 버전 제외 → ~1.5GB 절약)
RUN pip install --no-cache-dir \
    torch --index-url https://download.pytorch.org/whl/cpu

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# 프론트엔드 빌드 결과만 복사
COPY --from=frontend-build /app/frontend/dist ../frontend/dist

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
