"""辅导 Agent API 路由"""
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.utils.auth import get_current_user
from app.models.user import User
from app.models.profile import StudentProfile
from app.models.chat_history import ChatHistory
from app.agents.tutor_agent import tutor_agent
from app.utils.sse import sse_event

router = APIRouter(prefix="/api/tutor", tags=["辅导"])


class TutorRequest(BaseModel):
    question: str
    context_topic: str | None = None
    output_modes: list[str] = ["text"]  # text / image / audio
    session_id: str | None = None


@router.post("/ask")
async def ask_tutor(
    req: TutorRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """向辅导 Agent 提问（SSE 流式返回）"""

    # 获取学生画像
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    profile_dict = {}
    if profile:
        profile_dict = {
            "knowledge_base": profile.knowledge_base,
            "cognitive_style": profile.cognitive_style,
            "learning_ability": profile.learning_ability,
            "error_patterns": profile.error_patterns,
            "learning_goals": profile.learning_goals,
            "learning_preferences": profile.learning_preferences,
        }

    async def event_stream():
        try:
            async for event in tutor_agent.run_stream({
                "question": req.question,
                "context_topic": req.context_topic or "",
                "profile": profile_dict,
                "output_modes": req.output_modes,
            }):
                yield event
        except Exception as e:
            yield sse_event({"type": "error", "code": "GENERATION_FAILED", "message": str(e)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/ask/sync")
async def ask_tutor_sync(
    req: TutorRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """向辅导 Agent 提问（非流式，返回完整结果）"""

    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    profile_dict = {}
    if profile:
        profile_dict = {
            "knowledge_base": profile.knowledge_base,
            "cognitive_style": profile.cognitive_style,
            "learning_ability": profile.learning_ability,
            "error_patterns": profile.error_patterns,
            "learning_goals": profile.learning_goals,
            "learning_preferences": profile.learning_preferences,
        }

    try:
        result = await tutor_agent.run({
            "question": req.question,
            "context_topic": req.context_topic or "",
            "profile": profile_dict,
            "output_modes": req.output_modes,
        })

        # 保存对话记录
        if req.session_id:
            db.add(ChatHistory(
                user_id=current_user.id,
                session_id=req.session_id,
                role="user",
                content=req.question,
                agent_type="tutor",
            ))
            db.add(ChatHistory(
                user_id=current_user.id,
                session_id=req.session_id,
                role="assistant",
                content=result.get("text_answer", ""),
                agent_type="tutor",
                metadata_={"question_type": result.get("question_type")},
            ))
            db.commit()

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
