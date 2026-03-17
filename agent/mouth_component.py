"""发声器官：将大脑文本转化为声波 (模拟 TTS)"""


class MouthComponent:
    def __init__(self):
        self.status = "ONLINE"

    def speak(self, text: str) -> str:
        if self.status != "ONLINE":
            return "ERROR: MOUTH_OFFLINE"
        output = f"  [嘴巴] (合成语音播报): 「{text}」"
        print(output)
        return output
