from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from services.rag import get_retriever
from api.chat import router as chat_router
from api.consult import router as consult_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, get_retriever)

    from services import discord_bot
    bot_task = asyncio.create_task(discord_bot.start_bot())
    yield
    bot_task.cancel()
    try:
        await bot_task
    except (asyncio.CancelledError, Exception):
        pass


app = FastAPI(title="금융 챗봇 API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(consult_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


CLIENT_DIR = Path(__file__).parent.parent / "frontend" / "dist"
if CLIENT_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(CLIENT_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        static_file = CLIENT_DIR / full_path
        if static_file.is_file():
            return FileResponse(str(static_file))
        return FileResponse(str(CLIENT_DIR / "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
