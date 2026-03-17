"""远程版本检查模块 - 通过 HTTP 获取最新版本信息"""
import json
import urllib.request
import urllib.error
from version import __version__, UPDATE_CHECK_URL, is_newer

# 期望的远程 JSON 格式示例：
# {
#   "version": "1.2.0",
#   "release_notes": "修复若干问题，优化性能",
#   "assets": {
#     "windows": {
#       "url": "https://example.com/BrainAgent_1.2.0.exe",
#       "sha256": "abc123..."
#     },
#     "android": {
#       "url": "https://example.com/BrainAgent_1.2.0.apk",
#       "sha256": "def456..."
#     }
#   }
# }

_TIMEOUT = 10  # HTTP 超时秒数


def check_for_update(url: str = UPDATE_CHECK_URL) -> dict:
    """
    检查远程是否有新版本。

    返回值：
      {
        "has_update": bool,
        "current": str,          # 当前版本号
        "latest": str,           # 远程最新版本号
        "release_notes": str,
        "assets": {
          "windows": {"url": ..., "sha256": ...},
          "android": {"url": ..., "sha256": ...}
        },
        "error": str | None      # 出错时的错误信息
      }
    """
    result = {
        "has_update": False,
        "current": __version__,
        "latest": __version__,
        "release_notes": "",
        "assets": {},
        "error": None,
    }

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": f"JMVAgent/{__version__}"},
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        remote_version = data.get("version", __version__)
        result["latest"]        = remote_version
        result["release_notes"] = data.get("release_notes", "")
        result["assets"]        = data.get("assets", {})
        result["has_update"]    = is_newer(remote_version)

    except urllib.error.URLError as e:
        result["error"] = f"网络错误: {e.reason}"
    except json.JSONDecodeError as e:
        result["error"] = f"版本信息解析失败: {e}"
    except Exception as e:
        result["error"] = f"检查更新失败: {e}"

    return result
