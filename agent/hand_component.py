"""精细运动器官：操作工具、物理交互"""


class HandComponent:
    def __init__(self):
        self.status = "ONLINE"

    def manipulate(self, target: str, action: str) -> str:
        if self.status != "ONLINE":
            return "ERROR: HAND_OFFLINE"
        output = f"  [双手] 启动伺服电机，对 '{target}' 执行精细操作: {action}。"
        print(output)
        return output
