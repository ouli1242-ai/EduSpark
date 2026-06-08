"""端到端测试 — 通过 HTTP API 测试完整前端→后端→Agent→SSE 流程"""
import asyncio
import httpx
import json
import sys

BASE_URL = "http://localhost:8000"

async def test_health():
    """测试1：健康检查"""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{BASE_URL}/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
        print("  [PASS] 健康检查")

async def test_register():
    """测试2：用户注册"""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": "e2e_test_user", "password": "test123456"},
        )
        data = resp.json()
        assert resp.status_code == 200
        assert "user_id" in data
        print(f"  [PASS] 注册 (user_id={data['user_id']})")

async def test_login():
    """测试3：用户登录"""
    global ACCESS_TOKEN
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "e2e_test_user", "password": "test123456"},
        )
        data = resp.json()
        assert resp.status_code == 200
        assert "access_token" in data
        ACCESS_TOKEN = data["access_token"]
        print(f"  [PASS] 登录 (token={ACCESS_TOKEN[:30]}...)")

async def test_get_profile():
    """测试4：获取画像"""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{BASE_URL}/api/profile",
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
        )
        data = resp.json()
        assert resp.status_code == 200
        assert "knowledge_base" in data
        print(f"  [PASS] 画像查询 (conversation_turns={data.get('conversation_turns', 0)})")

async def test_chat_profile():
    """测试5：SSE对话 — 画像提取流程"""
    async with httpx.AsyncClient(timeout=60) as client:
        events = []
        async with client.stream(
            "POST",
            f"{BASE_URL}/api/chat",
            headers={
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"message": "你好，我是小王，大三学计算机。Python基础不错，但数学不太好。喜欢看视频教程和动手写代码，以后想做AI方向的工作。"},
        ) as resp:
            assert resp.status_code == 200
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    event = json.loads(line[6:])
                    events.append(event)

        event_types = [e["type"] for e in events]
        assert "agent_status" in event_types, "应该有 agent_status 事件"
        assert "chunk" in event_types, "应该有 chunk 事件"
        assert "done" in event_types, "应该有 done 事件"

        # 检查画像是否更新
        profile_events = [e for e in events if e["type"] == "profile_updated"]
        print(f"  [PASS] SSE对话-画像 (收到 {len(events)} 个事件, 画像更新={len(profile_events) > 0})")

async def test_chat_tutor():
    """测试6：SSE对话 — 辅导答疑流程"""
    async with httpx.AsyncClient(timeout=60) as client:
        events = []
        async with client.stream(
            "POST",
            f"{BASE_URL}/api/chat",
            headers={
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"message": "什么是过拟合？怎么解决过拟合问题？"},
        ) as resp:
            assert resp.status_code == 200
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    events.append(json.loads(line[6:]))

        event_types = [e["type"] for e in events]
        chunk_events = [e for e in events if e["type"] == "chunk"]
        tutor_events = [e for e in events if e["type"] == "tutor_analysis"]
        full_answer = "".join(e.get("content", "") for e in chunk_events)

        print(f"  [PASS] SSE对话-辅导 (回答{len(full_answer)}字, 类型分析={'有' if tutor_events else '无'})")

async def test_chat_resource():
    """测试7：SSE对话 — 资源生成流程"""
    async with httpx.AsyncClient(timeout=120) as client:
        events = []
        async with client.stream(
            "POST",
            f"{BASE_URL}/api/chat",
            headers={
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"message": "帮我生成决策树的讲解文档"},
        ) as resp:
            assert resp.status_code == 200
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    events.append(json.loads(line[6:]))

        event_types = [e["type"] for e in events]
        resource_events = [e for e in events if e["type"] == "resource_generated"]
        agent_events = [e for e in events if e["type"] == "agent_status"]

        print(f"  [PASS] SSE对话-资源 (生成 {len(resource_events)} 个资源, Agent状态 {len(agent_events)} 次)")

