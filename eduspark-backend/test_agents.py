"""Agent 效果测试脚本 — 无需启动服务器，直接测试各 Agent"""
import asyncio
import sys
import json
sys.path.insert(0, '.')

# 模拟画像数据
mock_profile = {
    "knowledge_base": {
        "mastered": ["Python编程", "NumPy基础"],
        "weak": ["线性代数", "概率论"],
        "blind_spots": ["深度学习"],
        "score": 0.45
    },
    "cognitive_style": {
        "visual": 0.8,
        "auditory": 0.3,
        "kinesthetic": 0.5,
        "summary": "偏向视觉学习，喜欢看图表和代码演示"
    },
    "learning_ability": {
        "absorption_speed": 0.6,
        "understanding_depth": 0.7,
        "transfer_ability": 0.5,
        "summary": "理解能力不错，但知识迁移需要加强"
    },
    "error_patterns": {
        "types": ["概念混淆", "公式误用"],
        "root_causes": ["基础数学不够扎实", "缺乏练习"],
        "severity": 0.5
    },
    "learning_goals": {
        "short_term": "系统掌握机器学习经典算法",
        "long_term": "转行AI工程师",
        "career": "AI工程师"
    },
    "learning_preferences": {
        "resource_types": ["代码实战", "视频教程"],
        "time_pref": "晚上",
        "difficulty_pref": "中等"
    }
}

# 空画像（新用户）
empty_profile = {}


async def test_profile_agent():
    """测试画像 Agent"""
    from app.agents.profile_agent import ProfileAgent
    agent = ProfileAgent()

    print("=" * 60)
    print("【测试1】ProfileAgent — 新用户首次对话")
    print("=" * 60)

    result = await agent.run({
        "message": "你好，我叫小明，是计算机系大三学生。最近开始学机器学习，但对数学基础（线代、概率）不太有信心。我比较喜欢看视频和动手写代码，目标是以后做AI工程师。",
        "history": [],
        "current_profile": empty_profile,
    })
    print(f"回复: {result['reply'][:200]}...\n")
    if result.get('profile_update'):
        print(f"画像提取: {json.dumps(result['profile_update'], ensure_ascii=False, indent=2)[:500]}")

    print("\n" + "=" * 60)
    print("【测试2】ProfileAgent — 知识问答（不应追问画像）")
    print("=" * 60)

    result2 = await agent.run({
        "message": "什么是梯度下降？怎么理解它？",
        "history": [{"role": "user", "content": "你好"}, {"role": "assistant", "content": "你好！我是你的学习助手"}],
        "current_profile": mock_profile,
    })
    print(f"回复: {result2['reply'][:300]}...\n")

    return True


async def test_tutor_agent():
    """测试辅导 Agent"""
    from app.agents.tutor_agent import TutorAgent
    agent = TutorAgent()

    print("=" * 60)
    print("【测试3】TutorAgent — 概念理解类问题")
    print("=" * 60)

    result = await agent.run({
        "question": "什么是过拟合？和欠拟合有什么区别？",
        "profile": mock_profile,
        "history": [],
    })
    print(f"问题类型: {result['question_type']}")
    print(f"涉及知识点: {result['knowledge_points']}")
    print(f"难度: {result['difficulty']}")
    print(f"回答(前300字): {result['answer'][:300]}...\n")

    print("=" * 60)
    print("【测试4】TutorAgent — 代码实现类问题")
    print("=" * 60)

    result2 = await agent.run({
        "question": "帮我写一个用Python实现梯度下降的代码",
        "profile": mock_profile,
        "history": [],
    })
    print(f"问题类型: {result2['question_type']}")
    print(f"回答(前300字): {result2['answer'][:300]}...\n")

    return True


