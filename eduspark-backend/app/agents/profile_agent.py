"""画像 Agent — 对话式学习画像构建"""
import json
import re
from app.agents.base import BaseAgent

SYSTEM_PROMPT = """你是一个学习画像分析专家。你的任务是通过与学生的自然对话，构建完整的6维度学习画像。

## 6维度画像说明

1. **知识基础（knowledge_base）**：学生已掌握的知识点、薄弱知识点、知识盲区、整体水平评分
   - JSON结构: {"mastered": ["Python编程", "数据结构"], "weak": ["线性代数"], "blind_spots": ["深度学习"], "score": 0.0-1.0}

2. **认知风格（cognitive_style）**：学习风格类型及详细描述
   - JSON结构: {"visual": 0.0-1.0, "auditory": 0.0-1.0, "kinesthetic": 0.0-1.0, "summary": "偏向视觉学习，喜欢看图表和演示"}
   - visual=视觉型(看文字/图表/视频)，auditory=听觉型(听讲解/讨论)，kinesthetic=动觉型(动手做/实操)
   - 三个维度各自独立评分，互不影响

3. **学习能力（learning_ability）**：知识吸收速度、理解深度、知识迁移能力
   - JSON结构: {"absorption_speed": 0.0-1.0, "understanding_depth": 0.0-1.0, "transfer_ability": 0.0-1.0, "summary": "吸收速度中等，但理解深刻，能举一反三"}
   - 0.0 = 极差，0.5 = 中等，1.0 = 极强

4. **易错点模式（error_patterns）**：常见错误类型及其根本原因
   - JSON结构: {"types": ["概念混淆", "计算粗心"], "root_causes": ["对核心定义理解不透彻", "练习量不足"], "severity": 0.0-1.0}
   - types=错误的表层表现，root_causes=深层原因，severity=严重程度

5. **学习目标（learning_goals）**：短期目标、长期目标、职业规划
   - JSON结构: {"short_term": "系统学习机器学习算法", "long_term": "找到AI相关工作", "career": "AI工程师"}

6. **学习偏好（learning_preferences）**：资源类型偏好、学习时段、难度偏好
   - JSON结构: {"resource_types": ["视频教程", "代码实战"], "time_pref": "晚上", "difficulty_pref": "中等"}

## 核心策略

### 1. 对话模式判断
- **知识问答模式**：学生问纯知识性问题（"什么是X""X和Y有什么区别""怎么实现Z"），正常回答，**禁止追问画像问题**。只从回答中被动提取可推断的信息。
- **画像探索模式**：学生做自我介绍、聊自己的情况/目标/困难，可以在回答末尾加一句自然的追问。

### 2. 分阶段追问规则（仅限画像探索模式）

根据当前画像各维度的完整度（已完成维度数）决定追问策略：

**初始阶段（0-2个维度完成）**：
- 优先补全：knowledge_base → learning_goals → cognitive_style
- 每次追问一个维度
- 追问要自然："你是刚开始学机器学习吗？之前有编程基础吗？"

**深化阶段（3-4个维度完成）**：
- 优先补全：error_patterns → learning_preferences → learning_ability
- 针对已有维度的薄弱项追问细节
- 追问要有针对性："你刚才提到线性代数比较弱，具体是矩阵运算还是特征值那块觉得难？"

**精细化阶段（5个维度完成）**：
- 基本不追问
- 只从对话中被动提取更新
- 对已有多项做微调

### 3. 通用追问规则
- 每次最多追问一个维度
- 追问不能超过一句话
- 已获取完整信息的维度不要再问
- 追问必须自然融入对话，不能生硬

### 4. 主动推断
从学生的话里推断信息填入。例如：
- "线性代数学得不好" → knowledge_base.weak 添加"线性代数"
- "喜欢看视频" → learning_preferences.resource_types 添加"视频教程"
- "我比较喜欢先看别人怎么做，再自己动手" → cognitive_style 中 visual 偏高
- "看完就忘" → learning_ability.absorption_speed 偏低

### 5. 持续更新
每次对话都要输出完整的 [PROFILE_UPDATE]，已有信息保留，新信息追加/更新。
注意：knowledge_base 的 score 应根据 mastered/weak/blind_spots 综合估算。
注意：不要无依据地随意修改已有分数，只有在新信息足够确定时才调整。

## 输出格式

先正常回复学生。

[PROFILE_UPDATE]
{"knowledge_base": {...}, "cognitive_style": {...}, "learning_ability": {...}, "error_patterns": {...}, "learning_goals": {...}, "learning_preferences": {...}}
[/PROFILE_UPDATE]

如果本轮没有任何新信息可更新，可以省略 [PROFILE_UPDATE] 标签。"""


