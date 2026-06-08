"""DeepSeek LLM 服务封装（OpenAI 兼容格式）"""
import json
from typing import AsyncGenerator
import httpx
from app.core.config import get_settings


class DeepSeekLLM:
    """DeepSeek 大模型 API 封装（兼容 OpenAI 格式）"""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = "https://api.deepseek.com"
        self.api_key = self.settings.DEEPSEEK_API_KEY

    def _build_headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _build_payload(
        self,
        messages: list[dict],
        stream: bool = False,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        return {
            "model": model or self.settings.DEEPSEEK_MODEL,
            "messages": messages,
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

    async def chat(
        self,
        messages: list[dict],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """非流式对话"""
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._build_headers(),
                json=self._build_payload(messages, stream=False, model=model, temperature=temperature, max_tokens=max_tokens),
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def chat_stream(
        self,
        messages: list[dict],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        """流式对话，逐 chunk 返回文本内容"""
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self._build_headers(),
                json=self._build_payload(messages, stream=True, model=model, temperature=temperature, max_tokens=max_tokens),
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload = line[6:]
                    if payload.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload)
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue


# 全局单例
deepseek_llm = DeepSeekLLM()
