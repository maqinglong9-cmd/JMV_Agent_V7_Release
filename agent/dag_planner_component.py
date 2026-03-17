import json
from collections import deque


class TaskNode:
    def __init__(self, task_id, description, tool_name, dependencies=None):
        self.task_id = task_id
        self.description = description
        self.tool_name = tool_name
        self.dependencies = dependencies if dependencies is not None else []
        self.status = "PENDING"
        self.result = None

    def __repr__(self):
        return f"TaskNode({self.task_id}, {self.status})"


class DAGPlannerComponent:
    def __init__(self):
        self.tasks = {}

    def parse_complex_intent(self, raw_plan_json: str):
        try:
            plan_list = json.loads(raw_plan_json)
        except json.JSONDecodeError as e:
            return False, f"JSON 解析失败: {e}"

        self.tasks = {}
        for item in plan_list:
            tid = item.get("task_id")
            if not tid:
                return False, "任务缺少 task_id 字段"
            node = TaskNode(
                task_id=tid,
                description=item.get("description", ""),
                tool_name=item.get("tool_name", ""),
                dependencies=item.get("dependencies", []),
            )
            self.tasks[tid] = node

        print(f"  [DAG] 已解析 {len(self.tasks)} 个任务节点。")
        return True, "解析成功"

    def topological_sort(self):
        in_degree = {tid: 0 for tid in self.tasks}
        for tid, node in self.tasks.items():
            for dep in node.dependencies:
                if dep not in self.tasks:
                    return None, f"FATAL_ERROR: 依赖节点 {dep} 不存在"
                in_degree[tid] += 1

        queue = deque([tid for tid, deg in in_degree.items() if deg == 0])
        sorted_order = []

        while queue:
            current = queue.popleft()
            sorted_order.append(current)
            for tid, node in self.tasks.items():
                if current in node.dependencies:
                    in_degree[tid] -= 1
                    if in_degree[tid] == 0:
                        queue.append(tid)

        if len(sorted_order) != len(self.tasks):
            return None, "FATAL_ERROR: 检测到循环依赖，拓扑排序失败"

        print(f"  [DAG] 拓扑排序成功，执行顺序: {sorted_order}")
        return sorted_order, "排序成功"

    def auto_heal_cycle(self):
        healed = []
        for tid, node in self.tasks.items():
            new_deps = []
            for dep in node.dependencies:
                if dep > tid:
                    print(f"  [DAG 自愈] 切断逆向依赖: {tid} -> {dep}")
                    healed.append((tid, dep))
                else:
                    new_deps.append(dep)
            node.dependencies = new_deps

        if healed:
            print(f"  [DAG 自愈] 共修复 {len(healed)} 条循环依赖边。")
        else:
            print("  [DAG 自愈] 未发现需要修复的逆向依赖。")
        return healed
