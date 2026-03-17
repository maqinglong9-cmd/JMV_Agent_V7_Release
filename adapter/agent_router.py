"""
多 Agent 路由器（AgentRouter）
================================
将 4 种 Agent 的不同接口统一为：
    run(visual, audio, tactile) -> list[str]

支持的模式：
  basic    → WholeBrainAgent          (9 脑区串行仿真，默认)
  ultimate → UltimateCompanionAgent   (长期记忆 + 情绪引擎)
  cyborg   → CyborgCompanionAgent     (具身多器官 + 工具执行)
  cns      → CentralNervousSystem     (神经信号总线)
"""
from __future__ import annotations
import os
import sys

# 确保项目根目录在 path 中
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# 模式标签（供 UI 使用）
AGENT_MODES = {
    "basic":    "基础脑区",
    "ultimate": "终极伴侣",
    "cyborg":   "赛博增强",
    "cns":      "CNS全感官",
}


class AgentRouter:
    """
    懒加载：只在首次切换到某模式时才实例化对应 Agent（避免启动卡顿）。
    """

    def __init__(self, mode: str = "basic"):
        self._mode    = mode
        self._agents: dict = {}  # mode → agent instance

    # ── 公共 API ─────────────────────────────────────────────

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def mode_label(self) -> str:
        return AGENT_MODES.get(self._mode, self._mode)

    def set_mode(self, mode: str) -> None:
        if mode not in AGENT_MODES:
            raise ValueError(f"不支持的模式: {mode}，可选: {list(AGENT_MODES)}")
        self._mode = mode

    def run(self, visual: str, audio: str, tactile: str) -> list[str]:
        """
        统一入口：根据当前模式调用对应 Agent 并返回 list[str] 步骤列表。
        每个字符串代表一个"感知步骤"（显示在日志区）。
        """
        agent = self._get_agent(self._mode)
        dispatch = {
            "basic":    self._run_basic,
            "ultimate": self._run_ultimate,
            "cyborg":   self._run_cyborg,
            "cns":      self._run_cns,
        }
        runner = dispatch.get(self._mode, self._run_basic)
        return runner(agent, visual, audio, tactile)

    # ── Agent 懒加载 ─────────────────────────────────────────

    def _get_agent(self, mode: str):
        if mode not in self._agents:
            self._agents[mode] = self._create_agent(mode)
        return self._agents[mode]

    @staticmethod
    def _create_agent(mode: str):
        if mode == "basic":
            from core.agent import WholeBrainAgent
            return WholeBrainAgent()
        elif mode == "ultimate":
            from agent.ultimate_companion_agent import UltimateCompanionAgent
            return UltimateCompanionAgent()
        elif mode == "cyborg":
            from agent.cyborg_companion_agent import CyborgCompanionAgent
            return CyborgCompanionAgent()
        elif mode == "cns":
            from agent.central_nervous_system import CentralNervousSystem
            return CentralNervousSystem()
        else:
            from core.agent import WholeBrainAgent
            return WholeBrainAgent()

    # ── 各模式适配器 ─────────────────────────────────────────

    @staticmethod
    def _run_basic(agent, visual: str, audio: str, tactile: str) -> list[str]:
        """WholeBrainAgent → 直接返回 list[str]"""
        try:
            return agent.perceive_and_react(visual, audio, tactile)
        except Exception as e:
            return [f"[基础脑区] 感知异常: {e}"]

    @staticmethod
    def _run_ultimate(agent, visual: str, audio: str, tactile: str) -> list[str]:
        """UltimateCompanionAgent.process_input(str) → list[str]"""
        combined = f"{visual}。{audio}。{tactile}" if (audio or tactile) else visual
        try:
            reply = agent.process_input(combined)
            emotion_state = getattr(agent.emotion, 'current_mood', '平静')
            return [
                f"[终极伴侣] 情绪状态: {emotion_state}",
                f"[长期记忆] 检索相关记忆...",
                f"[综合分析] 正在整合多模态输入: {combined[:40]}",
                f"[情绪驱动回复] {reply}",
            ]
        except Exception as e:
            return [f"[终极伴侣] 处理异常: {e}"]

    @staticmethod
    def _run_cyborg(agent, visual: str, audio: str, tactile: str) -> list[str]:
        """CyborgCompanionAgent.perceive_and_act(visual, audio) → list[str]"""
        steps = [
            f"[眼部传感器] 正在观测: {visual[:50]}",
            f"[耳部传感器] 正在监听: {audio[:50]}" if audio else "[耳部传感器] 无听觉输入",
            f"[触觉反馈] {tactile[:30]}" if tactile else "[触觉反馈] 无触觉输入",
        ]
        try:
            result = agent.perceive_and_act(
                visual_stimulus=visual or None,
                audio_stimulus=audio or None
            )
            if result == "SUCCESS":
                steps.append("[赛博增强] 多器官协调执行完毕 ✓")
            else:
                steps.append(f"[赛博增强] 执行结果: {result}")
            steps.append("[元认知] 动作已记录到短期记忆")
        except Exception as e:
            steps.append(f"[赛博增强] 执行异常: {e}")
        return steps

    @staticmethod
    def _run_cns(agent, visual: str, audio: str, tactile: str) -> list[str]:
        """CentralNervousSystem.perceive_and_react(visual, audio) → list[str]"""
        steps = [
            f"[感觉输入] 视觉: {visual[:40]}",
            "[眼神经] CNS-Eye 信号采集...",
            f"[听神经] CNS-Ear 信号采集: {audio[:30]}" if audio else "[听神经] 静默",
            "[丘脑] 多模态信号融合中...",
            "[元认知] 安全性评估...",
        ]
        try:
            signal, status = agent.perceive_and_react(
                visual_env=visual,
                audio_env=audio or "静默"
            )
            trace = getattr(signal, 'trace', [])
            if trace:
                steps.append(f"[神经链路] {' → '.join(trace[-4:])}")
            steps.append(f"[系统总线] 最终状态: {status}")
        except Exception as e:
            steps.append(f"[CNS] 信号传导异常: {e}")
        return steps
