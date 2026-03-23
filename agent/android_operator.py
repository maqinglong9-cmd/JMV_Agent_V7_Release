"""
Android 底层操作模块
===================
通过 Android shell 命令实现真实控制。
- 在 Android 设备上直接执行（无需 ADB）
- 在非 Android 环境下路由到 ADB 连接设备执行（支持开发调试）
零外部依赖——全部使用 subprocess + stdlib。
"""
import os
import re
import subprocess
import sys
import urllib.parse
from typing import Dict, List, Tuple

# ── Android Keycode 常量 ──────────────────────────────────────────────────
KEY_HOME        = 3
KEY_BACK        = 4
KEY_MENU        = 82
KEY_POWER       = 26
KEY_VOLUME_UP   = 24
KEY_VOLUME_DOWN = 25
KEY_ENTER       = 66
KEY_DELETE      = 67
KEY_SPACE       = 62
KEY_DPAD_UP     = 19
KEY_DPAD_DOWN   = 20
KEY_DPAD_LEFT   = 21
KEY_DPAD_RIGHT  = 22
KEY_DPAD_CENTER = 23

# 字符串名称到 keycode 映射
_KEYCODE_MAP: Dict[str, int] = {
    "HOME": KEY_HOME, "BACK": KEY_BACK, "MENU": KEY_MENU,
    "POWER": KEY_POWER, "VOLUME_UP": KEY_VOLUME_UP,
    "VOLUME_DOWN": KEY_VOLUME_DOWN, "ENTER": KEY_ENTER,
    "DELETE": KEY_DELETE, "SPACE": KEY_SPACE,
    "DPAD_UP": KEY_DPAD_UP, "DPAD_DOWN": KEY_DPAD_DOWN,
    "DPAD_LEFT": KEY_DPAD_LEFT, "DPAD_RIGHT": KEY_DPAD_RIGHT,
    "DPAD_CENTER": KEY_DPAD_CENTER,
}


def _is_android() -> bool:
    """判断当前运行环境是否为 Android。"""
    if os.path.exists('/system/build.prop'):
        return True
    try:
        with open('/proc/version', 'r') as f:
            return 'android' in f.read().lower()
    except OSError:
        return False


