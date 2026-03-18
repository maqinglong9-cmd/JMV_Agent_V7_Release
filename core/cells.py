"""微观组成：神经元、胶质细胞、脑脊液 —— 含真实神经网络计算"""
import math


# ── 基础数学工具 ──────────────────────────────────────────

def _sigmoid(x: float) -> float:
    """数值稳定的 Sigmoid 激活函数"""
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    ex = math.exp(x)
    return ex / (1.0 + ex)


def _lcg(seed: int) -> tuple:
    """线性同余伪随机数生成器，返回 ([0,1) 浮点数, 新种子)"""
    seed = (1664525 * seed + 1013904223) & 0xFFFFFFFF
    return seed / 0xFFFFFFFF, seed


def _init_weights(seed: int, n: int) -> list:
    """Xavier 风格权重初始化，范围 [-1/√n, 1/√n]"""
    scale = 1.0 / math.sqrt(max(n, 1))
    weights = []
    s = seed
    for _ in range(n):
        r, s = _lcg(s)
        weights.append((r * 2.0 - 1.0) * scale)
    return weights


# ── 8 维语义特征词汇表 ────────────────────────────────────

_VOCAB = [
    # 0 视觉
    ['看', '见', '光', '色', '图', '画', '视', '眼', '亮', '暗', '红', '蓝', '绿', '白', '黑',
     '闪', '星', '花', '树', '天', 'visual', 'see', 'light', 'color', 'bright'],
    # 1 听觉
    ['听', '声', '音', '响', '噪', '乐', '歌', '旋律', '节奏', '哔', '嘀', '嗡', '鸟', '雷',
     '嘈', '寂静', '钢琴', 'audio', 'sound', 'music', 'noise', 'hear', 'melody'],
    # 2 触觉
    ['触', '摸', '感', '压', '痛', '热', '冷', '温', '软', '硬', '粗', '细', '滑', '糙', '震动',
     '微风', 'touch', 'feel', 'pressure', 'temperature', 'vibration'],
    # 3 情感
    ['喜', '悦', '怒', '哀', '乐', '恐', '惊', '厌', '爱', '恨', '焦', '安', '快', '愉', '悲',
     '情', '心', 'emotion', 'feel', 'happy', 'sad', 'fear', 'love', 'anger'],
    # 4 认知
    ['想', '思', '考', '分析', '逻辑', '计划', '推理', '判断', '决策', '理解', '学习', '记忆',
     '知识', '概念', 'think', 'analyze', 'reason', 'plan', 'learn', 'decide'],
    # 5 紧迫
    ['紧急', '危险', '警告', '警报', '立即', '快速', '迅速', '急', '紧', '险', '威胁', '攻击',
     'urgent', 'danger', 'warning', 'alert', 'emergency', 'critical', 'immediate'],
    # 6 社交
    ['人', '说', '话', '交流', '沟通', '社', '群', '朋友', '合作', '对话', '交谈', '信任',
     'social', 'talk', 'speak', 'communicate', 'friend', 'group', 'trust'],
    # 7 运动
    ['动', '走', '跑', '跳', '移', '抬', '举', '推', '拉', '转', '扭', '踢', '抓', '协调',
     '动作', '运动', 'move', 'run', 'walk', 'jump', 'motor', 'action', 'gesture'],
]


def text_to_features(text: str) -> list:
    """将文本映射为 8 维语义特征向量（值域 [0, 1]）"""
    if not text:
        return [0.0] * 8
    text_lower = text.lower()
    length_factor = min(len(text) / 20.0, 1.0)
    features = []
    for vocab in _VOCAB:
        count = sum(1 for word in vocab if word in text_lower)
        normalized = min(count / 3.0, 1.0)
        # 文本长度作为调节因子（越长信息量越大）
        features.append(normalized * 0.85 + length_factor * 0.15)
    return features


# ── 神经元 ────────────────────────────────────────────────

class GlialCell:
    """神经胶质细胞：后勤保障部队"""
    def __init__(self, name: str = "少突胶质细胞"):
        self.name = name

    def maintain_environment(self) -> str:
        return f"[{self.name}] 正在清理代谢废物，提供营养，维持髓鞘绝缘..."


class Neuron:
    """神经元：含真实权重和 Sigmoid 激活函数的信息处理单元"""

    def __init__(self, neuron_id, n_inputs: int = 8, seed: int = 42, is_myelinated: bool = True):
        self.neuron_id = neuron_id
        self.is_myelinated = is_myelinated
        self.weights = _init_weights(seed, n_inputs)
        bias_r, _ = _lcg(seed + 99999)
        self.bias = (bias_r * 2.0 - 1.0) * 0.1

    def forward(self, inputs: list) -> float:
        """计算加权求和后经 Sigmoid 激活的输出"""
        n = min(len(inputs), len(self.weights))
        z = sum(self.weights[i] * inputs[i] for i in range(n)) + self.bias
        return _sigmoid(z)

    def process_signal(self, signal: str) -> str:
        """兼容旧版接口：将文本转特征后计算激活，返回描述字符串"""
        features = text_to_features(signal)
        activation = self.forward(features)
        processing = "高速髓鞘传递" if self.is_myelinated else "深度整合计算"
        return (f"信号 '{signal}' 经神经元(ID:{self.neuron_id}) {processing}，"
                f"激活强度={activation:.3f}")


class NeuralLayer:
    """神经网络层：多个并行神经元"""

    def __init__(self, n_neurons: int, n_inputs: int, seed: int = 0):
        self.neurons = [
            Neuron(i, n_inputs=n_inputs, seed=seed + i * 17, is_myelinated=True)
            for i in range(n_neurons)
        ]

    def forward(self, inputs: list) -> list:
        return [n.forward(inputs) for n in self.neurons]


class SynapticNetwork:
    """多层前馈突触网络，默认架构 [8 → 12 → 6 → 4]"""

    def __init__(self, layer_sizes: list = None, base_seed: int = 42):
        if layer_sizes is None:
            layer_sizes = [8, 12, 6, 4]
        self.layers: list = []
        seed = base_seed
        for i in range(1, len(layer_sizes)):
            self.layers.append(
                NeuralLayer(layer_sizes[i], n_inputs=layer_sizes[i - 1], seed=seed)
            )
            # 更新种子防止各层权重相同
            seed = (seed * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFF

    def forward(self, inputs: list) -> list:
        """前向传播，返回最终输出层的激活值列表"""
        x = list(inputs)
        for layer in self.layers:
            x = layer.forward(x)
        return x

    def dominant_index(self, inputs: list) -> int:
        """返回输出层激活值最大的神经元索引（0~3）"""
        outputs = self.forward(inputs)
        return outputs.index(max(outputs))

    def activation_strength(self, inputs: list) -> float:
        """返回输出层平均激活强度（0~1），用于判断响应强度"""
        outputs = self.forward(inputs)
        return sum(outputs) / len(outputs) if outputs else 0.5


class CerebrospinalFluid:
    """脑脊液 (CSF)：物理减震与代谢循环"""

    def __init__(self):
        self.status = "纯净透明"

    def circulate(self) -> str:
        return "[脑脊液] 正在循环：提供物理浮力，带走系统运行产生的代谢废物。"
