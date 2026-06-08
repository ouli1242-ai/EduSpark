# Task 7：学习路径规划Agent（5天）

> 知识图谱设计、路径规划算法、资源推荐、路径动态调整

---

## 7.1 知识图谱设计

- [ ] 定义知识节点：
  ```json
  {
    "id": "ml_001",
    "name": "线性回归",
    "chapter": 3,
    "difficulty": 2,
    "prerequisites": ["ml_002", "ml_003"],
    "related": ["ml_004", "ml_005"]
  }
  ```

- [ ] 定义依赖关系：
  - [ ] 前置知识
  - [ ] 并行知识
  - [ ] 进阶知识

- [ ] 构建《机器学习》知识图谱：
  - [ ] 提取教材目录
  - [ ] 分析知识点依赖
  - [ ] 存储为图结构

## 7.2 路径规划算法

- [ ] 设计规划策略：
  - [ ] 基础路径（按教材顺序）
  - [ ] 个性化路径（基于画像调整）
  - [ ] 强化路径（针对薄弱点）

- [ ] 实现拓扑排序：
  - [ ] 根据依赖关系排序
  - [ ] 过滤已掌握知识点

- [ ] 实现路径优化：
  - [ ] 学习效率最大化
  - [ ] 难度梯度合理
  - [ ] 时间分配均衡

## 7.3 资源推荐算法

- [ ] 设计推荐策略：
  - [ ] 基于画像匹配（认知风格、学习偏好）
  - [ ] 基于内容相关度（知识点匹配）
  - [ ] 基于难度适配（学习能力匹配）

- [ ] 实现推荐引擎：
  ```python
  def recommend_resources(profile, topic, available_resources):
      # 计算匹配分数
      scores = []
      for resource in available_resources:
          score = calculate_match_score(profile, resource)
          scores.append((resource, score))
      # 排序返回Top N
      return sorted(scores, key=lambda x: x[1], reverse=True)[:5]
  ```

- [ ] 实现推荐结果格式化

## 7.4 路径动态调整

- [ ] 实现学习进度跟踪：
  - [ ] 记录已完成知识点
  - [ ] 记录学习时长
  - [ ] 记录测试成绩

- [ ] 实现调整触发条件：
  - [ ] 进度落后
  - [ ] 成绩下降
  - [ ] 画像更新

- [ ] 实现路径重规划：
  - [ ] 基于当前进度
  - [ ] 基于最新画像
  - [ ] 保持连贯性

## 7.5 路径可视化

- [ ] 设计路径数据结构：
  ```json
  {
    "path_id": "xxx",
    "user_id": "xxx",
    "steps": [
      {
        "order": 1,
        "topic": "线性回归",
        "resources": [...],
        "status": "completed",
        "estimated_time": "2h"
      }
    ],
    "progress": 0.35
  }
  ```

- [ ] 实现路径查询接口
- [ ] 实现进度更新接口

---

## 输出物

- [ ] 知识图谱数据（knowledge_graph.py 模型 + /api/knowledge-graph 接口）
- [ ] 路径规划算法代码（path_agent.py — LLM 生成个性化路径步骤）
- [ ] 资源推荐算法代码（knowledge_graph.py — calculate_match_score 4维度匹配）
- [ ] 路径API接口（GET /api/path, GET /api/path/{id}, PUT /api/path/{id}/progress）
- [ ] 测试用例