async def test_resource_agent():
    """测试资源 Agent（以文档生成为例）"""
    from app.agents.resource_agents import DocumentAgent
    agent = DocumentAgent()

    print("=" * 60)
    print("【测试5】DocumentAgent — 个性化文档生成")
    print("=" * 60)

    result = await agent.run({
        "topic": "决策树算法",
        "profile": mock_profile,
        "context": "",
    })
    print(f"标题: {result['title']}")
    print(f"内容(前400字): {result['content'][:400]}...\n")

    return True


async def test_path_agent():
    """测试路径规划 Agent"""
    from app.agents.path_agent import PathAgent
    agent = PathAgent()

    print("=" * 60)
    print("【测试6】PathAgent — 个性化学习路径")
    print("=" * 60)

    result = await agent.run({
        "course": "机器学习",
        "profile": mock_profile,
        "resources": [],
        "request": "我想从零开始系统学习机器学习",
    })
    path = result["path"]
    print(f"路径名称: {path.get('name', 'N/A')}")
    print(f"描述: {path.get('description', 'N/A')}")
    print(f"步骤数: {len(path.get('steps', []))}")
    if path.get('steps'):
        print("前3步:")
        for step in path['steps'][:3]:
            print(f"  {step.get('order', '?')}. {step.get('topic', '?')} — {step.get('description', '')[:80]}")
    print()

    return True


async def test_evaluation_agent():
    """测试评估 Agent"""
    from app.agents.evaluation_agent import EvaluationAgent
    agent = EvaluationAgent()

    print("=" * 60)
    print("【测试7】EvaluationAgent — 学习效果评估")
    print("=" * 60)

    # 构造一些模拟学习记录
    mock_records = [
        {"action": "chat", "knowledge_point": "线性回归", "detail": {"question_type": "concept"}},
        {"action": "chat", "knowledge_point": "决策树", "detail": {"question_type": "code"}},
        {"action": "quiz", "knowledge_point": "线性回归", "detail": {"score": 80, "total": 100}},
        {"action": "quiz", "knowledge_point": "决策树", "detail": {"score": 65, "total": 100}},
        {"action": "view", "knowledge_point": "过拟合", "detail": {"duration_seconds": 300}},
        {"action": "complete", "knowledge_point": "线性回归", "detail": {"topic": "线性回归"}},
    ]

    result = await agent.run({
        "profile": mock_profile,
        "records": mock_records,
        "resources": [
            {"type": "document", "title": "决策树讲解文档"},
            {"type": "code", "title": "线性回归代码案例"},
        ],
        "paths": [],
    })
    report = result.get("report", {})
    print(f"综合评分: {report.get('summary', {}).get('overall_score', 'N/A')}")
    print(f"成长趋势: {report.get('summary', {}).get('growth_trend', 'N/A')}")
    print(f"优势: {json.dumps(report.get('strengths', [])[:2], ensure_ascii=False, indent=2)}")
    print(f"薄弱: {json.dumps(report.get('weaknesses', [])[:2], ensure_ascii=False, indent=2)}")
    print(f"统计数据: {json.dumps(result.get('stats', {}), ensure_ascii=False)}")
    print()

    return True


async def main():
    print("\n" + "=" * 60)
    print("  EduSpark 多智能体系统 — 效果测试")
    print("=" * 60 + "\n")

    try:
        await test_profile_agent()
        print("\n")
    except Exception as e:
        print(f"画像Agent测试失败: {e}\n")

    try:
        await test_tutor_agent()
        print("\n")
    except Exception as e:
        print(f"辅导Agent测试失败: {e}\n")

    try:
        await test_resource_agent()
        print("\n")
    except Exception as e:
        print(f"资源Agent测试失败: {e}\n")

    try:
        await test_path_agent()
        print("\n")
    except Exception as e:
        print(f"路径Agent测试失败: {e}\n")

    try:
        await test_evaluation_agent()
        print("\n")
    except Exception as e:
        print(f"评估Agent测试失败: {e}\n")

    print("=" * 60)
    print("  测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
