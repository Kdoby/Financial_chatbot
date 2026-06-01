# Finia — AI 금융 상담 챗봇

## 프로젝트 구조

```
finance_chatbot/
├── backend/
│   ├── main.py                  # FastAPI 진입점, 라우터 조합, lifespan(봇 시작)
│   ├── api/
│   │   ├── chat.py              # POST /chat, POST /chat/stream
│   │   └── consult.py           # POST /consult/start·message·close, GET /consult/stream
│   ├── services/
│   │   ├── rag.py               # 금융 키워드 필터 + BM25 n-gram 검색
│   │   ├── llm.py               # OpenAI-호환 LLM 클라이언트 (RunYourAI)
│   │   ├── entropy.py           # Semantic Entropy 계산 (SBERT 클러스터링)
│   │   ├── discord_bot.py       # Discord 봇 (상담사 ↔ 클라이언트 브릿지)
│   │   └── mcp_tools.py         # MCP 도구 스키마 및 실행 (stub)
│   ├── core/
│   │   ├── sbert.py             # SBERT 싱글턴 (paraphrase-multilingual-MiniLM-L12-v2)
│   │   └── session.py           # 상담 세션 인메모리 저장소
│   ├── extracted_financial_qa.json  # 4,917개 금융 Q&A 데이터셋
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── HomePage.jsx     # 랜딩 페이지 (히어로, 피처, CTA)
│   │   │   └── ChatPage.jsx     # 채팅 UI (메시지 목록 + 입력)
│   │   ├── components/
│   │   │   ├── ChatMessage.jsx  # 메시지 버블 (RAG/SE/MCP 배지, 상담 버튼)
│   │   │   └── ConsultPanel.jsx # 오른쪽 슬라이드 상담 패널 (SSE)
│   │   └── api.js               # API 베이스 URL (VITE_API_URL 환경변수)
│   ├── vercel.json              # SPA 라우팅 rewrite
│   └── vite.config.js
└── .env.example
```

## 기술 스택

### 백엔드
| 역할 | 라이브러리 |
|------|-----------|
| 웹 프레임워크 | FastAPI + Uvicorn |
| LLM API | OpenAI SDK → RunYourAI (claude-haiku-4-5 / claude-sonnet-4-6) |
| RAG 검색 | rank-bm25 (n-gram 토크나이징) |
| 임베딩/클러스터링 | sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2) + scikit-learn AgglomerativeClustering |
| Discord 봇 | discord.py >= 2.3 |
| 환경변수 | python-dotenv |

### 프론트엔드
| 역할 | 라이브러리 |
|------|-----------|
| 프레임워크 | React 19 + Vite 8 |
| 라우팅 | React Router DOM v7 |
| 애니메이션 | Framer Motion |
| 스타일 | CSS Modules (Pretendard + Cormorant Garamond) |
| 실시간 수신 | EventSource (SSE) |

## 실행 방법

```bash
# 1) 환경변수
cp .env.example .env
# RUNYOURAI_API_KEY, DISCORD_BOT_TOKEN, DISCORD_CHANNEL_ID 입력

# 2) 백엔드
cd backend
pip install -r requirements.txt
python main.py              # → http://localhost:8000

# 3) 프론트엔드 개발 모드 (선택)
cd frontend
npm install && npm run dev  # → http://localhost:5173
```

## 메인 플로우

```
사용자 질문
    │
    ▼
[금융 키워드 필터]  ── 없음 ──▶ score=0
    │ 있음
    ▼
[BM25 유사도 검색]
    │
    ├─ score >= 0.5 ──▶ [RAG 경로]  데이터셋 답변 직접 반환
    │
    └─ score < 0.5  ──▶ [SE 경로]   Haiku × 5회 샘플링
                            │
                            ├─ 신뢰도 높음/보통 ──▶ Sonnet 최종 답변
                            │                        + "보통"이면 상담 버튼 표시
                            │
                            └─ 신뢰도 낮음 ────▶ [MCP 경로] 도구 호출 후 답변
                                                   + 상담 버튼 표시
```

## 상담사 연결 플로우

```
클라이언트(브라우저) ─── POST /consult/start ──▶ Discord 채널에 스레드 생성
        │               GET /consult/stream  ──▶ SSE 구독
        │              POST /consult/message ──▶ 스레드에 메시지 전달
        │
Discord 봇 on_message ──▶ session.queue.put ──▶ SSE ──▶ 클라이언트
```

## Semantic Entropy

- **알고리즘**: Farquhar et al. (Nature 2024) count 기반 근사
  - `P(C_c) = |C_c| / N` (log prob 불필요)
  - `SE = -Σ P(c) log P(c)`
  - 정규화: `SE / log(N)` → [0, 1]
- **클러스터링**: SBERT 코사인 유사도 + AgglomerativeClustering (threshold=0.75)
- **임계값**: < 0.3 높음 / 0.3~0.6 보통 / > 0.6 낮음

## RAG 유사도 계산

- 금융 키워드 없으면 즉시 score=0 반환 (SE 경로로 강제)
- n-gram(2~3글자) BM25 점수 정규화: corpus cross-score p25 기준
- `RAG_SIMILARITY_THRESHOLD = 0.5`

## 환경변수

| 변수 | 설명 |
|------|------|
| `RUNYOURAI_API_KEY` | RunYourAI API 키 |
| `DISCORD_BOT_TOKEN` | Discord 봇 토큰 |
| `DISCORD_CHANNEL_ID` | 상담 알림 채널 ID |

## 배포

- **백엔드**: Cloudtype — Python, 루트 `backend/`, 시작 명령어 `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **프론트엔드**: Cloudtype / Vercel — Node.js, 루트 `frontend/`, 빌드 `npm run build`, 출력 `dist/`
- 프론트엔드 환경변수: `VITE_API_URL=https://백엔드도메인`

## 데이터셋

- 4,917개 금융 Q&A (`extracted_financial_qa.json`)
- 카테고리: `deposit_trust`, `fund`, `loan`, `forex`
- 기관: 하나증권 등
