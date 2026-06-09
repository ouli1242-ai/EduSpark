"""学习画像接口"""
import math
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Any
from app.core.database import get_db
from app.models.user import User
from app.models.profile import StudentProfile
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/profile", tags=["学习画像"])


def _sanitize_value(v: Any) -> Any:
    """递归清理 NaN/Inf/null 值 — 防止前端显示 NaN%"""
    if v is None:
        return None
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    if isinstance(v, dict):
        return {k: _sanitize_value(v) for k, v in v.items()}
    if isinstance(v, list):
        return [_sanitize_value(x) for x in v]
    return v


def _sanitize_profile(profile: StudentProfile) -> dict:
    """构建画像响应并清理其中的 NaN/Inf"""
    def clean(d: dict) -> dict:
        return _sanitize_value(d) or {}
    return {
        "id": profile.id,
        "knowledge_base": clean(profile.knowledge_base),
        "cognitive_style": clean(profile.cognitive_style),
        "learning_ability": clean(profile.learning_ability),
        "error_patterns": clean(profile.error_patterns),
        "learning_goals": clean(profile.learning_goals),
        "learning_preferences": clean(profile.learning_preferences),
        "conversation_turns": profile.conversation_turns,
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
    }


@router.get("")
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if not profile:
        # 首次访问，创建空画像
        profile = StudentProfile(user_id=user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    result = _sanitize_profile(profile)
    # 如果检测到数据中有脏数据，同步清理数据库
    _clean_db_profile(profile, result, db)
    return result


def _clean_db_profile(profile: StudentProfile, sanitized: dict, db: Session) -> None:
    """清理数据库中残留的 NaN/Inf 值（脏数据修复）"""
    dirty = False
    for key in ["knowledge_base", "cognitive_style", "learning_ability",
                 "error_patterns", "learning_goals", "learning_preferences"]:
        db_val = getattr(profile, key, None)
        clean_val = sanitized.get(key)
        if db_val is not None and db_val != clean_val:
            setattr(profile, key, clean_val)
            dirty = True
    if dirty:
        db.commit()


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
