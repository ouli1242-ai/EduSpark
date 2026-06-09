"""资源 Agent 群 — 5 种个性化资源生成"""
import json
import re
from app.agents.base import BaseAgent


def _safe_float(value, default=0.0):
    """安全转换数值，兼容字符串类型（如'中等'、'快'等中文描述）"""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        v = float(value)
        if v != v or v == float('inf') or v == float('-inf'):
            return default
        return v
    if isinstance(value, str):
        for kw, score in [("极快", 0.9), ("较快", 0.7), ("快", 0.7), ("一般", 0.5),
                          ("较慢", 0.3), ("慢", 0.3), ("极慢", 0.1),
                          ("强", 0.7), ("较弱", 0.3), ("弱", 0.3), ("极强", 0.9),
                          ("中等", 0.5), ("深", 0.7), ("浅", 0.3), ("中", 0.5)]:
            if kw in value:
                return score
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    return default


def _build_profile_context(profile: dict) -> str:
    """构建画像上下文（所有资源Agent共用）"""
    if not profile or not any(profile.get(k) for k in profile):
        return "学生画像：暂无信息，按标准难度生成。"

    parts = []

    # 知识基础
    kb = profile.get("knowledge_base", {})
    if kb:
        mastered = kb.get("mastered", [])
        weak = kb.get("weak", [])
        blind = kb.get("blind_spots", [])
        kb_lines = []
        if mastered:
            kb_lines.append(f"已掌握：{', '.join(mastered[:5])}")
        if weak:
            kb_lines.append(f"薄弱点：{', '.join(weak[:5])}")
        if blind:
            kb_lines.append(f"知识盲区：{', '.join(blind[:5])}")
        if kb.get("score") is not None:
            kb_lines.append(f"综合评分：{kb['score']}")
        if kb_lines:
            parts.append("【知识基础】\n" + "\n".join(kb_lines))

    # 认知风格
    cs = profile.get("cognitive_style", {})
    if cs:
        visual = _safe_float(cs.get("visual", 0))
        auditory = _safe_float(cs.get("auditory", 0))
        kinesthetic = _safe_float(cs.get("kinesthetic", 0))
        summary = cs.get("summary", "")
        style_hints = []
        if visual >= 0.5:
            style_hints.append(f"视觉型({visual}) — 偏好图表、文字、视频演示")
        if auditory >= 0.5:
            style_hints.append(f"听觉型({auditory}) — 偏好讲解、讨论、音频")
        if kinesthetic >= 0.5:
            style_hints.append(f"动觉型({kinesthetic}) — 偏好动手实操、代码练习")
        if summary:
            style_hints.append(f"描述：{summary}")
        if style_hints:
            parts.append("【认知风格】\n" + "\n".join(style_hints))

    # 学习能力
    la = profile.get("learning_ability", {})
    if la:
        speed = _safe_float(la.get("absorption_speed"), 0.5)
        depth = _safe_float(la.get("understanding_depth"), 0.5)
        transfer = _safe_float(la.get("transfer_ability"), 0.5)
        la_summary = la.get("summary", "")
        ability_desc = f"吸收速度：{'快' if speed > 0.6 else '中' if speed > 0.3 else '慢'}({speed})，理解深度：{'深' if depth > 0.6 else '中等' if depth > 0.3 else '浅'}({depth})，迁移能力：{'强' if transfer > 0.6 else '中' if transfer > 0.3 else '弱'}({transfer})"
        if la_summary:
            ability_desc += f"\n描述：{la_summary}"
        parts.append(f"【学习能力】\n{ability_desc}")

    # 学习目标
    lg = profile.get("learning_goals", {})
    if lg:
        short = lg.get("short_term", "")
        long_t = lg.get("long_term", "")
        career = lg.get("career", "")
        goal_lines = []
        if short:
            goal_lines.append(f"短期目标：{short}")
        if long_t:
            goal_lines.append(f"长期目标：{long_t}")
        if career:
            goal_lines.append(f"职业方向：{career}")
        if goal_lines:
            parts.append("【学习目标】\n" + "\n".join(goal_lines))

    # 学习偏好
    lp = profile.get("learning_preferences", {})
    if lp:
        pref_lines = []
        if lp.get("difficulty_pref"):
            pref_lines.append(f"难度偏好：{lp['difficulty_pref']}")
        if lp.get("resource_types"):
            pref_lines.append(f"资源偏好：{', '.join(lp['resource_types'])}")
        if lp.get("time_pref"):
            pref_lines.append(f"时段偏好：{lp['time_pref']}")
        if pref_lines:
            parts.append("【学习偏好】\n" + "\n".join(pref_lines))

    # 易错点
    ep = profile.get("error_patterns", {})
    if ep:
        types = ep.get("types", [])
        causes = ep.get("root_causes", [])
        if types or causes:
            ep_lines = []
            if types:
                ep_lines.append(f"常见错误：{', '.join(types)}")
            if causes:
                ep_lines.append(f"根本原因：{', '.join(causes)}")
            parts.append("【易错点】\n" + "\n".join(ep_lines))

    if not parts:
        return "学生画像：信息不足，按标准难度生成。"

    return "\n\n".join(parts)


