"""辅导 Agent — 智能多模态答疑"""
import json
import re
from app.agents.base import BaseAgent

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
    """辅导 Agent：智能答疑 + 多模态讲解"""

    async def run(self, input_data: dict) -> dict:
        """
        input_data:
            - question: 学生问题
            - profile: 学生画像
            - history: 对话历史（可选）
        """
        question = input_data["question"]
        profile = input_data.get("profile", {})
        history = input_data.get("history", [])

        # 1. 分类问题
        question_type, knowledge_points, difficulty = await self._classify_question(question)

        # 2. 构建画像上下文
        profile_context = self._build_profile_context(profile)

        # 3. 生成辅导回答
        system_prompt = TUTOR_SYSTEM_PROMPT.format(profile_context=profile_context)

        user_content = f"""问题类型：{question_type}
涉及知识点：{', '.join(knowledge_points)}
难度估计：{difficulty}

学生的问题：{question}

请生成辅导回答。"""

        messages = self._build_messages(system_prompt, user_content)

        # 插入历史
        for h in history[-8:]:
            messages.insert(-1, h)

        answer = await self.llm.chat(messages, temperature=0.7, max_tokens=4096)

        return {
            "type": "tutor",
            "question": question,
            "question_type": question_type,
            "knowledge_points": knowledge_points,
            "difficulty": difficulty,
            "answer": answer,
        }

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
