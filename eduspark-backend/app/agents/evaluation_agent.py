"""评估 Agent — 学习效果评估与策略调整"""
import json
from app.agents.base import BaseAgent

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
}
```"""


class EvaluationAgent(BaseAgent):
    """评估 Agent：学习效果评估 + 策略调整建议"""

    async def run(self, input_data: dict) -> dict:
        """
        input_data:
            - profile: 学生画像
            - records: 学习记录列表
            - resources: 已生成资源列表（可选）
            - paths: 学习路径列表（可选）
        """
        profile = input_data.get("profile", {})
        records = input_data.get("records", [])
        resources = input_data.get("resources", [])
        paths = input_data.get("paths", [])

        # 1. 统计分析
        stats = self._calculate_stats(records, profile)

        # 2. 构建评估上下文
        context_parts = [
            f"学生画像：\n{json.dumps(profile, ensure_ascii=False, indent=2)}",
            f"\n数据统计：\n{json.dumps(stats, ensure_ascii=False, indent=2)}",
        ]

        # 学习记录摘要
        if records:
            record_summary = "学习记录（最近20条）：\n"
            for r in records[:20]:
                rtype = r.action if hasattr(r, 'action') else r.get('action', '未知')
                rkp = r.knowledge_point if hasattr(r, 'knowledge_point') else r.get('knowledge_point', '')
                rdetail = r.detail if hasattr(r, 'detail') else r.get('detail', {})
                record_summary += f"  - [{rtype}] {rkp} {json.dumps(rdetail, ensure_ascii=False)}\n"
            context_parts.append(record_summary)

        # 资源列表
        if resources:
            res_summary = "已生成资源：\n"
            for r in resources[:10]:
                rtype = r.type.value if hasattr(r, 'type') else r.get('type', '')
                rtitle = r.title if hasattr(r, 'title') else r.get('title', '')
                res_summary += f"  - [{rtype}] {rtitle}\n"
            context_parts.append(res_summary)

        user_content = "\n".join(context_parts)
        messages = self._build_messages(EVALUATION_SYSTEM_PROMPT, user_content)
        response = await self.llm.chat(messages, temperature=0.5, max_tokens=4096)

        # 解析 JSON
        report = {}
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            report = json.loads(response[start:end])
        except (json.JSONDecodeError, ValueError):
            report = {
                "report": {
                    "summary": stats,
                    "strengths": [],
                    "weaknesses": [],
                    "recommendations": [],
                    "next_steps": [],
                }
            }

        return {
            "type": "evaluation",
            "report": report.get("report", report),
            "stats": stats,
            "raw_response": response,
        }

    def _calculate_stats(self, records: list, profile: dict) -> dict:
        """从原始数据计算统计指标"""
        if not records:
            return {
                "total_activities": 0,
                "quiz_attempts": 0,
                "resources_accessed": 0,
                "conversations": 0,
                "average_quiz_score": None,
                "topics_studied": [],
            }

        recs = []
        for r in records:
            if hasattr(r, '__dict__'):
                recs.append({
                    "action": getattr(r, 'action', ''),
                    "knowledge_point": getattr(r, 'knowledge_point', ''),
                    "detail": getattr(r, 'detail', {}),
                })
            else:
                recs.append(r)

        total = len(recs)
        quiz_attempts = [r for r in recs if r["action"] == "quiz"]
        resources_accessed = [r for r in recs if r["action"] in ("view", "complete")]
        conversations = [r for r in recs if r["action"] == "chat"]

        # 计算平均测验分数
        quiz_scores = []
        for q in quiz_attempts:
            detail = q.get("detail", {})
            score = detail.get("score", detail.get("correct", None))
            total_q = detail.get("total", None)
            if score is not None and total_q and total_q > 0:
                quiz_scores.append(score / total_q * 100)

        avg_score = round(sum(quiz_scores) / len(quiz_scores), 1) if quiz_scores else None

        # 统计学习过的知识点
        topics = list(set(r["knowledge_point"] for r in recs if r["knowledge_point"]))

        return {
            "total_activities": total,
            "quiz_attempts": len(quiz_attempts),
            "resources_accessed": len(resources_accessed),
            "conversations": len(conversations),
            "average_quiz_score": avg_score,
            "topics_studied": topics[:20],
            "topics_count": len(topics),
        }
