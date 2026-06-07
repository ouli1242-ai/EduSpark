"""学习资源接口"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.resource import Resource, ResourceStatus
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/resources", tags=["学习资源"])


@router.get("")
def list_resources(
    type: str = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Resource).filter(Resource.user_id == user.id)
    if type:
        query = query.filter(Resource.type == type)
    resources = query.order_by(Resource.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "type": r.type.value,
            "title": r.title,
            "description": r.description,
            "status": r.status.value,
            "difficulty": r.difficulty,
            "confidence": r.confidence,
            "knowledge_points": r.knowledge_points,
            "created_at": r.created_at.isoformat(),
        }
        for r in resources
    ]


@router.get("/{resource_id}")
def get_resource(
    resource_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    r = db.query(Resource).filter(Resource.id == resource_id, Resource.user_id == user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="资源不存在")
    return {
        "id": r.id,
        "type": r.type.value,
        "title": r.title,
        "description": r.description,
        "content": r.content,
        "status": r.status.value,
        "difficulty": r.difficulty,
        "confidence": r.confidence,
        "knowledge_points": r.knowledge_points,
        "storage_key": r.storage_key,
        "created_at": r.created_at.isoformat(),
    }


@router.delete("/{resource_id}")
def delete_resource(
    resource_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    r = db.query(Resource).filter(Resource.id == resource_id, Resource.user_id == user.id).first()
    if not r:
        raise HTTPException(status_code=404, detail="资源不存在")
    db.delete(r)
    db.commit()
    return {"message": "删除成功"}
