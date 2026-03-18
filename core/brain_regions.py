"""宏观脑区解剖结构 —— 含真实神经网络计算"""
from core.cells import GlialCell, Neuron, SynapticNetwork, text_to_features


class BrainRegion:
    """所有脑区的基类，含突触网络"""

    def __init__(self, name: str, seed: int = 42):
        self.name = name
        self.gray_matter = [
            Neuron(i, n_inputs=8, seed=seed + i, is_myelinated=False) for i in range(5)
        ]
        self.white_matter = [
            Neuron(i, n_inputs=8, seed=seed + i + 100, is_myelinated=True) for i in range(5)
        ]
        self.glial_cells = [GlialCell() for _ in range(3)]
        self._net = SynapticNetwork([8, 12, 6, 4], base_seed=seed)

    def _compute(self, text: str) -> tuple:
        """神经网络前向计算，返回 (dominant_index, activation_strength)"""
        features = text_to_features(text)
        dom = self._net.dominant_index(features)
        strength = self._net.activation_strength(features)
        return dom, strength


class FrontalLobe(BrainRegion):
    _PREFIXES = [
        "根据上下文进行高级逻辑推理与规划",
        "执行功能激活：目标导向决策分析",
        "前额叶皮质整合多源信息：评估风险与收益",
        "工作记忆调用，策略生成与行动序列编排",
    ]

    def __init__(self):
        super().__init__("额叶 (Frontal Lobe)", seed=4004)

    def decide_and_plan(self, context: str) -> str:
        dom, strength = self._compute(context)
        prefix = self._PREFIXES[dom % len(self._PREFIXES)]
        intensity = "高强度" if strength > 0.6 else "稳态"
        return f"[{self.name}] {prefix}（{intensity}激活）：'{context}'"


class ParietalLobe(BrainRegion):
    _PREFIXES = [
        "正在处理体感信息：分析触觉、痛觉与空间方位",
        "顶叶联合皮层：整合多模态空间感知",
        "感觉-运动协调：解析姿势与位置信息",
        "体感皮层激活：精细触觉判别与方向定位",
    ]

    def __init__(self):
        super().__init__("顶叶 (Parietal Lobe)", seed=3003)

    def process_somatosensory(self, stimulus: str) -> str:
        dom, strength = self._compute(stimulus)
        prefix = self._PREFIXES[dom % len(self._PREFIXES)]
        return f"[{self.name}] {prefix}，刺激源：'{stimulus}'"


class TemporalLobe(BrainRegion):
    _PREFIXES = [
        "正在解析听觉信息，并调用海马体形成记忆",
        "颞上回激活：语义理解与语音识别处理",
        "听觉皮层整合：节律、音调与意义解析",
        "海马体-颞叶回路：长时记忆编码启动",
    ]

    def __init__(self):
        super().__init__("颞叶 (Temporal Lobe)", seed=2002)

    def process_audio_and_memory(self, audio_signal: str) -> str:
        dom, strength = self._compute(audio_signal)
        prefix = self._PREFIXES[dom % len(self._PREFIXES)]
        return f"[{self.name}] {prefix}：'{audio_signal}'"


class OccipitalLobe(BrainRegion):
    _PREFIXES = [
        "正在解码视觉画面：提取形状、颜色和运动",
        "V1/V2初级视皮层：特征检测与边缘提取",
        "背侧流激活：空间位置与运动轨迹追踪",
        "腹侧流激活：物体识别与场景语义理解",
    ]

    def __init__(self):
        super().__init__("枕叶 (Occipital Lobe)", seed=1001)

    def process_vision(self, visual_signal: str) -> str:
        dom, strength = self._compute(visual_signal)
        prefix = self._PREFIXES[dom % len(self._PREFIXES)]
        return f"[{self.name}] {prefix}：'{visual_signal}'"


class Thalamus(BrainRegion):
    _PREFIXES = [
        "(信息中转站) 正在过滤并向大脑皮层转发感觉信号",
        "丘脑核团激活：注意力门控与信号选择性投射",
        "感觉信号路由：特异性中继核精准分发",
        "丘脑-皮层回路：振荡同步与信息整合",
    ]

    def __init__(self):
        super().__init__("丘脑 (Thalamus)", seed=5005)

    def relay_information(self, sensory_info: str) -> str:
        dom, strength = self._compute(sensory_info)
        prefix = self._PREFIXES[dom % len(self._PREFIXES)]
        return f"[{self.name}] {prefix}：{sensory_info}"


class Hypothalamus(BrainRegion):
    _STATES = [
        "正在调节体温、内分泌，维持内环境稳定",
        "下丘脑-垂体轴激活：应激激素分泌调控",
        "自主神经系统协调：交感/副交感平衡维持",
        "昼夜节律同步：生物钟校准与能量代谢优化",
    ]

    def __init__(self):
        super().__init__("下丘脑 (Hypothalamus)", seed=6006)

    def regulate_homeostasis(self, input_text: str = '') -> str:
        dom, _ = self._compute(input_text) if input_text else (0, 0.5)
        state = self._STATES[dom % len(self._STATES)]
        return f"[{self.name}] {state}。"


class Cerebellum(BrainRegion):
    _PREFIXES = [
        "正在协调运动，调节肌肉张力，确保动作精准流畅",
        "小脑皮质-深部核团回路：运动误差实时纠正",
        "前庭-小脑协调：平衡维持与姿势控制",
        "运动学习模块激活：动作模式优化存储",
    ]

    def __init__(self):
        super().__init__("小脑 (Cerebellum)", seed=7007)

    def coordinate_movement(self, motor_plan: str) -> str:
        dom, strength = self._compute(motor_plan)
        prefix = self._PREFIXES[dom % len(self._PREFIXES)]
        return f"[{self.name}] {prefix}：'{motor_plan}'"


class Brainstem(BrainRegion):
    _STATES = [
        "(生命中枢) 正在维持心跳节律、呼吸频率等最基础生命活动",
        "脑干网状激活系统：意识水平与觉醒状态调控",
        "中脑-脑桥整合：感觉运动反射弧快速响应",
        "延髓心血管中枢：血压与心率精细调节",
    ]

    def __init__(self):
        super().__init__("脑干 (Brainstem) - 含中脑, 脑桥, 延髓", seed=8008)

    def maintain_vital_functions(self, input_text: str = '') -> str:
        dom, _ = self._compute(input_text) if input_text else (0, 0.5)
        state = self._STATES[dom % len(self._STATES)]
        return f"[{self.name}] {state}。"
