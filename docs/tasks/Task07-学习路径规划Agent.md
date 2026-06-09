# Task 7：学习路径规划Agent（5天）

> 知识图谱设计、LLM路径规划、画像缺口分析

---

## 7.1 知识图谱设计

- [x] 定义 19 个《机器学习》知识点（knowledge_graph 表）
- [x] 定义前置依赖（prerequisites）和相关概念（related）
- [x] 难度分级（1-5 级）+ 章节分类（6 章）
- [x] 存储为 MySQL + ChromaDB 双存储
- [x] API 接口：GET /api/knowledge-graph?course=机器学习

## 7.2 路径规划算法

- [x] LLM 驱动的个性化路径生成（path_agent.py）
- [x] 知识图谱摘要（_get_knowledge_graph_summary）
- [x] 画像缺口分析（_analyze_profile_gaps）：
  - [x] 识别薄弱知识点
  - [x] 过滤已掌握知识点
  - [x] 强化需优先加强的环节
- [x] 拓扑排序 + 难度梯度控制
- [x] 职业目标对齐

## 7.3 资源推荐

- [x] _build_profile_summary() 将画像转为 LLM 上下文
- [x] _safe_float() 兼容字符串→数值转换（修复 str vs float bug）
- [x] 路径输出包含推荐资源类型

## 7.4 路径数据结构

- [x] learning_paths 表（name, course, steps JSON）
- [x] 路径步骤：order / title / topic / difficulty / duration / objectives / resources / milestones
- [x] 前端时间线弹窗展示

---

## 输出物

- [x] 知识图谱数据（knowledge_graph 表，19个知识点）
- [x] 路径规划 Agent 代码（path_agent.py — LLM 生成个性化路径）
- [x] 路径 API 接口（GET /api/path, GET /api/path/{id}）
- [x] 前端路径可视化（进度环 + 时间线弹窗 + 知识点标签）
- [x] 单元测试（路径缺口分析 + 知识图谱验证）

---

> **实际状态**：已完成。知识图谱 19节点 + LLM 路径规划 + 画像缺口分析全部就绪。
