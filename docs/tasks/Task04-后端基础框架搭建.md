# Task 4：后端基础框架搭建（3.5天）

> 项目初始化、数据库配置、FastAPI框架、用户认证、LangGraph集成、SSE流式输出

---

## 4.1 项目初始化

- [ ] 创建项目目录结构：
  ```
  eduspark/
  ├── app/
  │   ├── api/            # API路由
  │   ├── core/           # 核心配置
  │   ├── agents/         # 智能体模块
  │   ├── models/         # 数据模型
  │   ├── services/       # 业务逻辑
  │   └── utils/          # 工具函数
  ├── config/             # 配置文件
  ├── tests/              # 测试代码
  └── requirements.txt    # 依赖包
  ```

- [ ] 初始化Python项目：
  ```bash
  python -m venv venv
  pip install fastapi uvicorn langgraph chromadb pymupdf pdfplumber
  ```

## 4.2 数据库配置

- [ ] MySQL配置：
  - [ ] 安装MySQL
  - [ ] 创建数据库
  - [ ] 配置连接池
  - [ ] 使用SQLAlchemy ORM

- [ ] Chroma配置：
  - [ ] 本地模式或服务器模式
  - [ ] 配置持久化路径

- [ ] 文件存储配置：
  - [ ] 开发阶段：本地文件系统（./storage/）
  - [ ] 演示/提交：阿里云OSS（有学生免费额度）
  - [ ] 配置访问密钥与存储桶

## 4.3 FastAPI框架搭建

- [ ] 创建main.py：
  - [ ] 应用初始化
  - [ ] 中间件配置（CORS、日志）
  - [ ] 异常处理器

- [ ] 创建基础路由：
  - [ ] 健康检查
  - [ ] API版本管理

- [ ] 配置管理：
  - [ ] 环境变量
  - [ ] 配置文件加载

## 4.4 用户认证模块（JWT登录）

- [ ] 实现JWT工具类：
  - [ ] Token生成（access_token + refresh_token）
  - [ ] Token验证与解析
  - [ ] Token刷新机制

- [ ] 实现用户模型：
  ```python
  class User(Base):
      id: str
      username: str
      password_hash: str
      created_at: datetime
  ```

- [ ] 实现认证接口：
  - [ ] POST /api/auth/register（注册）
  - [ ] POST /api/auth/login（登录）
  - [ ] POST /api/auth/refresh（刷新Token）

- [ ] 实现认证中间件：
  - [ ] 请求拦截
  - [ ] Token验证
  - [ ] 用户信息注入

## 4.5 LangGraph集成

- [ ] 安装LangGraph：
  ```bash
  pip install langgraph
  ```

- [ ] 创建基础图结构：
  - [ ] 定义State（状态数据结构）
  - [ ] 定义Node（Agent节点）
  - [ ] 定义Edge（状态流转）

- [ ] 集成讯飞星火API：
  - [ ] 自定义LLM包装器（继承BaseChatModel）
  - [ ] 配置API密钥
  - [ ] 验证流式输出

## 4.6 SSE流式输出

- [ ] 实现SSE工具类：
  ```python
  async def event_stream(generator):
      async for chunk in generator:
          yield f"data: {json.dumps(chunk)}\n\n"
  ```

- [ ] 创建流式响应接口

## 4.7 日志与监控

- [ ] 配置日志系统：
  - [ ] 日志级别
  - [ ] 日志格式
  - [ ] 日志文件轮转

- [ ] 基础监控：
  - [ ] 请求耗时统计
  - [ ] 错误率统计

---

## 输出物

- [ ] 后端项目代码框架（FastAPI + 目录结构完整）
- [ ] 数据库配置完成（MySQL + SQLAlchemy ORM + 6张表自动建表）
- [ ] 用户认证模块（JWT登录）（注册/登录/刷新Token + 路由守卫）
- [ ] LangGraph基础集成（已用 asyncio 编排器替代，效果等价）
- [ ] SSE流式输出可用（chat 接口 SSE 流式响应正常）
- [ ] 环境配置文档（.env + .env.example）
