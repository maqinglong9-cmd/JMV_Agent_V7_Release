"""
测试 SelfEvolutionEngine（AI自我进化引擎）：
  - log_interaction 写入 JSONL 日志
  - read_recent_log 读取最近 N 条
  - analyze_failures 返回正确结构
  - apply_patch 调用元认知写入规则
  - bump_patch_version 正确递增版本号
  - export_latest_json 更新版本号
"""
import sys
import os
import json
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(autouse=True)
def isolate_paths(monkeypatch, tmp_path):
    """重定向所有文件路径到临时目录"""
    import agent.self_evolution_engine as see_mod
    monkeypatch.setattr(see_mod, '_WORKSPACE',      str(tmp_path))
    monkeypatch.setattr(see_mod, '_EVOLUTION_LOG',  str(tmp_path / 'evolution_log.jsonl'))
    monkeypatch.setattr(see_mod, '_DYNAMIC_TOOLS',  str(tmp_path / 'dynamic_tools.py'))
    monkeypatch.setattr(see_mod, '_LATEST_JSON',    str(tmp_path / 'latest.json'))
    monkeypatch.setattr(see_mod, '_VERSION_FILE',   str(tmp_path / 'version.py'))
    yield tmp_path


@pytest.fixture
def engine(tmp_path):
    from agent.self_evolution_engine import SelfEvolutionEngine
    return SelfEvolutionEngine()


class TestLogInteraction:
    def test_creates_log_file(self, engine, tmp_path):
        engine.log_interaction("用户输入", "Agent输出", success=True)
        log_file = tmp_path / 'evolution_log.jsonl'
        assert log_file.exists()

    def test_log_entry_structure(self, engine, tmp_path):
        engine.log_interaction("输入", "输出", success=False, score=0.3, error_msg="错误")
        log_file = tmp_path / 'evolution_log.jsonl'
        with open(log_file, 'r', encoding='utf-8') as f:
            entry = json.loads(f.readline())
        assert entry['input']   == "输入"
        assert entry['success'] is False
        assert entry['score']   == 0.3
        assert "错误" in entry['error']

    def test_multiple_entries(self, engine, tmp_path):
        for i in range(3):
            engine.log_interaction(f"输入{i}", f"输出{i}", success=True)
        entries = engine.read_recent_log(10)
        assert len(entries) == 3


class TestReadRecentLog:
    def test_returns_last_n(self, engine):
        for i in range(10):
            engine.log_interaction(f"input_{i}", f"output_{i}", success=True)
        recent = engine.read_recent_log(5)
        assert len(recent) == 5
        assert recent[-1]['input'] == 'input_9'

    def test_empty_log_returns_empty(self, engine):
        assert engine.read_recent_log() == []


class TestAnalyzeFailures:
    def test_empty_log_returns_summary(self, engine):
        result = engine.analyze_failures()
        assert 'analysis_summary' in result
        assert 'new_rules' in result

    def test_fail_rate_detection(self, engine):
        for _ in range(3):
            engine.log_interaction("失败输入", "", success=False, score=0.0)
        for _ in range(7):
            engine.log_interaction("成功输入", "输出", success=True, score=1.0)
        result = engine.analyze_failures()
        assert isinstance(result['new_rules'], list)

    def test_patch_version_when_high_fail_rate(self, engine):
        for _ in range(5):
            engine.log_interaction("失败", "", success=False, tool_used="CALL_TOOL_X")
        result = engine.analyze_failures()
        # 失败率 100% > 10%，应建议升版
        assert result.get('patch_version') is True


class TestApplyPatch:
    def test_apply_new_rules(self, engine, tmp_path):
        import agent.metacognition_component as mc_mod
        fake_rules = str(tmp_path / "mc_rules.json")
        mc_mod._RULES_FILE = fake_rules

        from agent.metacognition_component import MetacognitionComponent
        mc = MetacognitionComponent()
        engine._metacognition = mc

        patch = {
            "new_rules": [{"trigger": "测试触发", "action": "CALL_TOOL_SEARCH"}],
            "patch_version": False,
        }
        applied = engine.apply_patch(patch)
        assert applied is True
        assert mc.get_rule("测试触发") == "CALL_TOOL_SEARCH"

    def test_empty_patch_not_applied(self, engine):
        result = engine.apply_patch({"new_rules": [], "patch_version": False})
        assert result is False


class TestBumpVersion:
    def test_patch_incremented(self, tmp_path):
        version_file = tmp_path / 'version.py'
        version_file.write_text('__version__ = "1.2.3"\n', encoding='utf-8')

        from agent.self_evolution_engine import SelfEvolutionEngine
        engine = SelfEvolutionEngine()
        new_ver = engine.bump_patch_version()
        assert new_ver == "1.2.4"
        assert '1.2.4' in version_file.read_text(encoding='utf-8')

    def test_missing_version_file_returns_none(self, engine):
        # _VERSION_FILE 已被重定向到不存在的路径
        result = engine.bump_patch_version()
        assert result is None

    def test_export_latest_json(self, tmp_path):
        from agent.self_evolution_engine import SelfEvolutionEngine
        engine = SelfEvolutionEngine()
        engine.export_latest_json("1.3.0")
        latest = tmp_path / 'latest.json'
        assert latest.exists()
        data = json.loads(latest.read_text(encoding='utf-8'))
        assert data['version'] == "1.3.0"


class TestGetStats:
    def test_stats_structure(self, engine):
        stats = engine.get_evolution_stats()
        assert 'total_interactions' in stats
        assert 'failed_interactions' in stats
        assert 'fail_rate' in stats
        assert 'learned_rules' in stats

    def test_stats_reflect_logs(self, engine):
        engine.log_interaction("a", "b", success=True)
        engine.log_interaction("c", "d", success=False)
        stats = engine.get_evolution_stats()
        assert stats['total_interactions'] == 2
        assert stats['failed_interactions'] == 1
