"""任务规划组件：支持多步子任务依赖图的规划器"""
import re
from dataclasses import dataclass, field
from typing import List


SPLIT_KEYWORDS = ["然后", "接着", "最后", "再", "并且", "之后", "完成后"]


@dataclass
class SubTask:
    id: str
    intent: str
    params: str
    depends_on: List[str] = field(default_factory=list)
    status: str = "pending"   # pending | running | done | failed
    result: str = ""


@dataclass
class MultiStepPlan:
    goal: str
    steps: List[SubTask] = field(default_factory=list)


class PlannerComponent:
    """
    多步任务规划器。
    - 单步任务 → 1 个 SubTask（向后兼容）
    - 多步任务（含连接词）→ 多个 SubTask，线性顺序依赖
    """

    def parse(self, raw_task: str) -> MultiStepPlan:
        print(f"[规划器] 正在拆解任务: '{raw_task}'...")
        raw_task = raw_task.strip()
        if not raw_task:
            return MultiStepPlan(goal="", steps=[SubTask(id="step_1", intent="", params="")])

        # 按连接词切割
        pattern = "(" + "|".join(re.escape(kw) for kw in SPLIT_KEYWORDS) + ")"
        parts = re.split(pattern, raw_task)

        # 过滤掉分隔词本身，保留实质片段
        segments = [p.strip() for p in parts if p.strip() and p not in SPLIT_KEYWORDS]

        plan = MultiStepPlan(goal=raw_task)
        for i, seg in enumerate(segments):
            step_id = f"step_{i + 1}"
            depends = [f"step_{i}"] if i > 0 else []
            plan.steps.append(SubTask(id=step_id, intent=seg, params=seg, depends_on=depends))

        if len(plan.steps) > 1:
            print(f"[规划器] 识别到 {len(plan.steps)} 个子任务:")
            for s in plan.steps:
                dep = f" (依赖 {s.depends_on})" if s.depends_on else ""
                print(f"  [{s.id}]{dep} {s.intent}")
        return plan

    def get_ready_steps(self, plan: MultiStepPlan) -> List[SubTask]:
        """返回所有依赖已满足的待执行步骤"""
        done_ids = {s.id for s in plan.steps if s.status == "done"}
        return [
            s for s in plan.steps
            if s.status == "pending" and all(dep in done_ids for dep in s.depends_on)
        ]

    def mark_done(self, plan: MultiStepPlan, step_id: str, result: str) -> None:
        for s in plan.steps:
            if s.id == step_id:
                s.status = "done"
                s.result = result
                return

    def mark_failed(self, plan: MultiStepPlan, step_id: str, reason: str = "") -> None:
        for s in plan.steps:
            if s.id == step_id:
                s.status = "failed"
                s.result = reason
                # 级联失败：依赖此步骤的后续步骤也标记为 failed
                self._cascade_fail(plan, step_id)
                return

    def _cascade_fail(self, plan: MultiStepPlan, failed_id: str) -> None:
        for s in plan.steps:
            if failed_id in s.depends_on and s.status == "pending":
                s.status = "failed"
                s.result = f"前置步骤 {failed_id} 失败，跳过"
                self._cascade_fail(plan, s.id)

    def is_complete(self, plan: MultiStepPlan) -> bool:
        """所有步骤均已结束（done 或 failed）"""
        return all(s.status in ("done", "failed") for s in plan.steps)

    def summary(self, plan: MultiStepPlan) -> str:
        lines = [f"[计划摘要] 目标: {plan.goal}"]
        for s in plan.steps:
            icon = "√" if s.status == "done" else "X"
            lines.append(f"  [{icon}] {s.id} ({s.status}): {s.result}")
        return "\n".join(lines)
