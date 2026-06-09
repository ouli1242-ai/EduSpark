"""路径 Agent — 知识图谱驱动的个性化学习路径规划"""
import json
import re
from app.agents.base import BaseAgent


def _safe_float(value, default=0.0):
    """安全转换数值，兼容字符串类型"""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        v = float(value)
        if v != v or v == float('inf') or v == float('-inf'):
            return default
        return v
    if isinstance(value, str):
        for kw, score in [("极快", 0.9), ("较快", 0.7), ("快", 0.7), ("一般", 0.5),
                          ("较慢", 0.3), ("慢", 0.3), ("极慢", 0.1),
                          ("强", 0.7), ("较弱", 0.3), ("弱", 0.3), ("极强", 0.9),
                          ("中等", 0.5), ("深", 0.7), ("浅", 0.3), ("中", 0.5)]:
            if kw in value:
                return score
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    return default

# 机器学习课程知识图谱（知识点 → 前置依赖）
ML_KNOWLEDGE_GRAPH = {
    "数学基础复习": {
        "prerequisites": [],
        "difficulty": 2,
        "category": "基础",
        "description": "线性代数（矩阵、特征值）、概率论（贝叶斯、分布）、微积分（导数、梯度）",
    },
    "机器学习概述": {
        "prerequisites": [],
        "difficulty": 1,
        "category": "基础",
        "description": "什么是机器学习、监督/无监督/强化学习、基本流程",
    },
    "线性回归": {
        "prerequisites": ["数学基础复习", "机器学习概述"],
        "difficulty": 2,
        "category": "监督学习",
        "description": "最小二乘法、梯度下降、正则化（L1/L2）、模型评估",
    },
    "逻辑回归": {
        "prerequisites": ["线性回归"],
        "difficulty": 2,
        "category": "监督学习",
        "description": "Sigmoid函数、交叉熵损失、决策边界、多分类",
    },
    "决策树": {
        "prerequisites": ["机器学习概述"],
        "difficulty": 2,
        "category": "监督学习",
        "description": "信息增益、基尼系数、剪枝、ID3/C4.5/CART",
    },
    "随机森林": {
        "prerequisites": ["决策树"],
        "difficulty": 3,
        "category": "集成学习",
        "description": "Bagging、特征随机选择、OOB评估、特征重要性",
    },
    "支持向量机(SVM)": {
        "prerequisites": ["数学基础复习", "线性回归"],
        "difficulty": 3,
        "category": "监督学习",
        "description": "最大间隔、核函数、软间隔、对偶问题",
    },
    "K近邻(KNN)": {
        "prerequisites": ["机器学习概述"],
        "difficulty": 1,
        "category": "监督学习",
        "description": "距离度量、K值选择、KD树、维度灾难",
    },
    "朴素贝叶斯": {
        "prerequisites": ["数学基础复习"],
        "difficulty": 2,
        "category": "监督学习",
        "description": "贝叶斯定理、条件独立性假设、拉普拉斯平滑",
    },
    "K-Means聚类": {
        "prerequisites": ["机器学习概述"],
        "difficulty": 2,
        "category": "无监督学习",
        "description": "聚类原理、肘部法则、K-Means++、局限性",
    },
    "层次聚类": {
        "prerequisites": ["K-Means聚类"],
        "difficulty": 3,
        "category": "无监督学习",
        "description": "凝聚/分裂聚类、树状图、距离度量、连接准则",
    },
    "PCA降维": {
        "prerequisites": ["数学基础复习"],
        "difficulty": 3,
        "category": "降维",
        "description": "特征值分解、方差解释率、重构、t-SNE对比",
    },
    "集成学习": {
        "prerequisites": ["决策树", "线性回归"],
        "difficulty": 3,
        "category": "集成学习",
        "description": "Bagging/Boosting/Stacking、偏差方差权衡、XGBoost/LightGBM",
    },
    "神经网络基础": {
        "prerequisites": ["数学基础复习", "逻辑回归"],
        "difficulty": 4,
        "category": "深度学习",
        "description": "感知机、激活函数、反向传播、梯度消失/爆炸",
    },
    "卷积神经网络(CNN)": {
        "prerequisites": ["神经网络基础"],
        "difficulty": 4,
        "category": "深度学习",
        "description": "卷积层、池化层、经典架构(LeNet/AlexNet/ResNet)、迁移学习",
    },
    "过拟合与正则化": {
        "prerequisites": ["线性回归", "决策树"],
        "difficulty": 3,
        "category": "通用技巧",
        "description": "偏差-方差权衡、L1/L2正则化、Dropout、早停、数据增强",
    },
    "模型评估与选择": {
        "prerequisites": ["线性回归", "决策树"],
        "difficulty": 2,
        "category": "通用技巧",
        "description": "交叉验证、混淆矩阵、ROC/AUC、F1-score、网格搜索",
    },
    "特征工程": {
        "prerequisites": ["机器学习概述"],
        "difficulty": 2,
        "category": "通用技巧",
        "description": "特征缩放、编码、选择、构造、缺失值处理",
    },
}

