"""Android 前台服务入口（python-for-android Service）
此文件由 buildozer android.services 配置加载，在独立进程中运行。
作用：保持 App 后台存活，防止系统因内存不足杀死进程。
"""
import os
import sys
import time


def _start_foreground_service():
    """启动 Android 前台服务（显示持久通知条目）。"""
    try:
        from android import AndroidService  # type: ignore
        service = AndroidService('JMV智伴', '后台运行中...')
        service.start('JMV智伴 Agent 服务已启动')
        return service
    except ImportError:
        return None


def _write_pid():
    """写入 PID 文件，供主进程检测服务是否存活。"""
    try:
        workspace = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'jmv_workspace'
        )
        os.makedirs(workspace, exist_ok=True)
        with open(os.path.join(workspace, 'service.pid'), 'w') as f:
            f.write(str(os.getpid()))
    except Exception:
        pass


def main():
    """服务主循环：保持进程存活，每 30 秒心跳一次。"""
    _start_foreground_service()
    _write_pid()
    while True:
        time.sleep(30)


if __name__ == '__main__':
    main()
