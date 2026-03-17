"""宏观运动器官：底盘控制、导航、位移"""


class FootComponent:
    def __init__(self):
        self.status = "ONLINE"

    def navigate(self, destination: str, speed: str = "正常") -> str:
        if self.status != "ONLINE":
            return "ERROR: FOOT_OFFLINE"
        output = f"  [双脚] 规划路径中... 以 {speed} 速度移动至: {destination}。"
        print(output)
        return output