SYSTEM_PROMPT = """你是一位资深学习路径规划专家。你的任务是根据学生的画像和机器学习课程知识图谱，规划最优的个性化学习路径。

## 机器学习课程知识图谱（知识点 → 前置依赖）

{knowledge_graph}

## 规划原则

### 1. 拓扑排序优先
- 严格遵循前置依赖关系，前置知识必须在后续知识之前
- 对于已掌握的知识点，可以标记为"跳过"或"快速回顾"

### 2. 薄弱点强化
- 学生的薄弱知识点应安排在相关主题之前做重点强化
- 例如：学生线性代数弱 → 在学SVM之前先安排数学基础复习

### 3. 难度梯度合理
- 从难度低的概念开始，逐步递增
- 基础概念 → 核心算法 → 进阶方法 → 综合实战
- 相邻步骤的难度跳跃不超过2级

### 4. 个性化调整
- 视觉型学生：优先安排配有丰富图表/可视化的知识点
- 动觉型学生：优先安排有代码实操的知识点（如决策树、KNN）
- 根据学生能力调整每个步骤的学习时间估计
  - 能力强：缩短时间
  - 能力弱：增加时间，加入更多练习
- 结合学生职业目标选择重点方向
  - AI工程师 → 侧重深度学习、SVM
  - 数据分析师 → 侧重统计方法、特征工程
  - 算法工程师 → 侧重数学推导、优化方法

### 5. 路径结构
- 总步骤 6-12 个
- 每个步骤包含：知识点、学习目标、推荐资源类型、预计时间、完成标准
- 步骤之间要有逻辑递进关系

## 输出格式

严格输出 JSON，不要有额外文字：
```json
{
  "name": "路径名称（体现个性化定位）",
  "course": "机器学习",
  "description": "2-3句描述这个路径的设计思路",
  "total_estimated_hours": 40,
  "target_level": "初级→中级|中级→高级|零基础→入门",
  "steps": [
    {
      "order": 1,
      "topic": "知识点名称",
      "knowledge_points": ["具体知识点1", "具体知识点2"],
      "category": "分类标签",
      "description": "这一步要学什么、为什么先学这个",
      "learning_objectives": ["目标1", "目标2"],
      "estimated_time": "2h",
      "difficulty": 2,
      "recommended_resources": ["文档", "视频", "练习题"],
      "completion_criteria": "如何判断已经掌握（具体可验证的标准）",
      "prerequisites_fulfilled": ["依赖的前置知识点"],
      "status": "pending"
    }
  ],
  "milestones": [
    {"name": "阶段性目标", "at_step": 3, "description": "达成什么"},
    {"name": "阶段性目标", "at_step": 7, "description": "达成什么"}
  ]
}
```"""


