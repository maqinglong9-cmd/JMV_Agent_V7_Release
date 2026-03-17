"""多轮对话 Agent - 支持 LLM + 本地记忆回退"""
import os
import json
from typing import Optional

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_MAX_HISTORY = 20  # 最多保留 20 轮对话

_SYSTEM_PROMPT = """你是 JMV智伴，一个智能 AI 伴侣，拥有神经科学知识、情感理解能力和创造性思维。
你的特点：
- 中文为主，温暖、专业、有见地
- 善于分析用户的情感状态并给予共情回应
- 能够结合神经科学视角理解人类行为
- 记忆并利用对话历史提供连续体验
- 简洁有力，每次回复不超过200字，除非用户要求详细解释

请始终用中文回复，保持自然对话风格。"""

_FALLBACK_REPLIES = [
    "我在这里陪伴你。请先在设置页面配置 API Key，这样我就能真正理解你说的话了。",
    "你好！我目前在本地模式下运行。配置 AI 算力后，我能给你更深入的回应。",
    "感谢你的分享。去设置页面连接 AI 服务，我们就能开始真正的对话了。",
    "我听到你了。想要获得更智能的回应，请先配置你的 AI 供应商（设置 → 算力配置）。",
]

_fallback_idx = [0]


class ChatAgent:
    """多轮对话 Agent，支持 LLM 增强和本地回退"""

    def __init__(self, llm_client=None):
        self._llm = llm_client
        self._history: list[dict] = []  # [{"role": "user"/"assistant", "content": "..."}]
        self._memory_path = os.path.join(_PROJECT_ROOT, 'jmv_workspace', 'chat_memory.json')
        self._load_memory()

    def set_llm(self, client) -> None:
        self._llm = client

    def chat(self, user_text: str) -> str:
        """
        处理用户输入，返回 AI 回复字符串。
        无论 LLM 是否可用，都不会抛出异常。
        """
        user_text = user_text.strip()
        if not user_text:
            return '请输入您想说的话。'

        self._history.append({'role': 'user', 'content': user_text})
        self._trim_history()

        if self._llm:
            reply = self._llm_reply(user_text)
        else:
            reply = self._fallback_reply()

        self._history.append({'role': 'assistant', 'content': reply})
        self._trim_history()
        self._save_memory()
        return reply

    def clear_history(self) -> None:
        self._history.clear()
        self._save_memory()

    def get_history(self) -> list[dict]:
        return list(self._history)

    # ── 私有方法 ────────────────────────────────────────

    def _llm_reply(self, user_text: str) -> str:
        """调用 LLM 生成回复，出错时回退到本地"""
        try:
            # 构建对话历史上下文（最近 10 轮）
            recent = self._history[-(min(20, len(self._history))):]
            context_lines = []
            for msg in recent[:-1]:  # 不含当前用户消息
                role = '用户' if msg['role'] == 'user' else '助手'
                context_lines.append(f'{role}: {msg["content"]}')

            context = '\n'.join(context_lines)
            if context:
                user_prompt = f'[对话历史]\n{context}\n\n[当前消息]\n用户: {user_text}'
            else:
                user_prompt = user_text

            reply, status = self._llm.chat(_SYSTEM_PROMPT, user_prompt)
            if status == 'SUCCESS' and reply:
                return reply.strip()
            return f'AI 暂时无法回复（{status}），请稍后再试。'
        except Exception as e:
            return f'对话服务异常: {e}，请检查网络和 API Key 配置。'

    def _fallback_reply(self) -> str:
        """无 LLM 时的本地回退"""
        idx = _fallback_idx[0] % len(_FALLBACK_REPLIES)
        _fallback_idx[0] += 1
        return _FALLBACK_REPLIES[idx]

    def _trim_history(self) -> None:
        """保持历史不超过 _MAX_HISTORY 轮（每轮 = 1 user + 1 assistant）"""
        max_msgs = _MAX_HISTORY * 2
        if len(self._history) > max_msgs:
            self._history = self._history[-max_msgs:]

    def _load_memory(self) -> None:
        """从磁盘加载聊天历史"""
        try:
            if os.path.exists(self._memory_path):
                with open(self._memory_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    self._history = data[-_MAX_HISTORY * 2:]
        except Exception:
            self._history = []

    def _save_memory(self) -> None:
        """保存聊天历史到磁盘"""
        try:
            os.makedirs(os.path.dirname(self._memory_path), exist_ok=True)
            with open(self._memory_path, 'w', encoding='utf-8') as f:
                json.dump(self._history, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
