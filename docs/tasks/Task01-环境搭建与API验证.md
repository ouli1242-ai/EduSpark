# Task 1：环境搭建与API验证（2天）

> 讯飞开发者账号注册、各API测试、LangGraph集成验证

---

## 1.1 讯飞开发者账号注册

- [ ] 访问讯飞开放平台（https://open.xfyun.cn/）
- [ ] 注册开发者账号（需实名认证）
- [ ] 创建应用，获取AppID、APISecret、APIKey
- [ ] 开通以下服务：
  - [ ] 星火大模型API
  - [ ] 图像生成API
  - [ ] TTS语音合成API
  - [ ] SeeDance视频生成API

## 1.2 星火API测试

- [ ] 安装Python SDK：`pip install spark_ai_python`
- [ ] 测试文本生成能力：
  - [ ] 简单问答响应时间
  - [ ] 长文本生成质量
  - [ ] 流式输出功能
  - [ ] 并发调用限制
- [ ] 记录测试结果（响应时间、质量评分、限制参数）

## 1.3 SeeDance API测试

- [ ] 查看SeeDance API文档
- [ ] 测试视频生成：
  - [ ] 文本描述→视频生成（SeeDance是文生视频模型，输入是自然语言prompt）
  - [ ] 生成时长与质量
  - [ ] 支持的视频规格
  - [ ] prompt格式要求
- [ ] 记录API能力边界（重点记录：输入prompt格式、生成时长限制、分辨率支持）

## 1.4 图像生成API测试

- [ ] 测试图像生成：
  - [ ] 知识点配图生成
  - [ ] 思维导图节点图像
  - [ ] 图像分辨率与风格控制
- [ ] 记录测试结果

## 1.5 TTS API测试

- [ ] 测试语音合成：
  - [ ] 中文发音准确度
  - [ ] 语速、语调控制
  - [ ] 音频格式与质量
- [ ] 记录测试结果

## 1.6 LangGraph集成验证

- [ ] 安装LangGraph：`pip install langgraph`
- [ ] 验证LangGraph有状态图能否接入星火自定义LLM：
  - [ ] 自定义LLM包装器（继承BaseChatModel）
  - [ ] 有状态图（StateGraph）基础能力
  - [ ] 节点间状态传递机制
  - [ ] 流式输出支持
- [ ] 输出集成可行性报告（重点验证：状态图 + 星火API + 流式输出三者兼容性）

---

## 输出物

- [ ] API密钥配置文档（.env 配置完成）
- [ ] API能力测试报告（响应时间、限制、质量）
- [ ] LangGraph集成可行性报告
- [ ] 环境配置文档（Python 3.13 + venv + requirements.txt）
