"""AgentRouter 单元测试"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adapter.agent_router import AgentRouter, AGENT_MODES


class TestAgentModes:
    def test_all_modes_defined(self):
        assert set(AGENT_MODES.keys()) == {"basic", "ultimate", "cyborg", "cns"}

    def test_mode_labels_are_nonempty(self):
        for key, label in AGENT_MODES.items():
            assert label, f"Mode '{key}' has empty label"


class TestAgentRouterInit:
    def test_default_mode_is_basic(self):
        router = AgentRouter()
        assert router.mode == "basic"

    def test_custom_mode_on_init(self):
        router = AgentRouter(mode="cns")
        assert router.mode == "cns"

    def test_mode_label(self):
        router = AgentRouter(mode="basic")
        assert router.mode_label == "基础脑区"

    def test_unknown_mode_label_falls_back_to_key(self):
        router = AgentRouter(mode="basic")
        router._mode = "nonexistent"
        assert router.mode_label == "nonexistent"


class TestAgentRouterSetMode:
    def test_set_mode_valid(self):
        router = AgentRouter()
        for mode in AGENT_MODES:
            router.set_mode(mode)
            assert router.mode == mode

    def test_set_mode_invalid_raises(self):
        router = AgentRouter()
        with pytest.raises(ValueError, match="不支持的模式"):
            router.set_mode("unknown_mode")


class TestAgentRouterBasicRun:
    """仅测试 basic 模式（无需重型 Agent 依赖）"""

    def test_run_basic_returns_list(self):
        router = AgentRouter(mode="basic")
        result = router.run("前方红灯", "车喇叭", "方向盘")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_run_basic_nonempty_strings(self):
        router = AgentRouter(mode="basic")
        result = router.run("视觉输入", "听觉输入", "触觉输入")
        for item in result:
            assert isinstance(item, str)
            assert item.strip()

    def test_lazy_loading_creates_agent_once(self):
        router = AgentRouter(mode="basic")
        assert "basic" not in router._agents
        router.run("v", "a", "t")
        assert "basic" in router._agents
        agent_ref = router._agents["basic"]
        router.run("v2", "a2", "t2")
        # 同一对象，未重新创建
        assert router._agents["basic"] is agent_ref

    def test_mode_switch_does_not_lose_previous_agent(self):
        router = AgentRouter(mode="basic")
        router.run("v", "a", "t")  # 触发 basic 实例化
        basic_agent = router._agents["basic"]
        router.set_mode("cns")
        router.set_mode("basic")
        # basic 模式下再次运行，对象仍是同一个
        router.run("v2", "a2", "t2")
        assert router._agents["basic"] is basic_agent


class TestRunAdapterError:
    """模拟 Agent 内部抛异常时，Router 应优雅降级"""

    def test_basic_error_returns_error_string(self):
        router = AgentRouter(mode="basic")

        class FakeBadAgent:
            def perceive_and_react(self, *a):
                raise RuntimeError("模拟故障")

        router._agents["basic"] = FakeBadAgent()
        result = router.run("v", "a", "t")
        assert isinstance(result, list)
        assert len(result) == 1
        assert "异常" in result[0] or "模拟故障" in result[0]

    def test_ultimate_error_returns_error_string(self):
        router = AgentRouter(mode="ultimate")

        class FakeBadAgent:
            def process_input(self, *a):
                raise RuntimeError("ultimate 故障")
            emotion = type('E', (), {'current_mood': '平静'})()

        router._agents["ultimate"] = FakeBadAgent()
        result = router.run("v", "a", "t")
        assert any("故障" in s or "异常" in s for s in result)

    def test_cyborg_error_returns_error_string(self):
        router = AgentRouter(mode="cyborg")

        class FakeBadAgent:
            def perceive_and_act(self, **kw):
                raise RuntimeError("cyborg 故障")

        router._agents["cyborg"] = FakeBadAgent()
        result = router.run("v", "a", "t")
        assert any("故障" in s or "异常" in s for s in result)
