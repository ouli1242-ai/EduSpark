"""多智能体编排器 — 协调各 Agent 工作"""
import asyncio
import json
import uuid
from typing import AsyncGenerator
from sqlalchemy.orm import Session

from app.models.profile import StudentProfile
from app.models.resource import Resource, ResourceType, ResourceStatus
from app.models.learning_path import LearningPath
from app.models.chat_history import ChatHistory
from app.agents.profile_agent import ProfileAgent
from app.agents.resource_agents import RESOURCE_AGENTS
from app.agents.path_agent import PathAgent
from app.services.llm import deepseek_llm
from app.utils.sse import sse_event


class Orchestrator:
    """多智能体编排器"""

    def __init__(self):
        self.profile_agent = ProfileAgent()
        self.path_agent = PathAgent()
        self.resource_agents = RESOURCE_AGENTS

    async def handle_chat(
        self,
        message: str,
        session_id: str,
        user_id: int,
        db: Session,
    ) -> AsyncGenerator[str, None]:
        """处理用户对话：画像提取 → 资源生成 → 路径规划"""

        # 1. 获取历史对话和当前画像
        history = (
            db.query(ChatHistory)
            .filter(ChatHistory.user_id == user_id, ChatHistory.session_id == session_id)
            .order_by(ChatHistory.id.desc())
            .limit(20)
            .all()
        )
        history.reverse()
        history_messages = [{"role": h.role, "content": h.content} for h in history]

        profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
        current_profile = {}
        if profile:
            current_profile = {
                "knowledge_base": profile.knowledge_base,
                "cognitive_style": profile.cognitive_style,
                "learning_ability": profile.learning_ability,
                "error_patterns": profile.error_patterns,
                "learning_goals": profile.learning_goals,
                "learning_preferences": profile.learning_preferences,
            }

        # 2. 判断用户意图
        intent = await self._classify_intent(message)

        # 3. 根据意图调度不同 Agent
        if intent == "profile":
            async for event in self._handle_profile(message, history_messages, current_profile, user_id, session_id, db):
                yield event
        elif intent == "resource":
            async for event in self._handle_resource(message, current_profile, user_id, session_id, db):
                yield event
        elif intent == "path":
            async for event in self._handle_path(message, current_profile, user_id, session_id, db):
                yield event
        else:
            # 通用对话 → 画像提取
            async for event in self._handle_profile(message, history_messages, current_profile, user_id, session_id, db):
                yield event

    async def _classify_intent(self, message: str) -> str:
        """用 LLM 判断用户意图"""
        messages = [
            {"role": "system", "content": "你是一个意图分类器。判断用户消息的意图，只返回一个单词。\n\n"
             "- resource: 用户要求生成、创建、制作、写、出题等任何学习资源。包含'生成''文档''题目''练习''思维导图''代码''视频脚本''帮我写''制作'等词时属于此类\n"
             "- path: 用户要求规划学习路线、制定学习计划\n"
             "- profile: 其他所有情况（自我介绍、提问、闲聊、问知识、打招呼、问概念等）\n\n"
             "示例：\n"
             "用户：'帮我生成决策树的讲解文档' → resource\n"
             "用户：'什么是梯度下降' → profile\n"
             "用户：'你好' → profile\n"
             "用户：'给我出几道线性回归的题目' → resource\n"
             "用户：'帮我规划机器学习的学习路线' → path\n\n"
             "只返回一个单词，不要加标点。"},
            {"role": "user", "content": message},
        ]
        intent = await deepseek_llm.chat(messages, temperature=0.1, max_tokens=20)
        intent = intent.strip().lower()
        if intent not in ("profile", "resource", "path"):
            return "profile"
        return intent

    async def _handle_profile(
        self, message, history, current_profile, user_id, session_id, db
    ) -> AsyncGenerator[str, None]:
        """画像处理流程"""
        yield sse_event({"type": "agent_status", "agent": "profile", "status": "running"})

        result = await self.profile_agent.run({
            "message": message,
            "history": history,
            "current_profile": current_profile,
        })

        # 更新画像
        if result["profile_update"]:
            profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
            if not profile:
                profile = StudentProfile(user_id=user_id)
                db.add(profile)

            update = result["profile_update"]
            for key in ["knowledge_base", "cognitive_style", "learning_ability",
                        "error_patterns", "learning_goals", "learning_preferences"]:
                if key in update and update[key]:
                    setattr(profile, key, update[key])

            profile.conversation_turns = (profile.conversation_turns or 0) + 1
            db.commit()

            yield sse_event({"type": "profile_updated", "data": result["profile_update"]})

        # 返回对话内容
        yield sse_event({"type": "chunk", "content": result["reply"]})

        # 保存对话
        db.add(ChatHistory(user_id=user_id, session_id=session_id, role="user", content=message))
        db.add(ChatHistory(user_id=user_id, session_id=session_id, role="assistant", content=result["reply"], agent_type="profile"))
        db.commit()

        yield sse_event({"type": "agent_status", "agent": "profile", "status": "done"})
        yield sse_event({"type": "done", "session_id": session_id})

    async def _handle_resource(
        self, message, current_profile, user_id, session_id, db
    ) -> AsyncGenerator[str, None]:
        """资源生成流程"""
        # 从消息中提取知识点
        topic = await self._extract_topic(message)

        yield sse_event({"type": "agent_status", "agent": "orchestrator", "status": "running", "message": f"正在为「{topic}」生成学习资源..."})

        # 确定要生成的资源类型
        resource_types = self._determine_resource_types(message)
        total = len(resource_types)

        # 并发生成资源
        tasks = {}
        for i, rtype in enumerate(resource_types):
            agent = self.resource_agents.get(rtype)
            if agent:
                yield sse_event({
                    "type": "agent_status",
                    "agent": rtype,
                    "status": "running",
                    "progress": 0,
                    "order": i + 1,
                    "total": total,
                })
                tasks[rtype] = asyncio.create_task(agent.run({
                    "topic": topic,
                    "profile": current_profile,
                    "context": message,
                }))

        # 收集结果
        for rtype, task in tasks.items():
            try:
                result = await task
                # 存入数据库
                resource = Resource(
                    user_id=user_id,
                    type=ResourceType(rtype),
                    status=ResourceStatus.COMPLETED,
                    title=result.get("title", f"{topic}"),
                    content=json.dumps(result, ensure_ascii=False) if not isinstance(result.get("content"), str) else result.get("content", ""),
                    knowledge_points=[topic],
                )
                db.add(resource)
                db.commit()

                yield sse_event({
                    "type": "resource_generated",
                    "resource_type": rtype,
                    "resource_id": resource.id,
                    "data": result,
                })
                yield sse_event({
                    "type": "agent_status",
                    "agent": rtype,
                    "status": "done",
                    "progress": 100,
                })
            except Exception as e:
                yield sse_event({
                    "type": "agent_status",
                    "agent": rtype,
                    "status": "failed",
                    "error": str(e),
                })

        # 保存对话记录
        db.add(ChatHistory(user_id=user_id, session_id=session_id, role="user", content=message))
        db.add(ChatHistory(
            user_id=user_id, session_id=session_id, role="assistant",
            content=f"已为「{topic}」生成 {total} 种学习资源。",
            agent_type="resource",
        ))
        db.commit()

        yield sse_event({"type": "done", "session_id": session_id})

    async def _handle_path(
        self, message, current_profile, user_id, session_id, db
    ) -> AsyncGenerator[str, None]:
        """路径规划流程"""
        yield sse_event({"type": "agent_status", "agent": "path", "status": "running"})

        # 获取已有资源
        resources = db.query(Resource).filter(Resource.user_id == user_id).limit(20).all()
        resource_list = [
            {"id": r.id, "type": r.type.value, "title": r.title}
            for r in resources
        ]

        result = await self.path_agent.run({
            "course": "机器学习",
            "profile": current_profile,
            "resources": resource_list,
            "request": message,
        })

        # 存入数据库
        path_data = result["path"]
        learning_path = LearningPath(
            user_id=user_id,
            name=path_data.get("name", "学习路径"),
            course=path_data.get("course", "机器学习"),
            steps=path_data.get("steps", []),
        )
        db.add(learning_path)
        db.commit()

        # 保存对话
        db.add(ChatHistory(user_id=user_id, session_id=session_id, role="user", content=message))
        db.add(ChatHistory(
            user_id=user_id, session_id=session_id, role="assistant",
            content=f"已生成学习路径「{path_data.get('name', '')}」，共 {len(path_data.get('steps', []))} 个步骤。",
            agent_type="path",
        ))
        db.commit()

        yield sse_event({"type": "path_generated", "data": path_data})
        yield sse_event({"type": "agent_status", "agent": "path", "status": "done"})
        yield sse_event({"type": "done", "session_id": path_data.get("name", "")})

    async def _extract_topic(self, message: str) -> str:
        """从消息中提取知识点"""
        messages = [
            {"role": "system", "content": "从用户消息中提取核心知识点或主题，只返回知识点名称，不超过10个字。"},
            {"role": "user", "content": message},
        ]
        topic = await deepseek_llm.chat(messages)
        return topic.strip()[:20]

    def _determine_resource_types(self, message: str) -> list[str]:
        """根据消息确定要生成的资源类型"""
        type_keywords = {
            "document": ["文档", "讲解", "说明", "教程"],
            "quiz": ["题目", "练习", "测试", "考"],
            "mindmap": ["思维导图", "结构", "框架", "脉络"],
            "code": ["代码", "案例", "编程", "实现", "实操"],
            "video": ["视频", "动画", "演示"],
        }

        matched = []
        for rtype, keywords in type_keywords.items():
            if any(kw in message for kw in keywords):
                matched.append(rtype)

        # 默认生成全部 5 种
        if not matched:
            matched = ["document", "quiz", "mindmap", "code", "video"]

        return matched


# 全局编排器实例
orchestrator = Orchestrator()
