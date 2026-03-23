import sys
import os
import time
import json
if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding and \
        sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.dag_planner_component import DAGPlannerComponent
from agent.cot_memory import CoTMemory


class AdvancedAgentBus:
    def __init__(self):
        self.planner = DAGPlannerComponent()
        self.cot_memory = CoTMemory()

    def mock_tool_execute(self, tool_name: str, params: dict, context: str) -> str:
        time.sleep(0.5)
        if tool_name == "SEARCH":
            return f"[SEARCH 结果] 已检索关键词: {params.get('query', '')} | 上下文长度: {len(context)}"
        elif tool_name == "PAINTER":
            return f"[PAINTER 结果] 已渲染图像: {params.get('subject', '')} | 上下文长度: {len(context)}"
        elif tool_name == "MOUTH":
            return f"[MOUTH 结果] 已播报文本: {params.get('text', '')} | 上下文长度: {len(context)}"
        else:
            return f"[UNKNOWN] 工具 {tool_name} 未注册"

    def execute_plan(self, sorted_order: list) -> str:
        global_context = ""
        for tid in sorted_order:
            node = self.planner.tasks[tid]
            print(f"  [Bus] 执行任务 {tid}: {node.description} (工具: {node.tool_name})")

            params = {"query": node.description, "subject": node.description, "text": node.description}
            result = self.mock_tool_execute(node.tool_name, params, global_context)
            node.result = result
            node.status = "DONE"

            self.cot_memory.log_thought(
                task_id=tid,
                intent=node.description,
                thought=f"依赖 {node.dependencies} 已完成，选择工具 {node.tool_name}",
                action=result,
            )

            global_context += f"\n[{tid}] {result}"

        return global_context


class AdvancedEvaluator:
    def __init__(self):
        self.bus = AdvancedAgentBus()

    def run_strict_tests(self):
        print("\n========== AdvancedEvaluator 严格测试开始 ==========\n")

        # 含循环依赖的故障 JSON: T1->T3, T3->T2, T2->T1
        faulty_llm_plan = json.dumps([
            {"task_id": "T1", "description": "搜索背景资料", "tool_name": "SEARCH", "dependencies": ["T3"]},
            {"task_id": "T2", "description": "生成图像", "tool_name": "PAINTER", "dependencies": ["T1"]},
            {"task_id": "T3", "description": "播报结果", "tool_name": "MOUTH", "dependencies": ["T2"]},
        ], ensure_ascii=False)

        attempt = 0
        max_attempts = 3
        sorted_order = None

        while attempt < max_attempts:
            attempt += 1
            print(f"--- 第 {attempt} 轮尝试 ---")

            ok, msg = self.bus.planner.parse_complex_intent(faulty_llm_plan)
            if not ok:
                print(f"  [FAIL] 解析失败: {msg}")
                break

            sorted_order, sort_msg = self.bus.planner.topological_sort()
            if sorted_order is None:
                print(f"  [检测] {sort_msg}")
                print("  [自愈] 启动循环依赖修复...")
                self.bus.planner.auto_heal_cycle()

                # 重建修复后的 JSON 供下轮解析
                healed_tasks = []
                for tid, node in self.bus.planner.tasks.items():
                    healed_tasks.append({
                        "task_id": tid,
                        "description": node.description,
                        "tool_name": node.tool_name,
                        "dependencies": node.dependencies,
                    })
                faulty_llm_plan = json.dumps(healed_tasks, ensure_ascii=False)
                print("  [自愈] 已更新任务图，准备重试...\n")
            else:
                print(f"  [成功] 拓扑排序完成: {sorted_order}")
                break

        if sorted_order is None:
            print("\n[FAIL] 自愈失败，无法完成拓扑排序。")
            return

        print("\n--- 执行任务序列 ---")
        self.bus.execute_plan(sorted_order)

        print("\n--- 验证 CoT 审计日志 ---")
        log_count = len(self.bus.cot_memory.audit_log)
        print(f"  CoT 记录数: {log_count}")

        if log_count == 3:
            print("\n[PASS] 所有测试通过: CoT 审计日志包含 3 条推理链记录。")
        else:
            print(f"\n[FAIL] CoT 记录数期望 3，实际 {log_count}。")

        print("\n--- CoT 完整审计追踪 ---")
        print(self.bus.cot_memory.export_trace())
        print("\n========== 测试结束 ==========")


if __name__ == "__main__":
    evaluator = AdvancedEvaluator()
    evaluator.run_strict_tests()
