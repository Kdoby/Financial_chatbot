"""
RunYourAI LLM 클라이언트 (OpenAI 호환 API)
- SE 샘플: claude-haiku-4-5 (빠름)
- 최종 답변: claude-sonnet-4-6 (균형)
- MCP 도구 호출: claude-sonnet-4-6
"""

from __future__ import annotations
import asyncio
import os
from typing import AsyncIterator

from openai import AsyncOpenAI

BASE_URL = "https://api.runyour.ai/v1"
MODEL_SAMPLE = "anthropic/claude-haiku-4-5"    # SE 샘플 생성용
MODEL_MAIN   = "anthropic/claude-sonnet-4-6"   # 최종 답변용
N_SAMPLES = 5
SE_TEMPERATURE = 1.0

SYSTEM_PROMPT = """당신은 한국 금융 전문 상담 AI입니다.
예금, 펀드, 대출, 외환, 주식 등 금융 관련 질문에 정확하고 친절하게 답변하세요.

답변 원칙:
1. 참고 자료가 있으면 그 내용을 기반으로 답변하세요.
2. 확실하지 않은 정보는 "정확한 내용은 해당 금융기관에 문의하세요"라고 안내하세요.
3. 답변은 핵심만 간결하게 (3-5문장), 과도한 면책 문구는 생략하세요.
4. 수치나 조건은 변동될 수 있음을 간단히 언급하세요."""


def _make_user_message(question: str, context: str) -> str:
    if context:
        return f"[참고 자료]\n{context}\n\n[질문]\n{question}"
    return question


class LLMClient:
    def __init__(self):
        api_key = os.environ.get("RUNYOURAI_API_KEY")
        if not api_key:
            raise RuntimeError("RUNYOURAI_API_KEY 환경변수가 설정되지 않았습니다.")
        self._client = AsyncOpenAI(api_key=api_key, base_url=BASE_URL)

    async def generate_async(self, question: str, context: str = "") -> str:
        """RAG/SE 경로 최종 답변 생성"""
        resp = await self._client.chat.completions.create(
            model=MODEL_MAIN,
            max_tokens=512,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": _make_user_message(question, context)},
            ],
        )
        return resp.choices[0].message.content

    async def stream_async(self, question: str, context: str = "") -> AsyncIterator[str]:
        """스트리밍 답변 생성"""
        stream = await self._client.chat.completions.create(
            model=MODEL_MAIN,
            max_tokens=512,
            stream=True,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": _make_user_message(question, context)},
            ],
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def generate_samples(self, question: str, context: str = "") -> list[str]:
        """SE 계산용 다중 샘플 비동기 생성"""
        tasks = [
            self._client.chat.completions.create(
                model=MODEL_SAMPLE,
                max_tokens=256,
                temperature=SE_TEMPERATURE,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": _make_user_message(question, context)},
                ],
            )
            for _ in range(N_SAMPLES)
        ]
        responses = await asyncio.gather(*tasks)
        return [r.choices[0].message.content for r in responses]

    async def generate_with_tools(self, question: str) -> tuple[str, list[str]]:
        """MCP 경로: 도구 호출 후 최종 답변"""
        from services.mcp_tools import TOOLS, execute_tool

        # OpenAI 형식으로 tools 변환
        openai_tools = [
            {"type": "function", "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["input_schema"],
            }}
            for t in TOOLS
        ]

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": question},
        ]
        tools_used: list[str] = []

        for _ in range(3):
            resp = await self._client.chat.completions.create(
                model=MODEL_MAIN,
                max_tokens=1024,
                tools=openai_tools,
                messages=messages,
            )
            choice = resp.choices[0]

            if choice.finish_reason == "stop":
                return choice.message.content or "", tools_used

            if choice.finish_reason == "tool_calls":
                messages.append(choice.message.model_dump())
                for tc in choice.message.tool_calls:
                    import json
                    tools_used.append(tc.function.name)
                    result = execute_tool(tc.function.name, json.loads(tc.function.arguments))
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    })
            else:
                break

        return choice.message.content or "답변을 생성할 수 없습니다.", tools_used


# 싱글턴
_client: LLMClient | None = None


def get_client() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
