"""
测试 CentralNervousSystem 的神经路由自愈机制（BUG 2 验证）。
核心逻辑：
  - 首次调用因 neural_routing_ok=False 返回 FAILED_ROUTING（设计行为）
  - repair_neural_routing() 修复后第二次调用返回 COORDINATION_SUCCESS
  - COORDINATION_SUCCESS 时追踪路径必须包含三个关键标签
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent.central_nervous_system import CentralNervousSystem

TEST_VISUAL = "前方0.5米处有一个红色按钮"
TEST_AUDIO = "立刻按下那个红色按钮！"


class TestNeuralRoutingRepair:
    def test_first_call_returns_failed_routing(self):
        """首次调用必然因路由阻塞返回 FAILED_ROUTING。"""
        cns = CentralNervousSystem()
        _, status = cns.perceive_and_react(TEST_VISUAL, TEST_AUDIO)
        assert status == "FAILED_ROUTING"

    def test_after_repair_returns_coordination_success(self):
        """repair 后第二次调用应返回 COORDINATION_SUCCESS。"""
        cns = CentralNervousSystem()
        cns.perceive_and_react(TEST_VISUAL, TEST_AUDIO)  # 首次：FAILED_ROUTING
        cns.repair_neural_routing()
        _, status = cns.perceive_and_react(TEST_VISUAL, TEST_AUDIO)
        assert status == "COORDINATION_SUCCESS"

    def test_trace_contains_all_required_brain_areas(self):
        """COORDINATION_SUCCESS 时追踪路径必须包含三个关键标签。"""
        cns = CentralNervousSystem()
        cns.perceive_and_react(TEST_VISUAL, TEST_AUDIO)  # 首次：FAILED_ROUTING
        cns.repair_neural_routing()
        signal, status = cns.perceive_and_react(TEST_VISUAL, TEST_AUDIO)

        assert status == "COORDINATION_SUCCESS"
        trace_str = str(signal.trace_log)
        assert "大脑核心计算区" in trace_str, f"追踪路径缺少'大脑核心计算区'：{trace_str}"
        assert "运动神经(手)" in trace_str, f"追踪路径缺少'运动神经(手)'：{trace_str}"
        assert "发声器官(嘴)" in trace_str, f"追踪路径缺少'发声器官(嘴)'：{trace_str}"

    def test_repair_is_idempotent(self):
        """多次调用 repair 不应破坏系统状态。"""
        cns = CentralNervousSystem()
        cns.repair_neural_routing()
        cns.repair_neural_routing()
        cns.repair_neural_routing()

        _, status = cns.perceive_and_react(TEST_VISUAL, TEST_AUDIO)
        assert status == "COORDINATION_SUCCESS"

    def test_second_call_without_repair_still_fails(self):
        """未修复时即使重复调用仍然失败。"""
        cns = CentralNervousSystem()
        _, s1 = cns.perceive_and_react(TEST_VISUAL, TEST_AUDIO)
        _, s2 = cns.perceive_and_react(TEST_VISUAL, TEST_AUDIO)
        assert s1 == "FAILED_ROUTING"
        assert s2 == "FAILED_ROUTING"


class TestBrainDecision:
    def test_red_button_triggers_activation(self):
        """含'红色按钮'和'按'的输入应激活手/嘴协同。"""
        cns = CentralNervousSystem()
        cns.repair_neural_routing()
        _, status = cns.perceive_and_react("红色按钮", "按下它")
        assert status == "COORDINATION_SUCCESS"

    def test_irrelevant_input_returns_execution_error(self):
        """不含触发词的输入，大脑决策为 IDLE，应返回 EXECUTION_ERROR。"""
        cns = CentralNervousSystem()
        cns.repair_neural_routing()
        _, status = cns.perceive_and_react("蓝天白云", "今天天气不错")
        assert status == "EXECUTION_ERROR"


class TestNerveSignalTrace:
    def test_trace_starts_with_source(self):
        """NerveSignal 的追踪日志应从信号源开始。"""
        from agent.nerve_signal import NerveSignal
        sig = NerveSignal(source="测试源", payload="测试内容")
        assert len(sig.trace_log) == 1
        assert "测试源" in sig.trace_log[0]

    def test_pass_through_appends_to_trace(self):
        """pass_through 应向追踪日志追加条目。"""
        from agent.nerve_signal import NerveSignal
        sig = NerveSignal(source="测试源", payload="内容")
        sig.pass_through("处理单元A")
        sig.pass_through("处理单元B")
        assert len(sig.trace_log) == 3
        assert "处理单元A" in sig.trace_log[1]
        assert "处理单元B" in sig.trace_log[2]
