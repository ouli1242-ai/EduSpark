"""对话接口（SSE 流式）— 接入多智能体编排器"""
import uuid
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.models.user import User
from app.models.chat_history import ChatHistory
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


@router.get("/history")
def get_chat_history(
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的对话历史（按 session 分组）"""
    # 获取所有 session 列表
    sessions = (
        db.query(ChatHistory.session_id)
        .filter(ChatHistory.user_id == user.id)
        .group_by(ChatHistory.session_id)
        .all()
    )
    # 按最新消息时间排序
    session_order = []
    for (sid,) in sessions:
        latest = (
            db.query(ChatHistory.created_at)
            .filter(ChatHistory.session_id == sid)
            .order_by(ChatHistory.created_at.desc())
            .first()
        )
        session_order.append((sid, latest[0] if latest else None))
    session_order.sort(key=lambda x: x[1] or x[0], reverse=True)
    sessions = [(sid,) for sid, _ in session_order[:20]]

    result = []
    for (sid,) in sessions:
        messages = (
            db.query(ChatHistory)
            .filter(
                ChatHistory.user_id == user.id,
                ChatHistory.session_id == sid,
                ChatHistory.role.in_(["user", "assistant"]),
            )
            .order_by(ChatHistory.id.asc())
            .all()
        )
        if messages:
            result.append({
                "session_id": sid,
                "title": messages[0].content[:50] if messages[0].role == "user" else "对话",
                "messages": [
                    {
                        "role": m.role,
                        "content": m.content,
                        "agent_type": m.agent_type,
                        "created_at": m.created_at.isoformat(),
                    }
                    for m in messages
                ],
            })

    return result


@router.delete("/history/{session_id}")
def delete_chat_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除指定 session 的对话历史（不影响画像）"""
    messages = (
        db.query(ChatHistory)
        .filter(
            ChatHistory.user_id == user.id,
            ChatHistory.session_id == session_id,
        )
        .all()
    )
    if not messages:
        raise HTTPException(status_code=404, detail="对话记录不存在")
    for m in messages:
        db.delete(m)
    db.commit()
    return {"message": "删除成功"}
