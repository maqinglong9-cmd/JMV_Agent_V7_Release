"""工具箱组件：Agent 的手和脚，负责执行具体动作"""
import os
import re
import math
import struct
import time
import urllib.request
import urllib.parse
import urllib.error
import json
from typing import Callable, Dict, Optional


class ToolRegistry:
    """
    工具注册表：内置工具 + 支持动态注册自定义工具。
    所有工具均为纯函数，接收 params 字符串，返回结果字符串。
    """

    _WORKSPACE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'jmv_workspace'))

    def __init__(self, os_operator=None):
        self._tools: Dict[str, Callable[[str], str]] = {}
        self._os_operator = os_operator
        self._ensure_workspace()
        self._register_builtin_tools()

    def _ensure_workspace(self):
        if not os.path.exists(self._WORKSPACE):
            os.makedirs(self._WORKSPACE)

    def _register_builtin_tools(self) -> None:
        self.register("CALL_TOOL_PAINTER",    self._tool_painter)
        self.register("CALL_TOOL_CALCULATOR", self._tool_calculator)
        self.register("CALL_TOOL_SEARCH",     self._tool_search)
        self.register("CALL_TOOL_CODER",      self._tool_coder)
        self.register("CALL_TOOL_TRANSLATE",  self._tool_translate)
        self.register("CALL_TOOL_SUMMARIZE",  self._tool_summarize)
        self.register("CALL_TOOL_FILE_WRITE", self._tool_file_write)
        self.register("CALL_TOOL_SHELL",      self._tool_shell)
        # 保留旧名称兼容性（指向翻译工具）
        self.register("CALL_TOOL_SPACESHIP",  self._tool_translate)

    def register(self, name: str, fn: Callable[[str], str]) -> None:
        self._tools[name] = fn

    def execute(self, decision: str, params: str) -> str:
        tool_key = decision.split("|")[0].replace("DECISION:", "").strip()
        if tool_key in self._tools:
            return self._tools[tool_key](params)
        return f"[执行动作] 未找到工具 '{tool_key}'，仅作语言回复。"

    # ── 真实工具实现 ──────────────────────────────────────────────

    def _tool_painter(self, params: str) -> str:
        """真实图像生成：用纯 Python math/struct 生成 PPM 图像文件"""
        # 颜色主题映射
        color_map = {
            "红": (220, 50, 50), "蓝": (50, 100, 220), "绿": (50, 180, 80),
            "黄": (220, 200, 50), "紫": (150, 50, 200), "橙": (220, 130, 50),
            "白": (240, 240, 240), "黑": (30, 30, 30), "粉": (220, 130, 160),
            "青": (50, 200, 200),
        }
        base_r, base_g, base_b = 100, 150, 220  # 默认蓝色
        for key, rgb in color_map.items():
            if key in params:
                base_r, base_g, base_b = rgb
                break

        width, height = 200, 150
        timestamp = int(time.time())
        filename = f"jmv_image_{timestamp}.ppm"
        filepath = os.path.join(self._WORKSPACE, filename)

        with open(filepath, 'wb') as f:
            header = f"P6\n{width} {height}\n255\n".encode('ascii')
            f.write(header)
            for y in range(height):
                for x in range(width):
                    wave = math.sin(x * 0.08 + y * 0.05) * 40
                    grad = (x / width) * 60
                    r = max(0, min(255, int(base_r + wave - grad)))
                    g = max(0, min(255, int(base_g + wave * 0.5 + grad * 0.3)))
                    b = max(0, min(255, int(base_b - wave * 0.3 + grad * 0.5)))
                    f.write(struct.pack('BBB', r, g, b))

        size_kb = os.path.getsize(filepath) // 1024
        return (f"[执行动作] 图像已生成: {filepath} "
                f"({width}x{height}px, {size_kb}KB, PPM格式，可用图像查看器打开)")

    @staticmethod
    def _tool_calculator(params: str) -> str:
        """真实计算器：从 params 中提取数学表达式并用 eval 沙箱执行"""
        expr = re.sub(r"[^0-9+\-*/().\s]", "", params).strip()
        if not expr:
            return f"[执行动作] 计算器：无法从 '{params}' 中提取有效表达式。"
        try:
            result = eval(expr, {"__builtins__": {}})  # noqa: S307
            return f"[执行动作] 计算结果: {expr} = {result}"
        except Exception as e:
            return f"[执行动作] 计算失败: {e}"

    @staticmethod
    def _tool_search(params: str) -> str:
        """真实搜索：调用 DuckDuckGo Instant Answer API（零 API key）"""
        query = params.strip()
        encoded = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "JMVAgent/1.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            abstract = data.get("AbstractText", "").strip()
            if abstract:
                return f"[执行动作] 搜索结果: {abstract[:300]}"
            topics = data.get("RelatedTopics", [])
            if topics and isinstance(topics[0], dict):
                text = topics[0].get("Text", "").strip()
                if text:
                    return f"[执行动作] 搜索结果: {text[:300]}"
            return f"[执行动作] 搜索完成，未找到 '{query}' 的摘要信息（DuckDuckGo 无直接答案）。"
        except urllib.error.URLError as e:
            return f"[执行动作] 搜索网络错误: {e.reason}"
        except Exception as e:
            return f"[执行动作] 搜索失败: {str(e)}"

    def _tool_coder(self, params: str) -> str:
        """真实代码生成：根据关键词生成可运行的 Python 代码并写入文件"""
        templates = {
            "排序": (
                "quicksort",
                "def quicksort(arr):\n"
                "    if len(arr) <= 1:\n"
                "        return arr\n"
                "    pivot = arr[len(arr) // 2]\n"
                "    left = [x for x in arr if x < pivot]\n"
                "    mid  = [x for x in arr if x == pivot]\n"
                "    right = [x for x in arr if x > pivot]\n"
                "    return quicksort(left) + mid + quicksort(right)\n\n"
                "if __name__ == '__main__':\n"
                "    data = [3, 6, 8, 10, 1, 2, 1]\n"
                "    print('排序结果:', quicksort(data))\n"
            ),
            "斐波那契": (
                "fibonacci",
                "def fibonacci(n):\n"
                "    a, b = 0, 1\n"
                "    result = []\n"
                "    for _ in range(n):\n"
                "        result.append(a)\n"
                "        a, b = b, a + b\n"
                "    return result\n\n"
                "if __name__ == '__main__':\n"
                "    print('斐波那契数列:', fibonacci(10))\n"
            ),
            "文件": (
                "file_io",
                "def write_file(path, content):\n"
                "    with open(path, 'w', encoding='utf-8') as f:\n"
                "        f.write(content)\n\n"
                "def read_file(path):\n"
                "    with open(path, 'r', encoding='utf-8') as f:\n"
                "        return f.read()\n\n"
                "if __name__ == '__main__':\n"
                "    write_file('test.txt', 'Hello JMV!')\n"
                "    print(read_file('test.txt'))\n"
            ),
        }
        chosen_name, code = "general", (
            "# JMV Agent 生成的通用代码\n"
            "def process(data):\n"
            "    return str(data).upper()\n\n"
            "if __name__ == '__main__':\n"
            "    print(process('hello jmv agent'))\n"
        )
        for keyword, (name, template) in templates.items():
            if keyword in params:
                chosen_name, code = name, template
                break

        timestamp = int(time.time())
        filename = f"generated_{chosen_name}_{timestamp}.py"
        filepath = os.path.join(self._WORKSPACE, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code)

        return (f"[执行动作] 代码已生成: {filepath}\n"
                f"--- 代码内容 ---\n{code}--- 结束 ---")

    def _tool_file_write(self, params: str) -> str:
        """真实文件写入：解析 params 中的文件名和内容，写入沙盒"""
        # 格式：filename.txt 内容是 xxx  或  filename.txt:xxx
        match = re.search(r'(\S+\.\w+)\s+(?:内容是|内容为|:)\s*(.+)', params, re.DOTALL)
        if match:
            filename = match.group(1)
            content = match.group(2).strip()
        else:
            # 兜底：整个 params 作为内容，生成默认文件名
            filename = f"jmv_file_{int(time.time())}.txt"
            content = params.strip()

        if self._os_operator:
            ok, msg = self._os_operator.write_physical_file(filename, content)
            filepath = os.path.join(self._os_operator.workspace, filename)
        else:
            filepath = os.path.join(self._WORKSPACE, filename)
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                ok, msg = True, "写入成功"
            except Exception as e:
                ok, msg = False, str(e)

        if ok:
            return f"[执行动作] 文件已写入: {filepath} ({len(content)} 字符)"
        return f"[执行动作] 文件写入失败: {msg}"

    def _tool_shell(self, params: str) -> str:
        """真实终端执行：在沙盒中执行 shell 命令"""
        # 提取命令：去掉"执行命令"、"运行"等前缀
        command = re.sub(r'^(执行命令|运行命令|终端执行|shell|cmd)\s*', '', params.strip(), flags=re.IGNORECASE)
        if not command:
            return "[执行动作] 未提取到有效命令。"

        if self._os_operator:
            ok, msg = self._os_operator.execute_terminal_command(command)
        else:
            import subprocess
            try:
                result = subprocess.run(
                    command, shell=True, cwd=self._WORKSPACE,
                    capture_output=True, text=True,
                    encoding='utf-8', errors='replace', timeout=10
                )
                if result.returncode == 0:
                    out = result.stdout.strip()
                    ok, msg = True, f"执行成功。输出: {out if out else '<无输出>'}"
                else:
                    ok, msg = False, f"执行失败: {result.stderr.strip()}"
            except Exception as e:
                ok, msg = False, str(e)

        prefix = "[执行动作]" if ok else "[执行动作][错误]"
        return f"{prefix} {msg}"

    @staticmethod
    def _tool_translate(params: str) -> str:
        """
        真实翻译工具：优先调用 LLM，无 LLM 时执行简单字符串变换兜底。
        支持中→英、英→中、自动检测语言。
        """
        text = params.strip()
        if not text:
            return "[执行动作] 翻译工具：输入文本为空。"

        # 检测主要语言（简单启发：含汉字则为中文）
        has_cjk = any('\u4e00' <= c <= '\u9fff' for c in text)
        target_lang = "英语" if has_cjk else "中文"
        prompt_text = f"请将以下文字翻译成{target_lang}，只输出翻译结果，不要解释：\n{text}"

        # 尝试调用系统 LLM（通过环境变量配置）
        try:
            import os
            import json as _json
            import urllib.request as _req

            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'jmv_compute_config.json'
            )
            config: dict = {}
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = _json.load(f)

            # 补充环境变量密钥
            for field, env in [('gemini_key', 'GEMINI_API_KEY'),
                                ('openai_key', 'OPENAI_API_KEY'),
                                ('claude_key', 'ANTHROPIC_API_KEY'),
                                ('deepseek_key', 'DEEPSEEK_API_KEY')]:
                val = os.environ.get(env, '')
                if val:
                    config[field] = val

            if config:
                from agent.universal_llm_client import UniversalLLMClient
                client = UniversalLLMClient(config)
                result, status = client.chat(
                    '你是专业翻译，只输出翻译结果，不要任何解释或前缀。',
                    prompt_text
                )
                if status == 'SUCCESS' and result:
                    return f"[执行动作] 翻译结果（{target_lang}）：{result.strip()}"
        except Exception:
            pass

        # 兜底：无 LLM 时返回原文 + 提示
        return (f"[执行动作] 翻译工具：当前无 LLM 连接，无法执行翻译。"
                f"原文：{text[:200]}")

    @staticmethod
    def _tool_summarize(params: str) -> str:
        """
        真实摘要工具：调用 LLM 对长文本生成简洁摘要。
        无 LLM 时返回前 100 字符作为简单摘要。
        """
        text = params.strip()
        if not text:
            return "[执行动作] 摘要工具：输入文本为空。"

        try:
            import os
            import json as _json

            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'jmv_compute_config.json'
            )
            config: dict = {}
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = _json.load(f)

            for field, env in [('gemini_key', 'GEMINI_API_KEY'),
                                ('openai_key', 'OPENAI_API_KEY'),
                                ('claude_key', 'ANTHROPIC_API_KEY'),
                                ('deepseek_key', 'DEEPSEEK_API_KEY')]:
                val = os.environ.get(env, '')
                if val:
                    config[field] = val

            if config:
                from agent.universal_llm_client import UniversalLLMClient
                client = UniversalLLMClient(config)
                result, status = client.chat(
                    '你是摘要专家，用不超过100字概括核心内容，直接输出摘要。',
                    text[:2000]  # 限制输入长度
                )
                if status == 'SUCCESS' and result:
                    return f"[执行动作] 摘要：{result.strip()}"
        except Exception:
            pass

        # 兜底：截取前 100 字
        summary = text[:100] + ('...' if len(text) > 100 else '')
        return f"[执行动作] 摘要（无LLM，截取前段）：{summary}"

    def list_tools(self) -> list:
        return list(self._tools.keys())
