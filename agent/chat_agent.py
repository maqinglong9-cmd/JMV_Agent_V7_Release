"""多轮对话 Agent - 支持 LLM + 工具调用 + 本地记忆回退"""
import os
import re
import json
from typing import Optional

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_MAX_HISTORY = 20  # 最多保留 20 轮对话

_SYSTEM_PROMPT = """你是 JMV智伴，一个强大的 AI 助手，可以执行真实的操作任务。

## 工具调用格式
当需要执行操作时，在回复中使用以下格式：
[TOOL:工具名:参数]

## 可用工具

**通用工具**
- CALL_TOOL_CALCULATOR: 数学计算，参数为表达式，例：[TOOL:CALL_TOOL_CALCULATOR:123 * 456 + 789]
- CALL_TOOL_SEARCH: 网络搜索，参数为搜索词，例：[TOOL:CALL_TOOL_SEARCH:Python 最新版本]
- CALL_TOOL_TRANSLATE: 翻译，参数格式"目标语言|文本"，例：[TOOL:CALL_TOOL_TRANSLATE:英文|你好世界]
- CALL_TOOL_SUMMARIZE: 总结，参数为要总结的文本
- CALL_TOOL_FILE_WRITE: 写文件，参数格式"文件名|内容"，例：[TOOL:CALL_TOOL_FILE_WRITE:note.txt|内容]
- CALL_TOOL_SHELL: 执行 Shell 命令，参数为命令，例：[TOOL:CALL_TOOL_SHELL:ls -la]

**Android 专用（仅 Android 平台）**
- CALL_TOOL_ANDROID_LAUNCH: 启动应用，参数为包名
- CALL_TOOL_ANDROID_TAP: 点击坐标，参数为"x,y"
- CALL_TOOL_ANDROID_TYPE: 输入文字，参数为文字内容
- CALL_TOOL_ANDROID_SCREENSHOT: 截图，无参数
- CALL_TOOL_ANDROID_SYSINFO: 获取系统信息，无参数

**Windows 专用（仅 Windows 平台）**
- CALL_TOOL_WIN_FILE_READ: 读文件，参数为文件路径
- CALL_TOOL_WIN_FILE_LIST: 列出目录，参数为路径
- CALL_TOOL_WIN_PROCESS_LIST: 列出进程，无参数
- CALL_TOOL_WIN_RUN: 运行程序，参数为命令
- CALL_TOOL_WIN_SYSINFO: 系统信息，无参数

## 规则
1. 每次最多调用一个工具
2. 普通问答不需要工具
3. 执行完工具后，根据结果给出自然语言回复
4. 始终用中文回复
5. 简洁有力，每次回复不超过 200 字（详细解释时除外）
"""

_FALLBACK_REPLIES = [
    "我在这里陪伴你。请先在设置页面配置 API Key，这样我就能真正理解你说的话了。",
    "你好！我目前在本地模式下运行。配置 AI 算力后，我能给你更深入的回应。",
    "感谢你的分享。去设置页面连接 AI 服务，我们就能开始真正的对话了。",
    "我听到你了。想要获得更智能的回应，请先配置你的 AI 供应商（设置 → 算力配置）。",
]

_fallback_idx = [0]

# 工具调用正则：匹配 [TOOL:工具名:参数] 或 [TOOL:工具名]
_TOOL_RE = re.compile(r'\[TOOL:([A-Z_]+)(?::([^\]]*))?\]')


class ChatAgent:
    """多轮对话 Agent，支持 LLM 工具调用和本地回退"""

    def __init__(self, llm_client=None):
        self._llm = llm_client
        self._history: list[dict] = []
        self._memory_path = os.path.join(_PROJECT_ROOT, 'jmv_workspace', 'chat_memory.json')
        self._tools = None  # 延迟初始化，避免循环导入
        self._load_memory()

    def set_llm(self, client) -> None:
        self._llm = client

    def chat(self, user_text: str) -> str:
        """处理用户输入，返回 AI 回复。无论 LLM 是否可用都不抛异常。"""
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

    def _get_tools(self):
        """延迟初始化 ToolRegistry"""
        if self._tools is None:
            try:
                from agent.tool_registry import ToolRegistry
                self._tools = ToolRegistry()
            except Exception:
                self._tools = None
        return self._tools

    def _llm_reply(self, user_text: str) -> str:
        """调用 LLM，解析工具调用，执行后再次调用 LLM 生成最终回复"""
        try:
            recent = self._history[-(min(20, len(self._history))):]
            context_lines = []
            for msg in recent[:-1]:
                role = '用户' if msg['role'] == 'user' else '助手'
                context_lines.append(f'{role}: {msg["content"]}')

            context = '\n'.join(context_lines)
            if context:
                user_prompt = f'[对话历史]\n{context}\n\n[当前消息]\n用户: {user_text}'
            else:
                user_prompt = user_text

            reply, status = self._llm.chat(_SYSTEM_PROMPT, user_prompt)
            if status != 'SUCCESS' or not reply:
                return f'AI 暂时无法回复（{status}），请稍后再试。'

            reply = reply.strip()

            # 检测并执行工具调用
            tool_match = _TOOL_RE.search(reply)
            if tool_match:
                tool_name = tool_match.group(1)
                tool_params = tool_match.group(2) or ''
                tool_result = self._execute_tool(tool_name, tool_params)

                # 将工具结果发回 LLM 生成最终回复
                follow_prompt = (
                    f'用户请求：{user_text}\n\n'
                    f'工具 {tool_name} 执行结果：\n{tool_result}\n\n'
                    f'请根据以上结果，用自然语言向用户说明执行情况。'
                )
                final_reply, final_status = self._llm.chat(_SYSTEM_PROMPT, follow_prompt)
                if final_status == 'SUCCESS' and final_reply:
                    return final_reply.strip()
                # LLM 二次调用失败时直接展示工具结果
                return f'执行完成：\n{tool_result}'

            return reply

        except Exception as e:
            return f'对话服务异常: {e}，请检查网络和 API Key 配置。'

    def _execute_tool(self, tool_name: str, params: str) -> str:
        """执行工具，返回结果字符串"""
        try:
            tools = self._get_tools()
            if tools is None:
                return f'[工具不可用] {tool_name}'
            decision = f'DECISION:{tool_name}'
            result = tools.execute(decision, params)
            return result if result else '(无输出)'
        except Exception as e:
            return f'[工具执行出错] {tool_name}: {e}'

    def _fallback_reply(self) -> str:
        """无 LLM 时的本地回退"""
        idx = _fallback_idx[0] % len(_FALLBACK_REPLIES)
        _fallback_idx[0] += 1
        return _FALLBACK_REPLIES[idx]

    def _trim_history(self) -> None:
        max_msgs = _MAX_HISTORY * 2
        if len(self._history) > max_msgs:
            self._history = self._history[-max_msgs:]

    def _load_memory(self) -> None:
        try:
            if os.path.exists(self._memory_path):
                with open(self._memory_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    self._history = data[-_MAX_HISTORY * 2:]
        except Exception:
            self._history = []

    def _save_memory(self) -> None:
        try:
            os.makedirs(os.path.dirname(self._memory_path), exist_ok=True)
            with open(self._memory_path, 'w', encoding='utf-8') as f:
                json.dump(self._history, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
