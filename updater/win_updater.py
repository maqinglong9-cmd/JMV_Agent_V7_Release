"""Windows EXE 自替换升级逻辑

原理：
  1. 下载新 EXE 到临时目录并校验 SHA256
  2. 生成一个 .bat 中继脚本，内容：
       等待当前进程退出 → 替换 EXE → 启动新 EXE → 删除自身
  3. 以独立进程启动 .bat，然后当前进程调用 sys.exit()
"""
import os
import sys
import subprocess
import tempfile
from typing import Callable, Optional
from updater.downloader import download_file, verify_sha256, get_update_dir


def apply_update(
    download_url: str,
    sha256: str,
    progress_cb: Optional[Callable[[int, int], None]] = None,
) -> None:
    """
    下载 Windows 新版 EXE 并通过 .bat 脚本完成热替换。
    成功后当前进程会退出，新版本自动启动。
    失败时抛出 RuntimeError。
    """
    update_dir = get_update_dir()
    new_exe    = os.path.join(update_dir, "BrainAgent_new.exe")

    # ── 1. 下载 ────────────────────────────────────────────
    try:
        download_file(download_url, new_exe, progress_cb)
    except Exception as e:
        raise RuntimeError(f"下载失败: {e}") from e

    # ── 2. 校验 ────────────────────────────────────────────
    if not verify_sha256(new_exe, sha256):
        os.remove(new_exe)
        raise RuntimeError("SHA256 校验失败，已删除损坏文件，请重试。")

    # ── 3. 生成替换脚本 ────────────────────────────────────
    current_exe = sys.executable
    bat_path    = os.path.join(update_dir, "do_update.bat")
    bat_content = f"""@echo off
chcp 65001 >nul
echo [JMV 升级] 等待主程序退出...
:wait
tasklist /FI "PID eq {os.getpid()}" 2>nul | find "{os.getpid()}" >nul
if not errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto wait
)
echo [JMV 升级] 替换可执行文件...
move /Y "{new_exe}" "{current_exe}"
if errorlevel 1 (
    echo [JMV 升级] 替换失败，请手动复制 {new_exe} 到 {current_exe}
    pause
    exit /b 1
)
echo [JMV 升级] 启动新版本...
start "" "{current_exe}"
echo [JMV 升级] 完成，清理临时文件...
del "%~f0"
"""
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(bat_content)

    # ── 4. 启动脚本并退出当前进程 ──────────────────────────
    subprocess.Popen(
        ["cmd.exe", "/c", bat_path],
        creationflags=subprocess.CREATE_NEW_CONSOLE,
        close_fds=True,
    )
    sys.exit(0)
