# Task 6：资源生成Agent群（10天）

> Orchestrator 调度器设计、5个资源Agent实现、RAG内容校验

---

## 6.1 Orchestrator 调度器设计

- [x] 设计 Orchestrator：
  - [x] 接收资源生成请求
  - [x] 意图分类（5种：profile/tutor/resource/path/evaluation）
  - [x] 分发任务到各Agent
  - [x] 汇总生成结果（SSE event 推送）

- [x] 异步并发：
  - [x] asyncio.create_task 并发生成
  - [x] 并发控制
  - [x] 异常捕获（try/except + SSE 错误推送）

- [x] 进度追踪：
  - [x] agent_status 事件实时推送（running/progress/done/failed）
  - [x] 总体进度计算

## 6.2 文档生成Agent

- [x] 6段式文档结构：引言→概念→分节→示例→应用→总结
- [x] 6维度画像适配（_build_profile_context）
- [x] 认知风格适配（视觉型/听觉型/动觉型差异化）
- [x] 调用 DeepSeek API + _safe_json_parse

## 6.3 题库生成Agent

- [x] 5道混合题型（选择题/填空题/简答题/编程题）
- [x] 难度梯度：2基础 + 2中等 + 1困难
- [x] 错因针对性干扰项
- [x] 答案+解析生成

## 6.4 思维导图生成Agent

- [x] 3-4层知识树
- [x] 画像驱动深度控制
- [x] 薄弱点标记提醒 ⚠️
- [x] JSON 树形结构输出

## 6.5 案例生成Agent

- [x] 6段式案例：背景→思路→代码→结果→解析→扩展
- [x] 能力适配（基础/中等/困难）
- [x] 代码格式化 + 注释

## 6.6 视频脚本Agent

- [x] 5-8场景分镜脚本
- [x] 画像适配（个性化讲解节奏）
- [x] 画面描述（visual_description）
- [ ] 集成SeeDance视频生成（**未实现** — 需要第三方视频API）
- [ ] TTS配音（**未实现** — 需要第三方语音API）

## 6.7 RAG 内容校验

- [x] RAGValidator 实现（rag_validator.py）
- [x] 原子声明提取
- [x] 知识库检索 + 距离计算
- [x] 置信度标注（high/medium/low）
- [x] 集成到 TutorAgent
- [ ] 集成到 ResourceAgents（**代码已写，效果未充分验证**）

---

## 输出物

- [x] Orchestrator 调度器代码（orchestrator.py — 意图分类→Agent调度→SSE推送）
- [x] 5个资源Agent代码（Document/Quiz/MindMap/Code/VideoScript）
- [x] Prompt 模板库（每个Agent独立的系统Prompt + _build_profile_context）
- [x] RAG 校验模块（rag_validator.py — 原子声明提取→知识库校验→置信度计算）
- [x] 进度追踪模块（SSE agent_status 事件实时推送 + 前端 AgentStatusPanel）
- [ ] SeeDance 视频集成（**待实现**）
- [ ] TTS 语音集成（**待实现**）

---

> **实际状态**：5个资源Agent全部完成并可生成。多模态拓展（视频/语音）待集成。
> RAGValidator 代码已写，但实际检索效果未充分测试。
