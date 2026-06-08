"""后端 Agent 单元测试 — 不依赖 API 调用，测试核心逻辑"""
import sys
import json
sys.path.insert(0, '.')


def test_profile_agent_field_mapping():
    """测试画像Agent字段映射"""
    from app.agents.profile_agent import ProfileAgent
    agent = ProfileAgent()

    # 测试1：标准格式直接映射
    raw = {
        "knowledge_base": {"mastered": ["Python"], "weak": ["线代"], "score": 0.6},
        "cognitive_style": {"visual": 0.8, "auditory": 0.3, "kinesthetic": 0.4, "summary": "视觉型"},
        "learning_ability": {"absorption_speed": 0.7, "understanding_depth": 0.8, "transfer_ability": 0.5},
        "error_patterns": {"types": ["概念混淆"], "root_causes": ["基础不牢"], "severity": 0.5},
        "learning_goals": {"short_term": "学ML", "long_term": "转行", "career": "AI"},
        "learning_preferences": {"resource_types": ["视频"], "time_pref": "晚上", "difficulty_pref": "中等"},
    }
    mapped = agent._field_map(raw)
    assert mapped["knowledge_base"] == raw["knowledge_base"], "knowledge_base应直接映射"
    assert mapped["cognitive_style"]["visual"] == 0.8, "visual应保留"
    assert mapped["learning_ability"]["absorption_speed"] == 0.7, "absorption_speed应保留"
    assert mapped["error_patterns"]["types"] == ["概念混淆"], "error_patterns.types应映射"
    print("  [PASS] 标准格式字段映射")

    # 测试2：旧格式兼容（perception/thinking → visual/auditory/kinesthetic）
    old_cs = {"perception": "visual", "thinking": "inductive"}
    mapped_old = agent._field_map({"cognitive_style": old_cs})
    assert mapped_old["cognitive_style"]["visual"] == 0.7, "visual感知应映射为0.7"
    assert "归纳型思维" in mapped_old["cognitive_style"]["summary"], "归纳型思维应在summary中"
    print("  [PASS] 旧格式认知风格兼容")

    # 测试3：文本分数转换
    text_scores = {"absorption_speed": "较快", "understanding_depth": "一般", "transfer_ability": "极强"}
    mapped_text = agent._field_map({"learning_ability": text_scores})
    assert mapped_text["learning_ability"]["absorption_speed"] == 0.7, "较快→0.7"
    assert mapped_text["learning_ability"]["understanding_depth"] == 0.5, "一般→0.5"
    assert mapped_text["learning_ability"]["transfer_ability"] == 0.9, "极强→0.9"
    print("  [PASS] 文本分数转换")

    # 测试4：error_patterns字段兼容（common_types → types, reasons → root_causes）
    old_ep = {"common_types": ["粗心"], "reasons": ["练习少"], "score": 0.4}
    mapped_ep = agent._field_map({"error_patterns": old_ep})
    assert mapped_ep["error_patterns"]["types"] == ["粗心"], "common_types→types"
    assert mapped_ep["error_patterns"]["root_causes"] == ["练习少"], "reasons→root_causes"
    assert mapped_ep["error_patterns"]["severity"] == 0.4, "score→severity"
    print("  [PASS] error_patterns字段兼容")


