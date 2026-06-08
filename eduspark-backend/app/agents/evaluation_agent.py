"""评估 Agent — 学习效果评估与策略调整"""
import json
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.models.learning_record import LearningRecord
from app.models.resource import Resource
from app.models.profile import StudentProfile

EVALUATION_SYSTEM_PROMPT = """你是一个学习效果评估专家。根据学生的学习数据和画像，生成详细的评估报告。

## 评估维度

### 1. 知识掌握度
- 综合判断学生对各知识点的掌握程度
- 识别已牢固掌握的知识点
- 找出需要复习的知识点
- 发现有知识盲区

### 2. 学习效率
- 根据学习记录评估学习速度
- 判断资源利用效率
- 分析时间投入与产出比

### 3. 能力成长
- 对比不同时期的数据看趋势
- 评估难度等级的变化
- 分析错误率的变化

### 4. 学习行为分析
- 学习时段偏好
- 资源类型偏好
- 学习频率和持续性

## 输出格式

```json
{
  "report": {
    "period": "评估时间段",
    "summary": {
      "knowledge_mastered": 已掌握知识点数量估计,
      "learning_hours": 总学习时长估计(小时),
      "overall_score": 综合评分(0-100),
      "growth_trend": "上升|持平|下降"
    },
    "strengths": [
      {"area": "优势领域", "description": "具体说明"}
    ],
    "weaknesses": [
      {"area": "薄弱领域", "description": "具体说明", "improvement": "改进建议"}
    ],
    "recommendations": [
      {"type": "学习策略|资源推荐|时间安排", "content": "具体建议"}
    ],
    "next_steps": [
      {"priority": 1, "action": "下一步行动", "reason": "原因"}
    ]
  }
}```"""


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
        now = datetime.utcnow()
        period_map = {"1d": 1, "7d": 7, "30d": 30, "all": 36500}
        days = period_map.get(period, 7)
        start_date = now - timedelta(days=days)

        records = (
            db.query(LearningRecord)
            .filter(
                LearningRecord.user_id == user_id,
                LearningRecord.created_at >= start_date,
            )
            .all()
        )

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

        mastered_topics = []
        weak_topics = []
        for topic, stats in topic_stats.items():
            if stats["completes"] > 0:
                mastered_topics.append(topic)
            if stats["quiz_total"] > 0:
                accuracy = stats["quiz_correct"] / stats["quiz_total"]
                if accuracy < 0.6:
                    weak_topics.append({"topic": topic, "accuracy": round(accuracy, 2)})

        total_quiz_correct = sum(s["quiz_correct"] for s in topic_stats.values())
        total_quiz = sum(s["quiz_total"] for s in topic_stats.values())
        test_accuracy = round(total_quiz_correct / total_quiz, 2) if total_quiz > 0 else 0

        completed_resources = sum(1 for r in records if r.action == "complete")
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
        """调用 LLM 生成评估报告"""
        profile_context = self._build_profile_context(profile)

        prompt = EVALUATION_SYSTEM_PROMPT + f"""

## 实际数据

数据摘要：
- 周期：{analysis.get("period_start", "")} ~ {analysis.get("period_end", "")}
- 已掌握知识点：{analysis.get("knowledge_mastered", 0)} 个
- 薄弱知识点：{json.dumps(analysis.get("knowledge_weak", []), ensure_ascii=False)}
- 总学习时长：{analysis.get("learning_hours", 0)} 小时
- 完成资源数：{analysis.get("resources_completed", 0)}
- 测试平均正确率：{analysis.get("test_accuracy", 0)}
- 总学习记录数：{analysis.get("total_records", 0)}

{profile_context}

请根据以上数据生成 JSON 格式的评估报告，严格按照输出格式。"""

        messages = self._build_messages("", prompt)
        result = await self.llm.chat(messages, temperature=0.5, max_tokens=4096)

        # 解析 JSON
        try:
            json_start = result.find("{")
            json_end = result.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                report = json.loads(result[json_start:json_end])
            else:
                report = {
                    "report": {
                        "summary": {
                            "knowledge_mastered": analysis.get("knowledge_mastered", 0),
                            "learning_hours": analysis.get("learning_hours", 0),
                            "overall_score": 0,
                            "growth_trend": "持平",
                        },
                        "strengths": [],
                        "weaknesses": [],
                        "recommendations": [],
                        "next_steps": [],
                    }
                }
        except json.JSONDecodeError:
            report = {
                "report": {
                    "summary": analysis,
                    "strengths": [],
                    "weaknesses": [],
                    "recommendations": [],
                    "next_steps": [],
                }
            }

        return report.get("report", report)

    def _build_profile_context(self, profile: dict) -> str:
        """构建画像上下文（给 LLM 看的）"""
        if not profile:
            return "暂无学生画像信息，按标准评估。"

        parts = []

        # 知识基础
        kb = profile.get("knowledge_base", {})
        mastered = kb.get("mastered", [])
        weak = kb.get("weak", [])
        blind = kb.get("blind_spots", [])
        if mastered or weak or blind:
            kb_lines = []
            if mastered:
                kb_lines.append(f"  - 已掌握：{', '.join(mastered[:5])}")
            if weak:
                kb_lines.append(f"  - 薄弱点：{', '.join(weak[:5])}")
            if blind:
                kb_lines.append(f"  - 知识盲区：{', '.join(blind[:5])}")
            parts.append("知识基础：\n" + "\n".join(kb_lines))

        # 认知风格
        cs = profile.get("cognitive_style", {})
        cs_summary = cs.get("summary", "")
        if cs_summary:
            parts.append(f"认知风格：{cs_summary}")

        # 学习能力
        la = profile.get("learning_ability", {})
        la_summary = la.get("summary", "")
        if la_summary:
            parts.append(f"学习能力：{la_summary}")

        # 学习目标
        lg = profile.get("learning_goals", {})
        short = lg.get("short_term", "")
        career = lg.get("career", "")
        if short:
            parts.append(f"短期目标：{short}")
        if career:
            parts.append(f"职业方向：{career}")

        if not parts:
            return "暂无足够画像信息，按标准评估。"

        return "\n".join(parts)


# 全局评估 Agent 实例
evaluation_agent = EvaluationAgent()
