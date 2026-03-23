"""聊天记录持久化存储 - JSON 文件，支持多会话、自动轮转（最多 100 条/会话）"""
import json
import os
import time
from typing import Dict, List

_DEFAULT_SESSION = 'default'
_MAX_MESSAGES = 100


class HistoryStore:
    """
    聊天记录持久化存储。
    每个会话存储为独立 JSON 文件：jmv_workspace/chat_history/<session_id>.json
    自动轮转：超过 MAX_MESSAGES 时保留最新的消息。
    """

    def __init__(self, workspace_dir: str = None):
        if workspace_dir is None:
            workspace_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'jmv_workspace'
            )
        self._history_dir = os.path.join(workspace_dir, 'chat_history')
        os.makedirs(self._history_dir, exist_ok=True)

    def _path(self, session_id: str) -> str:
        """返回会话文件路径（清理非法字符防止路径遍历）。"""
        safe_id = ''.join(c for c in session_id if c.isalnum() or c in '-_')
        if not safe_id:
            safe_id = 'default'
        return os.path.join(self._history_dir, f"{safe_id}.json")

    def save(self, messages: List[Dict], session_id: str = _DEFAULT_SESSION) -> bool:
        """保存消息列表到磁盘。超过 MAX_MESSAGES 时自动截断最旧消息。"""
        try:
            if len(messages) > _MAX_MESSAGES:
                messages = messages[-_MAX_MESSAGES:]
            data = {
                'session_id': session_id,
                'updated_at': time.time(),
                'messages': list(messages),
            }
            with open(self._path(session_id), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def load(self, session_id: str = _DEFAULT_SESSION) -> List[Dict]:
        """从磁盘加载消息列表。文件不存在或损坏时返回空列表。"""
        try:
            path = self._path(session_id)
            if not os.path.isfile(path):
                return []
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            msgs = data.get('messages', [])
            # 验证格式：每条消息必须有 role 和 content
            return [m for m in msgs
                    if isinstance(m, dict) and 'role' in m and 'content' in m]
        except Exception:
            return []

    def list_sessions(self) -> List[str]:
        """列出所有已保存的会话 ID（按名称排序）。"""
        try:
            return sorted(
                fname[:-5]
                for fname in os.listdir(self._history_dir)
                if fname.endswith('.json')
            )
        except Exception:
            return []

    def delete(self, session_id: str = _DEFAULT_SESSION) -> bool:
        """删除指定会话的历史记录文件。"""
        try:
            path = self._path(session_id)
            if os.path.isfile(path):
                os.remove(path)
            return True
        except Exception:
            return False

    def clear_all(self) -> int:
        """删除所有会话记录，返回成功删除的数量。"""
        count = 0
        for sid in self.list_sessions():
            if self.delete(sid):
                count += 1
        return count
