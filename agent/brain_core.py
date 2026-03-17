"""大脑核心决策模块：集成 WholeBrainAgent，作为 Agent 的中央处理器"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.agent import WholeBrainAgent


class BrainCore:
    """
    大脑核心：将 WholeBrainAgent 的多模态感知能力接入 Agent 决策流程。
    额叶负责逻辑推理与工具路由，其余脑区提供感知上下文。
    """

    # 工具路由规则：关键词 -> 决策指令
    _ROUTING_RULES = [
        (["画图", "生成图像", "绘制", "画一", "图片", "画张", "画幅", "生成图", "绘图"], "CALL_TOOL_PAINTER"),
        (["计算", "算一下", "数学", "求值", "运算"],    "CALL_TOOL_CALCULATOR"),
        (["搜索", "查找", "查询", "搜一下"],            "CALL_TOOL_SEARCH"),
        (["写代码", "编程", "代码", "函数", "实现"],    "CALL_TOOL_CODER"),
        (["写文件", "创建文件", "保存文件", "写入文件"], "CALL_TOOL_FILE_WRITE"),
        (["执行命令", "运行命令", "终端执行", "shell"], "CALL_TOOL_SHELL"),
    ]

    def __init__(self):
        self._whole_brain = WholeBrainAgent()

    def process(self, context: str, task: str) -> str:
        """
        接收上下文和任务，返回决策指令字符串。
        同时触发全脑感知流程，将感知日志附加到决策中。
        """
        # 额叶：关键词路由决策
        decision = self._route(task)

        # 全脑感知（异步模拟，取第一条感知日志作为思考依据）
        perception = self._whole_brain.perceive_and_react(
            visual_input=f"任务画面:{task[:30]}",
            audio_input=f"用户语音:{task[:30]}",
            somatosensory_input="键盘输入触感"
        )
        frontal_thought = perception[-1] if perception else ""

        return f"DECISION: {decision} | FRONTAL: {frontal_thought}"

    def _route(self, task: str) -> str:
        for keywords, tool in self._ROUTING_RULES:
            if any(kw in task for kw in keywords):
                return tool
        return "CHAT_RESPONSE"
