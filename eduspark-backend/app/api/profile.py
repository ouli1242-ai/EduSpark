"""学习画像接口"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.models.user import User
from app.models.profile import StudentProfile
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/profile", tags=["学习画像"])


@router.get("")
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if not profile:
        # 首次访问，创建空画像
        profile = StudentProfile(user_id=user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return {
        "id": profile.id,
        "knowledge_base": profile.knowledge_base,
        "cognitive_style": profile.cognitive_style,
        "learning_ability": profile.learning_ability,
        "error_patterns": profile.error_patterns,
        "learning_goals": profile.learning_goals,
        "learning_preferences": profile.learning_preferences,
        "conversation_turns": profile.conversation_turns,
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
    }


@router.put("")
def update_profile(
    data: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if not profile:
        profile = StudentProfile(user_id=user.id)
        db.add(profile)

    # 允许更新的字段
    updatable = [
        "knowledge_base", "cognitive_style", "learning_ability",
        "error_patterns", "learning_goals", "learning_preferences",
    ]
    for key in updatable:
        if key in data:
            setattr(profile, key, data[key])

    db.commit()
    db.refresh(profile)
    return {"message": "画像更新成功"}
