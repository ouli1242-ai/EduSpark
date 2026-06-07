"""画像 Agent — 对话式学习画像构建"""
import json
from app.agents.base import BaseAgent

SYSTEM_PROMPT = """你是一个学习画像分析专家。通过与学生的对话，提取以下6个维度的信息：

1. 知识基础（knowledge_base）：已掌握知识点、薄弱知识点、知识盲区
2. 认知风格（cognitive_style）：视觉型/听觉型/动觉型，归纳型/演绎型
3. 学习能力（learning_ability）：知识吸收速度、理解深度、迁移能力
4. 易错点偏好（error_patterns）：常见错误类型、错误原因分析
5. 学习目标（learning_goals）：短期目标、长期目标、职业规划
6. 学习偏好（learning_preferences）：喜欢的资源类型、学习时间偏好、难度偏好

请通过自然对话获取信息，不要直接询问所有问题。每次回复后，提取已获得的画像信息。

输出格式：先正常回复学生，然后在末尾用 [PROFILE_UPDATE] 标记附上最新画像JSON：
[PROFILE_UPDATE]
{"knowledge_base": {...}, "cognitive_style": {...}, ...}
[/PROFILE_UPDATE]

如果某些维度信息不足，对应字段留空对象 {}。"""


class ProfileAgent(BaseAgent):
    """画像 Agent：从对话中提取学生学习画像"""

    async def run(self, input_data: dict) -> dict:
        """
        input_data:
            - message: 当前用户消息
            - history: 对话历史 [{"role": "user/assistant", "content": "..."}]
            - current_profile: 当前画像（可选）
        """
        message = input_data["message"]
        history = input_data.get("history", [])
        current_profile = input_data.get("current_profile", {})

        # 构建上下文
        context_parts = []
        if current_profile:
            context_parts.append(f"当前已知画像：\n{json.dumps(current_profile, ensure_ascii=False, indent=2)}")

        context_parts.append(f"学生最新消息：{message}")
        user_content = "\n\n".join(context_parts)

        messages = self._build_messages(SYSTEM_PROMPT, user_content)
        # 加入历史对话
        for h in history[-10:]:  # 最近10条
            messages.insert(-1, h)

        response = await self.llm.chat(messages)

        # 解析回复：分离正常回复和画像更新
        reply = response
        profile_update = None

        if "[PROFILE_UPDATE]" in response and "[/PROFILE_UPDATE]" in response:
            try:
                start = response.index("[PROFILE_UPDATE]") + len("[PROFILE_UPDATE]")
                end = response.index("[/PROFILE_UPDATE]")
                profile_json = response[start:end].strip()
                profile_update = json.loads(profile_json)
                reply = response[:response.index("[PROFILE_UPDATE]")].strip()
            except (ValueError, json.JSONDecodeError):
                pass

        return {
            "reply": reply,
            "profile_update": profile_update,
            "full_response": response,
        }

    async def run_stream(self, input_data: dict):
        """流式版本：先返回对话内容，最后返回画像更新"""
        result = await self.run(input_data)
        # 逐 chunk 返回对话内容
        content = result["reply"]
        chunk_size = 20
        for i in range(0, len(content), chunk_size):
            yield {"type": "chunk", "content": content[i:i + chunk_size]}

        if result["profile_update"]:
            yield {"type": "profile_update", "data": result["profile_update"]}

        yield {"type": "done"}
