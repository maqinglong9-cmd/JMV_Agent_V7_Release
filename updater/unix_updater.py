"""macOS / Linux 二进制自替换升级逻辑

原理：
  1. 下载新二进制文件到临时目录并校验 SHA256
  2. 生成一个 shell 脚本，内容：
       等待当前进程退出 → 替换二进制 → 启动新版本 → 删除自身
  3. 以独立进程启动 shell 脚本，然后当前进程调用 sys.exit()
"""
import os
import sys
import stat
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
    下载新版二进制并通过 shell 脚本完成热替换。
    成功后当前进程会退出，新版本自动启动。
    失败时抛出 RuntimeError。
    """
    update_dir = get_update_dir()
    new_bin = os.path.join(update_dir, "BrainAgent_new")

    # ── 1. 下载 ────────────────────────────────────────────
    try:
        download_file(download_url, new_bin, progress_cb)
    except Exception as e:
        raise RuntimeError(f"下载失败: {e}") from e

    # ── 2. 校验 ──────────────────────────────────��─────────
    if not verify_sha256(new_bin, sha256):
        os.remove(new_bin)
        raise RuntimeError("SHA256 校验失败，已删除损坏文件，请重试。")

    # ── 3. 设置可执行权限 ───────────────────────────────────
    os.chmod(new_bin, os.stat(new_bin).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    # ── 4. 生成替换脚本 ────────────────────────────────────
    current_bin = sys.executable
    pid = os.getpid()
    sh_path = os.path.join(update_dir, "do_update.sh")
    sh_content = f"""#!/bin/sh
echo "[JMV 升级] 等待主程序退出 (PID={pid})..."
while kill -0 {pid} 2>/dev/null; do
    sleep 1
done
echo "[JMV 升级] 替换可执行文件..."
mv -f "{new_bin}" "{current_bin}"
if [ $? -ne 0 ]; then
    echo "[JMV 升级] 替换失败，请手动复制 {new_bin} 到 {current_bin}"
    exit 1
fi
echo "[JMV 升级] 启动新版本..."
"{current_bin}" &
echo "[JMV 升级] 完成，清理临时文件..."
rm -f "$0"
"""
    with open(sh_path, "w", encoding="utf-8") as f:
        f.write(sh_content)
    os.chmod(sh_path, os.stat(sh_path).st_mode | stat.S_IXUSR)

    # ── 5. 启动脚本并退出当前进程 ──────────────────────────
    subprocess.Popen(
        ["/bin/sh", sh_path],
        start_new_session=True,
        close_fds=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    sys.exit(0)
