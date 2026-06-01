"""
Discord 봇 — 웹 챗봇과 상담사 간 브릿지

흐름:
  클라이언트 → /consult/start → 채널에 메시지+스레드 생성
  클라이언트 → /consult/message → 스레드에 메시지 전달
  상담사가 스레드에 답변 → on_message → 세션 큐에 push → SSE로 클라이언트에 전달
"""
from __future__ import annotations
import asyncio
import os

import discord
from core.session import get_session_by_thread

intents = discord.Intents.default()
intents.message_content = True

_client = discord.Client(intents=intents)
_ready  = asyncio.Event()


@_client.event
async def on_ready():
    _ready.set()
    print(f"[Discord] 봇 로그인: {_client.user}")


@_client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if not isinstance(message.channel, discord.Thread):
        return

    session = get_session_by_thread(message.channel.id)
    if session and not session.closed:
        await session.queue.put({
            "type": "message",
            "author": message.author.display_name,
            "content": message.content,
        })


async def create_consult_thread(
    session_id: str,
    question: str,
    confidence: str | None = None,
    normalized_se: float | None = None,
) -> int:
    """채널에 메시지를 보내고 그 메시지에서 스레드를 생성한 뒤 thread_id 반환"""
    await asyncio.wait_for(_ready.wait(), timeout=15.0)

    channel_id = int(os.environ.get("DISCORD_CHANNEL_ID", "0"))
    channel = _client.get_channel(channel_id)
    if channel is None:
        raise RuntimeError(f"DISCORD_CHANNEL_ID={channel_id} 채널을 찾을 수 없습니다.")

    se_line = ""
    if normalized_se is not None:
        se_line = f"\n📊 신뢰도: **{confidence or '낮음'}** (SE {normalized_se * 100:.1f}%)"

    msg = await channel.send(
        f"📞 **새 상담 요청** `#{session_id}`{se_line}\n\n> {question}"
    )
    thread = await msg.create_thread(name=f"상담-{session_id}")
    await thread.send("상담사님, 고객이 연결을 기다리고 있습니다. 이 스레드에서 답변해주세요.")
    return thread.id


async def send_to_thread(thread_id: int, content: str) -> None:
    thread = _client.get_channel(thread_id)
    if thread:
        await thread.send(f"💬 **고객:** {content}")


async def start_bot() -> None:
    token = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
    if not token:
        print("[Discord] DISCORD_BOT_TOKEN 미설정 — 봇 비활성화")
        return
    await _client.start(token)