def _safe_json_parse(response: str, expect_array: bool = False):
    """安全解析 JSON，支持 ```json 代码块"""
    # 移除代码块标记
    cleaned = re.sub(r'```json\s*', '', response)
    cleaned = re.sub(r'```\s*$', '', cleaned)
    cleaned = cleaned.strip()

    if expect_array:
        start = cleaned.find("[")
        end = cleaned.rfind("]") + 1
    else:
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1

    if start >= 0 and end > start:
        try:
            return json.loads(cleaned[start:end])
        except (json.JSONDecodeError, ValueError):
            pass

    return None


class DocumentAgent(BaseAgent):
    """文档 Agent：生成个性化课程讲解文档"""

    SYSTEM_PROMPT = """你是一位资深高等教育课程设计专家。你需要根据学生的画像信息，生成量身定制的课程讲解文档。

## 生成要求

### 结构要求
1. **引言**（200字内）：用一个引人入胜的问题或场景引出主题，激发学习兴趣
2. **核心概念**：清晰的定义，配合直观的类比/比喻
3. **分节讲解**（3-5节）：每节一个子知识点
   - 概念阐述 → 公式（如有）→ 具体示例 → 要点小结
4. **综合示例**：一个贯穿多个子知识点的综合例子
5. **应用场景**：结合实际应用说明这个知识有什么用
6. **总结与要点回顾**：3-5个关键要点

### 个性化适配
- 根据学生的认知风格选择表达方式
  - 视觉型：多用图表描述、层次分明的标题、对比表格
  - 听觉型：多用对话式表达、设问-解答模式
  - 动觉型：多给动手实验的指引、交互式思考题
- 根据学习能力调整深度
  - 能力强：深入原理和推导，提供延伸阅读方向
  - 能力中等：标准讲解 + 练习巩固
  - 能力弱：从基础概念讲起，多给类比和具体例子
- 针对学生的薄弱知识点，在相关部分做重点强化
- 如果学生的知识盲区涉及当前主题，主动补充前置知识

### 格式要求
- 使用 Markdown 格式
- 层次分明（## → ### → ####）
- 代码块标注语言类型
- 重要概念用 **加粗**
- 公式用 $$ 或 $ 包裹（LaTeX 格式）"""

    async def run(self, input_data: dict) -> dict:
        topic = input_data["topic"]
        profile = input_data.get("profile", {})
        context = input_data.get("context", "")

        profile_context = _build_profile_context(profile)
        difficulty = profile.get("learning_preferences", {}).get("difficulty_pref", "中等")

        user_content = f"""## 生成任务
知识点：{topic}
难度级别：{difficulty}
补充资料：{context if context else '无'}

## 学生画像
{profile_context}

请根据以上信息生成个性化课程讲解文档。"""

        messages = self._build_messages(self.SYSTEM_PROMPT, user_content)
        content = await self.llm.chat(messages, temperature=0.7, max_tokens=4096)

        return {
            "type": "document",
            "title": f"{topic} 讲解文档",
            "content": content,
            "topic": topic,
        }