class PathAgent(BaseAgent):
    """路径 Agent：知识图谱驱动的个性化学习路径规划"""

    def _get_knowledge_graph_summary(self) -> str:
        """将知识图谱转为 LLM 可读的摘要"""
        lines = []
        for topic, info in ML_KNOWLEDGE_GRAPH.items():
            prereqs = ", ".join(info["prerequisites"]) if info["prerequisites"] else "无"
            lines.append(
                f"- **{topic}** (难度{info['difficulty']}/5, {info['category']})\n"
                f"  前置依赖：{prereqs}\n"
                f"  内容：{info['description']}"
            )
        return "\n".join(lines)

    def _analyze_profile_gaps(self, profile: dict) -> dict:
        """分析画像中的知识缺口和特殊需求"""
        kb = profile.get("knowledge_base", {})
        weak_points = kb.get("weak", []) if kb else []
        blind_spots = kb.get("blind_spots", []) if kb else []
        mastered = kb.get("mastered", []) if kb else []

        # 根据弱点和盲区找到需要优先强化的知识点
        priority_topics = []
        for topic, info in ML_KNOWLEDGE_GRAPH.items():
            desc = info.get("description", "")
            # 检查弱点和盲区是否与知识点或描述相关
            for weak in weak_points + blind_spots:
                if weak in topic or weak in desc or topic in weak:
                    priority_topics.append(topic)
                    break

        return {
            "mastered": mastered,
            "weak": weak_points,
            "blind_spots": blind_spots,
            "priority_topics": priority_topics[:5],
        }

    async def run(self, input_data: dict) -> dict:
        """
        input_data:
            - course: 课程名称
            - profile: 学生画像
            - resources: 已有资源列表（可选）
            - request: 学生具体需求（可选）
        """
        course = input_data.get("course", "机器学习")
        profile = input_data.get("profile", {})
        resources = input_data.get("resources", [])
        request = input_data.get("request", "")

        # 1. 分析画像
        gap_analysis = self._analyze_profile_gaps(profile)
        profile_context = self._build_profile_summary(profile, gap_analysis)

        # 2. 构建知识图谱摘要
        kg_summary = self._get_knowledge_graph_summary()

        # 3. 构建系统提示（用 replace 避免 JSON 花括号与 format 冲突）
        system_prompt = SYSTEM_PROMPT.replace("{knowledge_graph}", kg_summary)

        # 4. 构建用户输入
        context_parts = [f"课程：{course}"]

        if request:
            context_parts.append(f"学生特殊需求：{request}")

        context_parts.append(f"\n## 学生画像分析\n{profile_context}")

        if resources:
            res_summary = "已有学习资源：\n" + "\n".join(
                f"- [{r.get('type', r.type.value if hasattr(r, 'type') else '')}] {r.get('title', getattr(r, 'title', ''))}"
                for r in resources[:20]
            )
            context_parts.append(res_summary)

        context_parts.append(
            "\n## 规划要求\n"
            "请根据以上知识图谱和学生画像，规划个性化学习路径。\n"
            "- 已掌握知识点可跳过或标记为快速回顾\n"
            "- 薄弱点相关的知识要安排前置强化\n"
            "- 知识盲区内的概念要重点覆盖\n"
            "- 路径要有明确的阶段里程碑"
        )

        user_content = "\n".join(context_parts)
        messages = self._build_messages(system_prompt, user_content)
        response = await self.llm.chat(messages, temperature=0.5, max_tokens=8192)

        # 解析 JSON
        path_data = self._parse_response(response, course)
        path_data["_gap_analysis"] = gap_analysis

        return {
            "path": path_data,
            "raw_response": response,
        }

    def _build_profile_summary(self, profile: dict, gaps: dict) -> str:
        """构建画像摘要"""
        if not profile:
            return "暂无画像信息，按标准路径规划。"

        parts = []

        if gaps.get("mastered"):
            parts.append(f"已掌握：{', '.join(gaps['mastered'][:8])}")
        if gaps.get("weak"):
            parts.append(f"薄弱点：{', '.join(gaps['weak'])}")
        if gaps.get("blind_spots"):
            parts.append(f"知识盲区：{', '.join(gaps['blind_spots'])}")
        if gaps.get("priority_topics"):
            parts.append(f"需优先强化：{', '.join(gaps['priority_topics'])}")

        la = profile.get("learning_ability", {})
        if la:
            avg_speed = _safe_float(la.get("absorption_speed"), 0.5)
            parts.append(f"学习速度：{'快' if avg_speed > 0.6 else '中' if avg_speed > 0.3 else '慢'}")

        cs = profile.get("cognitive_style", {})
        if cs:
            v = _safe_float(cs.get("visual", 0))
            a = _safe_float(cs.get("auditory", 0))
            k = _safe_float(cs.get("kinesthetic", 0))
            max_style = max(v, a, k)
            style_name = "视觉型" if v >= max_style else "听觉型" if a >= max_style else "动觉型"
            parts.append(f"主导认知风格：{style_name}")

        lg = profile.get("learning_goals", {})
        if lg.get("career"):
            parts.append(f"职业目标：{lg['career']}")

        lp = profile.get("learning_preferences", {})
        if lp.get("difficulty_pref"):
            parts.append(f"难度偏好：{lp['difficulty_pref']}")

        return "\n".join(f"- {p}" for p in parts)

    def _parse_response(self, response: str, course: str) -> dict:
        """解析 LLM 返回的路径 JSON"""
        import re
        cleaned = response

        # 移除代码块标记
        cleaned = re.sub(r'```json\s*', '', cleaned)
        cleaned = re.sub(r'```\s*', '', cleaned)
        cleaned = cleaned.strip()

        try:
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(cleaned[start:end])
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[PathAgent] JSON解析失败: {e}")
            print(f"[PathAgent] 原始响应前200字: {response[:200]}")

        return {
            "name": f"{course} 学习路径",
            "course": course,
            "description": "路径解析失败，请重试",
            "steps": [],
        }
