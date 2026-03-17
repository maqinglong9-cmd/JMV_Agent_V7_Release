"""JMV智伴 Tkinter 算力配置面板"""
import os
import json
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox, ttk


def _pick_cjk_font(size=10, bold=False):
    """
    返回当前系统可用的最佳中文字体 tuple。
    候选列表按 CJK 支持度和常见度排序，确保中文不乱码。
    找不到任何 CJK 字体时回退到系统默认（极少见）。
    """
    available = set(tkfont.families())
    # 按优先级排序：UI 字体 > 常规字体 > 兜底
    candidates = [
        # Windows 高质量 CJK UI 字体
        "Microsoft YaHei UI",
        "Microsoft YaHei",
        # Windows 常见 CJK 字体（几乎所有 Windows 都有）
        "SimSun",
        "NSimSun",
        "SimHei",
        "KaiTi",
        "FangSong",
        # 繁体中文 Windows
        "Microsoft JhengHei UI",
        "Microsoft JhengHei",
        # macOS
        "PingFang SC",
        "PingFang TC",
        "Heiti SC",
        "STHeiti",
        # Linux / 跨平台
        "Noto Sans CJK SC",
        "Noto Sans SC",
        "WenQuanYi Micro Hei",
        "WenQuanYi Zen Hei",
        "Droid Sans Fallback",
    ]
    family = next((f for f in candidates if f in available), None)
    weight = "bold" if bold else "normal"
    if family:
        return (family, size, weight)
    # 终极兜底：用 tkinter 内置默认字体（可能不支持 CJK，但不会崩溃）
    return ("TkDefaultFont", size, weight)

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONFIG_FILE = os.path.join(_PROJECT_ROOT, "jmv_compute_config.json")


_KEY_FIELDS = {"gemini_key", "openai_key", "claude_key", "deepseek_key"}
_ENV_MAP = {
    "gemini_key": "GEMINI_API_KEY",
    "openai_key": "OPENAI_API_KEY",
    "claude_key": "ANTHROPIC_API_KEY",
    "deepseek_key": "DEEPSEEK_API_KEY",
}


class JMVConfigUI:
    def __init__(self, root, on_test_callback):
        self.root = root
        self.root.title("JMV智伴 - 全球算力枢纽中控台")
        self.root.geometry("550x650")
        self.root.configure(padx=20, pady=20)

        self.on_test_callback = on_test_callback
        self.config = self._load_config()
        self.entries = {}

        self._build_ui()

    def _load_config(self):
        config = {
            "active_provider": "Ollama",
            "ollama_endpoint": "http://localhost:11434/api/generate",
            "ollama_model": "llama3",
            "gemini_model": "gemini-2.5-flash",
            "openai_model": "gpt-3.5-turbo",
            "claude_model": "claude-3-haiku-20240307",
            "deepseek_model": "deepseek-chat",
        }
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
            # 只加载非密钥字段
            for k, v in saved.items():
                if k not in _KEY_FIELDS:
                    config[k] = v
        # 密钥从环境变量读取（仅用于 UI 显示占位，不持久化）
        for field, env_var in _ENV_MAP.items():
            config[field] = os.environ.get(env_var, "")
        return config

    def _save_config(self):
        for key, entry in self.entries.items():
            val = entry.get()
            if key in _KEY_FIELDS:
                # 密钥写入环境变量，不写入文件
                if val:
                    os.environ[_ENV_MAP[key]] = val
            else:
                self.config[key] = val
        self.config["active_provider"] = self.active_var.get()
        # 只保存非密钥字段到文件
        safe_config = {k: v for k, v in self.config.items() if k not in _KEY_FIELDS}
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(safe_config, f, indent=2)
        return self.config

    def _build_ui(self):
        tk.Label(self.root, text="JMV智伴 核心算力引擎配置",
                 font=_pick_cjk_font(size=16, bold=True)).pack(pady=(0, 20))

        frame_top = tk.Frame(self.root)
        frame_top.pack(fill="x", pady=5)
        tk.Label(frame_top, text="当前主控算力:").pack(side="left")
        self.active_var = tk.StringVar(value=self.config.get("active_provider", "Ollama"))
        providers = ["Ollama", "Gemini", "OpenAI", "Claude", "DeepSeek"]
        ttk.Combobox(frame_top, textvariable=self.active_var,
                     values=providers, state="readonly").pack(side="left", padx=10)

        fields = [
            ("ollama_endpoint", "Ollama 接口地址 (本地断网用):"),
            ("ollama_model",    "Ollama 模型名称 (如 llama3):"),
            ("gemini_key",      "Google Gemini API Key:"),
            ("gemini_model",    "Gemini 模型名称 (如 gemini-2.5-flash):"),
            ("openai_key",      "OpenAI API Key:"),
            ("openai_model",    "OpenAI 模型名称 (如 gpt-4o):"),
            ("claude_key",      "Anthropic Claude API Key:"),
            ("claude_model",    "Claude 模型名称 (如 claude-sonnet-4-6):"),
            ("deepseek_key",    "DeepSeek API Key:"),
            ("deepseek_model",  "DeepSeek 模型名称 (如 deepseek-chat):"),
        ]

        frame_form = tk.Frame(self.root)
        frame_form.pack(fill="both", expand=True)

        for key, label_text in fields:
            row = tk.Frame(frame_form)
            row.pack(fill="x", pady=5)
            tk.Label(row, text=label_text, width=25, anchor="w").pack(side="left")
            entry = tk.Entry(row, width=40)
            if "key" in key:
                entry.config(show="*")
            entry.insert(0, self.config.get(key, ""))
            entry.pack(side="left", fill="x", expand=True)
            self.entries[key] = entry

        frame_btn = tk.Frame(self.root)
        frame_btn.pack(pady=20)
        tk.Button(frame_btn, text="保存配置",
                  command=self._save_ui, bg="#4CAF50", fg="white", width=15).pack(side="left", padx=10)
        tk.Button(frame_btn, text="运行神经握手测试",
                  command=self._run_test_ui, bg="#2196F3", fg="white", width=20).pack(side="left", padx=10)

    def _save_ui(self):
        self._save_config()
        messagebox.showinfo("成功", "JMV智伴 算力配置已写入本地硬盘。")

    def _run_test_ui(self):
        config = self._save_config()
        self.on_test_callback(config, self.root)
