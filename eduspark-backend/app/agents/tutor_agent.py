"""辅导 Agent — 智能多模态答疑"""
import json
from typing import AsyncGenerator

from app.agents.base import BaseAgent
from app.services.storage import get_storage
from app.services.rag_validator import rag_validator
from app.utils.sse import sse_event

QUESTION_CLASSIFY_PROMPT = """你是一个问题分类器。分析学生的问题，判断问题类型和涉及的知识点。

问题类型：
- concept: 概念理解类（"什么是X"、"X和Y有什么区别"、"X的原理是什么"）
- code: 代码实现类（"怎么写这段代码"、"帮我实现X"、"这段代码为什么报错"）
- application: 应用场景类（"X有什么用"、"实际怎么用"、"能举例子吗"）
- calculation: 计算推导类（"怎么推公式"、"帮我算X"、"这个怎么推导出来的"）

只返回 JSON，不要加其他内容：
{"type": "...", "knowledge_points": ["知识点1", "知识点2"], "difficulty": "基础|中等|困难"}"""

TUTOR_SYSTEM_PROMPT = """你是一个经验丰富的高等教育辅导老师。你的任务是用学生能理解的方式解答问题。

## 辅导原则

### 1. 因材施教
- 根据学生的认知风格调整讲解方式
  - 视觉型学生：多用图表描述、结构化的分步讲解
  - 听觉型学生：多用口语化表达、生动的比喻
  - 动觉型学生：多给动手实验、可操作的代码示例
- 根据学生的学习能力调整深度
  - 能力强：深入原理，引导独立思考
  - 能力中等：标准讲解，配合练习
  - 能力弱：从基础讲起，多给具体例子

### 2. 讲解策略

**概念理解类问题**：
1. 先用一句话给出核心定义
2. 用通俗的类比/比喻帮助理解
3. 给出 1-2 个具体例子
4. 如果学生有相关薄弱点，主动关联讲解

**代码实现类问题**：
1. 先解释思路/算法流程
2. 给出完整可运行的 Python 代码（带注释）
3. 逐段解释关键代码
4. 指出常见错误和注意事项

**应用场景类问题**：
1. 列举 2-3 个实际应用场景
2. 至少一个场景来自学生感兴趣的领域（根据画像）
3. 简要说明为什么适合这个场景

**计算推导类问题**：
1. 分步推导，每步注明依据
2. 关键步骤给出直观解释
3. 推导完成后做结果解释

### 3. 回答格式
- 使用 Markdown 格式
- 代码块用 ```python ... ```
- 重点内容用 **加粗** 标注
- 分层次，使用标题、列表

## 当前学生画像
{profile_context}

## 回答要求
用中文回答，语气亲切但专业。如果你发现学生有知识薄弱点，在回答末尾可以主动问是否需要进一步讲解。"""


