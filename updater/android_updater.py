"""Android APK 安装触发逻辑

Android 不允许应用覆盖自身 APK，必须通过系统 PackageInstaller 安装。
本模块使用 pyjnius 调用 Android Java API。
"""
import os
from typing import Callable, Optional
from updater.downloader import download_file, verify_sha256, get_update_dir

# Android 专用下载目录（应用私有存储，无需额外权限）
_ANDROID_DOWNLOAD_DIR = "/data/data/org.jmv.jmvagent/files/update"


def _get_android_download_dir() -> str:
    """优先使用应用私有目录，回退到临时目录"""
    private = _ANDROID_DOWNLOAD_DIR
    try:
        os.makedirs(private, exist_ok=True)
        return private
    except OSError:
        return get_update_dir()


def apply_update(
    download_url: str,
    sha256: str,
    progress_cb: Optional[Callable[[int, int], None]] = None,
) -> None:
    """
    下载 APK 并调用系统安装器完成安装。
    安装完成后系统会自动重启应用。
    失败时抛出 RuntimeError。
    """
    apk_path = os.path.join(_get_android_download_dir(), "update.apk")

    # ── 1. 下载 ────────────────────────────────────────────
    try:
        download_file(download_url, apk_path, progress_cb)
    except Exception as e:
        raise RuntimeError(f"下载失败: {e}") from e

    # ── 2. 校验 ────────────────────────────────────────────
    if not verify_sha256(apk_path, sha256):
        os.remove(apk_path)
        raise RuntimeError("SHA256 校验失败，已删除损坏文件，请重试。")

    # ── 3. 调用系统安装器 ───────────────────────────────────
    try:
        from jnius import autoclass  # type: ignore  # pyjnius，仅 Android 可用

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Intent         = autoclass("android.content.Intent")
        Uri            = autoclass("android.net.Uri")
        File           = autoclass("java.io.File")
        Build          = autoclass("android.os.Build")

        ctx     = PythonActivity.mActivity
        apk_uri = _get_install_uri(ctx, apk_path, Build, Uri, File)

        intent = Intent(Intent.ACTION_VIEW)
        intent.setDataAndType(apk_uri, "application/vnd.android.package-archive")
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_GRANT_READ_URI_PERMISSION)
        ctx.startActivity(intent)

    except ImportError:
        raise RuntimeError("pyjnius 不可用，仅支持在 Android 设备上运行此操作。")
    except Exception as e:
        raise RuntimeError(f"启动安装器失败: {e}") from e


def _get_install_uri(ctx, apk_path: str, Build, Uri, File):
    """
    Android 7+ 需要通过 FileProvider 获取 content:// URI；
    旧版本可直接使用 file:// URI。
    """
    Build_VERSION = __import__("jnius").autoclass("android.os.Build$VERSION")
    if Build_VERSION.SDK_INT >= 24:
        # 需要在 AndroidManifest 中声明 FileProvider（Buildozer 会自动处理）
        FileProvider = __import__("jnius").autoclass(
            "androidx.core.content.FileProvider"
        )
        authority = "org.jmv.jmvagent.fileprovider"
        java_file = File(apk_path)
        return FileProvider.getUriForFile(ctx, authority, java_file)
    else:
        return Uri.parse(f"file://{apk_path}")
