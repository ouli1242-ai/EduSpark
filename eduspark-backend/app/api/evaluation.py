"""学习评估接口"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.profile import StudentProfile
from app.models.learning_record import LearningRecord
from app.models.resource import Resource
from app.models.learning_path import LearningPath
from app.utils.auth import get_current_user
from app.agents.evaluation_agent import EvaluationAgent

router = APIRouter(prefix="/api/evaluation", tags=["学习评估"])

evaluation_agent = EvaluationAgent()


@router.get("")
async def get_evaluation(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取学习评估报告"""
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    current_profile = {}
    if profile:
        current_profile = {
            "knowledge_base": profile.knowledge_base,
            "cognitive_style": profile.cognitive_style,
            "learning_ability": profile.learning_ability,
            "error_patterns": profile.error_patterns,
            "learning_goals": profile.learning_goals,
            "learning_preferences": profile.learning_preferences,
        }

    records = (
        db.query(LearningRecord)
        .filter(LearningRecord.user_id == user.id)
        .order_by(LearningRecord.created_at.desc())
        .limit(100)
        .all()
    )

    resources = db.query(Resource).filter(Resource.user_id == user.id).all()
    paths = db.query(LearningPath).filter(LearningPath.user_id == user.id).all()

    result = await evaluation_agent.run({
        "profile": current_profile,
        "records": records,
        "resources": resources,
        "paths": paths,
    })

    return result


@router.get("/stats")
def get_learning_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取学习统计数据（轻量级，无需 LLM）"""
    records = (
        db.query(LearningRecord)
        .filter(LearningRecord.user_id == user.id)
        .order_by(LearningRecord.created_at.desc())
        .limit(200)
        .all()
    )

    if not records:
        return {"total_activities": 0, "message": "暂无学习记录"}

    total = len(records)
    quiz_attempts = sum(1 for r in records if r.action == "quiz")
    chats = sum(1 for r in records if r.action == "chat")
    views = sum(1 for r in records if r.action in ("view", "complete"))

    # 计算平均测验分数
    quiz_scores = []
    for r in records:
        if r.action == "quiz" and r.detail:
            score = r.detail.get("score")
            total_q = r.detail.get("total")
            if score is not None and total_q and total_q > 0:
                quiz_scores.append(score / total_q * 100)

    avg_score = round(sum(quiz_scores) / len(quiz_scores), 1) if quiz_scores else None

    # 统计知识点
    topics = list(set(r.knowledge_point for r in records if r.knowledge_point))

    # 按日期统计活跃度
    from collections import Counter
    from datetime import date
    daily_counts = Counter(r.created_at.strftime("%Y-%m-%d") for r in records if r.created_at)

    return {
        "total_activities": total,
        "quiz_attempts": quiz_attempts,
        "chats": chats,
        "resources_accessed": views,
        "average_quiz_score": avg_score,
        "topics_count": len(topics),
        "topics_studied": topics[:20],
        "daily_activity": dict(daily_counts.most_common(30)),
    }
