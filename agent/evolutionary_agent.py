"""进化版 Agent 总线：整合元认知模块，具备自我进化能力"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent.metacognition_component import MetacognitionComponent
from agent.evolving_brain_core import EvolvingBrainCore
from agent.memory_component import MemoryComponent
from agent.tool_registry import ToolRegistry
from agent.planner_component import PlannerComponent


class EvolutionaryAgent:
    """
    具备进化能力的 Agent 总线。
    在 SmartCompanionAgent 基础上新增元认知层：
    Observe → Plan → Evaluate(Meta) → Think → Act
    支持多步子任务规划，每步执行前经元认知评估。
    """

    def __init__(self):
        self.meta = MetacognitionComponent()
        self.brain = EvolvingBrainCore(self.meta)
        self.memory = MemoryComponent(max_size=10)
        self.tools = ToolRegistry()
        self.planner = PlannerComponent()
        self.is_ready: bool = False

    def run_step(self, user_input: str) -> str:
        """执行一个完整的元认知增强多步 ReAct 循环"""
        print(f"\n[用户输入] {user_input}")
        self.memory.add("user", user_input)

        # 1. 多步规划
        plan = self.planner.parse(user_input)

        # 2. 按依赖顺序逐步执行
        while not self.planner.is_complete(plan):
            ready = self.planner.get_ready_steps(plan)
            if not ready:
                break
            for step in ready:
                # 元认知事前评估
                is_feasible, reason = self.meta.evaluate_feasibility(step.intent)
                if not is_feasible:
                    msg = f"[内部拦截] 元认知否决了步骤 {step.id}。理由: {reason}"
                    print(msg)
                    self.memory.add("agent", msg)
                    self.planner.mark_failed(plan, step.id, reason)
                    if "未知指令" in step.intent:
                        # 整体返回 NEED_UPGRADE 触发进化
                        return "NEED_UPGRADE"
                    continue

                # 大脑决策
                decision = self.brain.process(self.memory.get_context(), step.intent)
                print(f"  [大脑决策] {decision}")
                self.memory.add("brain_thought", decision)

                # 执行行动
                if "CALL_TOOL" in decision:
                    result = self.tools.execute(decision, step.params)
                else:
                    result = "[执行动作] 大脑组织语言回答: 理解了你的需求。"

                print(f"  [系统输出] {result}")
                self.memory.add("agent_action", result)
                self.planner.mark_done(plan, step.id, result)

        # 若所有步骤均被拦截，返回 REJECTED
        all_failed = all(s.status == "failed" for s in plan.steps)
        if all_failed:
            return "REJECTED_BY_METACOGNITION"

        return self.planner.summary(plan)

    def reset(self) -> None:
        """重置 Agent 状态（用于自我修复）"""
        self.memory.clear()
        self.is_ready = False
