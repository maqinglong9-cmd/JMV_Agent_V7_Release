"""神经电信号载体，记录信号的生命周期，供 Inspector 审计"""
import uuid


class NerveSignal:
    def __init__(self, source: str, payload: str):
        self.signal_id = str(uuid.uuid4())[:8]
        self.source = source
        self.payload = payload
        self.trace_log = [f"[{self.source}] 产生信号"]

    def pass_through(self, component_name: str):
        self.trace_log.append(f"-> [{component_name}] 处理完毕")