class QuizAgent(BaseAgent):
    """题库 Agent：生成个性化练习题"""

    SYSTEM_PROMPT = """你是一位资深教育测评专家。根据知识点和学生画像生成针对性练习题。

## 题目要求

### 题型与数量（共5道）
1. **选择题 × 2**（4个选项）：考察概念辨析和理解
2. **填空题 × 1**：考察关键词或关键步骤记忆
3. **判断题 × 1**：考察常见误区识别
4. **简答题 × 1**：考察综合理解和表达能力

### 难度分配
- 基础题 × 2：知识点直接应用，用于建立信心
- 中等题 × 2：知识点综合应用，需要一定思考
- 困难题 × 1：知识点迁移应用，考察深度理解

### 个性化策略
- 针对学生的薄弱知识点，多出相关练习
- 对学生的知识盲区，出基础题帮助发现盲点
- 如果学生偏好代码实操，简答题改为编程题
- 如果学生是动觉型，增加实操导向的题目
- 每道题的错误选项要对应学生常见的错误类型（如果画像中有）

### 输出格式
严格输出 JSON 数组，不要有额外文字：
```json
[
  {
    "type": "choice",
    "difficulty": "基础",
    "question": "题目内容",
    "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"],
    "answer": "B",
    "explanation": "详细解析，说明为什么选B和其他选项错在哪",
    "knowledge_point": "考察的知识点名称"
  }
]
```"""

    async def run(self, input_data: dict) -> dict:
        topic = input_data["topic"]
        profile = input_data.get("profile", {})
        profile_context = _build_profile_context(profile)
        difficulty = profile.get("learning_preferences", {}).get("difficulty_pref", "中等")

        user_content = f"""知识点：{topic}
目标难度：{difficulty}

{profile_context}

请生成5道个性化练习题。"""

        messages = self._build_messages(self.SYSTEM_PROMPT, user_content)
        response = await self.llm.chat(messages, temperature=0.7, max_tokens=4096)

        questions = _safe_json_parse(response, expect_array=True)
        if not questions:
            questions = [{"type": "raw", "content": response}]

        return {
            "type": "quiz",
            "title": f"{topic} 练习题",
            "questions": questions,
            "topic": topic,
        }


class MindMapAgent(BaseAgent):
    """思维导图 Agent：生成知识结构图"""

    SYSTEM_PROMPT = """你是一位知识体系架构专家。根据知识点生成层次化的思维导图。

## 生成要求

### 结构层次
- **根节点**：核心概念（一句话概括）
- **第1层**（3-6个节点）：主要分支/子概念
- **第2层**（每节点2-4个子节点）：每个分支的具体要点
- **第3层**（可选）：关键细节、公式、示例

### 内容质量
- 每个节点包含 title（标题）和 description（1-2句说明）
- 覆盖：定义、原理、方法、应用、注意事项
- 节点之间的逻辑关系要清晰
- 针对学生薄弱点，在相关节点加 ⚠️ 标记提醒重点关注

### 个性化适配
- 根据学生能力水平调整深度
  - 能力强：更深层次，包含延伸知识
  - 能力弱：聚焦核心，减少分支
- 如果学生是视觉型，增加对比/分类维度的分支
- 结合学生的职业目标，在应用层节点加入相关方向

### 输出格式
严格输出 JSON，不要有额外文字：
```json
{
  "title": "核心概念名称",
  "description": "一句话概括这个概念",
  "children": [
    {
      "title": "分支1",
      "description": "这个分支的简要说明",
      "children": [
        {"title": "要点1.1", "description": "具体说明"},
        {"title": "要点1.2", "description": "具体说明"}
      ]
    }
  ]
}
```"""

    async def run(self, input_data: dict) -> dict:
        topic = input_data["topic"]
        profile = input_data.get("profile", {})
        context = input_data.get("context", "")
        profile_context = _build_profile_context(profile)

        user_content = f"""知识点：{topic}
参考信息：{context if context else '无'}

{profile_context}

请生成个性化思维导图。"""

        messages = self._build_messages(self.SYSTEM_PROMPT, user_content)
        response = await self.llm.chat(messages, temperature=0.7, max_tokens=4096)

        tree = _safe_json_parse(response, expect_array=False)
        if not tree:
            tree = {"title": topic, "description": response[:200]}

        return {
            "type": "mindmap",
            "title": f"{topic} 思维导图",
            "tree": tree,
            "topic": topic,
        }