class AndroidOperator:
    """
    Android 底层操作：可操作市面上所有 App 和 Android 操作系统本身。
    在 Android 设备上直接执行 shell 命令；在非 Android 环境下使用 adb。
    零外部依赖——全部使用 subprocess + stdlib。
    """

    def __init__(self, adb_device: str = ''):
        """
        adb_device: ADB 设备序列号（非 Android 环境可选指定，空则使用默认连接设备）。
        """
        self._on_android = _is_android()
        self._adb_device = adb_device

    # ── 内部 shell 执行 ────────────────────────────────────────────────────

    def _shell(self, cmd: str, timeout: int = 10) -> Tuple[bool, str]:
        """
        执行 shell 命令。
        Android 环境：直接 sh -c cmd。
        非 Android 环境：通过 adb shell 执行。
        返回 (success, output)。
        """
        try:
            if self._on_android:
                args = ['sh', '-c', cmd]
            else:
                adb_args = ['adb']
                if self._adb_device:
                    adb_args += ['-s', self._adb_device]
                adb_args.append('shell')
                args = adb_args + [cmd]

            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=timeout,
            )
            output = (result.stdout + result.stderr).strip()
            if result.returncode == 0:
                return True, output
            return False, output or f"退出码 {result.returncode}"
        except subprocess.TimeoutExpired:
            return False, f"命令超时（{timeout}s）"
        except FileNotFoundError as e:
            return False, f"命令未找到: {e}"
        except Exception as e:
            return False, f"执行异常: {e}"

    # ── App 管理 ───────────────────────────────────────────────────────────

    def launch_app(self, package: str, activity: str = '') -> Tuple[bool, str]:
        """启动 App。"""
        if activity:
            target = f"{package}/{activity}"
        else:
            target = package
        if activity:
            cmd = f"am start -n {target}"
        else:
            cmd = f"monkey -p {package} -c android.intent.category.LAUNCHER 1"
        return self._shell(cmd)

    def stop_app(self, package: str) -> Tuple[bool, str]:
        """强制停止 App。"""
        return self._shell(f"am force-stop {package}")

    def clear_app_data(self, package: str) -> Tuple[bool, str]:
        """清除 App 数据。"""
        return self._shell(f"pm clear {package}")

    def install_apk(self, apk_path: str) -> Tuple[bool, str]:
        """安装 APK（-r 允许覆盖安装）。"""
        return self._shell(f"pm install -r {apk_path}", timeout=60)

    def uninstall_app(self, package: str) -> Tuple[bool, str]:
        """卸载 App。"""
        return self._shell(f"pm uninstall {package}")

    def list_packages(self, filter_str: str = '') -> List[str]:
        """列出已安装的包名。filter_str 可选过滤关键字。"""
        ok, output = self._shell("pm list packages")
        if not ok:
            return []
        packages = []
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("package:"):
                pkg = line[len("package:"):]
                if not filter_str or filter_str in pkg:
                    packages.append(pkg)
        return packages

    def get_app_info(self, package: str) -> Dict:
        """获取 App 详细信息（版本/安装路径/权限）。"""
        ok, output = self._shell(f"dumpsys package {package}")
        if not ok:
            return {"error": output}
        info: Dict = {"package": package, "raw": output[:2000]}
        # 提取版本号
        m = re.search(r'versionName=(\S+)', output)
        if m:
            info["version"] = m.group(1)
        m = re.search(r'versionCode=(\d+)', output)
        if m:
            info["version_code"] = m.group(1)
        # 提取安装路径
        m = re.search(r'codePath=(\S+)', output)
        if m:
            info["install_path"] = m.group(1)
        return info

    # ── UI 交互 ────────────────────────────────────────────────────────────

    def tap(self, x: int, y: int) -> Tuple[bool, str]:
        """点击屏幕坐标 (x, y)。"""
        return self._shell(f"input tap {x} {y}")

    def swipe(self, x1: int, y1: int, x2: int, y2: int,
              duration_ms: int = 300) -> Tuple[bool, str]:
        """滑动：从 (x1,y1) 到 (x2,y2)，持续 duration_ms 毫秒。"""
        return self._shell(f"input swipe {x1} {y1} {x2} {y2} {duration_ms}")

    def type_text(self, text: str) -> Tuple[bool, str]:
        """输入文字（自动处理空格和特殊字符）。"""
        # 替换空格为 %s（input text 的兼容写法），并做 URL 编码
        encoded = urllib.parse.quote(text, safe='')
        # input text 接受 URL 编码字符串
        return self._shell(f"input text '{encoded}'")

    def press_key(self, keycode) -> Tuple[bool, str]:
        """按下按键。keycode 可传 int 或字符串名称（如 'HOME'）。"""
        if isinstance(keycode, str):
            code = _KEYCODE_MAP.get(keycode.upper(), keycode)
        else:
            code = keycode
        return self._shell(f"input keyevent {code}")

    def long_press(self, x: int, y: int, duration_ms: int = 1000) -> Tuple[bool, str]:
        """长按坐标 (x, y)，持续 duration_ms 毫秒。"""
        return self._shell(f"input swipe {x} {y} {x} {y} {duration_ms}")

    # ── 屏幕与视觉 ────────────────────────────────────────────────────────

    def screenshot(self, save_path: str = '') -> Tuple[bool, str]:
        """
        截图并保存。
        save_path 为空时保存到 /sdcard/jmv_screenshot.png。
        返回 (success, file_path_or_error)。
        """
        dest = save_path or '/sdcard/jmv_screenshot.png'
        ok, out = self._shell(f"screencap -p {dest}")
        if ok:
            return True, dest
        return False, out

    def get_ui_hierarchy(self) -> Tuple[bool, str]:
        """获取当前界面 UI 层级 XML（uiautomator dump）。"""
        dump_path = '/sdcard/jmv_ui_dump.xml'
        ok, out = self._shell(f"uiautomator dump {dump_path} && cat {dump_path}", timeout=15)
        return ok, out

    def get_screen_size(self) -> Tuple[int, int]:
        """获取屏幕分辨率，返回 (width, height)。失败时返回 (0, 0)。"""
        ok, output = self._shell("wm size")
        if ok:
            m = re.search(r'(\d+)x(\d+)', output)
            if m:
                return int(m.group(1)), int(m.group(2))
        return 0, 0

    # ── 系统控制 ───────────────────────────────────────────────────────────

    def get_system_info(self) -> Dict:
        """获取设备系统信息（型号/Android版本/内存/电量）。"""
        info: Dict = {}
        # 基本属性
        ok, out = self._shell("getprop ro.product.model")
        if ok:
            info["model"] = out.strip()
        ok, out = self._shell("getprop ro.build.version.release")
        if ok:
            info["android_version"] = out.strip()
        ok, out = self._shell("getprop ro.product.manufacturer")
        if ok:
            info["manufacturer"] = out.strip()
        # 内存信息
        ok, out = self._shell("cat /proc/meminfo | head -3")
        if ok:
            info["memory_info"] = out.strip()
        # 电池信息
        ok, out = self._shell("dumpsys battery | grep level")
        if ok:
            m = re.search(r'level:\s*(\d+)', out)
            if m:
                info["battery_level"] = int(m.group(1))
        return info

    def set_setting(self, namespace: str, key: str, value: str) -> Tuple[bool, str]:
        """
        设置系统设置。
        namespace: 'system' | 'secure' | 'global'
        """
        return self._shell(f"settings put {namespace} {key} {value}")

    def get_setting(self, namespace: str, key: str) -> str:
        """读取系统设置。"""
        ok, out = self._shell(f"settings get {namespace} {key}")
        return out.strip() if ok else ""

    def send_broadcast(self, action: str, extras: Dict = None) -> Tuple[bool, str]:
        """
        发送系统广播。
        extras 格式：{'str_key': 'str_val', 'int_key': 42}（自动判断类型）。
        """
        if extras is None:
            extras = {}
        cmd = f"am broadcast -a {action}"
        for k, v in extras.items():
            if isinstance(v, bool):
                cmd += f" --ez {k} {str(v).lower()}"
            elif isinstance(v, int):
                cmd += f" --ei {k} {v}"
            else:
                cmd += f" --es {k} '{v}'"
        return self._shell(cmd)

    def start_service(self, package: str, service: str) -> Tuple[bool, str]:
        """启动 Android Service。"""
        return self._shell(f"am startservice -n {package}/{service}")