class TutorAgent(BaseAgent):
    """辅导 Agent：问题分类 → 文字解答 → 图解生成 → 语音生成"""

    async def run(self, input_data: dict) -> dict:
        """非流式执行"""
        question = input_data.get("question", "")
        profile = input_data.get("profile", {})
        history = input_data.get("history", [])
        context_topic = input_data.get("context_topic", "")
        output_modes = input_data.get("output_modes", ["text"])

        # 1. 分类
        question_type, knowledge_points, difficulty = await self._classify_question(question)

        # 2. 构建画像上下文
        profile_context = self._build_profile_context(profile)

        # 3. 生成文字解答
        text_answer = await self._generate_text_answer(question, question_type, knowledge_points, difficulty, profile_context, history, context_topic)

        # 3.5 RAG 知识库校验
        validation = await rag_validator.validate(text_answer, knowledge_points)

        result = {
            "question": question,
            "question_type": question_type,
            "knowledge_points": knowledge_points,
            "difficulty": difficulty,
            "answer": text_answer,
            "confidence": validation.confidence,
            "validation": {
                "total_claims": validation.total_claims,
                "supported_claims": validation.supported_claims,
                "unsupported_claims": validation.unsupported_claims,
            },
            "images": [],
            "audio": None,
        }

        # 4. 可选：生成图解
        if "image" in output_modes:
            try:
                image_key = await self.generate_image(text_answer)
                if image_key:
                    result["images"].append(image_key)
            except Exception:
                pass

        # 5. 可选：生成语音
        if "audio" in output_modes:
            try:
                audio_key = await self.generate_audio(text_answer)
                if audio_key:
                    result["audio"] = audio_key
            except Exception:
                pass

        return result

    async def run_stream(self, input_data: dict) -> AsyncGenerator[dict, None]:
        """流式执行：逐步返回文字 + 图解 + 语音"""
        question = input_data.get("question", "")
        context_topic = input_data.get("context_topic", "")
        profile = input_data.get("profile", {})
        output_modes = input_data.get("output_modes", ["text"])
        history = input_data.get("history", [])

        # 1. 分类
        yield sse_event({"type": "agent_status", "agent": "tutor", "status": "classifying"})
        question_type, knowledge_points, difficulty = await self._classify_question(question)

        # 2. 流式生成文字解答
        yield sse_event({"type": "agent_status", "agent": "tutor", "status": "generating_text"})
        profile_context = self._build_profile_context(profile)

        system_prompt = TUTOR_SYSTEM_PROMPT.format(profile_context=profile_context)
        user_content = f"""问题类型：{question_type}
涉及知识点：{', '.join(knowledge_points)}
难度估计：{difficulty}

学生的问题：{question}

请生成辅导回答。"""

        messages = self._build_messages(system_prompt, user_content)
        for h in history[-8:]:
            messages.insert(-1, h)

        full_answer = ""
        async for chunk in self.llm.chat_stream(messages):
            full_answer += chunk
            yield sse_event({"type": "chunk", "content": chunk})

        yield sse_event({"type": "text_done", "content": full_answer})

        # 2.5 RAG 知识库校验
        if full_answer:
            validation = await rag_validator.validate(full_answer, knowledge_points)
            yield sse_event({
                "type": "rag_validation",
                "confidence": validation.confidence,
                "total_claims": validation.total_claims,
                "supported_claims": validation.supported_claims,
                "unsupported_claims": validation.unsupported_claims,
            })

        # 3. 可选：生成图解
        if "image" in output_modes:
            yield sse_event({"type": "agent_status", "agent": "tutor", "status": "generating_image"})
            try:
                image_key = await self.generate_image(full_answer)
                if image_key:
                    yield sse_event({"type": "image_done", "url": f"/api/files/{image_key}"})
            except Exception as e:
                yield sse_event({"type": "image_error", "message": str(e)})

        # 4. 可选：生成语音
        if "audio" in output_modes:
            yield sse_event({"type": "agent_status", "agent": "tutor", "status": "generating_audio"})
            try:
                audio_key = await self.generate_audio(full_answer)
                if audio_key:
                    yield sse_event({"type": "audio_done", "url": f"/api/files/{audio_key}"})
            except Exception as e:
                yield sse_event({"type": "audio_error", "message": str(e)})

        yield sse_event({"type": "done"})

    async def _classify_question(self, question: str) -> tuple:
        """分类问题类型"""
        messages = self._build_messages(QUESTION_CLASSIFY_PROMPT, question)
        response = await self.llm.chat(messages, temperature=0.1, max_tokens=200)

        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            data = json.loads(response[start:end])
            return (
                data.get("type", "concept"),
                data.get("knowledge_points", []),
                data.get("difficulty", "中等"),
            )
        except (json.JSONDecodeError, ValueError):
            return "concept", [], "中等"

    async def _generate_text_answer(
        self, question: str, q_type: str, knowledge_points: list, difficulty: str,
        profile_context: str, history: list, context_topic: str = "",
    ) -> str:
        """生成文字解答"""
        system_prompt = TUTOR_SYSTEM_PROMPT.format(profile_context=profile_context)

        user_content = f"""问题类型：{q_type}
涉及知识点：{', '.join(knowledge_points)}
难度估计：{difficulty}

学生的问题：{question}

请生成辅导回答。"""

        messages = self._build_messages(system_prompt, user_content)
        for h in history[-8:]:
            messages.insert(-1, h)

        return await self.llm.chat(messages, temperature=0.7, max_tokens=4096)

    async def generate_image(self, text_answer: str) -> str | None:
        """从文字解答中提取可视化需求，调用图像生成 API"""
        try:
            extract_prompt = """从以下解答中提取一个适合可视化的关键概念，输出为简短的图像描述（不超过50字），用于 AI 图像生成。
如果内容不适合可视化，返回"无"。

解答：{answer}"""

            messages = self._build_messages("", extract_prompt.format(answer=text_answer[:500]))
            desc = await self.llm.chat(messages)
            desc = desc.strip()

            if not desc or desc == "无":
                return None

            # TODO: 实际调用图像生成 API
            return None

        except Exception:
            return None

    async def generate_audio(self, text_answer: str) -> str | None:
        """调用 TTS API 生成语音"""
        try:
            tts_prompt = """从以下解答中提取核心内容，转换为适合朗读的口语化表达（不超过300字）：

解答：{answer}"""

            messages = self._build_messages("", tts_prompt.format(answer=text_answer[:1000]))
            tts_text = await self.llm.chat(messages)
            tts_text = tts_text.strip()

            if not tts_text:
                return None

            # TODO: 实际调用 TTS API
            return None

        except Exception:
            return None

    def _build_profile_context(self, profile: dict) -> str:
        """构建画像上下文（给 LLM 看的）"""
        if not profile:
            return "暂无学生画像信息，按标准难度和通用方式讲解。"

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
        else:
            visual = cs.get("visual", 0)
            auditory = cs.get("auditory", 0)
            kinesthetic = cs.get("kinesthetic", 0)
            if max(visual, auditory, kinesthetic) > 0.5:
                style_desc = []
                if visual > 0.5:
                    style_desc.append("视觉型")
                if auditory > 0.5:
                    style_desc.append("听觉型")
                if kinesthetic > 0.5:
                    style_desc.append("动觉型")
                parts.append(f"认知风格：{' + '.join(style_desc)}")

        # 学习能力
        la = profile.get("learning_ability", {})
        la_summary = la.get("summary", "")
        if la_summary:
            parts.append(f"学习能力：{la_summary}")
        else:
            speed = la.get("absorption_speed", 0.5)
            depth = la.get("understanding_depth", 0.5)
            parts.append(f"学习能力：吸收速度{'快' if speed > 0.6 else '中' if speed > 0.3 else '慢'}，理解深度{'深' if depth > 0.6 else '中等' if depth > 0.3 else '浅'}")

        # 学习目标
        lg = profile.get("learning_goals", {})
        short = lg.get("short_term", "")
        career = lg.get("career", "")
        if short:
            parts.append(f"短期目标：{short}")
        if career:
            parts.append(f"职业方向：{career}")

        if not parts:
            return "暂无足够画像信息，按标准难度和通用方式讲解。"

        return "\n".join(parts)


# 全局辅导 Agent 实例
tutor_agent = TutorAgent()
