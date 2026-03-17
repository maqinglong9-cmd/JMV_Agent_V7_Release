"""听觉感受器：将声波信号转化为文本指令 (模拟 ASR)"""


class EarComponent:
    def __init__(self):
        self.status = "ONLINE"

    def listen(self, audio_data: str) -> str:
        if self.status != "ONLINE":
            return "ERROR: EAR_OFFLINE"
        print(f"  [耳朵] 捕获声纹波形: '{audio_data}' -> 语音转文字中...")
        return f"听觉情报: 听到 {audio_data}"
