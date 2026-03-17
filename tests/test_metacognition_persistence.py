"""
测试 MetacognitionComponent 规则持久化：
  - reflect_and_upgrade 写入规则到磁盘
  - 重新初始化后规则仍然存在
  - evolution_level 也被持久化
  - evaluate_feasibility 正确过滤危险词
  - evaluate_feasibility 使用已习得规则
"""
import sys
import os
import json
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(autouse=True)
def isolate_rules_file(monkeypatch, tmp_path):
    """将 _RULES_FILE 重定向到临时目录，避免污染真实数据"""
    import agent.metacognition_component as mc_mod
    fake_rules = str(tmp_path / "metacognition_rules.json")
    monkeypatch.setattr(mc_mod, '_RULES_FILE', fake_rules)
    yield fake_rules


from agent.metacognition_component import MetacognitionComponent


class TestPersistence:
    def test_reflect_writes_to_disk(self, tmp_path, isolate_rules_file):
        mc = MetacognitionComponent()
        mc.reflect_and_upgrade("未知指令A", "CALL_TOOL_SEARCH")
        assert os.path.exists(isolate_rules_file)
        with open(isolate_rules_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert "未知指令A" in data.get("rules", {})

    def test_rules_survive_restart(self, isolate_rules_file):
        mc1 = MetacognitionComponent()
        mc1.reflect_and_upgrade("飞行任务", "CALL_TOOL_TRANSLATE")

        mc2 = MetacognitionComponent()
        assert "飞行任务" in mc2.learned_rules
        assert mc2.learned_rules["飞行任务"] == "CALL_TOOL_TRANSLATE"

    def test_evolution_level_persisted(self, isolate_rules_file):
        mc1 = MetacognitionComponent()
        mc1.reflect_and_upgrade("规则1", "CALL_TOOL_SEARCH")
        mc1.reflect_and_upgrade("规则2", "CALL_TOOL_SEARCH")
        level = mc1.evolution_level

        mc2 = MetacognitionComponent()
        assert mc2.evolution_level == level

    def test_multiple_rules_persisted(self, isolate_rules_file):
        mc = MetacognitionComponent()
        mc.reflect_and_upgrade("任务A", "CALL_TOOL_SEARCH")
        mc.reflect_and_upgrade("任务B", "CALL_TOOL_CALCULATOR")
        mc.reflect_and_upgrade("任务C", "CALL_TOOL_TRANSLATE")

        mc2 = MetacognitionComponent()
        assert mc2.rule_count() == 3


class TestEvaluateFeasibility:
    def test_dangerous_word_rejected(self):
        mc = MetacognitionComponent()
        feasible, reason = mc.evaluate_feasibility("帮我毁灭世界")
        assert not feasible
        assert "毁灭世界" in reason

    def test_normal_input_accepted(self):
        mc = MetacognitionComponent()
        feasible, reason = mc.evaluate_feasibility("帮我查询天气")
        assert feasible
        assert "可行" in reason

    def test_learned_rule_available(self, isolate_rules_file):
        mc = MetacognitionComponent()
        mc.reflect_and_upgrade("未知指令X", "CALL_TOOL_SEARCH")
        assert mc.get_rule("未知指令X") == "CALL_TOOL_SEARCH"

    def test_rule_count_increments(self):
        mc = MetacognitionComponent()
        initial = mc.rule_count()
        mc.reflect_and_upgrade("新规则A", "CALL_TOOL_SEARCH")
        assert mc.rule_count() == initial + 1
