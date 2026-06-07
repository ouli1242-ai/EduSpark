"""讯飞星火 LLM 服务封装（HTTP Open API）"""
import json
import time
import hashlib
import hmac
import base64
from datetime import datetime
from urllib.parse import urlencode, urlparse
import httpx
from typing import AsyncGenerator
from app.core.config import get_settings

# 模型映射
MODEL_MAP = {
    "spark-max": "generalv3.5",       # Spark Max
    "spark-pro": "generalv3",         # Spark Pro
    "spark-pro-128k": "pro-128k",     # Spark Pro-128K
    "spark-max-32k": "max-32k",       # Spark Max-32K
    "spark-lite": "general",          # Spark Lite
}


class SparkLLM:
    """讯飞星火大模型 HTTP Open API 封装"""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = "https://spark-api-open.xf-yun.com/v1/chat/completions"
        self.default_model = "generalv3.5"  # Spark Max

    def _get_auth_url(self) -> str:
        """生成带鉴权的请求 URL（讯飞 HMAC 签名方式）"""
        api_key = self.settings.SPARK_API_KEY
        api_secret = self.settings.SPARK_API_SECRET
        app_id = self.settings.SPARK_APP_ID

        # 拼接鉴权参数
        now = datetime.utcnow()
        date = now.strftime('%a, %d %b %Y %H:%M:%S GMT')

        # 构造签名原文
        parsed = urlparse(self.base_url)
        host = parsed.hostname
        path = parsed.path
        signature_origin = f"host: {host}\ndate: {date}\nPOST {path} HTTP/1.1"

        # HMAC-SHA256 签名
        signature_sha = hmac.new(
            api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        signature = base64.b64encode(signature_sha).decode('utf-8')

        # 构造 Authorization
        authorization_origin = f'api_key="{api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')

        # 拼接最终 URL
        params = {
            "authorization": authorization,
            "date": date,
            "host": host,
        }
        return f"{self.base_url}?{urlencode(params)}"

    def _build_headers(self):
        return {
            "Content-Type": "application/json",
        }

    def _build_payload(self, messages: list[dict], stream: bool = False, model: str = None):
        return {
            "model": model or self.default_model,
            "messages": messages,
            "stream": stream,
            "temperature": 0.7,
            "max_tokens": 2048,
        }

    async def chat(self, messages: list[dict], model: str = None) -> str:
        """非流式对话"""
        url = self._get_auth_url()
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                url,
                headers=self._build_headers(),
                json=self._build_payload(messages, stream=False, model=model),
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def chat_stream(self, messages: list[dict], model: str = None) -> AsyncGenerator[str, None]:
        """流式对话，逐 chunk 返回"""
        url = self._get_auth_url()
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                url,
                headers=self._build_headers(),
                json=self._build_payload(messages, stream=True, model=model),
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
spark_llm = SparkLLM()
