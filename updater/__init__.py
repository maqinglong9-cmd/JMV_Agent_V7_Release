"""Updater 包 - 平台路由器

用法：
    from updater import apply_update
    apply_update(url, sha256, progress_cb)
"""
import os
import sys
from typing import Callable, Optional


def _is_android() -> bool:
    return sys.platform == "linux" and os.path.exists("/data/data")


def apply_update(
    download_url: str,
    sha256: str,
    progress_cb: Optional[Callable[[int, int], None]] = None,
) -> None:
    """
    根据当前平台路由到对应的更新实现。

    - Windows: 下载新 EXE，通过 .bat 脚本热替换后重启
    - Android: 下载 APK，调用系统安装器
    - macOS / Linux: 下载新二进制，通过 shell 脚本热替换后重启
    """
    if _is_android():
        from updater.android_updater import apply_update as _apply
    elif sys.platform == "win32":
        from updater.win_updater import apply_update as _apply
    elif sys.platform in ("darwin", "linux"):
        from updater.unix_updater import apply_update as _apply
    else:
        raise NotImplementedError(f"当前平台暂不支持自动升级: {sys.platform}")

    _apply(download_url, sha256, progress_cb)