async def test_chat_path():
    """测试8：SSE对话 — 路径规划流程"""
    async with httpx.AsyncClient(timeout=120) as client:
        events = []
        async with client.stream(
            "POST",
            f"{BASE_URL}/api/chat",
            headers={
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"message": "帮我规划从零开始学机器学习的学习路线"},
        ) as resp:
            assert resp.status_code == 200
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    events.append(json.loads(line[6:]))

        path_events = [e for e in events if e["type"] == "path_generated"]
        chunk_events = [e for e in events if e["type"] == "chunk"]
        full_answer = "".join(e.get("content", "") for e in chunk_events)

        print(f"  [PASS] SSE对话-路径 (路径生成={'有' if path_events else '无'}, 回答{len(full_answer)}字)")

async def test_chat_evaluation():
    """测试9：SSE对话 — 学习评估流程"""
    async with httpx.AsyncClient(timeout=60) as client:
        events = []
        async with client.stream(
            "POST",
            f"{BASE_URL}/api/chat",
            headers={
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"message": "帮我评估一下我的学习进度"},
        ) as resp:
            assert resp.status_code == 200
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    events.append(json.loads(line[6:]))

        eval_events = [e for e in events if e["type"] == "evaluation_report"]
        chunk_events = [e for e in events if e["type"] == "chunk"]
        full_answer = "".join(e.get("content", "") for e in chunk_events)

        print(f"  [PASS] SSE对话-评估 (报告={'有' if eval_events else '无'}, 回答{len(full_answer)}字)")

async def test_get_resources():
    """测试10：资源列表查询"""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{BASE_URL}/api/resources",
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
        )
        data = resp.json()
        assert resp.status_code == 200
        print(f"  [PASS] 资源列表 (共 {len(data) if isinstance(data, list) else data.get('total', '?')} 条)")

async def test_get_paths():
    """测试11：学习路径查询"""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{BASE_URL}/api/path",
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
        )
        data = resp.json()
        assert resp.status_code == 200
        print(f"  [PASS] 路径列表 (共 {len(data) if isinstance(data, list) else data.get('total', '?')} 条)")

async def test_get_evaluation():
    """测试12：评估报告API"""
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(
            f"{BASE_URL}/api/evaluation/stats",
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
        )
        data = resp.json()
        assert resp.status_code == 200
        print(f"  [PASS] 评估统计 (活动{data.get('total_activities', 0)}次)")

async def test_auth_required():
    """测试13：未登录拦截"""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{BASE_URL}/api/profile")
        assert resp.status_code == 401 or resp.status_code == 403
        print(f"  [PASS] 未登录拦截 (HTTP {resp.status_code})")

async def test_swagger():
    """测试14：API文档可访问"""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{BASE_URL}/docs")
        assert resp.status_code == 200
        print(f"  [PASS] Swagger文档 (HTTP 200)")

ACCESS_TOKEN = None

async def main():
    print("\n" + "=" * 60)
    print("  EduSpark 端到端测试")
    print("=" * 60 + "\n")

    tests = [
        ("健康检查", test_health),
        ("注册", test_register),
        ("登录", test_login),
        ("JWT鉴权", test_auth_required),
        ("画像查询", test_get_profile),
        ("SSE对话-画像提取", test_chat_profile),
        ("SSE对话-智能辅导", test_chat_tutor),
        ("SSE对话-资源生成", test_chat_resource),
        ("SSE对话-路径规划", test_chat_path),
        ("SSE对话-学习评估", test_chat_evaluation),
        ("资源列表", test_get_resources),
        ("路径列表", test_get_paths),
        ("评估报告", test_get_evaluation),
        ("Swagger文档", test_swagger),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            await test_fn()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"  [FAIL] {name}: {str(e)[:100]}")

    print(f"\n{'=' * 60}")
    print(f"  结果: {passed} 通过, {failed} 失败, 共 {len(tests)} 项")
    print(f"{'=' * 60}\n")

if __name__ == "__main__":
    asyncio.run(main())
