"""神经系统总线：整合感受器/效应器/大脑，含内联大脑存根"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent.nerve_signal import NerveSignal
from agent.cns_eye import EyeComponent
from agent.cns_ear import EarComponent
from agent.cns_hand import HandComponent
from agent.cns_mouth import MouthComponent


class _Metacognition:
    def evaluate(self, signal):
        signal.pass_through("元认知(前额叶)")
        return True, "安全"


class _BrainCore:
    def process(self, signal):
        signal.pass_through("大脑核心计算区")
        if "红色按钮" in signal.payload and "按" in signal.payload:
            return "DECISION: ACTIVATE_HANDS_AND_MOUTH"
        return "DECISION: IDLE"


class _Memory:
    def record(self, signal):
        signal.pass_through("海马体(记忆写入)")


class CentralNervousSystem:
    def __init__(self):
        self.eyes = EyeComponent()
        self.ears = EarComponent()
        self.hands = HandComponent()
        self.mouth = MouthComponent()

        self.brain = _BrainCore()
        self.meta = _Metacognition()
        self.memory = _Memory()

        self.neural_routing_ok = False  # 故障初始态，强制触发自我修复

    def perceive_and_react(self, visual_env: str, audio_env: str):
        print("\n[系统总线] 接收到外界刺激，开始神经传导...")

        sig_eye = self.eyes.scan(visual_env)
        sig_ear = self.ears.listen(audio_env)

        fused_payload = f"{sig_eye.payload} | {sig_ear.payload}"
        main_signal = NerveSignal(source="丘脑(整合)", payload=fused_payload)

        self.memory.record(main_signal)
        is_safe, _ = self.meta.evaluate(main_signal)

        if not is_safe:
            return main_signal, "BLOCKED"

        decision = self.brain.process(main_signal)

        if not self.neural_routing_ok:
            main_signal.pass_through("!!! 脊髓神经传导阻滞 !!!")
            return main_signal, "FAILED_ROUTING"

        if "ACTIVATE_HANDS_AND_MOUTH" in decision:
            hand_ok = self.hands.execute("精准按下红色按钮", main_signal)
            mouth_ok = self.mouth.speak("报告：按钮已按下，操作完毕。", main_signal)
            if hand_ok and mouth_ok:
                return main_signal, "COORDINATION_SUCCESS"

        return main_signal, "EXECUTION_ERROR"

    def repair_neural_routing(self):
        print("    -> [底层内核] 正在重写神经路由表，对齐运动皮层与周围神经的接口...")
        time.sleep(0.8)
        self.neural_routing_ok = True
        self.hands.is_ready = True
        self.mouth.is_ready = True
        print("    -> [底层内核] 神经接口修复完毕，突触连接已畅通。")
