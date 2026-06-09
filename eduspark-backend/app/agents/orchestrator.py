"""多智能体编排器 — 协调各 Agent 工作"""
import asyncio
import json
import uuid
from typing import AsyncGenerator
from sqlalchemy.orm import Session

from app.models.profile import StudentProfile
from app.models.resource import Resource, ResourceType, ResourceStatus
from app.models.learning_path import LearningPath
from app.models.learning_record import LearningRecord
from app.models.chat_history import ChatHistory
from app.agents.profile_agent import ProfileAgent
from app.agents.resource_agents import RESOURCE_AGENTS
from app.agents.path_agent import PathAgent
from app.agents.tutor_agent import TutorAgent
from app.agents.evaluation_agent import EvaluationAgent
from app.services.llm import deepseek_llm
from app.utils.sse import sse_event


class Orchestrator:
    """多智能体编排器"""

    def __init__(self):
        self.profile_agent = ProfileAgent()
        self.path_agent = PathAgent()
        self.tutor_agent = TutorAgent()
        self.evaluation_agent = EvaluationAgent()
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
        elif intent == "tutor":
            async for event in self._handle_tutor(message, history_messages, current_profile, user_id, session_id, db):
                yield event
        elif intent == "evaluation":
            async for event in self._handle_evaluation(message, current_profile, user_id, session_id, db):
                yield event
        else:
            # 通用对话 → 画像提取
            async for event in self._handle_profile(message, history_messages, current_profile, user_id, session_id, db):
                yield event

    async def _classify_intent(self, message: str) -> str:
        """用 LLM 判断用户意图（含关键词预筛选兜底）"""
        # 关键词预筛选，避免 LLM 误分类
        msg_lower = message.lower()
        # 路径规划类关键词 → 直接走 path
        path_keywords = ["规划学习路线", "学习路线", "学习计划", "学习路径", "学习顺序", "规划路线", "帮我规划", "路线规划"]
        if any(kw in message for kw in path_keywords):
            return "path"
        # 资源生成类关键词 → 直接走 resource
        resource_keywords = ["生成", "文档", "思维导图", "视频脚本", "出题", "制作", "帮我写"]
        if any(kw in message for kw in resource_keywords):
            return "resource"

        messages = [
            {"role": "system", "content": """你是一个意图分类器。判断用户消息的意图，只返回一个单词。

分类规则（优先级从高到低）：
- resource: 明确要求生成/创建/制作学习资源。关键词：生成、文档、题目、练习、思维导图、代码、视频脚本、帮我写、制作、出题
- path: 要求规划学习路线/学习计划/学习顺序
- evaluation: 要求评估/查看学习进度/学习报告/学习总结
- tutor: 问具体学科知识/概念/公式/代码实现/怎么做/为什么/怎么理解。这是最常见的类型
- profile: 自我介绍/打招呼/闲聊/设置偏好/其他不明确的消息

关键区分示例：
"什么是梯度下降" → tutor
"帮我写一份决策树的文档" → resource
"帮我规划学习路线" → path
"我的学习情况怎么样" → evaluation
"你好" → profile

只返回一个单词，不要解释。""",
            },
            {"role": "user", "content": message},
        ]
        intent = await deepseek_llm.chat(messages, temperature=0.1, max_tokens=20)
        intent = intent.strip().lower()
        if intent not in ("profile", "resource", "path", "tutor", "evaluation"):
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
        try:
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
            generated_count = 0
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

                    generated_count += 1
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
                    print(f"[Orchestrator] Resource {rtype} error: {e}")
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
                content=f"已为「{topic}」生成 {generated_count}/{total} 种学习资源。",
                agent_type="resource",
            ))
            db.commit()

            yield sse_event({"type": "agent_status", "agent": "orchestrator", "status": "done"})

        except Exception as e:
            error_msg = f"资源生成失败：{str(e)}"
            print(f"[Orchestrator] Resource error: {e}")
            yield sse_event({"type": "chunk", "content": f"\n\n{error_msg}，请稍后重试。"})
            yield sse_event({"type": "agent_status", "agent": "orchestrator", "status": "failed", "error": str(e)})
            # 即使失败也保存对话记录
            db.add(ChatHistory(user_id=user_id, session_id=session_id, role="user", content=message))
            db.add(ChatHistory(
                user_id=user_id, session_id=session_id, role="assistant",
                content=error_msg, agent_type="resource",
            ))
            db.commit()

        yield sse_event({"type": "done", "session_id": session_id})

    async def _handle_path(
        self, message, current_profile, user_id, session_id, db
    ) -> AsyncGenerator[str, None]:
        """路径规划流程"""
        yield sse_event({"type": "agent_status", "agent": "path", "status": "running"})

        try:
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

        except Exception as e:
            error_msg = f"路径规划失败：{str(e)}"
            print(f"[Orchestrator] Path error: {e}")
            yield sse_event({"type": "chunk", "content": f"\n\n{error_msg}，请稍后重试。"})
            yield sse_event({"type": "agent_status", "agent": "path", "status": "failed", "error": str(e)})
            # 即使失败也保存对话记录
            db.add(ChatHistory(user_id=user_id, session_id=session_id, role="user", content=message))
            db.add(ChatHistory(
                user_id=user_id, session_id=session_id, role="assistant",
                content=error_msg, agent_type="path",
            ))
            db.commit()

        yield sse_event({"type": "done", "session_id": session_id})

    async def _handle_tutor(
        self, message, history, current_profile, user_id, session_id, db
    ) -> AsyncGenerator[str, None]:
        """辅导答疑流程"""
        yield sse_event({"type": "agent_status", "agent": "tutor", "status": "running"})

        result = await self.tutor_agent.run({
            "question": message,
            "profile": current_profile,
            "history": history,
        })

        # 流式返回答案（模拟逐句输出）
        answer = result["answer"]
        chunk_size = 30
        for i in range(0, len(answer), chunk_size):
            yield sse_event({
                "type": "chunk",
                "content": answer[i:i + chunk_size],
            })

        # 推送问题分类信息
        yield sse_event({
            "type": "tutor_analysis",
            "question_type": result["question_type"],
            "knowledge_points": result["knowledge_points"],
            "difficulty": result["difficulty"],
        })

        # 推送 RAG 校验结果
        if result.get("validation"):
            yield sse_event({
                "type": "rag_validation",
                "confidence": result["confidence"],
                "data": result["validation"],
            })

        # 保存对话
        db.add(ChatHistory(user_id=user_id, session_id=session_id, role="user", content=message))
        db.add(ChatHistory(
            user_id=user_id, session_id=session_id, role="assistant",
            content=answer, agent_type="tutor",
        ))
        db.add(LearningRecord(
            user_id=user_id,
            action="chat",
            knowledge_point=result["knowledge_points"][0] if result["knowledge_points"] else "",
            detail={"question_type": result["question_type"], "difficulty": result["difficulty"]},
        ))
        db.commit()

        yield sse_event({"type": "agent_status", "agent": "tutor", "status": "done"})
        yield sse_event({"type": "done", "session_id": session_id})

    async def _handle_evaluation(
        self, message, current_profile, user_id, session_id, db
    ) -> AsyncGenerator[str, None]:
        """学习评估流程"""
        yield sse_event({"type": "agent_status", "agent": "evaluation", "status": "running", "message": "正在分析学习数据..."})

        result = await self.evaluation_agent.run({
            "user_id": user_id,
            "period": "30d",
            "db": db,
            "profile": current_profile,
        })

        report = result["report"]

        # 推送评估报告
        yield sse_event({
            "type": "evaluation_report",
            "data": report,
        })

        # 生成一段总结文字
        strengths_lines = []
        for s in report.get('strengths', [])[:3]:
            area = s.get('area', '')
            desc = s.get('description', '')
            strengths_lines.append(f'- {area}: {desc}')
        weaknesses_lines = []
        for w in report.get('weaknesses', [])[:3]:
            area = w.get('area', '')
            desc = w.get('description', '')
            weaknesses_lines.append(f'- {area}: {desc}')
        rec_lines = []
        for r in report.get('recommendations', [])[:3]:
            rec_lines.append(f'- {r.get("content", "")}')

        summary = report.get('summary', {})
        summary_text = f"""## 学习评估报告

**综合评分**：{summary.get('overall_score', 'N/A')} 分
**成长趋势**：{summary.get('growth_trend', 'N/A')}

### 优势方面
{chr(10).join(strengths_lines) if strengths_lines else '- 暂无数据'}

### 需要加强
{chr(10).join(weaknesses_lines) if weaknesses_lines else '- 暂无数据'}

### 学习建议
{chr(10).join(rec_lines) if rec_lines else '- 暂无数据'}
"""

        for i in range(0, len(summary_text), 40):
            yield sse_event({"type": "chunk", "content": summary_text[i:i + 40]})

        # 保存对话
        db.add(ChatHistory(user_id=user_id, session_id=session_id, role="user", content=message))
        db.add(ChatHistory(
            user_id=user_id, session_id=session_id, role="assistant",
            content=summary_text, agent_type="evaluation",
        ))
        db.commit()

        yield sse_event({"type": "agent_status", "agent": "evaluation", "status": "done"})
        yield sse_event({"type": "done", "session_id": session_id})

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
