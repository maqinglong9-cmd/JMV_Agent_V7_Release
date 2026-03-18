"""全脑 Agent 集成"""
from core.cells import CerebrospinalFluid
from core.brain_regions import (
    FrontalLobe, ParietalLobe, TemporalLobe, OccipitalLobe,
    Thalamus, Hypothalamus, Cerebellum, Brainstem
)


class WholeBrainAgent:
    """完整的大脑 Agent 系统集成"""

    def __init__(self):
        self.csf = CerebrospinalFluid()
        self.frontal = FrontalLobe()
        self.parietal = ParietalLobe()
        self.temporal = TemporalLobe()
        self.occipital = OccipitalLobe()
        self.thalamus = Thalamus()
        self.hypothalamus = Hypothalamus()
        self.cerebellum = Cerebellum()
        self.brainstem = Brainstem()
        # 进化引擎兼容属性
        self.tool_registry = None
        self.metacognition = None

    def perceive_and_react(self, visual_input: str, audio_input: str, somatosensory_input: str) -> list:
        """模拟大脑处理多模态信息并作出反应，返回步骤日志列表。单个脑区失败不中断整体流程。"""
        logs = []

        def _safe(fn, *args):
            try:
                return fn(*args)
            except Exception as e:
                if hasattr(fn, '__self__'):
                    label = getattr(fn.__self__, 'name', type(fn.__self__).__name__)
                else:
                    label = getattr(fn, '__name__', str(fn))
                return f"[错误] {label}: {e}"

        combined = f"视觉:[{visual_input}], 听觉:[{audio_input}], 触觉:[{somatosensory_input}]"

        logs.append(_safe(self.csf.circulate))
        logs.append(_safe(self.brainstem.maintain_vital_functions))
        logs.append(_safe(self.hypothalamus.regulate_homeostasis))
        logs.append(_safe(self.thalamus.relay_information, combined))
        logs.append(_safe(self.occipital.process_vision, visual_input))
        logs.append(_safe(self.temporal.process_audio_and_memory, audio_input))
        logs.append(_safe(self.parietal.process_somatosensory, somatosensory_input))
        context = f"视觉:{visual_input} + 听觉:{audio_input}"
        logs.append(_safe(self.frontal.decide_and_plan, context))
        logs.append(_safe(self.cerebellum.coordinate_movement, "综合感知后的协调动作"))
        return logs
