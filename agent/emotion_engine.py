"""情绪与内驱力引擎：管理 Agent 的情绪状态和主观能动性"""


class EmotionEngine:
    def __init__(self):
        self.energy = 100
        self.boredom = 0
        self.current_mood = "平静"

    def tick(self):
        self.energy = max(10, self.energy - 5)
        self.boredom = min(100, self.boredom + 10)
        self._update_mood()

    def _update_mood(self):
        if self.energy < 30:
            self.current_mood = "疲惫"
        elif self.boredom > 70:
            self.current_mood = "无聊"
        else:
            self.current_mood = "专注"

    def apply_mood_modifier(self, base_response):
        if self.current_mood == "疲惫":
            return f"(低电量待机模式) {base_response} ...如果你没有重要的事情，我想休眠整理一下内存。"
        elif self.current_mood == "无聊":
            return f"(主动搭话) {base_response} 对了，我最近闲着没事，你要不要和我一起开发点新项目？"
        return base_response
