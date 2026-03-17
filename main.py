"""应用入口"""
import sys
import os

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivy.logger import Logger
from ui.brain_app import BrainAgentApp

if __name__ == "__main__":
    try:
        BrainAgentApp().run()
    except Exception as e:
        Logger.error("main", f"应用启动失败: {e}")
        raise
