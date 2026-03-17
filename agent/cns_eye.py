"""视觉感受器 (CNS 版)：返回 NerveSignal"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from agent.nerve_signal import NerveSignal


class EyeComponent:
    def scan(self, visual_input: str) -> NerveSignal:
        return NerveSignal(source="视觉神经", payload=visual_input)
