"""CoT 推理链审计记忆：持久化记录 Agent 每个子任务的完整思考过程"""
import time
import json


class CoTMemory:
    def __init__(self):
        self.audit_log = []

    def log_thought(self, task_id: str, intent: str, thought: str, action: str):
        record = {
            "timestamp": time.time(),
            "task_id": task_id,
            "intent": intent,
            "thought": thought,
            "action_taken": action
        }
        self.audit_log.append(record)
        print(f"  [CoT 审计] 已记录节点 {task_id} 的推理链。")

    def export_trace(self) -> str:
        return json.dumps(self.audit_log, ensure_ascii=False, indent=2)
