"""带进度回调的文件下载器 + SHA256 完整性校验"""
import hashlib
import os
import tempfile
import urllib.request
import urllib.error
from typing import Callable, Optional

_CHUNK = 65536  # 64 KB 分块读取


def download_file(
    url: str,
    dest_path: str,
    progress_cb: Optional[Callable[[int, int], None]] = None,
) -> str:
    """
    下载 url 到 dest_path，支持进度回调。

    progress_cb(downloaded_bytes, total_bytes) — total_bytes 为 -1 表示未知大小。
    返回实际写入的路径（与 dest_path 相同）。
    抛出 OSError / urllib.error.URLError 等异常。
    """
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "JMVAgent-Updater/1.0"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        total = int(resp.headers.get("Content-Length", -1))
        downloaded = 0

        with open(dest_path, "wb") as f:
            while True:
                chunk = resp.read(_CHUNK)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if progress_cb:
                    progress_cb(downloaded, total)

    return dest_path


def verify_sha256(file_path: str, expected: str) -> bool:
    """
    计算文件 SHA256 并与 expected 比较（大小写不敏感）。
    文件不存在或哈希不匹配均返回 False。
    """
    if not os.path.isfile(file_path):
        return False

    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(_CHUNK), b""):
            h.update(chunk)

    return h.hexdigest().lower() == expected.strip().lower()


def get_update_dir() -> str:
    """返回平台对应的临时下载目录"""
    return os.path.join(tempfile.gettempdir(), "jmv_update")
