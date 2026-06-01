from __future__ import annotations
import asyncio
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.llm import get_client
from services.rag import get_retriever
from services.entropy import get_calculator

router = APIRouter()
RAG_SIMILARITY_THRESHOLD = 0.5


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    mode: str
    top_similarity: float
    retrieved: list[dict]
    semantic_entropy: float | None = None
    normalized_se: float | None = None
    n_clusters: int | None = None
    confidence: str | None = None
    is_uncertain: bool | None = None
    samples: list[str] = []
    tools_used: list[str] = []


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="질문을 입력해주세요.")

    client = get_client()
    retriever = get_retriever()
    calc = get_calculator()

    retrieved = retriever.retrieve(req.question)
    top_similarity = retrieved[0]["score"] if retrieved else 0.0

    if top_similarity >= RAG_SIMILARITY_THRESHOLD:
        return ChatResponse(
            answer=retrieved[0]["answer"], mode="rag",
            top_similarity=top_similarity, retrieved=retrieved,
        )

    context = retriever.format_context(retrieved)
    samples = await client.generate_samples(req.question, context)
    loop = asyncio.get_event_loop()
    se_result = await loop.run_in_executor(None, calc.compute, samples)

    if se_result.is_uncertain:
        answer, tools_used = await client.generate_with_tools(req.question)
        return ChatResponse(
            answer=answer, mode="mcp", top_similarity=top_similarity,
            retrieved=retrieved, semantic_entropy=se_result.semantic_entropy,
            normalized_se=se_result.normalized_se, n_clusters=se_result.n_clusters,
            confidence=se_result.confidence, is_uncertain=True,
            samples=se_result.answers, tools_used=tools_used,
        )

    answer = await client.generate_async(req.question, context)
    return ChatResponse(
        answer=answer, mode="se", top_similarity=top_similarity,
        retrieved=retrieved, semantic_entropy=se_result.semantic_entropy,
        normalized_se=se_result.normalized_se, n_clusters=se_result.n_clusters,
        confidence=se_result.confidence, is_uncertain=False,
        samples=se_result.answers,
    )


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="질문을 입력해주세요.")

    client = get_client()
    retriever = get_retriever()
    calc = get_calculator()

    retrieved = retriever.retrieve(req.question)
    top_similarity = retrieved[0]["score"] if retrieved else 0.0

    async def generate():
        if top_similarity >= RAG_SIMILARITY_THRESHOLD:
            meta = {"type": "meta", "mode": "rag", "top_similarity": top_similarity,
                    "confidence": "높음", "is_uncertain": False,
                    "retrieved_topics": [r["topic"] for r in retrieved]}
            yield f"data: {json.dumps(meta, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'text', 'text': retrieved[0]['answer']}, ensure_ascii=False)}\n\n"
        else:
            context = retriever.format_context(retrieved)
            samples = await client.generate_samples(req.question, context)
            loop = asyncio.get_event_loop()
            se_result = await loop.run_in_executor(None, calc.compute, samples)

            if se_result.is_uncertain:
                answer, tools_used = await client.generate_with_tools(req.question)
                meta = {"type": "meta", "mode": "mcp", "top_similarity": top_similarity,
                        "confidence": se_result.confidence, "is_uncertain": True,
                        "semantic_entropy": se_result.semantic_entropy,
                        "normalized_se": se_result.normalized_se,
                        "n_clusters": se_result.n_clusters, "tools_used": tools_used}
                yield f"data: {json.dumps(meta, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'text', 'text': answer}, ensure_ascii=False)}\n\n"
            else:
                meta = {"type": "meta", "mode": "se", "top_similarity": top_similarity,
                        "confidence": se_result.confidence, "is_uncertain": False,
                        "semantic_entropy": se_result.semantic_entropy,
                        "normalized_se": se_result.normalized_se,
                        "n_clusters": se_result.n_clusters}
                yield f"data: {json.dumps(meta, ensure_ascii=False)}\n\n"
                async for chunk in client.stream_async(req.question, context):
                    yield f"data: {json.dumps({'type': 'text', 'text': chunk}, ensure_ascii=False)}\n\n"

        yield 'data: {"type":"done"}\n\n'

    return StreamingResponse(generate(), media_type="text/event-stream")
