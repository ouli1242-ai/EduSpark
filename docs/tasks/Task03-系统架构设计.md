# Task 3：系统架构设计（3天）

> 多智能体角色定义、协作流程设计、学习画像模型、数据流与存储方案

---

## 3.1 多智能体角色定义

- [x] 编排器（Orchestrator）
  - 职责：意图分类、Agent 调度、SSE 推送
  - 输入：用户消息
  - 输出：分流到对应 Agent

- [x] 画像Agent（Profile Agent）
  - 职责：对话式学习画像构建与更新
  - 输入：学生对话
  - 输出：6维度画像数据

- [x] 资源Agent群（Resource Agents）
  - [x] 文档Agent：生成课程讲解文档
  - [x] 题库Agent：生成练习题目
  - [x] 思维导图Agent：生成知识点结构图
  - [x] 案例Agent：生成代码实操案例
  - [x] 视频Agent：生成教学视频脚本

- [x] 路径Agent（Path Agent）
  - 职责：学习路径规划与资源推荐
  - 输入：画像 + 资源元数据
  - 输出：个性化学习路径

- [x] 评估Agent（Evaluation Agent）
  - 职责：学习效果评估与策略调整
  - 输入：学习行为数据
  - 输出：评估报告 + 调整建议

- [x] 辅导Agent（Tutor Agent）
  - 职责：即时文字答疑（已实现）
  - 多模态拓展：图像/语音（**待实现**）
  - 输入：学生问题
  - 输出：文字解答

## 3.2 协作流程设计（实际架构）

- [x] 设计自研编排器（替代 LangGraph）：
  ```
  用户输入 → Orchestrator（意图分类：5种）
               ↓
  ├─ profile → ProfileAgent（画像更新）
  ├─ tutor → TutorAgent（智能辅导）
  ├─ resource → ResourceAgents（5个并发生成）
  ├─ path → PathAgent（路径规划）
  └─ evaluation → EvaluationAgent（评估报告）
  ```
- [x] 定义意图分类策略（关键词预筛选 + LLM 兜底）
- [x] 定义异常处理流程（try/except + SSE 错误推送）
- [x] 定义并行执行策略（asyncio.create_task 并发生成资源）

## 3.3 学习画像6维度模型

- [x] 知识基础（Knowledge Base）
  - mastered（已掌握）/ weak（薄弱）/ blind_spots（盲区）/ score
- [x] 认知风格（Cognitive Style）
  - visual / auditory / kinesthetic / summary
- [x] 学习能力（Learning Ability）
  - absorption_speed / understanding_depth / transfer_ability
- [x] 易错点模式（Error Patterns）
  - types / root_causes / severity
- [x] 学习目标（Learning Goals）
  - short_term / long_term / career
- [x] 学习偏好（Learning Preferences）
  - resource_types / time_pref / difficulty_pref

## 3.4 数据流设计

- [x] 用户输入数据流（HTTP → SSE）
- [x] Agent 间通信数据流（Orchestrator 调度）
- [x] 存储数据流（SQLAlchemy → MySQL）
- [x] 输出数据流（SSE → 前端）

## 3.5 存储方案设计

- [x] MySQL（9张表）：
  - [x] users / student_profiles / resources
  - [x] learning_paths / learning_records / chat_histories
  - [x] knowledge_documents / evaluation_reports / knowledge_graph
- [x] Chroma（向量数据）：
  - [x] ml_knowledge（机器学习知识库）
  - [ ] 资源向量检索（**功能已实现，效果未验证**）
- [x] 本地文件系统（./storage/）：
  - [x] 上传的文档
  - [x] 生成的资源文件

## 3.6 API接口设计

- [x] 对话接口（SSE 流式）：POST /api/chat
- [x] 画像查询/更新：GET/PUT /api/profile
- [x] 资源列表/详情：GET /api/resources /api/resources/{id}
- [x] 路径查询：GET /api/path /api/path/{id}
- [x] 评估报告：GET /api/evaluation /api/evaluation/stats
- [x] 知识图谱：GET /api/knowledge-graph
- [x] 文件上传：POST/GET/DELETE /api/upload
- [x] 智能辅导：POST /api/tutor/ask
- [x] 认证：POST /api/auth/register /login /refresh

---

## 输出物

- [x] 架构设计文档（4层架构：前端→Orchestrator→Agent→存储）
- [x] 多智能体协作流程图（自研编排器 意图分类→Agent调度→SSE推送）
- [x] API 接口文档（Swagger 自动生成：/docs）
- [x] 6维度画像模型定义文档（student_profiles 表 JSON 字段）

---

> **实际状态**：已完成。与初始设计相比，多智能体框架从 LangGraph 改为自研编排器。
