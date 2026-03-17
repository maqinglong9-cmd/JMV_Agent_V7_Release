"""智伴智能体总线：协调大脑、记忆、工具与规划的完整 ReAct 循环"""
from agent.brain_core import BrainCore
from agent.memory_component import MemoryComponent
from agent.tool_registry import ToolRegistry
from agent.planner_component import PlannerComponent
from agent.native_os_operator import NativeOSOperator


class SmartCompanionAgent:
    """
    完整集成的智能体，实现 Observe → Plan → Think → Act 循环（ReAct 模式）。
    支持多步子任务规划，按依赖顺序逐步执行。
    """

    def __init__(self):
        self.brain = BrainCore()
        self.memory = MemoryComponent(max_size=10)
        self.os_operator = NativeOSOperator()
        self.tools = ToolRegistry(os_operator=self.os_operator)
        self.planner = PlannerComponent()
        self.is_ready: bool = False

    def run_step(self, user_input: str) -> str:
        """执行一个完整的多步 Agent 思考-行动循环"""
        # 1. 观察与记忆 (Observe)
        self.memory.add("user", user_input)

        # 2. 多步规划 (Plan)
        plan = self.planner.parse(user_input)

        # 3. 按依赖顺序逐步执行 (Think → Act)
        while not self.planner.is_complete(plan):
            ready = self.planner.get_ready_steps(plan)
            if not ready:
                # 无可执行步骤（依赖死锁或全部失败），退出
                break
            for step in ready:
                context = self.memory.get_context()
                decision = self.brain.process(context, step.intent)
                self.memory.add("brain_thought", decision)

                if "CALL_TOOL" in decision:
                    result = self.tools.execute(decision, step.params)
                else:
                    result = f"[执行动作] 大脑组织语言回答: 理解了你的需求。"

                print(f"  [系统输出] {result}")
                self.memory.add("agent_action", result)
                self.planner.mark_done(plan, step.id, result)

        return self.planner.summary(plan)

    def reset(self) -> None:
        """重置 Agent 状态（用于自我修复）"""
        self.memory.clear()
        self.is_ready = False
