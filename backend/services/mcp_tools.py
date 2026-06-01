"""
MCP 도구 정의 — Claude API tool use 형식으로 선언.
SE가 높아 신뢰도가 낮을 때 호출됨.

실제 외부 API 연결 시 각 _impl 함수를 교체하면 됩니다.
"""

from __future__ import annotations
import json
from typing import Any

# ── 도구 스키마 (Claude API tools 파라미터에 직접 전달) ────────────────

TOOLS: list[dict] = [
    {
        "name": "search_financial_info",
        "description": (
            "금융 관련 최신 정보를 검색합니다. "
            "금리, 환율, 펀드 수익률, 대출 조건 등 실시간 데이터가 필요할 때 사용하세요."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "검색할 금융 키워드 (예: '기준금리 현황', '달러 환율')",
                },
                "category": {
                    "type": "string",
                    "enum": ["금리", "환율", "펀드", "대출", "주식", "기타"],
                    "description": "정보 카테고리",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_exchange_rate",
        "description": "특정 통화쌍의 현재 환율을 조회합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "base": {"type": "string", "description": "기준 통화 (예: USD, JPY, EUR)"},
                "target": {"type": "string", "description": "대상 통화 (기본값: KRW)", "default": "KRW"},
            },
            "required": ["base"],
        },
    },
    {
        "name": "get_interest_rate",
        "description": "한국은행 기준금리 또는 시중은행 평균 금리를 조회합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "rate_type": {
                    "type": "string",
                    "enum": ["기준금리", "예금금리", "대출금리", "CD금리"],
                    "description": "조회할 금리 종류",
                }
            },
            "required": ["rate_type"],
        },
    },
]


# ── 도구 실행 (실제 API 연결 시 여기를 수정) ─────────────────────────

def _search_financial_info(query: str, category: str = "기타") -> str:
    """TODO: 실제 금융 뉴스 API / 웹 검색 API 연결"""
    return json.dumps({
        "status": "stub",
        "query": query,
        "category": category,
        "message": "실시간 금융 정보 API가 연결되면 여기에 결과가 표시됩니다.",
    }, ensure_ascii=False)


def _get_exchange_rate(base: str, target: str = "KRW") -> str:
    """TODO: 환율 API (예: 한국수출입은행, 하나금융 등) 연결"""
    return json.dumps({
        "status": "stub",
        "pair": f"{base}/{target}",
        "message": "환율 API 연결 후 실시간 환율이 제공됩니다.",
    }, ensure_ascii=False)


def _get_interest_rate(rate_type: str) -> str:
    """TODO: 한국은행 ECOS API 연결"""
    return json.dumps({
        "status": "stub",
        "rate_type": rate_type,
        "message": "한국은행 ECOS API 연결 후 실시간 금리가 제공됩니다.",
    }, ensure_ascii=False)


# ── 디스패처 ────────────────────────────────────────────────────────────

def execute_tool(name: str, inputs: dict[str, Any]) -> str:
    if name == "search_financial_info":
        return _search_financial_info(**inputs)
    if name == "get_exchange_rate":
        return _get_exchange_rate(**inputs)
    if name == "get_interest_rate":
        return _get_interest_rate(**inputs)
    return json.dumps({"error": f"알 수 없는 도구: {name}"})
