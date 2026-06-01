"""상담 세션 인메모리 저장소"""
from __future__ import annotations
import asyncio
from dataclasses import dataclass, field


@dataclass
class ConsultSession:
    session_id: str
    question: str
    discord_thread_id: int | None = None
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    closed: bool = False


_sessions: dict[str, ConsultSession] = {}


def create_session(session_id: str, question: str) -> ConsultSession:
    s = ConsultSession(session_id=session_id, question=question)
    _sessions[session_id] = s
    return s


def get_session(session_id: str) -> ConsultSession | None:
    return _sessions.get(session_id)


def get_session_by_thread(thread_id: int) -> ConsultSession | None:
    return next((s for s in _sessions.values() if s.discord_thread_id == thread_id), None)


def close_session(session_id: str) -> None:
    s = _sessions.get(session_id)
    if s:
        s.closed = True
