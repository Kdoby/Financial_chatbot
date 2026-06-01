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

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

# BM25 인덱스 빌드 & pickle 저장 (런타임 startup 제거)
RUN python -c "from services.rag import get_retriever; import pickle; r = get_retriever(); pickle.dump(r, open('rag_cache.pkl','wb'))"

# 프론트엔드 빌드 결과만 복사
COPY --from=frontend-build /app/frontend/dist ../frontend/dist

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