class CodeAgent(BaseAgent):
    """代码案例 Agent：生成实操代码案例"""

    SYSTEM_PROMPT = """你是一位资深编程教育专家。根据知识点和学生画像生成代码实操案例。

## 生成要求

### 案例结构
1. **背景说明**（100字内）：这个案例要解决什么问题
2. **核心思路**（3-5步）：用文字描述算法/实现思路
3. **完整代码**：Python 代码，带详细中文注释
4. **运行结果**：展示预期输出
5. **关键点解析**（3-5点）：解释代码中的关键部分
6. **扩展思考**：1-2个变式问题，引导学生深入

### 代码质量
- 代码可运行，语法正确
- 变量命名清晰有意义
- 注释用中文，关键步骤必须注释
- 包含必要的 import 语句
- 展示完整的运行示例

### 个性化适配
- 根据学生能力水平调整代码复杂度
  - 能力强：更多高级语法（lambda，推导式，装饰器），更少注释
  - 能力弱：逐行注释，避免复杂语法，增加中间输出
- 如果学生偏好项目实战，设计一个完整的小项目
- 如果学生有特定薄弱点（如"数据处理"），在案例中重点练习
- 动觉型学生：多给"试试修改这个参数"之类的交互指令

### 格式要求
- Markdown 格式
- 代码用 ```python ... ``` 包裹
- 输出用 ``` ... ``` 或直接文字描述"""

    async def run(self, input_data: dict) -> dict:
        topic = input_data["topic"]
        profile = input_data.get("profile", {})
        profile_context = _build_profile_context(profile)
        ability = profile.get("learning_ability", {})
        ability_level = "中等"
        if ability:
            avg = (ability.get("absorption_speed", 0.5) + ability.get("understanding_depth", 0.5)) / 2
            if avg > 0.65:
                ability_level = "较强"
            elif avg < 0.35:
                ability_level = "较弱"

        user_content = f"""知识点：{topic}
学生编程能力：{ability_level}

{profile_context}

请生成个性化代码实操案例。"""

        messages = self._build_messages(self.SYSTEM_PROMPT, user_content)
        content = await self.llm.chat(messages, temperature=0.7, max_tokens=4096)

        return {
            "type": "code",
            "title": f"{topic} 代码案例",
            "content": content,
            "topic": topic,
        }


class VideoScriptAgent(BaseAgent):
    """视频脚本 Agent：生成教学视频脚本"""

    SYSTEM_PROMPT = """你是一位教学视频制作专家。根据知识点和学生画像生成视频脚本。

## 脚本要求

### 视频结构（总时长 3-5 分钟）
1. **开场钩子**（15-20秒）：一个问题/场景/现象，吸引注意力
2. **核心讲解**（2-3分钟）：分2-3个要点逐步讲解
3. **演示/示例**（30-60秒）：展示一个具体例子
4. **总结回顾**（15-20秒）：复述关键要点
5. **课后思考**（10秒）：留一个思考题

### 场景设计（5-8个场景）
每个场景包含：
- timestamp：时间段
- narration：旁白文本（口语化，自然流畅）
- visual_description：画面描述（用于后续视频生成）
- on_screen_text：屏幕上显示的文字（关键词/公式）

### 个性化适配
- 视觉型学生：画面描述要丰富，多用动画/图表/对比
- 听觉型学生：旁白更详细，多用对话式和设问
- 动觉型学生：在画面中展示操作步骤，鼓励跟着做
- 根据学生能力调整讲解速度
  - 能力强：节奏快，信息密度高
  - 能力弱：慢节奏，多重复关键点
- 针对学生薄弱点，在相关场景暂停做重点讲解

### 输出格式
严格输出 JSON：
```json
{
  "title": "视频标题（吸引人）",
  "duration": "4min",
  "target_audience": "描述目标学生水平",
  "learning_objectives": ["目标1", "目标2"],
  "scenes": [
    {
      "scene_number": 1,
      "timestamp": "0:00-0:20",
      "scene_type": "开场",
      "narration": "旁白文本（第一人称，口语化）",
      "visual_description": "描述画面内容，用于视频生成",
      "on_screen_text": "屏幕上显示的文字"
    }
  ]
}
```"""

    async def run(self, input_data: dict) -> dict:
        topic = input_data["topic"]
        profile = input_data.get("profile", {})
        context = input_data.get("context", "")
        profile_context = _build_profile_context(profile)

        user_content = f"""知识点：{topic}
补充信息：{context if context else '无'}

{profile_context}

请生成个性化教学视频脚本。"""

        messages = self._build_messages(self.SYSTEM_PROMPT, user_content)
        response = await self.llm.chat(messages, temperature=0.7, max_tokens=4096)

        script = _safe_json_parse(response, expect_array=False)
        if not script:
            script = {
                "title": f"{topic} 教学视频",
                "duration": "3-5min",
                "scenes": [{"scene_number": 1, "timestamp": "0:00", "narration": response[:500]}],
            }

        return {
            "type": "video",
            "title": f"{topic} 教学视频脚本",
            "script": script,
            "topic": topic,
        }


# 资源 Agent 注册表
RESOURCE_AGENTS = {
    "document": DocumentAgent(),
    "quiz": QuizAgent(),
    "mindmap": MindMapAgent(),
    "code": CodeAgent(),
    "video": VideoScriptAgent(),
}
