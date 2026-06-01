"""
RAG 모듈: 금융 키워드 필터 + BM25 검색
- 금융 키워드가 없으면 즉시 score=0 반환 (SE 경로)
- 있으면 n-gram BM25로 유사 Q&A 검색
- 정규화 ceiling: corpus cross-score p25 (빌드 시 1회 계산)
"""

from __future__ import annotations
import json
import numpy as np
import random
from pathlib import Path

DATA_PATH  = Path(__file__).parent.parent / "extracted_financial_qa.json"
CACHE_PATH = Path(__file__).parent.parent / "rag_embeddings.npy"

# 금융 도메인 키워드 — 하나라도 포함되면 BM25 검색 진행
_FINANCE_KEYWORDS = {
    "예금", "적금", "금리", "이자", "이율", "대출", "환율", "외환", "외화",
    "펀드", "신탁", "주식", "채권", "etf", "ETF", "보험", "연금",
    "수수료", "환전", "달러", "엔화", "유로", "위안", "원화",
    "저축", "투자", "원금", "만기", "해지", "수익", "배당",
    "상환", "담보", "신용", "금융", "은행", "증권", "자산",
    "파생", "선물", "옵션", "리츠", "mmf", "MMF", "cma", "CMA",
    "isa", "ISA", "els", "ELS", "dls", "DLS",
    "변동금리", "고정금리", "기준금리", "예치", "출금", "입금",
    "계좌", "잔액", "이체", "송금", "외국환",
}


def _has_finance_keyword(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in _FINANCE_KEYWORDS)


def _tokenize(text: str) -> list[str]:
    """공백 분리 + 2~3글자 n-gram"""
    text = text.strip()
    tokens = text.split()
    for n in (2, 3):
        tokens += [text[i:i+n] for i in range(len(text) - n + 1)]
    return tokens


class RAGRetriever:
    def __init__(self, top_k: int = 3):
        self.top_k = top_k
        self._items: list[dict] = []
        self._bm25 = None
        self._score_ceiling = 1.0

    def build(self) -> None:
        from rank_bm25 import BM25Okapi

        print("[RAG] 데이터 로딩 중...")
        with open(DATA_PATH, encoding="utf-8") as f:
            self._items = json.load(f)

        corpus = [_tokenize(d["question"]) for d in self._items]
        self._bm25 = BM25Okapi(corpus)

        # Cross-score p25: 같은 코퍼스 내 유사 문서 간 점수 분포
        # → "비슷한 질문이 실제로 얼마나 매칭되는가"의 하한선
        sample_idx = random.sample(range(len(self._items)), min(300, len(self._items)))
        cross_scores = []
        for i in sample_idx:
            scores = self._bm25.get_scores(corpus[i])
            scores[i] = 0.0  # 자기 자신 제외
            cross_scores.append(float(scores.max()))

        self._score_ceiling = float(np.percentile(cross_scores, 25))
        print(f"[RAG] BM25 빌드 완료: {len(self._items)}개 | ceiling(p25)={self._score_ceiling:.1f}")

    def retrieve(self, query: str) -> list[dict]:
        # 금융 키워드 없으면 즉시 score=0 → SE 경로
        if not _has_finance_keyword(query):
            return [{"question": "", "answer": "", "category": "",
                     "topic": "", "source": "", "score": 0.0}] * self.top_k

        tokens = _tokenize(query)
        scores = self._bm25.get_scores(tokens)
        top_indices = scores.argsort()[::-1][:self.top_k]

        results = []
        for idx in top_indices:
            item = self._items[idx]
            normalized = min(float(scores[idx]) / self._score_ceiling, 1.0) if self._score_ceiling > 0 else 0.0
            results.append({
                "question": item["question"],
                "answer":   item["answer"],
                "category": item.get("category", ""),
                "topic":    item.get("topic", ""),
                "source":   item.get("source_institution", ""),
                "score":    normalized,
            })
        return results

    def format_context(self, retrieved: list[dict]) -> str:
        lines = []
        for i, r in enumerate(retrieved, 1):
            lines.append(f"[참고 {i}] ({r['topic']} / {r['source']})")
            lines.append(f"Q: {r['question']}")
            lines.append(f"A: {r['answer']}")
            lines.append("")
        return "\n".join(lines).strip()


_retriever: RAGRetriever | None = None


def get_retriever() -> RAGRetriever:
    global _retriever
    if _retriever is None:
        _retriever = RAGRetriever(top_k=3)
        _retriever.build()
    return _retriever