def test_profile_agent_dimension_merge():
    """测试画像增量合并"""
    from app.agents.profile_agent import ProfileAgent
    agent = ProfileAgent()

    # 测试列表合并去重
    old = {"mastered": ["Python", "NumPy"], "weak": ["线代"], "score": 0.5}
    new = {"mastered": ["Python", "Pandas"], "weak": [], "score": 0.7}
    merged = agent._merge_dimension(old, new)
    assert set(merged["mastered"]) == {"Python", "NumPy", "Pandas"}, "列表应合并去重"
    assert merged["score"] == 0.7, "score应用最新值"
    print("  [PASS] 列表合并去重 + score覆盖")

    # 测试数值加权平均
    old_la = {"absorption_speed": 0.5, "understanding_depth": 0.7, "transfer_ability": 0.3}
    new_la = {"absorption_speed": 0.9, "understanding_depth": 0.9, "transfer_ability": 0.9}
    merged_la = agent._merge_dimension(old_la, new_la)
    assert 0.5 < merged_la["absorption_speed"] < 0.9, "应为加权平均(旧0.7+新0.3)"
    expected = round(0.5 * 0.7 + 0.9 * 0.3, 2)
    assert merged_la["absorption_speed"] == expected, f"应为{expected}"
    print("  [PASS] 数值加权平均(旧0.7+新0.3)")

    # 测试字符串选择更详细的
    old_str = {"summary": "短"}
    new_str = {"summary": "更详细更长的描述"}
    merged_str = agent._merge_dimension(old_str, new_str)
    assert merged_str["summary"] == "更详细更长的描述", "应选更长的字符串"
    print("  [PASS] 字符串长度优先")

    # 测试嵌套字典递归合并
    old_nested = {"a": {"x": 1, "y": 2}}
    new_nested = {"a": {"x": 3, "z": 4}}
    merged_nested = agent._merge_dimension(old_nested, new_nested)
    assert merged_nested["a"]["x"] == round(1 * 0.7 + 3 * 0.3, 2), "嵌套数值加权"
    assert merged_nested["a"]["y"] == 2, "旧值保留"
    assert merged_nested["a"]["z"] == 4, "新值添加"
    print("  [PASS] 嵌套字典递归合并")

    # 测试空值处理
    merged_empty = agent._merge_dimension(None, {"x": 1})
    assert merged_empty == {"x": 1}, "旧值为None应全用新的"
    merged_keep = agent._merge_dimension({"x": 1}, None)
    assert merged_keep == {"x": 1}, "新值为None应保留旧的"
    print("  [PASS] 空值处理")


def test_profile_agent_dimension_count():
    """测试画像维度完成度统计"""
    from app.agents.profile_agent import ProfileAgent
    agent = ProfileAgent()

    empty = {}
    assert agent._count_completed_dimensions(empty) == 0, "空画像=0维"
    print("  [PASS] 空画像→0维")

    partial = {
        "knowledge_base": {"mastered": ["Python"]},
        "cognitive_style": {"summary": "视觉型"},
        "learning_ability": {},
        "error_patterns": {},
        "learning_goals": {},
        "learning_preferences": {},
    }
    assert agent._count_completed_dimensions(partial) == 2, "2个有实际信息的维度"
    print("  [PASS] 部分画像→精确计数")


def test_evaluation_agent_stats():
    """测试评估Agent统计计算"""
    from app.agents.evaluation_agent import EvaluationAgent
    agent = EvaluationAgent()

    # 空记录
    stats = agent._calculate_stats([], {})
    assert stats["total_activities"] == 0
    print("  [PASS] 空记录统计")

    # 模拟记录
    records = [
        {"action": "quiz", "knowledge_point": "线性回归", "detail": {"score": 80, "total": 100}},
        {"action": "quiz", "knowledge_point": "决策树", "detail": {"score": 90, "total": 100}},
        {"action": "chat", "knowledge_point": "过拟合", "detail": {}},
        {"action": "view", "knowledge_point": "SVM", "detail": {"duration_seconds": 300}},
    ]
    stats = agent._calculate_stats(records, {})
    assert stats["total_activities"] == 4
    assert stats["quiz_attempts"] == 2
    assert stats["resources_accessed"] == 1
    assert stats["conversations"] == 1
    assert stats["average_quiz_score"] == 85.0
    assert stats["topics_count"] == 4
    print("  [PASS] 模拟记录统计")


def test_path_agent_gap_analysis():
    """测试路径Agent画像缺口分析"""
    from app.agents.path_agent import PathAgent
    agent = PathAgent()

    profile = {
        "knowledge_base": {
            "weak": ["线性代数"],
            "blind_spots": ["深度学习"],
            "mastered": ["Python编程"],
        }
    }
    gaps = agent._analyze_profile_gaps(profile)
    assert "Python编程" in gaps["mastered"]
    assert "线性代数" in gaps["weak"]
    assert "深度学习" in gaps["blind_spots"]
    assert len(gaps["priority_topics"]) > 0, "应有优先强化的知识点"
    print(f"  [PASS] 缺口分析 (优先强化: {gaps['priority_topics'][:3]})")


