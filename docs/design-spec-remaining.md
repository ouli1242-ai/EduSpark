# EduSpark 剩余任务设计规格

> 架构师输出，供 Dev 实现

---

## 一、Task 8：辅导 Agent（Tutor Agent）

### 1. 模块边界

**职责：** 接收学生问题，返回多模态解答（文字 + 图解 + 语音）

**不做的事：**
- 不负责画像更新（那是 ProfileAgent）
- 不负责资源生成（那是 ResourceAgents）
- 不存储学习记录（那是 LearningRecord）

**依赖：**
- `services/llm.py` — 调用 DeepSeek API
- `services/storage.py` — 存储生成的图片/音频文件
- `models/resource.py` — 查询知识库资源（RAG）

### 2. 接口契约

```
POST /api/tutor/ask
```

**Request:**
```json
{
  "question": "什么是梯度下降？",
  "context_topic": "线性回归",       // 可选，当前学习的知识点
  "output_modes": ["text", "image", "audio"]  // 可选，默认 ["text"]
}
```

**Response (SSE 流):**
```json
{"type": "agent_status", "agent": "tutor", "status": "classifying"}
{"type": "agent_status", "agent": "tutor", "status": "generating_text"}
{"type": "chunk", "content": "梯度下降是..."}
{"type": "text_done", "content": "完整文字解答"}
{"type": "agent_status", "agent": "tutor", "status": "generating_image"}
{"type": "image_done", "url": "/api/files/tutor/xxx.png"}
{"type": "agent_status", "agent": "tutor", "status": "generating_audio"}
{"type": "audio_done", "url": "/api/files/tutor/xxx.mp3"}
{"type": "done"}
```

**Error:**
```json
{"type": "error", "code": "GENERATION_FAILED", "message": "..."}
```

### 3. 内部组件设计

```
TutorAgent
├── classify(question) → QuestionType
│   枚举: concept | calculation | code | application
│
├── generate_text(question, type, profile, context) → str
│   调用: deepseek_llm.chat()
│   Prompt: 根据问题类型选择不同 Prompt 模板
│
├── generate_image(text_answer) → str (storage_key)
│   调用: 第三方图像生成 API（待集成）
│   逻辑: 从文字解答中提取可视化需求 → 生成 prompt → 调用 API
│   降级: API 不可用时跳过，不阻塞主流程
│
├── generate_audio(text_answer) → str (storage_key)
│   调用: 第三方 TTS API（待集成）
│   逻辑: 提取关键段落 → 口语化改写 → 调用 TTS
│   降级: API 不可用时跳过
│
└── run(input_data) → AsyncGenerator
    编排: classify → generate_text → [generate_image, generate_audio] 并发
```

### 4. 数据模型

**不新增表。** 复用 `resources` 表，`type` 使用现有枚举或新增 `ANSWER` 类型。

**决策：** 是否在 `resources` 表新增 `answer` 类型？

- Option A: 新增 `ResourceType.ANSWER` 枚举值
  - 优点：统一资源管理
  - 缺点：辅导解答和学习资源性质不同
- **Option B（推荐）:** 不入库，直接返回
  - 优点：辅导是即时行为，不需要持久化
  - 缺点：无法查看历史辅导记录

**推荐 Option B。** 辅导解答实时返回即可。如需历史记录，复用 `chat_histories` 表，`agent_type = "tutor"`。

### 5. Prompt 模板

**概念理解类：**
```
学生问了一个概念理解类问题。
问题：{question}
相关知识点：{context_topic}
学生画像：{profile}

请用通俗易懂的语言解释这个概念，要求：
1. 先给一句话的精确定义
2. 用一个生活中的类比来帮助理解
3. 给出 1-2 个具体例子
4. 指出常见的误解
5. Markdown 格式
```

**计算推导类：**
```
学生问了一个计算推导类问题。
问题：{question}
相关知识点：{context_topic}

请给出详细的推导过程，要求：
1. 列出所需的前提知识
2. 分步骤推导，每步都有解释
3. 标注关键公式
4. 最后给一个练习题巩固
```

**代码实现类：**
```
学生问了一个代码实现类问题。
问题：{question}

请给出代码解答，要求：
1. 先用文字说明思路
2. 给出完整可运行的 Python 代码
3. 代码中有详细注释
4. 给出运行结果示例
5. 指出可能的边界情况
```

### 6. 失败条件

| 失败点 | 影响 | 降级策略 |
|--------|------|---------|
| DeepSeek API 超时 | 无法生成文字 | 返回错误提示 |
| 图像生成失败 | 无图解 | 跳过，只返回文字 |
| TTS 失败 | 无语音 | 跳过，只返回文字 |
| 问题分类错误 | Prompt 不匹配 | 兜底使用通用 Prompt |

---

## 二、Task 9：评估 Agent（Evaluation Agent）

### 1. 模块边界

**职责：** 基于学习行为数据，生成评估报告 + 调整建议

**不做的事：**
- 不采集数据（数据由其他 Agent 在正常流程中写入 `learning_records`）
- 不直接修改学习路径（只输出建议，由 PathAgent 执行）

