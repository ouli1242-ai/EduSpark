"""评估 Agent — 基于学习行为数据，生成评估报告 + 调整建议"""
import json
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.agents.base import BaseAgent
from app.models.learning_record import LearningRecord
from app.models.resource import Resource
from app.models.profile import StudentProfile


class EvaluationAgent(BaseAgent):
    """评估 Agent：数据采集 → 统计分析 → LLM 生成报告"""

    async def run(self, input_data: dict) -> dict:
        """执行评估流程"""
        user_id = input_data.get("user_id")
        period = input_data.get("period", "7d")
        db: Session = input_data.get("db")
        profile = input_data.get("profile", {})

        # 1. 采集数据
        eval_data = self.collect_data(user_id, period, db)

        # 2. 统计分析
        analysis = self.analyze(eval_data)

        # 3. LLM 生成报告
        report = await self.generate_report(analysis, profile)

        return {
            "summary": analysis,
            "report": report,
        }

    def collect_data(self, user_id: int, period: str, db: Session) -> dict:
        """采集学习行为数据"""
        # 计算时间范围
        now = datetime.utcnow()
        period_map = {"1d": 1, "7d": 7, "30d": 30, "all": 36500}
        days = period_map.get(period, 7)
        start_date = now - timedelta(days=days)

        # 查询学习记录
        records = (
            db.query(LearningRecord)
            .filter(
                LearningRecord.user_id == user_id,
                LearningRecord.created_at >= start_date,
            )
            .all()
        )

        # 查询已生成的资源
        resources = (
            db.query(Resource)
            .filter(Resource.user_id == user_id)
            .all()
        )

        return {
            "records": records,
            "resources": resources,
            "period_start": start_date,
            "period_end": now,
        }

    def analyze(self, eval_data: dict) -> dict:
        """统计分析（纯统计，不依赖 LLM）"""
        records = eval_data["records"]
        resources = eval_data["resources"]

        # 按知识点分组
        topic_stats = defaultdict(lambda: {"views": 0, "completes": 0, "quiz_correct": 0, "quiz_total": 0})
        total_duration = 0
        action_counts = defaultdict(int)

        for r in records:
            action_counts[r.action] += 1
            detail = r.detail or {}

            if r.knowledge_point:
                stats = topic_stats[r.knowledge_point]
                if r.action == "view":
                    stats["views"] += 1
                    total_duration += detail.get("duration_seconds", 0)
                elif r.action == "complete":
                    stats["completes"] += 1
                elif r.action == "quiz":
                    stats["quiz_total"] += 1
                    if detail.get("correct"):
                        stats["quiz_correct"] += 1

        # 计算掌握度和薄弱点
        mastered_topics = []
        weak_topics = []
        for topic, stats in topic_stats.items():
            if stats["completes"] > 0:
                mastered_topics.append(topic)
            if stats["quiz_total"] > 0:
                accuracy = stats["quiz_correct"] / stats["quiz_total"]
                if accuracy < 0.6:
                    weak_topics.append({"topic": topic, "accuracy": round(accuracy, 2)})

        # 测试正确率
        total_quiz_correct = sum(s["quiz_correct"] for s in topic_stats.values())
        total_quiz = sum(s["quiz_total"] for s in topic_stats.values())
        test_accuracy = round(total_quiz_correct / total_quiz, 2) if total_quiz > 0 else 0

        # 资源完成数
        completed_resources = sum(1 for r in records if r.action == "complete")

        # 学习时长（小时）
        learning_hours = round(total_duration / 3600, 1)

        return {
            "knowledge_mastered": len(mastered_topics),
            "knowledge_weak": weak_topics,
            "learning_hours": learning_hours,
            "resources_completed": completed_resources,
            "test_accuracy": test_accuracy,
            "total_records": len(records),
            "action_counts": dict(action_counts),
            "period_start": eval_data["period_start"].isoformat(),
            "period_end": eval_data["period_end"].isoformat(),
        }

    async def generate_report(self, analysis: dict, profile: dict) -> dict:
        """调用 LLM 生成自然语言评估报告"""
        prompt = """你是一个学习效果评估专家。根据以下数据分析结果，生成一份学习评估报告。

数据摘要：
- 周期：{period_start} ~ {period_end}
- 已掌握知识点：{knowledge_mastered} 个
- 薄弱知识点：{weak_topics}
- 总学习时长：{learning_hours} 小时
- 完成资源数：{resources_completed}
- 测试平均正确率：{test_accuracy}
- 总学习记录数：{total_records}

学生画像：{profile}

请以 JSON 格式返回评估报告，包含以下字段：
{{
  "summary": "总结学习表现（2-3句话）",
  "strengths": ["优势1", "优势2", "优势3"],
  "weaknesses": ["需要改进的地方1", "需要改进的地方2"],
  "recommendations": [
    {{"action": "复习/练习/深入学习", "topic": "知识点", "reason": "原因", "suggested_resources": []}}
  ]
}}

要求：
1. 语气鼓励为主，建设性为辅
2. 建议具体可执行
3. 只返回 JSON，不要其他内容"""

        weak_topics_str = json.dumps(analysis.get("knowledge_weak", []), ensure_ascii=False)
        profile_str = json.dumps(profile, ensure_ascii=False) if profile else "暂无画像数据"

        messages = self._build_messages("", prompt.format(
            period_start=analysis.get("period_start", ""),
            period_end=analysis.get("period_end", ""),
            knowledge_mastered=analysis.get("knowledge_mastered", 0),
            weak_topics=weak_topics_str,
            learning_hours=analysis.get("learning_hours", 0),
            resources_completed=analysis.get("resources_completed", 0),
            test_accuracy=analysis.get("test_accuracy", 0),
            total_records=analysis.get("total_records", 0),
            profile=profile_str,
        ))

        result = await self.llm.chat(messages)

        # 解析 JSON
        try:
            # 提取 JSON 部分
            json_start = result.find("{")
            json_end = result.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                report = json.loads(result[json_start:json_end])
            else:
                report = {"summary": result, "strengths": [], "weaknesses": [], "recommendations": []}
        except json.JSONDecodeError:
            report = {"summary": result, "strengths": [], "weaknesses": [], "recommendations": []}

        return report


# 全局评估 Agent 实例
evaluation_agent = EvaluationAgent()
