"""
测试 WholeBrainAgent.perceive_and_react：
  - 正常流程返回 9 条日志
  - 单个脑区异常不中断整体流程
  - 日志内容包含各脑区名称
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.agent import WholeBrainAgent


class TestPerceiveAndReact:
    def test_returns_nine_logs(self):
        """正常感知应返回恰好 9 条日志（对应 9 个脑区）。"""
        agent = WholeBrainAgent()
        logs = agent.perceive_and_react("树木", "鸟鸣", "微风")
        assert len(logs) == 9

    def test_all_logs_are_strings(self):
        """所有日志条目都应是字符串。"""
        agent = WholeBrainAgent()
        logs = agent.perceive_and_react("树木", "鸟鸣", "微风")
        for log in logs:
            assert isinstance(log, str), f"非字符串日志：{log!r}"

    def test_logs_contain_brain_region_names(self):
        """关键脑区名称应出现在对应日志中。"""
        agent = WholeBrainAgent()
        logs = agent.perceive_and_react("红色光线", "哔哔声", "震动")
        combined = "\n".join(logs)
        for region in ["额叶", "顶叶", "颞叶", "枕叶", "丘脑", "下丘脑", "小脑", "脑干"]:
            assert region in combined, f"日志中缺少脑区 '{region}'"

    def test_faulty_region_does_not_crash(self):
        """单个脑区抛出异常不应中断整体流程，仍应返回 9 条日志。"""
        agent = WholeBrainAgent()

        # 注入一个故障脑区
        original_frontal = agent.frontal

        class _FaultyFrontal:
            name = "额叶 (Frontal Lobe)"
            def decide_and_plan(self, context):
                raise RuntimeError("模拟额叶故障")

        agent.frontal = _FaultyFrontal()
        try:
            logs = agent.perceive_and_react("输入", "信号", "触觉")
            assert len(logs) == 9
            # 故障日志应包含错误标记
            error_logs = [l for l in logs if "[错误]" in l]
            assert len(error_logs) == 1
        finally:
            agent.frontal = original_frontal

    def test_visual_input_reflected_in_occipital_log(self):
        """枕叶日志应包含视觉输入内容。"""
        agent = WholeBrainAgent()
        logs = agent.perceive_and_react("闪烁的星星", "寂静", "冷")
        occipital_log = next((l for l in logs if "枕叶" in l), None)
        assert occipital_log is not None
        assert "闪烁的星星" in occipital_log

    def test_audio_input_reflected_in_temporal_log(self):
        """颞叶日志应包含听觉输入内容。"""
        agent = WholeBrainAgent()
        logs = agent.perceive_and_react("暗", "钢琴旋律", "平静")
        temporal_log = next((l for l in logs if "颞叶" in l), None)
        assert temporal_log is not None
        assert "钢琴旋律" in temporal_log

    def test_empty_inputs_do_not_crash(self):
        """空字符串输入不应导致崩溃。"""
        agent = WholeBrainAgent()
        logs = agent.perceive_and_react("", "", "")
        assert len(logs) == 9


class TestBrainRegionComponents:
    """直接测试各脑区组件的方法。"""

    def test_frontal_lobe_returns_context(self):
        from core.brain_regions import FrontalLobe
        lobe = FrontalLobe()
        result = lobe.decide_and_plan("紧急情况")
        assert "额叶" in result
        assert "紧急情况" in result

    def test_cerebellum_coordinates_movement(self):
        from core.brain_regions import Cerebellum
        cb = Cerebellum()
        result = cb.coordinate_movement("跑步动作")
        assert "小脑" in result
        assert "跑步动作" in result

    def test_brainstem_maintains_vital(self):
        from core.brain_regions import Brainstem
        bs = Brainstem()
        result = bs.maintain_vital_functions()
        assert "脑干" in result

    def test_thalamus_relays_info(self):
        from core.brain_regions import Thalamus
        th = Thalamus()
        result = th.relay_information("感觉信号包")
        assert "丘脑" in result
        assert "感觉信号包" in result
