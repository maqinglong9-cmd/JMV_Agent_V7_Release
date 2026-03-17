"""持久化记忆模块：保存每次感知的输入/输出到 JSON 文件"""
import json
import os
import time
from typing import List, Dict


def _get_memory_path() -> str:
    """获取跨平台可写的存储路径：Android 用 Kivy user_data_dir，桌面用 ~/.brainagent"""
    try:
        from kivy.app import App
        app = App.get_running_app()
        if app is not None:
            base = app.user_data_dir
        else:
            raise RuntimeError("no running app")
    except Exception:
        base = os.path.join(os.path.expanduser("~"), ".brainagent")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "memory.json")


class MemoryStore:
    """将每次感知记录持久化到本地 JSON 文件（延迟初始化路径，确保 Kivy App 已启动）"""

    def __init__(self):
        self._path: str = ""

    def _ensure_path(self):
        """首次使用时才解析存储路径，此时 App 已确保启动"""
        if not self._path:
            self._path = _get_memory_path()

    def save(self, visual: str, audio: str, tactile: str, steps: List[str]):
        """追加一条感知记录"""
        self._ensure_path()
        record = {
            "timestamp": time.time(),
            "input": {"visual": visual, "audio": audio, "tactile": tactile},
            "steps": steps,
        }
        history = self._load_raw()
        history.append(record)
        # 最多保留 100 条
        if len(history) > 100:
            history = history[-100:]
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def load_history(self, limit: int = 10) -> List[Dict]:
        """读取最近 limit 条记录"""
        self._ensure_path()
        return self._load_raw()[-limit:]

    def _load_raw(self) -> List[Dict]:
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError):
            return []
