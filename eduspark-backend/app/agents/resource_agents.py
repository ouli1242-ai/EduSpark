"""资源 Agent 群 — 5 种资源生成"""
import json
from app.agents.base import BaseAgent


class DocumentAgent(BaseAgent):
    """文档 Agent：生成课程讲解文档"""

    SYSTEM_PROMPT = """你是一个专业的课程文档生成专家。根据以下信息生成课程讲解文档：

要求：
- 语言风格适合学生认知水平
- 包含概念解释、示例、应用场景
- Markdown 格式输出
- 包含知识点的层次结构（标题、小节）
- 每个概念配 1-2 个具体示例
- 文档末尾附总结和要点回顾"""

    async def run(self, input_data: dict) -> dict:
        topic = input_data["topic"]
        profile = input_data.get("profile", {})
        context = input_data.get("context", "")

        difficulty = profile.get("learning_preferences", {}).get("difficulty_pref", "中等")
        style = profile.get("cognitive_style", {}).get("summary", "视觉型")

        user_content = f"""知识点：{topic}
学生难度偏好：{difficulty}
学生认知风格：{style}
参考资料：{context}

请生成完整的课程讲解文档。"""

        messages = self._build_messages(self.SYSTEM_PROMPT, user_content)
        content = await self.llm.chat(messages)

        return {
            "type": "document",
            "title": f"{topic} 讲解文档",
            "content": content,
            "topic": topic,
        }


class QuizAgent(BaseAgent):
    """题库 Agent：生成练习题目"""

    SYSTEM_PROMPT = """你是一个专业的题目生成专家。根据知识点生成练习题目。

要求：
- 生成 5 道题目，包含以下题型：
  - 2 道选择题（4选1）
  - 1 道填空题
  - 1 道判断题
  - 1 道简答题
- 每道题包含：题目、选项（如有）、正确答案、详细解析
- 难度分为：基础、中等、困难
- 输出 JSON 格式

输出格式：
```json
[
  {
    "type": "choice",
    "difficulty": "基础",
    "question": "...",
    "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
    "answer": "B",
    "explanation": "..."
  }
]
```"""

    async def run(self, input_data: dict) -> dict:
        topic = input_data["topic"]
        profile = input_data.get("profile", {})
        difficulty = profile.get("learning_preferences", {}).get("difficulty_pref", "中等")

        user_content = f"知识点：{topic}\n难度偏好：{difficulty}\n请生成练习题目。"
        messages = self._build_messages(self.SYSTEM_PROMPT, user_content)
        response = await self.llm.chat(messages)

        # 提取 JSON
        questions = []
        try:
            start = response.find("[")
            end = response.rfind("]") + 1
            questions = json.loads(response[start:end])
        except (json.JSONDecodeError, ValueError):
            questions = [{"type": "raw", "content": response}]

        return {
            "type": "quiz",
            "title": f"{topic} 练习题",
            "questions": questions,
            "topic": topic,
        }


class MindMapAgent(BaseAgent):
    """思维导图 Agent：生成知识点结构图"""

    SYSTEM_PROMPT = """你是一个知识结构专家。根据知识点生成思维导图的树形结构。

要求：
- 从核心概念出发，逐层展开
- 3-4 层深度
- 每个节点包含：标题、简要说明
- 输出 JSON 格式的树形结构

输出格式：
```json
{
  "title": "核心概念",
  "description": "简要说明",
  "children": [
    {
      "title": "子概念1",
      "description": "...",
      "children": [...]
    }
  ]
}
```"""

    async def run(self, input_data: dict) -> dict:
        topic = input_data["topic"]
        context = input_data.get("context", "")

        user_content = f"知识点：{topic}\n参考信息：{context}\n请生成思维导图结构。"
        messages = self._build_messages(self.SYSTEM_PROMPT, user_content)
        response = await self.llm.chat(messages)

        # 提取 JSON
        tree = {}
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            tree = json.loads(response[start:end])
        except (json.JSONDecodeError, ValueError):
            tree = {"title": topic, "description": response}

        return {
            "type": "mindmap",
            "title": f"{topic} 思维导图",
            "tree": tree,
            "topic": topic,
        }


class CodeAgent(BaseAgent):
    """代码案例 Agent：生成实操案例"""

    SYSTEM_PROMPT = """你是一个编程教学专家。根据知识点生成代码实操案例。

要求：
- 包含案例背景说明
- 完整可运行的 Python 代码
- 代码中添加详细注释
- 展示运行结果
- 提供扩展思考题
- 代码难度适合学生水平"""

    async def run(self, input_data: dict) -> dict:
        topic = input_data["topic"]
        profile = input_data.get("profile", {})
        difficulty = profile.get("learning_preferences", {}).get("difficulty_pref", "中等")

        user_content = f"知识点：{topic}\n难度偏好：{difficulty}\n请生成代码实操案例。"
        messages = self._build_messages(self.SYSTEM_PROMPT, user_content)
        content = await self.llm.chat(messages)

        return {
            "type": "code",
            "title": f"{topic} 代码案例",
            "content": content,
            "topic": topic,
        }


class VideoScriptAgent(BaseAgent):
    """视频脚本 Agent：生成教学视频脚本"""

    SYSTEM_PROMPT = """你是一个教学视频脚本专家。根据知识点生成教学视频脚本。

要求：
- 视频时长控制在 3-5 分钟
- 包含多个场景（scene），每个场景有：
  - 时间段（timestamp）
  - 旁白文本（narration）
  - 画面描述（visual_description）
- 语言口语化，适合视频讲解
- 输出 JSON 格式

输出格式：
```json
{
  "title": "...",
  "duration": "3-5min",
  "scenes": [
    {
      "timestamp": "0:00-0:30",
      "narration": "...",
      "visual_description": "..."
    }
  ]
}
```"""

    async def run(self, input_data: dict) -> dict:
        topic = input_data["topic"]
        context = input_data.get("context", "")

        user_content = f"知识点：{topic}\n参考信息：{context}\n请生成教学视频脚本。"
        messages = self._build_messages(self.SYSTEM_PROMPT, user_content)
        response = await self.llm.chat(messages)

        # 提取 JSON
        script = {}
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            script = json.loads(response[start:end])
        except (json.JSONDecodeError, ValueError):
            script = {"title": topic, "scenes": [{"narration": response}]}

        return {
            "type": "video",
            "title": f"{topic} 教学视频脚本",
            "script": script,
            "topic": topic,
        }


# 资源 Agent 调度器
RESOURCE_AGENTS = {
    "document": DocumentAgent(),
    "quiz": QuizAgent(),
    "mindmap": MindMapAgent(),
    "code": CodeAgent(),
    "video": VideoScriptAgent(),
}
