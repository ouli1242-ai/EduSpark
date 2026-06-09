# Task 8：智能辅导Agent（5天）

> 问题理解与分类、文字解答生成、RAG 校验、画像适配

---

## 8.1 问题理解与分类

- [x] 设计问题类型：
  - [x] 概念理解类（concept）
  - [x] 计算推导类（calculation）
  - [x] 代码实现类（code）
  - [x] 应用场景类（application）

- [x] 实现问题分类器（LLM 分类）
- [x] 上下文关联：
  - [x] 关联当前学习内容
  - [x] 关联6维度画像

## 8.2 文字解答生成

- [x] 设计解答 Prompt（因材施教策略）
  - [x] 认知风格适配（视觉型/听觉型/动觉型差异化讲解）
  - [x] 知识基础适配（避免已掌握内容重复讲）
  - [x] 学习能力适配（吸收速度/理解深度调整讲解节奏）

- [x] 调用 DeepSeek API 生成解答
- [x] 流式输出（SSE chunk）
- [x] Markdown 格式（代码块 + 数学公式）

- [x] RAG 知识库校验：
  - [x] 回答后自动校验
  - [x] 置信度标注（high/medium/low）
  - [x] 支持/不支持的声明列表

## 8.3 图解说明生成

- [ ] 设计图像生成 Prompt（**待实现**）
- [ ] 调用第三方图像生成 API（**待实现**）
- [ ] 图文整合展示（**待实现**）

## 8.4 语音讲解生成

- [ ] 提取讲解文本转为口语化表达（**待实现**）
- [ ] 调用第三方 TTS API（**待实现**）
- [ ] 语音播放控制（**待实现**）

## 8.5 答案融合

- [x] SSE 事件：chunk + tutor_analysis + rag_validation + agent_status
- [x] 学习记录写入（learning_records 表）
- [ ] 多模态融合（**待实现**）

---

## 输出物

- [x] 辅导Agent代码（tutor_agent.py — classify→generate_answer→RAG验证）
- [x] 问题分类器（concept/calculation/code/application 四分类）
- [x] 文字解答生成（因材施教 + 认知风格适配）
- [ ] 图解生成模块（**待实现**）
- [ ] TTS语音生成模块（**待实现**）
- [x] 辅导API接口（POST /api/tutor/ask SSE流式）
- [x] RAG 校验集成（rag_validation 事件）

---

> **实际状态**：文字解答部分已完成，支持4类问题+画像适配+RAG校验。
> 图解和语音部分尚未实现，需要接入第三方多模态API。
