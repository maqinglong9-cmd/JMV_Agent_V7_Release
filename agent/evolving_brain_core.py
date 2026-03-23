"""进化大脑核心：支持动态规则注入和元认知联动的新一代 BrainCore"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.agent import WholeBrainAgent
from agent.metacognition_component import MetacognitionComponent


class EvolvingBrainCore:
    """
    进化版大脑核心，三层决策优先级：
    1. 元认知后天习得规则（突触强化，优先级最高）
    2. 全脑感知路由（WholeBrainAgent 额叶决策）
    3. 基础本能规则（兜底）
    """

    BASE_RULES = {
        "画图":    "CALL_TOOL_PAINTER",
        "生成图像": "CALL_TOOL_PAINTER",
        "绘制":    "CALL_TOOL_PAINTER",
        "画一":    "CALL_TOOL_PAINTER",
        "画张":    "CALL_TOOL_PAINTER",
        "画幅":    "CALL_TOOL_PAINTER",
        "生成图":  "CALL_TOOL_PAINTER",
        "绘图":    "CALL_TOOL_PAINTER",
        "计算":    "CALL_TOOL_CALCULATOR",
        "搜索":    "CALL_TOOL_SEARCH",
        "查询":    "CALL_TOOL_SEARCH",
        "写代码":  "CALL_TOOL_CODER",
        "编程":    "CALL_TOOL_CODER",
        "写文件":  "CALL_TOOL_FILE_WRITE",
        "创建文件": "CALL_TOOL_FILE_WRITE",
        "保存文件": "CALL_TOOL_FILE_WRITE",
        "写入文件": "CALL_TOOL_FILE_WRITE",
        "执行命令": "CALL_TOOL_SHELL",
        "运行命令": "CALL_TOOL_SHELL",
        "终端执行": "CALL_TOOL_SHELL",
        # Android 底层操作关键字
        "启动APP":  "CALL_TOOL_ANDROID_LAUNCH",
        "启动app":  "CALL_TOOL_ANDROID_LAUNCH",
        "点击屏幕": "CALL_TOOL_ANDROID_TAP",
        "输入文字": "CALL_TOOL_ANDROID_TYPE",
        "截屏":     "CALL_TOOL_ANDROID_SCREENSHOT",
        "截图":     "CALL_TOOL_ANDROID_SCREENSHOT",
        # Windows 底层操作关键字
        "读取文件": "CALL_TOOL_WIN_FILE_READ",
        "写入文件": "CALL_TOOL_WIN_FILE_WRITE",
        "注册表":   "CALL_TOOL_WIN_REG_READ",
        "进程列表": "CALL_TOOL_WIN_PROCESS_LIST",
        "剪贴板":   "CALL_TOOL_WIN_CLIPBOARD",
    }

    def __init__(self, metacognition: MetacognitionComponent):
        self.meta = metacognition
        self._whole_brain = WholeBrainAgent()

    def process(self, context: str, task_intent: str) -> str:
        """
        三层决策：后天规则 > 全脑感知路由 > 基础本能
        """
        # 层 1：元认知后天习得规则
        if task_intent in self.meta.learned_rules:
            tool = self.meta.learned_rules[task_intent]
            return f"DECISION: {tool}"

        # 层 2：全脑感知路由（额叶决策）
        perception = self._whole_brain.perceive_and_react(
            visual_input=task_intent[:30],
            audio_input=task_intent[:30],
            somatosensory_input="键盘输入"
        )
        frontal = perception[-1] if perception else ""

        # 层 3：基础本能关键词匹配
        for keyword, tool in self.BASE_RULES.items():
            if keyword in task_intent:
                return f"DECISION: {tool} | FRONTAL: {frontal}"

        return f"DECISION: CHAT_RESPONSE | FRONTAL: {frontal}"
