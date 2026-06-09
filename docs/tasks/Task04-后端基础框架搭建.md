# Task 4：后端基础框架搭建（3.5天）

> 项目初始化、数据库配置、FastAPI框架、用户认证、Orchestrator、SSE流式输出

---

## 4.1 项目初始化

- [x] 创建项目目录结构（app/api/ core/ agents/ models/ services/ utils/）
- [x] 初始化 Python 项目（Python 3.11 + requirements.txt）

## 4.2 数据库配置

- [x] MySQL 配置：
  - [x] 安装 MySQL，创建 eduspark 数据库
  - [x] SQLAlchemy ORM + 连接池（pool_size=10, max_overflow=20）
  - [x] 9 张表自动建表（init_db()）
- [x] Chroma 配置：
  - [x] 本地持久化模式（./storage/chroma）
  - [x] 延迟导入避免阻塞
- [x] 文件存储：本地文件系统（./storage/）

## 4.3 FastAPI框架搭建

- [x] 创建 main.py：应用初始化、CORS 中间件、lifespan
- [x] 健康检查接口：GET /api/health
- [x] 配置管理：.env + pydantic-settings

## 4.4 用户认证模块（JWT登录）

- [x] JWT 工具类：hash_password / verify_password / create_access_token / create_refresh_token / decode_token
- [x] 用户模型（User）：id / username / password_hash / created_at
- [x] 认证接口：
  - [x] POST /api/auth/register（注册）
  - [x] POST /api/auth/login（登录）
  - [x] POST /api/auth/refresh（刷新Token）
- [x] 认证中间件：HTTPBearer + get_current_user 依赖注入

## 4.5 多智能体编排器（Orchestrator）

- [x] 实现 Orchestrator 类（替代 LangGraph）：
  - [x] 意图分类（LLM + 关键词预筛选）
  - [x] 5 种意图分流（profile / tutor / resource / path / evaluation）
  - [x] 异步并发生成（asyncio.create_task）
  - [x] 异常捕获 + SSE 错误推送
- [x] 集成 DeepSeek V4 Flash（OpenAI 兼容 SDK）

## 4.6 SSE流式输出

- [x] 实现 SSE 工具类（sse_event() + StreamingResponse）
- [x] SSE 事件类型：chunk / agent_status / profile_updated / resource_generated / path_generated / evaluation_report / tutor_analysis / done

## 4.7 日志与路由

- [x] 配置 SQLAlchemy 日志（DEBUG 模式）
- [x] 注册 9 个路由模块（auth / profile / chat / resources / path / evaluation / upload / tutor / knowledge_graph）

---

## 输出物

- [x] 后端项目代码框架（FastAPI + 目录结构完整）
- [x] 数据库配置完成（MySQL + SQLAlchemy ORM + 9张表自动建表）
- [x] 用户认证模块（JWT：注册/登录/刷新Token + 路由守卫）
- [x] 多智能体编排器（Orchestrator：意图分类→Agent调度→SSE推送）
- [x] SSE 流式输出可用（chat 接口 SSE 流式响应正常）
- [x] 环境配置文档（.env + .env.example）

---

> **实际状态**：已完成。多智能体框架采用自研编排器而非 LangGraph，效果等价且更轻量。