class ProfileAgent(BaseAgent):
    """画像 Agent：从对话中提取学生学习画像"""

    DIMENSION_KEYS = [
        "knowledge_base", "cognitive_style", "learning_ability",
        "error_patterns", "learning_goals", "learning_preferences",
    ]

    DIMENSION_LABELS = {
        "knowledge_base": "知识基础",
        "cognitive_style": "认知风格",
        "learning_ability": "学习能力",
        "error_patterns": "易错点模式",
        "learning_goals": "学习目标",
        "learning_preferences": "学习偏好",
    }

    # 文本 → 分数映射（兼容旧版 LLM 文本输出）
    TEXT_TO_SCORE = {
        "极慢": 0.1, "较慢": 0.3, "一般": 0.5, "较快": 0.7, "极快": 0.9,
        "很弱": 0.1, "较弱": 0.3, "中等": 0.5, "较强": 0.7, "极强": 0.9,
        "很差": 0.1, "较差": 0.3, "较好": 0.7, "极好": 0.9,
        "深刻": 0.8, "透彻": 0.9, "表面": 0.3, "粗浅": 0.2,
        "强": 0.7, "弱": 0.3, "好": 0.7, "差": 0.3, "快": 0.7, "慢": 0.3,
    }

    def _get_dimension_summary(self, profile: dict) -> str:
        """生成画像维度摘要（给 LLM 看）"""
        lines = []
        for key in self.DIMENSION_KEYS:
            label = self.DIMENSION_LABELS[key]
            val = profile.get(key, {})
            has_info = bool(
                val and isinstance(val, dict) and any(
                    v is not None and v != "" and v != [] and v != {}
                    for v in val.values()
                )
            )
            status = "已有信息" if has_info else "待补充"
            lines.append(f"  - {key} ({label}): {status}")
        return "\n".join(lines)

    def _count_completed_dimensions(self, profile: dict) -> int:
        """统计已有信息维度数"""
        count = 0
        for key in self.DIMENSION_KEYS:
            val = profile.get(key, {})
            if val and isinstance(val, dict) and any(
                v is not None and v != "" and v != [] and v != {}
                for v in val.values()
            ):
                count += 1
        return count

    def _get_stage_guidance(self, completed: int) -> str:
        """根据已完成维度数生成阶段提示"""
        if completed <= 2:
            return (
                "【当前阶段：初始探索】\n"
                "优先补充缺失维度，尤其是：知识基础、学习目标、认知风格。\n"
                "如果正在聊相关话题，可以在回复末尾加一句自然的追问。"
            )
        elif completed <= 4:
            return (
                "【当前阶段：深度挖掘】\n"
                "重点补充：易错点模式、学习偏好、学习能力的细节。\n"
                "针对已有维度的薄弱项可追问细节。"
            )
        else:
            return (
                "【当前阶段：精细调优】\n"
                "基本不追问，仅从对话中被动提取。\n"
                "如果发现已有信息不准确，才做修正。"
            )

    def _field_map(self, raw_update: dict) -> dict:
        """字段映射：LLM 输出 → 数据库字段名"""
        mapped = {}

        # 1. knowledge_base — 直接映射
        if "knowledge_base" in raw_update:
            mapped["knowledge_base"] = raw_update["knowledge_base"]

        # 2. cognitive_style — 兼容 perception/thinking → visual/auditory/kinesthetic/summary
        if "cognitive_style" in raw_update:
            cs = raw_update["cognitive_style"]
            new_cs = {}
            if any(k in cs for k in ("visual", "auditory", "kinesthetic", "summary")):
                for k in ("visual", "auditory", "kinesthetic", "summary"):
                    if k in cs:
                        v = cs[k]
                        if k == "summary":
                            new_cs[k] = v if isinstance(v, str) else str(v)
                        elif isinstance(v, str):
                            # 文本转分数
                            new_cs[k] = self.TEXT_TO_SCORE.get(v, 0.5)
                        else:
                            new_cs[k] = min(1.0, max(0.0, float(v)))
            else:
                # 旧格式：perception + thinking → summary
                parts = []
                percep = cs.get("perception", "")
                if percep == "visual":
                    new_cs["visual"] = 0.7
                    parts.append("偏向视觉学习")
                elif percep == "auditory":
                    new_cs["auditory"] = 0.7
                    parts.append("偏向听觉学习")
                elif percep == "kinesthetic":
                    new_cs["kinesthetic"] = 0.7
                    parts.append("偏向动觉学习")
                else:
                    new_cs["visual"] = 0.5
                    parts.append("学习风格待明确")
                think = cs.get("thinking", "")
                if think == "inductive":
                    parts.append("归纳型思维")
                elif think == "deductive":
                    parts.append("演绎型思维")
                elif think == "analogical":
                    parts.append("类比型思维")
                extra_summary = cs.get("summary", "")
                if extra_summary:
                    parts.append(extra_summary)
                new_cs["summary"] = "，".join(parts)
            mapped["cognitive_style"] = new_cs

        # 3. learning_ability — 文本转分数
        if "learning_ability" in raw_update:
            la = raw_update["learning_ability"]
            new_la = {}
            for key in ("absorption_speed", "understanding_depth", "transfer_ability"):
                val = la.get(key)
                if val is None:
                    continue
                if isinstance(val, (int, float)):
                    new_la[key] = min(1.0, max(0.0, float(val)))
                elif isinstance(val, str):
                    score = 0.5
                    for kw, s in self.TEXT_TO_SCORE.items():
                        if kw in val:
                            score = s
                            break
                    new_la[key] = score
            if la.get("summary"):
                new_la["summary"] = la["summary"]
            mapped["learning_ability"] = new_la

        # 4. error_patterns — common_types/reasons → types/root_causes
        if "error_patterns" in raw_update:
            ep = raw_update["error_patterns"]
            new_ep = {}
            if "types" in ep:
                new_ep["types"] = ep["types"]
            elif "common_types" in ep:
                new_ep["types"] = ep["common_types"]
            if "root_causes" in ep:
                new_ep["root_causes"] = ep["root_causes"]
            elif "reasons" in ep:
                new_ep["root_causes"] = ep["reasons"]
            if "severity" in ep:
                new_ep["severity"] = ep["severity"]
            elif "score" in ep:
                new_ep["severity"] = ep["score"]
            mapped["error_patterns"] = new_ep

        # 5. learning_goals — 直接映射
        if "learning_goals" in raw_update:
            mapped["learning_goals"] = raw_update["learning_goals"]

        # 6. learning_preferences — 对齐字段名
        if "learning_preferences" in raw_update:
            lp = raw_update["learning_preferences"]
            new_lp = {}
            if "resource_types" in lp:
                new_lp["resource_types"] = lp["resource_types"]
            if "time_pref" in lp:
                new_lp["time_pref"] = lp["time_pref"]
            elif "time_preference" in lp:
                new_lp["time_pref"] = lp["time_preference"]
            if "difficulty_pref" in lp:
                new_lp["difficulty_pref"] = lp["difficulty_pref"]
            elif "difficulty_preference" in lp:
                new_lp["difficulty_pref"] = lp["difficulty_preference"]
            mapped["learning_preferences"] = new_lp

        return mapped

    def _merge_dimension(self, old: dict, new: dict) -> dict:
        """智能合并新旧维度数据，避免简单覆盖"""
        if not old:
            return new
        if not new:
            return old

        merged = dict(old)

        for key, new_val in new.items():
            old_val = old.get(key)

            if old_val is None:
                merged[key] = new_val
                continue

            # 列表 → 合并去重
            if isinstance(new_val, list) and isinstance(old_val, list):
                seen = set(str(x) for x in old_val)
                combined = list(old_val)
                for x in new_val:
                    if str(x) not in seen:
                        combined.append(x)
                        seen.add(str(x))
                merged[key] = combined

            # 数值 → 加权平均（新 0.3, 旧 0.7），但 score/severity 用最新
            elif isinstance(new_val, (int, float)) and isinstance(old_val, (int, float)):
                if key in ("score", "severity"):
                    merged[key] = new_val
                else:
                    merged[key] = round(old_val * 0.7 + new_val * 0.3, 2)

            # 字符串 → 选择更详细的
            elif isinstance(new_val, str) and isinstance(old_val, str):
                if len(new_val) > len(old_val):
                    merged[key] = new_val

            # 字典 → 递归合并
            elif isinstance(new_val, dict) and isinstance(old_val, dict):
                merged[key] = self._merge_dimension(old_val, new_val)

            else:
                merged[key] = new_val

        return merged

    async def run(self, input_data: dict) -> dict:
        message = input_data["message"]
        history = input_data.get("history", [])
        current_profile = input_data.get("current_profile", {})

        # 构建上下文
        context_parts = []

        completed = self._count_completed_dimensions(current_profile)
        context_parts.append(f"维度完成度：{completed}/6")
        context_parts.append(self._get_dimension_summary(current_profile))
        context_parts.append(self._get_stage_guidance(completed))

        if current_profile:
            context_parts.append(
                f"当前画像完整数据：\n{json.dumps(current_profile, ensure_ascii=False, indent=2)}"
            )

        context_parts.append(f"学生最新消息：{message}")
        user_content = "\n\n".join(context_parts)

        messages = self._build_messages(SYSTEM_PROMPT, user_content)
        for h in history[-10:]:
            messages.insert(-1, h)

        response = await self.llm.chat(
            messages,
            temperature=0.7,
            max_tokens=4096,
        )

        # 解析匹配
        reply = response
        raw_profile_update = {}

        pattern = r'\[PROFILE_UPDATE\](.*?)\[/PROFILE_UPDATE\]'
        match = re.search(pattern, response, re.DOTALL)
        if match:
            try:
                raw_update = json.loads(match.group(1).strip())
                mapped_update = self._field_map(raw_update)
                # 增量合并
                for dim_key in self.DIMENSION_KEYS:
                    if dim_key in mapped_update and mapped_update[dim_key]:
                        old_dim = current_profile.get(dim_key, {})
                        new_dim = self._merge_dimension(old_dim, mapped_update[dim_key])
                        if new_dim:
                            raw_profile_update[dim_key] = new_dim
                reply = response[:match.start()].strip()
            except json.JSONDecodeError:
                pass

        return {
            "reply": reply,
            "profile_update": raw_profile_update or None,
            "full_response": response,
        }

    async def run_stream(self, input_data: dict):
        result = await self.run(input_data)
        content = result["reply"]
        chunk_size = 20
        for i in range(0, len(content), chunk_size):
            yield {"type": "chunk", "content": content[i:i + chunk_size]}

        if result["profile_update"]:
            yield {"type": "profile_update", "data": result["profile_update"]}

        yield {"type": "done"}
