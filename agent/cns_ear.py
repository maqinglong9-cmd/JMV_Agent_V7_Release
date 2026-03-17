"""听觉感受器 (CNS 版)：返回 NerveSignal"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from agent.nerve_signal import NerveSignal


class EarComponent:
    def listen(self, audio_input: str) -> NerveSignal:
        return NerveSignal(source="听觉神经", payload=audio_input)