**依赖：**
- `models/learning_record.py` — 读取学习行为数据
- `models/resource.py` — 读取资源使用数据
- `models/profile.py` — 读取当前画像
- `services/llm.py` — 调用 DeepSeek API 生成评估报告

### 2. 接口契约

```
POST /api/evaluation/generate
```

**Request:**
```json
{
  "period": "7d",           // 评估周期: 1d / 7d / 30d / all
  "focus_topics": []        // 可选，重点关注的知识点
}
```

**Response:**
```json
{
  "evaluation_id": 1,
  "period": "2026-06-01 ~ 2026-06-08",
  "summary": {
    "knowledge_mastered": 12,
    "knowledge_weak": 5,
    "learning_hours": 8.5,
    "resources_completed": 15,
    "test_accuracy": 0.82
  },
  "strengths": ["线性回归理解扎实", "代码实操能力强"],
  "weaknesses": ["梯度下降推导不熟练", "正则化概念模糊"],
  "recommendations": [
    {
      "action": "复习",
      "topic": "梯度下降",
      "reason": "测试正确率低于 60%",
      "suggested_resources": [1, 3]
    }
  ],
  "generated_at": "2026-06-08T10:00:00"
}
```

```
GET /api/evaluation/list
```

**Response:** 评估报告列表（分页）

```
GET /api/evaluation/{id}
```

**Response:** 单个评估报告详情

### 3. 内部组件设计

```
EvaluationAgent
├── collect_data(user_id, period, db) → EvalData
│   查询: learning_records, resources, student_profiles
│   聚合: 按知识点分组统计
│
├── analyze(eval_data) → AnalysisResult
│   计算: 掌握度、薄弱点、学习效率、趋势
│   方法: 统计分析（非 LLM）
│
├── generate_report(analysis, profile) → EvaluationReport
│   调用: deepseek_llm.chat()
│   逻辑: 将分析结果 + 画像传给 LLM，生成自然语言报告
│
└── run(input_data) → dict
    编排: collect_data → analyze → generate_report → 存储
```

### 4. 数据模型

**新增表：`evaluation_reports`**

```python
class EvaluationReport(Base):
    __tablename__ = "evaluation_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    period_start: Mapped[datetime]
    period_end: Mapped[datetime]

    # 聚合数据（JSON）
    summary: Mapped[dict] = mapped_column(JSON)
    # {"knowledge_mastered": 12, "knowledge_weak": 5,
    #  "learning_hours": 8.5, "resources_completed": 15, "test_accuracy": 0.82}

    strengths: Mapped[list] = mapped_column(JSON, default=list)
    weaknesses: Mapped[list] = mapped_column(JSON, default=list)
    recommendations: Mapped[list] = mapped_column(JSON, default=list)
    # [{"action": "复习", "topic": "...", "reason": "...", "suggested_resources": [1,3]}]

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

### 5. 分析算法（纯统计，不依赖 LLM）

```python
def analyze(eval_data):
    return {
        # 知识掌握度：完成学习的知识点数
        "knowledge_mastered": count(distinct topics where action == "complete"),

        # 薄弱点：测试正确率 < 60% 的知识点
        "knowledge_weak": [topic for topic in topics if accuracy(topic) < 0.6],

        # 学习时长：所有 view 事件的 duration_seconds 之和
        "learning_hours": sum(durations) / 3600,

        # 资源完成数：action == "complete" 的记录数
        "resources_completed": count(action == "complete"),

        # 测试正确率：所有 quiz 事件的加权平均
        "test_accuracy": weighted_avg(correct, total),

        # 趋势：最近 3 天 vs 之前 3 天的正确率变化
        "trend": recent_accuracy - previous_accuracy,
    }
```

### 6. Prompt 模板

```
你是一个学习效果评估专家。根据以下数据分析结果，生成一份学习评估报告。

数据摘要：
- 周期：{period_start} ~ {period_end}
- 已掌握知识点：{knowledge_mastered} 个
- 薄弱知识点：{knowledge_weak}
- 总学习时长：{learning_hours} 小时
- 完成资源数：{resources_completed}
- 测试平均正确率：{test_accuracy}
- 学习趋势：{trend}

学生画像：{profile}

请生成评估报告，要求：
1. 总结学习表现（2-3 句话）
2. 列出 2-3 个优势
3. 列出 2-3 个需要改进的地方
4. 给出 3-5 条具体的改进建议，每条包含：行动、知识点、原因
5. 语气鼓励为主，建设性为辅
```

### 7. 失败条件

| 失败点 | 影响 | 降级策略 |
|--------|------|---------|
| 无学习数据 | 无法分析 | 返回"暂无足够数据，请先开始学习" |
| LLM 生成失败 | 无自然语言报告 | 只返回统计数据摘要 |
| 数据量太少 | 分析不准 | 提示"数据不足，建议积累更多学习记录" |

---

## 三、Task 7 补全：知识图谱 + 资源推荐

### 1. 知识图谱数据结构

**存储方式：** MySQL JSON 字段（不引入图数据库，当前规模不需要）

**新增表：`knowledge_graph`**

```python
class KnowledgeGraphNode(Base):
    __tablename__ = "knowledge_graph"

    id: Mapped[int] = mapped_column(primary_key=True)
    course: Mapped[str] = mapped_column(String(100), index=True)  # "机器学习"
    name: Mapped[str] = mapped_column(String(200))                # "线性回归"
    chapter: Mapped[int] = mapped_column(Integer, default=0)      # 教材章节号
    difficulty: Mapped[int] = mapped_column(Integer, default=1)   # 1-5

    # 依赖关系（存储为 ID 列表）
    prerequisites: Mapped[list] = mapped_column(JSON, default=list)  # 前置知识 ID
    related: Mapped[list] = mapped_column(JSON, default=list)        # 相关知识 ID

    # 描述
    description: Mapped[str] = mapped_column(Text, default="")
