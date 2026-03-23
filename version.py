"""JMV智伴 版本常量 - 所有模块通过此文件获取当前版本号"""

__version__ = "1.2.2"
APP_NAME    = "JMV智伴"
PACKAGE_ID  = "org.jmv.jmvagent"   # 与 buildozer.spec 保持一致

# 远程版本信息 JSON 地址（替换为你的实际发布地址）
# 推荐使用 GitHub Releases raw 文件或自有 OSS/CDN
UPDATE_CHECK_URL = "https://raw.githubusercontent.com/maqinglong9-cmd/JMV_Agent_V7_Release/main/latest.json"

# 本地开发测试 URL（指向项目根目录的 latest.json，开发期间使用）
# 使用方式：将 version_checker.py 中的 url 参数替换为此值
import os as _os
_LOCAL_LATEST = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'latest.json')
LOCAL_UPDATE_URL = f"file:///{_LOCAL_LATEST.replace(chr(92), '/')}"


def parse_version(v: str) -> tuple:
    """将 '1.2.3' 解析为 (1, 2, 3) 便于比较"""
    try:
        return tuple(int(x) for x in v.strip().split("."))
    except Exception:
        return (0, 0, 0)


def is_newer(remote: str, local: str = __version__) -> bool:
    """返回 True 表示 remote 版本比 local 更新"""
    return parse_version(remote) > parse_version(local)
