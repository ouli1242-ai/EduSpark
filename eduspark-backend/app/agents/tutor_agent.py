"""辅导 Agent — 接收学生问题，返回多模态解答（文字 + 图解 + 语音）"""
import json
from typing import AsyncGenerator
from app.agents.base import BaseAgent
from app.services.storage import get_storage
from app.utils.sse import sse_event


# 问题类型枚举
QUESTION_TYPES = ["concept", "calculation", "code", "application"]

# 各类型 Prompt 模板
PROMPTS = {
    "concept": """学生问了一个概念理解类问题。
问题：{question}
相关知识点：{context_topic}
学生画像：{profile}

请用通俗易懂的语言解释这个概念，要求：
1. 先给一句话的精确定义
2. 用一个生活中的类比来帮助理解
3. 给出 1-2 个具体例子
4. 指出常见的误解
5. Markdown 格式""",

    "calculation": """学生问了一个计算推导类问题。
问题：{question}
相关知识点：{context_topic}

请给出详细的推导过程，要求：
1. 列出所需的前提知识
2. 分步骤推导，每步都有解释
3. 标注关键公式
4. 最后给一个练习题巩固""",

    "code": """学生问了一个代码实现类问题。
问题：{question}

请给出代码解答，要求：
1. 先用文字说明思路
2. 给出完整可运行的 Python 代码
3. 代码中有详细注释
4. 给出运行结果示例
5. 指出可能的边界情况""",

    "application": """学生问了一个应用场景类问题。
问题：{question}
相关知识点：{context_topic}
学生画像：{profile}

请给出详细解答，要求：
1. 解释该知识点的实际应用场景
2. 给出 2-3 个真实案例
3. 分析应用中的关键考量
4. 总结最佳实践
5. Markdown 格式""",
}

# 通用兜底 Prompt
FALLBACK_PROMPT = """学生问了一个问题。
问题：{question}
相关知识点：{context_topic}
学生画像：{profile}

请给出详细、易懂的解答，要求：
1. 语言适合学生水平
2. 结构清晰，分点说明
3. 包含具体例子
4. Markdown 格式"""


