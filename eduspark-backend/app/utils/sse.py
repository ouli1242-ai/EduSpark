"""SSE (Server-Sent Events) 工具"""
import json
from typing import AsyncGenerator


async def sse_generator(generator: AsyncGenerator[dict, None]) -> AsyncGenerator[str, None]:
    """将异步数据生成器转为 SSE 格式"""
    async for chunk in generator:
        yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"


def sse_event(data: dict) -> str:
    """构造单条 SSE 消息"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
