"""Agent 基类"""
from abc import ABC, abstractmethod
from typing import AsyncGenerator
from app.services.llm import deepseek_llm


class BaseAgent(ABC):
    """所有 Agent 的基类"""

    def __init__(self):
        self.llm = deepseek_llm

    @abstractmethod
    async def run(self, input_data: dict) -> dict:
        """执行 Agent 逻辑，返回结果"""
        ...

    async def run_stream(self, input_data: dict) -> AsyncGenerator[dict, None]:
        """流式执行（默认实现：非流式包装为单次 yield）"""
        result = await self.run(input_data)
        yield {"type": "result", "data": result}

    def _build_messages(self, system_prompt: str, user_content: str) -> list[dict]:
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
