# Task 5：对话式学习画像Agent（5天）

> 画像提取Prompt设计、对话状态管理、特征抽取、画像存储与更新、可视化接口

---

## 5.1 画像提取Prompt设计

- [x] 设计系统 Prompt：
  - 6 维度画像提取指令
  - 对话模式判断（知识问答模式 vs 画像探索模式）
  - 分阶段追问规则（初始/深化/精细化）
  - 主动推断策略
  - [PROFILE_UPDATE] 标记机制

## 5.2 对话状态管理

- [x] 对话历史存储（chat_histories 表 + session_id）
- [x] 上下文窗口管理（最近 20 条消息）
- [x] 会话状态机（Orchestrator 管理 session_id）

## 5.3 特征抽取算法

- [x] _field_map() 字段映射：
  - [x] 标准格式兼容
  - [x] 旧格式兼容（perception/thinking → visual/auditory/kinesthetic）
  - [x] 文本→分数映射（TEXT_TO_SCORE 字典）
  - [x] NaN/Inf 过滤（_field_map + _merge_dimension 双层防护）
- [x] JSON 安全解析
- [x] _merge_dimension() 智能增量合并：
  - [x] 列表去重
  - [x] 数值加权平均（新0.3/旧0.7）
  - [x] 字符串择优（选更详细的）
  - [x] 嵌套字典递归合并
  - [x] NaN/Inf 数值过滤

## 5.4 画像存储与更新

- [x] student_profiles 表（6个 JSON 字段）
- [x] 画像 CRUD 操作（GET/PUT /api/profile）
- [x] _count_completed_dimensions() 维度完成度统计
- [x] 增量更新（Orchestrator 调用 → setattr → commit）
- [x] NaN 脏数据自动清理（API 响应层 _clean_db_profile）

## 5.5 画像可视化接口

- [x] GET /api/profile 返回完整 6 维度数据
- [x] 前端 ECharts 雷达图（6 维度）
- [x] 前端 3x2 维度卡片网格（百分比显示 + 描述文字）

## 5.6 测试与优化

- [x] 单元测试（字段映射 / 增量合并 / 维度计数 共 11 个子测试）
- [x] NaN 边界情况处理
- [x] 空画像默认值（首次访问自动创建）

---

## 输出物

- [x] 画像Agent代码（profile_agent.py — 对话提取→JSON→DB更新）
- [x] Prompt 模板库（6维度画像提取 Prompt + [PROFILE_UPDATE] 标记机制 + 分阶段追问策略）
- [x] 画像数据结构定义（student_profiles 表 JSON 字段）
- [x] 画像API接口（GET/PUT /api/profile）
- [x] 测试用例与测试报告
- [x] NaN 防护（前后端双层保护）

---

> **实际状态**：已完成。6维度画像提取、增量合并、NaN防护全部就绪。
