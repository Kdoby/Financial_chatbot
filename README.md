# Finia — AI 금융 상담 챗봇

> RAG + Semantic Entropy 기반 신뢰도 검증 · 전문 상담사 Discord 실시간 연결

---

## 소개

Finia는 4,917개 한국어 금융 Q&A 데이터셋과 Semantic Entropy 기반 불확실성 측정을 결합한 AI 금융 상담 챗봇입니다.  
AI가 확신하지 못할 때는 자동으로 상담 버튼을 노출하고, 클릭 시 Discord를 통해 전문 상담사와 실시간 대화를 연결합니다.

## 주요 기능

| 기능 | 설명 |
|------|------|
| **RAG 검색** | 금융 키워드 필터 후 BM25 n-gram 검색 → 유사도 ≥ 0.5면 데이터셋 답변 즉시 반환 |
| **Semantic Entropy** | Haiku × 5회 샘플링 → 한국어 char bigram Jaccard 클러스터링 → 신뢰도 판정 |
| **상담사 연결** | 신뢰도 보통/낮음 시 Discord 스레드 생성 → SSE로 실시간 양방향 채팅 |

## 기술 스택

### 백엔드

![Python](https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)
![discord.py](https://img.shields.io/badge/discord.py-2.3-5865F2?logo=discord&logoColor=white)

| 역할 | 라이브러리 |
|------|-----------|
| 웹 프레임워크 | FastAPI + Uvicorn |
| LLM | OpenAI SDK → RunYourAI (`claude-haiku-4-5` / `claude-sonnet-4-6`) |
| RAG 검색 | rank-bm25 (2~3글자 n-gram 토크나이징) |
| 불확실성 추정 | character 2-gram Jaccard + Union-Find 클러스터링 (외부 ML 의존성 없음) |
| 상담사 브릿지 | discord.py ≥ 2.3 |
| 환경변수 | python-dotenv |

### 프론트엔드

![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-8-646CFF?logo=vite&logoColor=white)

| 역할 | 라이브러리 |
|------|-----------|
| 프레임워크 | React 19 + Vite 8 |
| 라우팅 | React Router DOM v7 |
| 애니메이션 | Framer Motion v12 |
| 스타일 | CSS Modules (Pretendard + Cormorant Garamond) |
| 실시간 수신 | EventSource (SSE) |

## 아키텍처

```
사용자 질문
    │
    ▼
[금융 키워드 필터]  ── 없음 ──▶  score = 0
    │ 있음
    ▼
[BM25 n-gram 검색]
    │
    ├─ 유사도 ≥ 0.5 ──▶  RAG   데이터셋 답변 직접 반환
    │
    └─ 유사도 < 0.5
            │
            ▼
        Haiku × 5회 샘플링
        char 2-gram Jaccard 클러스터링
        SE = −Σ P(c)·log P(c)  /  log(N)  ∈ [0, 1]
            │
            ├─ SE < 0.3  신뢰도 높음 ──▶  SE    Sonnet 최종 답변
            ├─ SE ≤ 0.6  신뢰도 보통 ──▶  SE    Sonnet 답변 + 상담 버튼
            └─ SE > 0.6  신뢰도 낮음 ──▶  MCP   도구 호출 → Sonnet 재답변 + 상담 버튼

상담 버튼 클릭
    │
    ▼
POST /consult/start ──▶ Discord 스레드 생성
GET  /consult/stream ──▶ SSE 구독
POST /consult/message ──▶ 스레드에 메시지 전송
                                    │
Discord 봇 on_message ──▶ session.queue.put ──▶ SSE ──▶ 브라우저
```

## 프로젝트 구조

```
finance_chatbot/
├── backend/
│   ├── main.py                      # FastAPI 진입점 · lifespan(RAG 빌드, 봇 시작)
│   ├── api/
│   │   ├── chat.py                  # POST /chat, POST /chat/stream
│   │   └── consult.py               # POST /consult/start·message·close, GET /consult/stream
│   ├── services/
│   │   ├── rag.py                   # 금융 키워드 필터 + BM25 n-gram 검색
│   │   ├── llm.py                   # OpenAI 호환 LLM 클라이언트 (RunYourAI)
│   │   ├── entropy.py               # Semantic Entropy (char bigram Jaccard + Union-Find)
│   │   ├── discord_bot.py           # Discord 봇 · 스레드 생성 · 메시지 브릿지
│   │   └── mcp_tools.py             # MCP 도구 스키마 및 실행
│   ├── core/
│   │   └── session.py               # 상담 세션 인메모리 저장소
│   ├── extracted_financial_qa.json  # 4,917개 금융 Q&A 데이터셋
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── api.js                   # API 베이스 URL (VITE_API_URL)
│       ├── pages/
│       │   ├── HomePage.jsx         # 랜딩 페이지 (히어로, 피처, CTA)
│       │   └── ChatPage.jsx         # 채팅 UI (메시지 목록 + 입력)
│       └── components/
│           ├── ChatMessage.jsx      # 메시지 버블 (RAG/SE/MCP 배지, 상담 버튼)
│           └── ConsultPanel.jsx     # 오른쪽 슬라이드 상담 패널 (SSE)
├── Dockerfile                       # 멀티스테이지 빌드 (프론트 → 백엔드 합본)
└── .env.example
```

## 로컬 실행

### 사전 준비

- Python 3.10+
- Node.js 20+
- Discord 봇 토큰 ([Discord Developer Portal](https://discord.com/developers/applications))
- RunYourAI API 키

### 환경변수 설정

```bash
cp .env.example .env
```

`.env` 파일에 아래 값을 입력합니다:

```env
RUNYOURAI_API_KEY=your_api_key_here
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_CHANNEL_ID=your_channel_id_here
```

### 백엔드 실행

```bash
cd backend
pip install -r requirements.txt
python main.py
# → http://localhost:8000
```

최초 실행 시 BM25 인덱스 빌드(4,917개 문서)가 수행됩니다.

### 프론트엔드 개발 서버

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### Discord 봇 설정

1. [Discord Developer Portal](https://discord.com/developers/applications) → 새 애플리케이션 생성
2. **Bot** 탭 → **Message Content Intent** 활성화
3. **OAuth2 → URL Generator** → `bot` 스코프 + `Send Messages`, `Create Public Threads`, `Read Message History` 권한 체크 → 서버 초대
4. 알림받을 채널의 ID를 `DISCORD_CHANNEL_ID`에 입력

## 배포

### Docker (단일 컨테이너)

```bash
docker build -t finia .
docker run -p 8000:8000 \
  -e RUNYOURAI_API_KEY=... \
  -e DISCORD_BOT_TOKEN=... \
  -e DISCORD_CHANNEL_ID=... \
  finia
```

Dockerfile은 멀티스테이지 빌드로 프론트엔드 `dist`를 백엔드 정적 파일로 서빙합니다.

### Cloudtype

**백엔드**

| 항목 | 값 |
|------|----|
| 런타임 | Python |
| 루트 디렉토리 | `backend` |
| 시작 명령어 | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| 환경변수 | `RUNYOURAI_API_KEY`, `DISCORD_BOT_TOKEN`, `DISCORD_CHANNEL_ID` |

**프론트엔드**

| 항목 | 값 |
|------|----|
| 런타임 | Node.js |
| 루트 디렉토리 | `frontend` |
| 빌드 명령어 | `npm run build` |
| 출력 디렉토리 | `dist` |
| 환경변수 | `VITE_API_URL=https://백엔드도메인` |

## 데이터셋

- **4,917개** 한국어 금융 Q&A (`extracted_financial_qa.json`)
- 카테고리: `deposit_trust`(예금/신탁) · `fund`(펀드) · `loan`(대출) · `forex`(외환)
- 출처: 하나증권 등

## Semantic Entropy 알고리즘

[Farquhar et al., *Nature* 2024](https://www.nature.com/articles/s41586-024-07421-0) 기반의 count 근사 구현입니다.  
Claude API는 log-prob을 제공하지 않으므로 아래 방식으로 근사합니다.

| 단계 | 내용 |
|------|------|
| 샘플링 | `claude-haiku-4-5` × 5회 생성 (temperature=1.0) |
| 클러스터링 | character 2-gram Jaccard 유사도 + Union-Find (threshold=0.4) |
| 확률 추정 | `P(C_c) = \|C_c\| / N` |
| 엔트로피 | `SE = −Σ P(c) · log P(c)` |
| 정규화 | `SE / log(N)` → [0, 1] |

| 범위 | 신뢰도 | 처리 |
|------|--------|------|
| SE < 0.3 | 높음 | Sonnet 최종 답변 |
| 0.3 ≤ SE ≤ 0.6 | 보통 | Sonnet 답변 + 상담 버튼 |
| SE > 0.6 | 낮음 | MCP 도구 호출 → Sonnet 재답변 + 상담 버튼 |

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/health` | 헬스체크 |
| `POST` | `/chat` | 단일 답변 요청 |
| `POST` | `/chat/stream` | 스트리밍 답변 (SSE) |
| `POST` | `/consult/start` | 상담 세션 시작 + Discord 스레드 생성 |
| `GET` | `/consult/stream` | 상담사 메시지 SSE 구독 |
| `POST` | `/consult/message` | 클라이언트 → 상담사 메시지 전송 |
| `POST` | `/consult/close` | 상담 세션 종료 |

## 참고 문헌

- Farquhar, S. et al. (2024). *Detecting hallucinations in large language models using semantic entropy*. **Nature**, 630, 625–630.

---

> ⚠️ 본 서비스는 정보 제공 목적이며 투자 권유가 아닙니다.
