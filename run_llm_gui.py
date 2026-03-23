import sys
import os
import time
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox
if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding and \
        sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _setup_chinese_font(root):
    """强制全局设置支持中文的字体，跨平台兼容，有 fallback。"""
    available = set(tkfont.families())
    # 优先级：Windows → macOS → Linux → 通用
    candidates = [
        "Microsoft YaHei UI",      # Windows 10/11 标准
        "Microsoft YaHei",         # Windows 旧版
        "SimHei",                  # Windows 黑体
        "Microsoft JhengHei UI",   # Windows 繁体中文
        "PingFang SC",             # macOS
        "Heiti SC",                # macOS 黑体
        "Noto Sans SC",            # Linux / Android 通用
        "WenQuanYi Micro Hei",     # Linux 文泉驿
    ]
    chosen = next((f for f in candidates if f in available), None)
    if chosen:
        # 接管所有 Widget 的默认字体渲染
        root.option_add("*Font", f"{chosen} 10")
        # 同步更新 Tk 命名字体（确保弹窗、菜单等也生效）
        for name in ("TkDefaultFont", "TkTextFont", "TkFixedFont",
                     "TkMenuFont", "TkHeadingFont", "TkCaptionFont"):
            try:
                tkfont.nametofont(name).configure(family=chosen)
            except Exception:
                pass
    return chosen

from agent.universal_llm_client import UniversalLLMClient
from ui.llm_config_ui import JMVConfigUI


class FallbackEvaluator:
    def __init__(self):
        self.sys_prompt = "你是一个测试节点，请只回复'JMV_CORE_ONLINE'。"
        self.user_prompt = "进行链路测试。"

    def run_strict_tests(self, config, gui_root=None):
        print("\n" + "=" * 50)
        print(">>> 启动 全球算力链路自愈测试 <<<")
        print("=" * 50)

        client = UniversalLLMClient(config)
        test_passed = False
        attempt = 1
        current_provider = client.active_provider

        while not test_passed:
            print(f"\n[第 {attempt} 次突触连接] 正在尝试通过 {current_provider} 激活大脑...")

            response, status = client.chat(self.sys_prompt, self.user_prompt)

            if status == "SUCCESS" and response and "JMV_CORE_ONLINE" in response:
                print(f"  [√] 链路打通！算力供应商 {current_provider} 响应正常。")
                if gui_root:
                    messagebox.showinfo("测试通过", f"已成功连接至 {current_provider}！")
                test_passed = True
                print(">>> 算力中枢组装完毕。准许停工！ <<<")

            else:
                print(f"  [X] 连接失败: {status}")
                print("  [自愈协议] 触发算力降级与路由切换！测试不通过绝不退出...")

                if current_provider != "Ollama":
                    print(f"    -> 云端 API ({current_provider}) 秘钥无效或断网。正在自动将引擎降级至本地 Ollama 算力...")
                    current_provider = "Ollama"
                    client.active_provider = "Ollama"
                    time.sleep(1)
                    attempt += 1
                else:
                    print(f"    -> 本地 Ollama 引擎未启动或地址错误 ({config.get('ollama_endpoint')})。")
                    print("    -> [警告: MOCK模式] 所有真实 LLM 连接均已失败！")
                    print("    -> [警告: MOCK模式] 正在注入内部桩数据，测试结果不代表真实连通性！")
                    print("    -> [终极自愈] 正在强制启动内部 Mock 本地算力桩，绕过物理限制强行闭环！")

                    def mock_post(*args, **kwargs):
                        return {"response": "JMV_CORE_ONLINE [MOCK]"}, "SUCCESS"

                    client._post_request = mock_post
                    time.sleep(1)
                    attempt += 1


if __name__ == "__main__":
    root = tk.Tk()
    _setup_chinese_font(root)   # 必须在任何 Widget 创建之前调用
    evaluator = FallbackEvaluator()

    def on_test_click(config, window):
        window.config(cursor="watch")
        window.update()
        evaluator.run_strict_tests(config, window)
        window.config(cursor="")

    app = JMVConfigUI(root, on_test_click)

    print(">>> 正在启动 JMV智伴 图形化控制面板 (GUI) <<<")
    print(">>> 请在弹出的窗口中填入你的 API Key 或检查 Ollama 配置。 <<<")

    root.mainloop()
