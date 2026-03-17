"""记忆组件：对应海马体与突触权重记录，管理短期上下文窗口"""
from typing import List, Dict


class MemoryComponent:
    """
    短期记忆（上下文窗口）+ 遗忘机制。
    保持最近 max_size 条记录，超出时丢弃最旧的条目。
    """

    def __init__(self, max_size: int = 10):
        self._max_size = max_size
        self.short_term_memory: List[Dict[str, str]] = []

    def add(self, role: str, content: str) -> None:
        """追加一条记忆，超出窗口时自动遗忘最旧条目"""
        self.short_term_memory.append({"role": role, "content": content})
        if len(self.short_term_memory) > self._max_size:
            self.short_term_memory.pop(0)

    def get_context(self) -> str:
        """返回当前上下文的字符串摘要"""
        return " | ".join(
            f"{m['role']}:{m['content']}" for m in self.short_term_memory
        )

    def get_last(self, role: str = None) -> Dict[str, str]:
        """获取最后一条记忆，可按 role 过滤"""
        if role is None:
            return self.short_term_memory[-1] if self.short_term_memory else {}
        for item in reversed(self.short_term_memory):
            if item["role"] == role:
                return item
        return {}

    def clear(self) -> None:
        """清空所有记忆"""
        self.short_term_memory.clear()

    def __len__(self) -> int:
        return len(self.short_term_memory)
