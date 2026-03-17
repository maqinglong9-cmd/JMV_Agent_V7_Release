"""手部效应器 (CNS 版)：接受 NerveSignal 并追踪"""


class HandComponent:
    def __init__(self):
        self.is_ready = True

    def execute(self, command: str, signal) -> bool:
        if not self.is_ready:
            return False
        signal.pass_through("运动神经(手)")
        print(f"  [手部执行] 收到中枢指令，执行动作: {command}")
        return True
