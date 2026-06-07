"""路径 Agent — 学习路径规划"""
import json
from app.agents.base import BaseAgent

SYSTEM_PROMPT = """你是一个学习路径规划专家。根据学生的画像和已有资源，规划个性化学习路径。

要求：
- 考虑知识点之间的依赖关系（前置知识 → 进阶知识）
- 根据学生画像调整顺序（薄弱点优先强化）
- 每个步骤包含：知识点名称、推荐资源、预计学习时间
- 总步骤数 5-10 个
- 输出 JSON 格式

输出格式：
```json
{
  "name": "机器学习入门路径",
  "course": "机器学习",
  "steps": [
    {
      "order": 1,
      "topic": "线性回归",
      "knowledge_points": ["最小二乘法", "梯度下降"],
      "description": "...",
      "estimated_time": "2h",
      "status": "pending"
    }
  ]
}
```"""


class PathAgent(BaseAgent):
    """路径 Agent：规划个性化学习路径"""

    async def run(self, input_data: dict) -> dict:
        """
        input_data:
            - course: 课程名称
            - profile: 学生画像
            - resources: 已有资源列表（可选）
            - request: 学生具体需求（可选）
        """
        course = input_data.get("course", "机器学习")
        profile = input_data.get("profile", {})
        resources = input_data.get("resources", [])
        request = input_data.get("request", "")

        context_parts = [
            f"课程：{course}",
            f"学生画像：{json.dumps(profile, ensure_ascii=False)}",
        ]
        if resources:
            res_summary = [
                f"- [{r['type']}] {r['title']}" for r in resources[:20]
            ]
            context_parts.append("已有资源：\n" + "\n".join(res_summary))
        if request:
            context_parts.append(f"学生需求：{request}")

        user_content = "\n\n".join(context_parts)
        messages = self._build_messages(SYSTEM_PROMPT, user_content)
        response = await self.llm.chat(messages)

        # 解析 JSON
        path_data = {}
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            path_data = json.loads(response[start:end])
        except (json.JSONDecodeError, ValueError):
            path_data = {"name": f"{course}学习路径", "course": course, "steps": []}

        return {
            "path": path_data,
            "raw_response": response,
        }