def test_path_agent_knowledge_graph():
    """测试知识图谱完整性"""
    from app.agents.path_agent import ML_KNOWLEDGE_GRAPH
    topics = list(ML_KNOWLEDGE_GRAPH.keys())
    assert len(topics) >= 15, "至少15个知识点"

    # 检查每个知识点都有必要字段
    for topic, info in ML_KNOWLEDGE_GRAPH.items():
        assert "prerequisites" in info, f"{topic}缺少prerequisites"
        assert "difficulty" in info, f"{topic}缺少difficulty"
        assert "category" in info, f"{topic}缺少category"
        assert "description" in info, f"{topic}缺少description"
        assert 1 <= info["difficulty"] <= 5, f"{topic}难度应在1-5之间"
    print(f"  [PASS] 知识图谱 ({len(topics)}个知识点, 全部字段完整)")

    # 检查前置依赖的有效性
    for topic, info in ML_KNOWLEDGE_GRAPH.items():
        for prereq in info["prerequisites"]:
            assert prereq in topics, f"{topic}的前置依赖'{prereq}'不在知识图谱中"
    print("  [PASS] 前置依赖有效性验证")


def test_resource_profile_context():
    """测试资源Agent画像上下文构建"""
    from app.agents.resource_agents import _build_profile_context

    # 空画像
    result = _build_profile_context({})
    assert "暂无信息" in result
    print("  [PASS] 空画像→默认提示")

    # 完整画像
    full_profile = {
        "knowledge_base": {
            "mastered": ["Python", "NumPy"],
            "weak": ["线代"],
            "blind_spots": ["深度学习"],
            "score": 0.5,
        },
        "cognitive_style": {
            "visual": 0.8,
            "auditory": 0.3,
            "kinesthetic": 0.5,
            "summary": "视觉型学习者",
        },
        "learning_ability": {
            "absorption_speed": 0.6,
            "understanding_depth": 0.7,
            "transfer_ability": 0.5,
        },
        "learning_goals": {
            "short_term": "掌握ML",
            "career": "AI工程师",
        },
        "learning_preferences": {
            "difficulty_pref": "中等",
            "resource_types": ["视频", "代码"],
        },
        "error_patterns": {
            "types": ["概念混淆"],
            "root_causes": ["基础不牢"],
        },
    }
    result = _build_profile_context(full_profile)
    assert "知识基础" in result
    assert "认知风格" in result
    assert "学习能力" in result
    assert "学习目标" in result
    assert "学习偏好" in result
    assert "易错点" in result
    print("  [PASS] 完整6维画像→全维度上下文")


def test_safe_json_parse():
    """测试JSON安全解析"""
    from app.agents.resource_agents import _safe_json_parse

    # 标准JSON
    result = _safe_json_parse('{"key": "value"}')
    assert result == {"key": "value"}
    print("  [PASS] 标准JSON解析")

    # 带代码块的JSON
    result = _safe_json_parse('```json\n{"key": "value"}\n```')
    assert result == {"key": "value"}
    print("  [PASS] 代码块清理解析")

    # 带空格的代码块
    result = _safe_json_parse('```json  \n{"key": "value"}\n```  ')
    assert result == {"key": "value"}
    print("  [PASS] 带空格代码块解析")

    # 无效JSON
    result = _safe_json_parse("这不是JSON")
    assert result is None
    print("  [PASS] 无效JSON返回None")

    # 数组格式
    result = _safe_json_parse('[{"a": 1}, {"b": 2}]', expect_array=True)
    assert result == [{"a": 1}, {"b": 2}]
    print("  [PASS] 数组格式解析")

    # 内嵌在文本中的JSON
    result = _safe_json_parse("这里有一些文字 {\"key\": \"value\"} 还有一些文字")
    assert result == {"key": "value"}
    print("  [PASS] 文本内嵌JSON提取")


def main():
    print("\n" + "=" * 60)
    print("  EduSpark Agent 单元测试")
    print("=" * 60 + "\n")

    tests = [
        ("画像字段映射", test_profile_agent_field_mapping),
        ("画像增量合并", test_profile_agent_dimension_merge),
        ("画像维度计数", test_profile_agent_dimension_count),
        ("评估统计计算", test_evaluation_agent_stats),
        ("路径缺口分析", test_path_agent_gap_analysis),
        ("知识图谱完整性", test_path_agent_knowledge_graph),
        ("画像上下文构建", test_resource_profile_context),
        ("JSON安全解析", test_safe_json_parse),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            failed += 1
            import traceback
            print(f"  [FAIL] {name}: {e}")
            traceback.print_exc()

    print(f"\n{'=' * 60}")
    print(f"  结果: {passed} 通过, {failed} 失败, 共 {len(tests)} 项")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
