# Finia — AI 금융 상담 챗봇

> RAG + Semantic Entropy 기반 신뢰도 검증 · 전문 상담사 Discord 연결

---

## 소개

Finia는 4,917개 금융 Q&A 데이터셋과 Semantic Entropy 기반 신뢰도 분석을 결합한 AI 금융 상담 챗봇입니다. AI가 불확실하다고 판단할 경우 실시간으로 전문 상담사와 연결합니다.

## 주요 기능

| 기능 | 설명 |
|------|------|
| **RAG 검색** | 4,917개 금융 Q&A에서 유사 답변 즉시 반환 |
| **Semantic Entropy** | LLM 샘플 5회 생성 후 SBERT 클러스터링으로 신뢰도 측정 |
| **MCP 도구 호출** | 신뢰도 낮음 시 외부 금융 데이터 조회 |
| **상담사 연결** | 신뢰도 보통/낮음 시 Discord 스레드 생성 → 실시간 양방향 채팅 |

## 기술 스택

### 백엔드
![Python](https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)
![discord.py](https://img.shields.io/badge/discord.py-2.3-5865F2?logo=discord&logoColor=white)

- **FastAPI** — REST API + SSE 스트리밍
- **RunYourAI** (OpenAI 호환) — claude-haiku-4-5 (샘플링), claude-sonnet-4-6 (최종 답변)
- **rank-bm25** — n-gram 기반 금융 Q&A 검색
- **sentence-transformers** — SBERT 임베딩 (paraphrase-multilingual-MiniLM-L12-v2)
- **scikit-learn** — AgglomerativeClustering (SE 계산)
- **discord.py** — 상담사 ↔ 클라이언트 브릿지

### 프론트엔드
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-8-646CFF?logo=vite&logoColor=white)

- **React 19** + **React Router DOM v7**
- **Framer Motion** — 페이지 전환 및 메시지 애니메이션
- **CSS Modules** — Pretendard + Cormorant Garamond 폰트

## 아키텍처

```
사용자 질문
    │
    ▼
[금융 키워드 필터]
    │
    ├─ 유사도 >= 0.5 ──▶ 📚 RAG  데이터셋 답변 직접 반환
    │
    └─ 유사도 < 0.5
            │
            ▼
        [SE 경로] Haiku × 5회 샘플링 → SBERT 클러스터링
            │
            ├─ 신뢰도 높음 ──▶ 🧠 SE    Sonnet 최종 답변
            ├─ 신뢰도 보통 ──▶ 🧠 SE    Sonnet 답변 + 상담 버튼
            └─ 신뢰도 낮음 ──▶ 🔧 MCP   도구 호출 + 상담 버튼

상담 버튼 클릭
    │
    ▼
클라이언트(웹) ──── FastAPI ──── Discord 봇 ──── 상담사(Discord)
              SSE로 실시간 수신 ◀─────────────────────────────
```

## 로컬 실행

### 사전 준비

- Python 3.10+
- Node.js 18+
- Discord 봇 토큰 ([Discord Developer Portal](https://discord.com/developers/applications))

### 설치 및 실행

```bash
# 1. 저장소 클론
git clone https://github.com/YOUR_ID/finance_chatbot.git
cd finance_chatbot

# 2. 환경변수 설정
cp .env.example .env
# 아래 값을 .env에 입력:
#   RUNYOURAI_API_KEY=
#   DISCORD_BOT_TOKEN=
#   DISCORD_CHANNEL_ID=

# 3. 백엔드 실행
cd backend
pip install -r requirements.txt
python main.py
# → http://localhost:8000

# 4. 프론트엔드 개발 서버 (선택)
cd ../frontend
npm install
npm run dev
# → http://localhost:5173
```

### Discord 봇 설정

1. [Discord Developer Portal](https://discord.com/developers/applications) → 봇 생성
2. **Bot** 메뉴 → **Message Content Intent** 활성화
3. **OAuth2** → URL Generator → `bot` 스코프 + 필요 권한으로 서버 초대
4. 상담 알림 받을 채널 ID를 `DISCORD_CHANNEL_ID`에 입력

## 배포

### Cloudtype (권장)

**백엔드**
- 런타임: Python
- 루트 디렉토리: `backend`
- 시작 명령어: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- 환경변수: `RUNYOURAI_API_KEY`, `DISCORD_BOT_TOKEN`, `DISCORD_CHANNEL_ID`

**프론트엔드**
- 런타임: Node.js
- 루트 디렉토리: `frontend`
- 빌드 명령어: `npm run build`
- 출력 디렉토리: `dist`
- 환경변수: `VITE_API_URL=https://백엔드도메인`

## 파일 구조

```
finance_chatbot/
├── backend/
│   ├── main.py              # FastAPI 진입점
│   ├── api/
│   │   ├── chat.py          # 채팅 라우터
│   │   └── consult.py       # 상담 라우터
│   ├── services/
│   │   ├── rag.py           # BM25 검색
│   │   ├── llm.py           # LLM 클라이언트
│   │   ├── entropy.py       # Semantic Entropy
│   │   ├── discord_bot.py   # Discord 봇
│   │   └── mcp_tools.py     # MCP 도구
│   ├── core/
│   │   ├── sbert.py         # SBERT 싱글턴
│   │   └── session.py       # 상담 세션
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/           # HomePage, ChatPage
│       └── components/      # ChatMessage, ConsultPanel
└── extracted_financial_qa.json
```

## 데이터셋

- **4,917개** 한국어 금융 Q&A
- 카테고리: 예금/신탁, 펀드, 대출, 외환
- 출처: 하나증권 등

## 참고 문헌

- Farquhar, S. et al. (2024). *Detecting hallucinations in large language models using semantic entropy*. **Nature**, 630, 625–630.

---

> ⚠️ 본 서비스는 정보 제공 목적이며 투자 권유가 아닙니다.
