from __future__ import annotations
import asyncio
import json
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()


class ConsultStartRequest(BaseModel):
    question: str
    semantic_entropy: float | None = None
    normalized_se: float | None = None
    confidence: str | None = None


class ConsultMessageRequest(BaseModel):
    content: str


@router.post("/consult/start")
async def consult_start(req: ConsultStartRequest):
    from services.discord_bot import create_consult_thread
    from core.session import create_session

    session_id = uuid.uuid4().hex[:8]
    session = create_session(session_id, req.question)

    try:
        thread_id = await create_consult_thread(
            session_id=session_id, question=req.question,
            confidence=req.confidence, normalized_se=req.normalized_se,
        )
        session.discord_thread_id = thread_id
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Discord 스레드 생성 실패: {e}")

    return {"session_id": session_id}


@router.post("/consult/message/{session_id}")
async def consult_message(session_id: str, req: ConsultMessageRequest):
    from services.discord_bot import send_to_thread
    from core.session import get_session

    session = get_session(session_id)
    if not session or session.discord_thread_id is None:
        raise HTTPException(status_code=404, detail="세션 없음")

    await send_to_thread(session.discord_thread_id, req.content)
    return {"status": "ok"}


@router.post("/consult/close/{session_id}")
async def consult_close(session_id: str):
    from core.session import close_session
    close_session(session_id)
    return {"status": "ok"}


@router.get("/consult/stream/{session_id}")
async def consult_stream(session_id: str):
    from core.session import get_session

    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="세션 없음")

    async def event_gen():
        while not session.closed:
            try:
                msg = await asyncio.wait_for(session.queue.get(), timeout=25.0)
                yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"
            except asyncio.TimeoutError:
                yield 'data: {"type":"ping"}\n\n'

    return StreamingResponse(event_gen(), media_type="text/event-stream")
