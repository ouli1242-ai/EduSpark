"""知识图谱 + 资源推荐 API 路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.utils.auth import get_current_user
from app.models.user import User
from app.models.profile import StudentProfile
from app.models.resource import Resource
from app.models.knowledge_graph import KnowledgeGraphNode

router = APIRouter(prefix="/api", tags=["知识图谱"])


class RecommendRequest(BaseModel):
    topic: str
    limit: int = 5


# ─── 知识图谱接口 ──────────────────────────────────────────────────────────────

@router.get("/knowledge-graph")
async def get_knowledge_graph(
    course: str = Query("机器学习", description="课程名称"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取课程知识图谱"""
    nodes = (
        db.query(KnowledgeGraphNode)
        .filter(KnowledgeGraphNode.course == course)
        .all()
    )

    return {
        "course": course,
        "nodes": [
            {
                "id": n.id,
                "name": n.name,
                "chapter": n.chapter,
                "difficulty": n.difficulty,
                "prerequisites": n.prerequisites,
                "related": n.related,
                "description": n.description,
            }
            for n in nodes
        ],
    }


@router.post("/knowledge-graph")
async def create_knowledge_node(
    node_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建知识图谱节点"""
    node = KnowledgeGraphNode(
        course=node_data.get("course", "机器学习"),
        name=node_data.get("name", ""),
        chapter=node_data.get("chapter", 0),
        difficulty=node_data.get("difficulty", 1),
        prerequisites=node_data.get("prerequisites", []),
        related=node_data.get("related", []),
        description=node_data.get("description", ""),
    )
    db.add(node)
    db.commit()
    db.refresh(node)

    return {"id": node.id, "message": "节点创建成功"}


# ─── 资源推荐接口 ──────────────────────────────────────────────────────────────

def calculate_match_score(profile: dict, resource: Resource, topic: str) -> float:
    """计算资源与画像的匹配分数"""
    score = 0.0

    # 维度 1：知识点匹配度（权重 0.4）
    if topic in (resource.knowledge_points or []):
        score += 0.4

    # 维度 2：难度适配（权重 0.3）
    pref_diff = profile.get("learning_preferences", {}).get("difficulty_pref", "中等")
    diff_map = {"简单": 2, "中等": 3, "困难": 4}
    target = diff_map.get(pref_diff, 3)
    diff_score = 1 - abs((resource.difficulty or 3) - target) / 4
    score += 0.3 * diff_score

    # 维度 3：资源类型偏好（权重 0.2）
    pref_types = profile.get("learning_preferences", {}).get("resource_types", [])
    if resource.type.value in pref_types:
        score += 0.2

    # 维度 4：置信度（权重 0.1）
    conf_map = {"high": 1.0, "medium": 0.6, "low": 0.3}
    score += 0.1 * conf_map.get(resource.confidence, 0.5)

    return score


@router.get("/resources/recommend")
async def recommend_resources(
    topic: str = Query(..., description="知识点"),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """根据知识点推荐资源"""
    # 获取用户画像
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    profile_dict = {}
    if profile:
        profile_dict = {
            "learning_preferences": profile.learning_preferences,
        }

    # 查询相关资源
    resources = (
        db.query(Resource)
        .filter(Resource.user_id == current_user.id)
        .all()
    )

    # 计算匹配分数
    scored = []
    for r in resources:
        score = calculate_match_score(profile_dict, r, topic)
        scored.append((r, score))

    # 排序取 Top N
    scored.sort(key=lambda x: x[1], reverse=True)
    top_resources = scored[:limit]

    return {
        "topic": topic,
        "recommendations": [
            {
                "id": r.id,
                "type": r.type.value,
                "title": r.title,
                "description": r.description,
                "difficulty": r.difficulty,
                "knowledge_points": r.knowledge_points,
                "confidence": r.confidence,
                "match_score": round(score, 2),
                "created_at": r.created_at.isoformat(),
            }
            for r, score in top_resources
        ],
    }
