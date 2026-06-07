"""对话接口（SSE 流式）— 接入多智能体编排器"""
import uuid
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.models.user import User
from app.utils.auth import get_current_user
from app.agents.orchestrator import orchestrator

router = APIRouter(prefix="/api/chat", tags=["对话"])


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


@router.post("")
async def chat(
    req: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session_id = req.session_id or uuid.uuid4().hex[:16]

    async def generate():
        async for event in orchestrator.handle_chat(
            message=req.message,
            session_id=session_id,
            user_id=user.id,
            db=db,
        ):
            yield event

    return StreamingResponse(generate(), media_type="text/event-stream")