```

### 2. 资源推荐算法

**输入：** student_profile + topic + available_resources

**输出：** 排序后的资源列表

```python
def recommend_resources(profile, topic, resources):
    scored = []
    for r in resources:
        score = 0.0

        # 维度 1：知识点匹配度（权重 0.4）
        if topic in r.knowledge_points:
            score += 0.4

        # 维度 2：难度适配（权重 0.3）
        pref_diff = profile.get("learning_preferences", {}).get("difficulty_pref", "中等")
        diff_map = {"简单": 2, "中等": 3, "困难": 4}
        target = diff_map.get(pref_diff, 3)
        diff_score = 1 - abs(r.difficulty - target) / 4
        score += 0.3 * diff_score

        # 维度 3：资源类型偏好（权重 0.2）
        pref_types = profile.get("learning_preferences", {}).get("resource_types", [])
        if r.type.value in pref_types:
            score += 0.2

        # 维度 4：置信度（权重 0.1）
        conf_map = {"high": 1.0, "medium": 0.6, "low": 0.3}
        score += 0.1 * conf_map.get(r.confidence, 0.5)

        scored.append((r, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [r for r, s in scored[:5]]
```

### 3. 接口契约

```
GET /api/knowledge-graph?course=机器学习
```

**Response:** 知识图谱节点列表（含依赖关系）

```
GET /api/resources/recommend?topic=线性回归
```

**Response:** 推荐的 Top 5 资源

---

## 四、Task 6 补全：RAG 校验模块

### 1. 模块边界

**职责：** 对生成的内容进行知识库校验，输出置信度

**依赖：**
- ChromaDB（向量检索）
- 生成的资源内容

### 2. 接口（内部调用，不对外暴露）

```python
class RAGValidator:
    async def validate(self, content: str, knowledge_points: list[str]) -> ValidationResult:
        """
        输入: 生成的内容文本 + 关联知识点
        输出: 置信度 + 校验详情
        """
        ...

@dataclass
class ValidationResult:
    confidence: str           # "high" | "medium" | "low"
    total_claims: int         # 总声明数
    supported_claims: int     # 有知识库支持的声明数
    unsupported_claims: list  # 无支持的声明列表
    details: list[dict]       # 每条声明的校验详情
```

### 3. 校验流程

```
输入内容
  │
  ▼
提取原子声明（LLM）
  │  Prompt: "将以下内容拆分为可独立验证的原子声明，每条一行"
  │
  ▼
对每条声明做向量检索（ChromaDB）
  │  查询: 声明文本 → top-3 相似文档
  │  判断: 最高相似度 > 0.7 → 支持
  │
  ▼
计算置信度
  │  supported / total > 0.8 → "high"
  │  supported / total > 0.5 → "medium"
  │  else → "low"
  │
  ▼
返回 ValidationResult
```

### 4. 集成点

在 Orchestrator 的资源生成流程中，每个 Agent 生成完毕后调用：

```python
# orchestrator.py 中的 _handle_resource 方法
result = await agent.run(input_data)

# RAG 校验
validator = RAGValidator(chroma_client)
validation = await validator.validate(
    content=result.get("content", ""),
    knowledge_points=[topic]
)

# 写入数据库时带上置信度
resource.confidence = validation.confidence
```

---

## 五、实现优先级

| 优先级 | 任务 | 理由 |
|--------|------|------|
| P0 | Task 8 辅导Agent | 核心功能，赛题明确要求 |
| P0 | Task 9 评估Agent | 加分项但实现简单，性价比高 |
| P1 | Task 7 知识图谱 + 推荐 | 增强路径规划质量 |
| P2 | Task 6 RAG 校验 | 有知识库后才有意义 |

---

## 六、给 Dev 的注意事项

1. **所有 Agent 必须有降级策略** — DeepSeek API 可能不稳定，任何外部调用都要 try-catch
2. **SSE 事件格式必须统一** — 参照 Chat.vue 中的 `handleSSEEvent` 函数
3. **新增表需要在 `models/__init__.py` 中导出**
4. **新增路由需要在 `app/main.py` 中注册**
5. **测试时先用 DeepSeek V4 Flash，确认功能正常后再考虑降级**

---

*文档版本：v1.0*
*输出者：架构师角色*
*日期：2026-06-08*
