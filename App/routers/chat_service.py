import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..internal.db import get_db
from ..models.sessions import MusicSession
from ..models.chat_messages import ChatMessage
from ..services.ollama_client import chat_stream, chat_stream_with_rag
from ..internal.config import get_settings

_settings = get_settings()

router = APIRouter()


class MessageItem(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    session_id: str
    history: list[MessageItem] = []


@router.post("")
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    # 세션 없으면 생성
    session = await db.get(MusicSession, req.session_id)
    if not session:
        session = MusicSession(id=req.session_id)
        db.add(session)
        await db.commit()

    history = [{"role": m.role, "content": m.content} for m in req.history]

    async def event_stream():
        full_response = ""
        stream_fn = chat_stream_with_rag if _settings.rag_enabled else chat_stream
        async for token in stream_fn(req.message, history):
            full_response += token
            yield f"data: {json.dumps({'token': token})}\n\n"

        # DB에 저장
        db.add(ChatMessage(session_id=req.session_id, role="user", content=req.message))
        db.add(ChatMessage(session_id=req.session_id, role="assistant", content=full_response))
        await db.commit()

        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
