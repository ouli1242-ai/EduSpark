"""学习路径接口"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.learning_path import LearningPath
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/path", tags=["学习路径"])


@router.get("")
def list_paths(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    paths = db.query(LearningPath).filter(LearningPath.user_id == user.id).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "course": p.course,
            "progress": p.progress,
            "steps_count": len(p.steps),
            "created_at": p.created_at.isoformat(),
        }
        for p in paths
    ]


@router.get("/{path_id}")
def get_path(
    path_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    p = db.query(LearningPath).filter(
        LearningPath.id == path_id, LearningPath.user_id == user.id
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="路径不存在")
    return {
        "id": p.id,
        "name": p.name,
        "course": p.course,
        "steps": p.steps,
        "progress": p.progress,
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


@router.put("/{path_id}/progress")
def update_progress(
    path_id: int,
    data: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    p = db.query(LearningPath).filter(
        LearningPath.id == path_id, LearningPath.user_id == user.id
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="路径不存在")

    # 更新步骤状态
    if "steps" in data:
        p.steps = data["steps"]
    if "progress" in data:
        p.progress = data["progress"]

    db.commit()
    return {"message": "进度更新成功"}
