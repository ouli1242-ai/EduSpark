"""学习评估接口"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.utils.auth import get_current_user
from app.models.user import User
from app.models.profile import StudentProfile
from app.models.learning_record import LearningRecord
from app.models.resource import Resource
from app.models.learning_path import LearningPath
from app.models.evaluation import EvaluationReport
from app.agents.evaluation_agent import EvaluationAgent

router = APIRouter(prefix="/api/evaluation", tags=["学习评估"])

evaluation_agent = EvaluationAgent()


class EvaluationRequest(BaseModel):
    period: str = "7d"  # 1d / 7d / 30d / all
    focus_topics: list[str] = []


@router.get("")
async def get_evaluation(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取学习评估报告（兼容旧接口，直接返回）"""
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
        "user_id": user.id,
        "period": "30d",
        "db": db,
        "profile": current_profile,
    })

    return result


@router.post("/generate")
async def generate_evaluation(
    req: EvaluationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """生成学习效果评估报告并保存"""
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
        result = await evaluation_agent.run({
            "user_id": current_user.id,
            "period": req.period,
            "db": db,
            "profile": profile_dict,
        })

        summary = result.get("summary", {})
        report = result.get("report", {})

        # 保存评估报告
        eval_report = EvaluationReport(
            user_id=current_user.id,
            period_start=datetime.fromisoformat(summary.get("period_start", datetime.utcnow().isoformat())),
            period_end=datetime.fromisoformat(summary.get("period_end", datetime.utcnow().isoformat())),
            summary=summary,
            strengths=report.get("strengths", []),
            weaknesses=report.get("weaknesses", []),
            recommendations=report.get("recommendations", []),
            report_text=report.get("summary", ""),
        )
        db.add(eval_report)
        db.commit()
        db.refresh(eval_report)

        return {
            "evaluation_id": eval_report.id,
            "period": f"{eval_report.period_start.strftime('%Y-%m-%d')} ~ {eval_report.period_end.strftime('%Y-%m-%d')}",
            "summary": summary,
            "strengths": eval_report.strengths,
            "weaknesses": eval_report.weaknesses,
            "recommendations": eval_report.recommendations,
            "report_text": eval_report.report_text,
            "generated_at": eval_report.created_at.isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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

    quiz_scores = []
    for r in records:
        if r.action == "quiz" and r.detail:
            score = r.detail.get("score")
            total_q = r.detail.get("total")
            if score is not None and total_q and total_q > 0:
                quiz_scores.append(score / total_q * 100)

    avg_score = round(sum(quiz_scores) / len(quiz_scores), 1) if quiz_scores else None

    topics = list(set(r.knowledge_point for r in records if r.knowledge_point))

    from collections import Counter
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


@router.get("/list")
async def list_evaluations(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取历史评估报告列表"""
    query = (
        db.query(EvaluationReport)
        .filter(EvaluationReport.user_id == current_user.id)
        .order_by(EvaluationReport.created_at.desc())
    )
    total = query.count()
    reports = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": r.id,
                "period": f"{r.period_start.strftime('%Y-%m-%d')} ~ {r.period_end.strftime('%Y-%m-%d')}",
                "summary": r.summary,
                "strengths": r.strengths,
                "weaknesses": r.weaknesses,
                "recommendations": r.recommendations,
                "report_text": r.report_text,
                "created_at": r.created_at.isoformat(),
            }
            for r in reports
        ],
    }


@router.get("/detail/{evaluation_id}")
async def get_evaluation_detail(
    evaluation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单个评估报告详情"""
    report = (
        db.query(EvaluationReport)
        .filter(
            EvaluationReport.id == evaluation_id,
            EvaluationReport.user_id == current_user.id,
        )
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="评估报告不存在")

    return {
        "id": report.id,
        "period": f"{report.period_start.strftime('%Y-%m-%d')} ~ {report.period_end.strftime('%Y-%m-%d')}",
        "summary": report.summary,
        "strengths": report.strengths,
        "weaknesses": report.weaknesses,
        "recommendations": report.recommendations,
        "report_text": report.report_text,
        "created_at": report.created_at.isoformat(),
    }
