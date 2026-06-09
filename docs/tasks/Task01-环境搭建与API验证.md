# Task 1：环境搭建与API验证（2天）

> DeepSeek API 申请、测试与集成验证

---

## 1.1 DeepSeek API 申请

- [x] 访问 DeepSeek 开放平台，获取 API Key
- [x] 确认 API 调用地址与认证方式（Bearer Token）
- [x] 确认模型版本：**DeepSeek V4 Flash**

## 1.2 DeepSeek API 测试

- [x] 测试文本生成能力：
  - [x] 简单问答响应时间
  - [x] 长文本生成质量（资源生成场景）
  - [x] 流式输出功能（SSE）
  - [x] 并发调用限制
- [x] 确认 API 兼容 OpenAI SDK 格式：`pip install openai`
- [x] 记录测试结果（响应时间、质量评分、限制参数）

## 1.3 项目环境搭建

- [x] Python 3.11 + FastAPI 项目初始化
- [x] 安装依赖：`fastapi uvicorn sqlalchemy pymysql python-dotenv`
- [x] DeepSeek LLM 服务封装（`app/services/llm.py`）
- [x] 配置 .env 环境变量（DEEPSEEK_API_KEY、JWT_SECRET 等）

---

## 输出物

- [x] API 密钥配置文档（.env 配置完成）
- [x] API 能力测试记录
- [x] 环境配置文档（Python 3.11 + requirements.txt）

---

> **实际状态**：已完成。DeepSeek V4 Flash 已集成并稳定运行，覆盖所有 Agent 的文字生成需求。
