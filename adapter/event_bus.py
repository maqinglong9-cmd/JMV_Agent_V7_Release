"""简单事件总线，用于业务层与 UI 层解耦"""
from typing import Any, Callable, Dict, List
from kivy.logger import Logger


class EventBus:
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable):
        self._listeners.setdefault(event_type, []).append(callback)

    def unsubscribe(self, event_type: str, callback: Callable):
        listeners = self._listeners.get(event_type, [])
        if callback in listeners:
            listeners.remove(callback)

    def emit(self, event_type: str, data: Any):
        for cb in list(self._listeners.get(event_type, [])):
            try:
                cb(data)
            except Exception as e:
                Logger.error("EventBus", f"callback error [{event_type}]: {e}")