class TutorAgent(BaseAgent):
    """辅导 Agent：问题分类 → 文字解答 → 图解生成 → 语音生成"""

    async def run(self, input_data: dict) -> dict:
        """非流式执行（兼容基类接口）"""
        question = input_data.get("question", "")
        context_topic = input_data.get("context_topic", "")
        profile = input_data.get("profile", {})
        output_modes = input_data.get("output_modes", ["text"])

        # 1. 分类
        q_type = await self.classify(question)

        # 2. 生成文字解答
        text_answer = await self.generate_text(question, q_type, profile, context_topic)

        result = {
            "question": question,
            "question_type": q_type,
            "text_answer": text_answer,
            "images": [],
            "audio": None,
        }

        # 3. 可选：生成图解
        if "image" in output_modes:
            try:
                image_key = await self.generate_image(text_answer)
                if image_key:
                    result["images"].append(image_key)
            except Exception:
                pass  # 降级：跳过

        # 4. 可选：生成语音
        if "audio" in output_modes:
            try:
                audio_key = await self.generate_audio(text_answer)
                if audio_key:
                    result["audio"] = audio_key
            except Exception:
                pass  # 降级：跳过

        return result

    async def run_stream(self, input_data: dict) -> AsyncGenerator[dict, None]:
        """流式执行：逐步返回文字 + 图解 + 语音"""
        question = input_data.get("question", "")
        context_topic = input_data.get("context_topic", "")
        profile = input_data.get("profile", {})
        output_modes = input_data.get("output_modes", ["text"])

        # 1. 分类
        yield sse_event({"type": "agent_status", "agent": "tutor", "status": "classifying"})
        q_type = await self.classify(question)

        # 2. 流式生成文字解答
        yield sse_event({"type": "agent_status", "agent": "tutor", "status": "generating_text"})
        system_prompt = self._get_prompt(q_type, context_topic, profile)
        messages = self._build_messages(system_prompt, question)

        full_answer = ""
        async for chunk in self.llm.chat_stream(messages):
            full_answer += chunk
            yield sse_event({"type": "chunk", "content": chunk})

        yield sse_event({"type": "text_done", "content": full_answer})

        # 3. 可选：生成图解
        image_key = None
        if "image" in output_modes:
            yield sse_event({"type": "agent_status", "agent": "tutor", "status": "generating_image"})
            try:
                image_key = await self.generate_image(full_answer)
                if image_key:
                    yield sse_event({"type": "image_done", "url": f"/api/files/{image_key}"})
            except Exception as e:
                yield sse_event({"type": "image_error", "message": str(e)})

        # 4. 可选：生成语音
        audio_key = None
        if "audio" in output_modes:
            yield sse_event({"type": "agent_status", "agent": "tutor", "status": "generating_audio"})
            try:
                audio_key = await self.generate_audio(full_answer)
                if audio_key:
                    yield sse_event({"type": "audio_done", "url": f"/api/files/{audio_key}"})
            except Exception as e:
                yield sse_event({"type": "audio_error", "message": str(e)})

        yield sse_event({"type": "done"})

    async def classify(self, question: str) -> str:
        """对问题进行分类"""
        prompt = """将以下学生问题分类为以下四种类型之一，只返回类型名称：
- concept: 概念理解类（问"是什么"、"什么意思"）
- calculation: 计算推导类（涉及公式、推导、计算）
- code: 代码实现类（要求写代码、编程）
- application: 应用场景类（问"怎么用"、"有什么用"）

问题：{question}

只返回类型名称，不要其他内容。"""

        messages = self._build_messages("", prompt.format(question=question))
        result = await self.llm.chat(messages)
        result = result.strip().lower()

        if result in QUESTION_TYPES:
            return result
        return "concept"  # 默认

    async def generate_text(self, question: str, q_type: str, profile: dict, context_topic: str) -> str:
        """生成文字解答"""
        system_prompt = self._get_prompt(q_type, context_topic, profile)
        messages = self._build_messages(system_prompt, question)
        return await self.llm.chat(messages)

    async def generate_image(self, text_answer: str) -> str | None:
        """从文字解答中提取可视化需求，调用讯飞图像生成 API"""
        try:
            import httpx
            from app.core.config import get_settings
            settings = get_settings()

            # 提取可视化需求
            extract_prompt = """从以下解答中提取一个适合可视化的关键概念，输出为简短的图像描述（不超过50字），用于 AI 图像生成。
如果内容不适合可视化，返回"无"。

解答：{answer}"""

            messages = self._build_messages("", extract_prompt.format(answer=text_answer[:500]))
            desc = await self.llm.chat(messages)
            desc = desc.strip()

            if not desc or desc == "无":
                return None

            # 调用讯飞图像生成 API
            # 注意：实际 API 调用需要根据讯飞文档实现
            # 这里使用 storage 存储占位
            storage = get_storage()

            # TODO: 实际调用讯飞图像生成 API
            # 暂时返回 None，降级处理
            return None

        except Exception:
            return None

    async def generate_audio(self, text_answer: str) -> str | None:
        """调用讯飞 TTS API 生成语音"""
        try:
            import httpx
            from app.core.config import get_settings
            settings = get_settings()

            # 提取关键段落用于 TTS
            tts_prompt = """从以下解答中提取核心内容，转换为适合朗读的口语化表达（不超过300字）：

解答：{answer}"""

            messages = self._build_messages("", tts_prompt.format(answer=text_answer[:1000]))
            tts_text = await self.llm.chat(messages)
            tts_text = tts_text.strip()

            if not tts_text:
                return None

            # 调用讯飞 TTS API
            # 注意：实际 API 调用需要根据讯飞文档实现
            # 这里使用 storage 存储占位
            storage = get_storage()

            # TODO: 实际调用讯飞 TTS API
            # 暂时返回 None，降级处理
            return None

        except Exception:
            return None

    def _get_prompt(self, q_type: str, context_topic: str, profile: dict) -> str:
        """获取对应类型的 Prompt"""
        prompt_template = PROMPTS.get(q_type, FALLBACK_PROMPT)
        return prompt_template.format(
            question="{question}",  # 占位，实际在 _build_messages 中替换
            context_topic=context_topic or "未指定",
            profile=json.dumps(profile, ensure_ascii=False) if profile else "暂无画像数据",
        )


# 全局辅导 Agent 实例
tutor_agent = TutorAgent()
