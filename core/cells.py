"""微观组成：神经元、胶质细胞、脑脊液"""


class GlialCell:
    """神经胶质细胞：后勤保障部队"""
    def __init__(self, name="少突胶质细胞"):
        self.name = name

    def maintain_environment(self):
        return f"[{self.name}] 正在清理代谢废物，提供营养，维持髓鞘绝缘..."


class Neuron:
    """神经元：大脑的信息载体"""
    def __init__(self, neuron_id, is_myelinated=True):
        self.neuron_id = neuron_id
        self.is_myelinated = is_myelinated

    def process_signal(self, signal):
        processing_power = "高速传递" if self.is_myelinated else "深度计算"
        return f"信号 '{signal}' 经过神经元(ID:{self.neuron_id}) {processing_power}"


class CerebrospinalFluid:
    """脑脊液 (CSF)：物理减震与代谢循环"""
    def __init__(self):
        self.status = "纯净透明"

    def circulate(self):
        return "[脑脊液] 正在循环：提供物理浮力，带走系统运行产生的代谢废物。"
