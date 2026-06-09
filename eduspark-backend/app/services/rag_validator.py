"""RAG 内容校验模块 — 对生成内容进行知识库校验，输出置信度"""
import json
from dataclasses import dataclass, field
from app.services.llm import deepseek_llm


@dataclass
class ValidationResult:
    """校验结果"""
    confidence: str = "low"  # high / medium / low
    total_claims: int = 0
    supported_claims: int = 0
    unsupported_claims: list = field(default_factory=list)
    details: list = field(default_factory=list)


class RAGValidator:
    """RAG 内容校验器"""

    def __init__(self, chroma_client=None):
        """
        Args:
            chroma_client: ChromaDB Collection 实例（可选）
        """
        self.chroma_client = chroma_client  # 可以是 Collection 或 Client

    async def validate(self, content: str, knowledge_points: list[str]) -> ValidationResult:
        """
        对生成内容进行知识库校验

        Args:
            content: 生成的内容文本
            knowledge_points: 关联的知识点列表

        Returns:
            ValidationResult: 校验结果
        """
        result = ValidationResult()

        if not content or not content.strip():
            return result

        # 1. 提取原子声明
        claims = await self._extract_claims(content)
        result.total_claims = len(claims)

        if not claims:
            result.confidence = "medium"
            return result

        # 2. 对每条声明进行校验
        for claim in claims:
            is_supported = await self._verify_claim(claim, knowledge_points)
            detail = {
                "claim": claim,
                "supported": is_supported,
            }
            result.details.append(detail)

            if is_supported:
                result.supported_claims += 1
            else:
                result.unsupported_claims.append(claim)

        # 3. 计算置信度
        if result.total_claims > 0:
            support_ratio = result.supported_claims / result.total_claims
            if support_ratio > 0.8:
                result.confidence = "high"
            elif support_ratio > 0.5:
                result.confidence = "medium"
            else:
                result.confidence = "low"

        return result

    async def _extract_claims(self, content: str) -> list[str]:
        """从内容中提取原子声明"""
        prompt = """将以下内容拆分为可独立验证的原子声明，每条一行。
只提取事实性声明，忽略过渡句和修辞表达。
如果内容很短或没有可拆分的声明，返回"无"。

内容：
{content}"""

        messages = [
            {"role": "system", "content": "你是一个内容分析专家，擅长提取文本中的关键声明。"},
            {"role": "user", "content": prompt.format(content=content[:2000])},
        ]

        result = await deepseek_llm.chat(messages)
        result = result.strip()

        if not result or result == "无":
            return []

        # 按行分割
        claims = [line.strip() for line in result.split("\n") if line.strip()]
        return claims[:10]  # 最多 10 条

    async def _verify_claim(self, claim: str, knowledge_points: list[str]) -> bool:
        """验证单条声明是否被知识库支持"""
        # 如果没有 ChromaDB，使用 LLM 判断
        if not self.chroma_client:
            return await self._verify_with_llm(claim, knowledge_points)

        # 使用 ChromaDB 向量检索
        try:
            # 兼容 Collection 和 Client 两种类型
            collection = self.chroma_client
            if hasattr(collection, 'get_or_create_collection'):
                collection = collection.get_or_create_collection("knowledge_base")

            results = collection.query(
                query_texts=[claim],
                n_results=3,
            )

            if results and results.get("distances") and results["distances"][0]:
                # 距离越小越相似
                min_distance = min(results["distances"][0])
                return min_distance < 1.0  # ChromaDB 余弦距离阈值

            return False

        except Exception as e:
            # 降级到 LLM 判断
            return await self._verify_with_llm(claim, knowledge_points)

    async def _verify_with_llm(self, claim: str, knowledge_points: list[str]) -> bool:
        """使用 LLM 判断声明是否合理"""
        prompt = """判断以下声明是否与给定的知识点一致。
如果声明正确或基本正确，返回"正确"。
如果声明有误或无法确认，返回"错误"。
只返回"正确"或"错误"，不要其他内容。

知识点：{knowledge_points}
声明：{claim}"""

        messages = [
            {"role": "system", "content": "你是一个知识校验专家。"},
            {"role": "user", "content": prompt.format(
                knowledge_points="、".join(knowledge_points) if knowledge_points else "未指定",
                claim=claim,
            )},
        ]

        result = await deepseek_llm.chat(messages)
        return "正确" in result


# 全局实例（无 ChromaDB 客户端，使用 LLM 校验）
rag_validator = RAGValidator()
