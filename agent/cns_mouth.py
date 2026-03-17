"""嘴部效应器 (CNS 版)：接受 NerveSignal 并追踪"""


class MouthComponent:
    def __init__(self):
        self.is_ready = True

    def speak(self, text: str, signal) -> bool:
        if not self.is_ready:
            return False
        signal.pass_through("发声器官(嘴)")
        print(f"  [嘴部发声] {text}")
        return True
