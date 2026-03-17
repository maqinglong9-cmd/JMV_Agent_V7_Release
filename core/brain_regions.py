"""宏观脑区解剖结构"""
from core.cells import GlialCell, Neuron


class BrainRegion:
    """所有脑区的基类"""
    def __init__(self, name):
        self.name = name
        self.gray_matter = [Neuron(i, is_myelinated=False) for i in range(5)]
        self.white_matter = [Neuron(i, is_myelinated=True) for i in range(5)]
        self.glial_cells = [GlialCell() for _ in range(3)]


class FrontalLobe(BrainRegion):
    def __init__(self): super().__init__("额叶 (Frontal Lobe)")
    def decide_and_plan(self, context):
        return f"[{self.name}] 根据上下文 '{context}' 进行高级逻辑思考和自主运动规划。"


class ParietalLobe(BrainRegion):
    def __init__(self): super().__init__("顶叶 (Parietal Lobe)")
    def process_somatosensory(self, stimulus):
        return f"[{self.name}] 正在处理体感信息：分析 '{stimulus}' 的触觉、痛觉与空间方位。"


class TemporalLobe(BrainRegion):
    def __init__(self): super().__init__("颞叶 (Temporal Lobe)")
    def process_audio_and_memory(self, audio_signal):
        return f"[{self.name}] 正在解析听觉信息 '{audio_signal}'，并调用海马体形成记忆。"


class OccipitalLobe(BrainRegion):
    def __init__(self): super().__init__("枕叶 (Occipital Lobe)")
    def process_vision(self, visual_signal):
        return f"[{self.name}] 正在解码视觉画面：提取 '{visual_signal}' 的形状、颜色和运动。"


class Thalamus(BrainRegion):
    def __init__(self): super().__init__("丘脑 (Thalamus)")
    def relay_information(self, sensory_info):
        return f"[{self.name}] (信息中转站) 正在过滤并向大脑皮层转发感觉信号：{sensory_info}"


class Hypothalamus(BrainRegion):
    def __init__(self): super().__init__("下丘脑 (Hypothalamus)")
    def regulate_homeostasis(self):
        return f"[{self.name}] (总司令) 正在调节体温、内分泌，维持内环境稳定。"


class Cerebellum(BrainRegion):
    def __init__(self): super().__init__("小脑 (Cerebellum)")
    def coordinate_movement(self, motor_plan):
        return f"[{self.name}] 正在协调运动 '{motor_plan}'，调节肌肉张力，确保动作精准流畅。"


class Brainstem(BrainRegion):
    def __init__(self): super().__init__("脑干 (Brainstem) - 含中脑, 脑桥, 延髓")
    def maintain_vital_functions(self):
        return f"[{self.name}] (生命中枢) 正在维持心跳节律、呼吸频率等最基础生命活动。"
