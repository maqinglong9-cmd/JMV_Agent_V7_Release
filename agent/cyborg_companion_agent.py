"""具身智能体总线：整合大脑、眼、耳、口、手、脚"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent.brain_core import BrainCore
from agent.metacognition_component import MetacognitionComponent
from agent.memory_component import MemoryComponent
from agent.eye_component import EyeComponent
from agent.ear_component import EarComponent
from agent.mouth_component import MouthComponent
from agent.hand_component import HandComponent
from agent.foot_component import FootComponent

# 本地路由关键词表（兜底，不依赖 BrainCore 具体实现）
_HAND_KEYWORDS = ["绘制", "灭火", "操作", "抓取", "按压", "明火", "烟雾", "警报", "呼救"]
_FOOT_KEYWORDS = ["移动", "跑", "前往", "导航", "撤离"]


class CyborgCompanionAgent:
    def __init__(self):
        self.brain = BrainCore()
        self.meta = MetacognitionComponent()
        self.memory = MemoryComponent()

        self.eyes = EyeComponent()
        self.ears = EarComponent()
        self.mouth = MouthComponent()
        self.hands = HandComponent()
        self.feet = FootComponent()

        self.is_ready = False

    def perceive_and_act(self, visual_stimulus: str = None, audio_stimulus: str = None) -> str:
        print("\n[系统] --- 外部刺激输入 ---")
        combined_intent = ""

        if visual_stimulus:
            eye_result = self.eyes.observe(visual_stimulus)
            if "ERROR" in eye_result:
                return eye_result
            combined_intent += eye_result + "；"

        if audio_stimulus:
            ear_result = self.ears.listen(audio_stimulus)
            if "ERROR" in ear_result:
                return ear_result
            combined_intent += ear_result

        print(f"  [大脑] 正在融合多模态信息并决策: '{combined_intent}'")

        # 本地关键词路由兜底
        decision = self._local_route(combined_intent)

        if "HAND_OPERATE" in decision:
            hand_result = self.hands.manipulate(target="目标对象", action="执行工具调用或物理交互")
            if "ERROR" in hand_result:
                return hand_result
            self.mouth.speak("我已开始操作。")
        elif "FOOT_MOVE" in decision:
            foot_result = self.feet.navigate(destination="安全区域", speed="急速")
            if "ERROR" in foot_result:
                return foot_result
            self.mouth.speak("正在前往目标地点。")
        else:
            mouth_result = self.mouth.speak("我已收到并理解你的指令。")
            if "ERROR" in mouth_result:
                return mouth_result

        return "SUCCESS"

    def _local_route(self, intent: str) -> str:
        for kw in _HAND_KEYWORDS:
            if kw in intent:
                return "ACTION: HAND_OPERATE"
        for kw in _FOOT_KEYWORDS:
            if kw in intent:
                return "ACTION: FOOT_MOVE"
        return "ACTION: MOUTH_SPEAK"

    def run_hardware_diagnostics(self) -> bool:
        """修复第一个离线器官，返回 True；全部在线返回 False"""
        organs = [self.eyes, self.ears, self.mouth, self.hands, self.feet]
        for organ in organs:
            if organ.status != "ONLINE":
                organ.status = "ONLINE"
                return True
        return False
