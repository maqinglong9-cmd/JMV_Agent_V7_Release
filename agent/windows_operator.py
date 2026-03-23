"""
Windows 底层操作模块
====================
赋予 Agent 真实的 Windows 底层操作能力：
文件系统、注册表、进程管理、窗口控制、键鼠模拟、剪贴板。
零外部依赖——全部使用 ctypes + winreg + subprocess + stdlib。
非 Windows 平台：优雅降级，不崩溃。
"""
import os
import platform
import shutil
import subprocess
import sys
import time
from typing import Dict, List, Tuple, Union

_IS_WINDOWS = sys.platform == 'win32'

# ── 懒加载 Windows 特定模块 ────────────────────────────────────────────────
if _IS_WINDOWS:
    import ctypes
    import ctypes.wintypes as _wt
    try:
        import winreg
    except ImportError:
        winreg = None  # type: ignore
else:
    ctypes = None   # type: ignore
    winreg = None   # type: ignore

# ── Windows 虚拟键码常量 ───────────────────────────────────────────────────
VK_CONTROL = 0x11
VK_SHIFT   = 0x10
VK_MENU    = 0x12  # Alt
VK_LWIN    = 0x5B
VK_C       = 0x43
VK_V       = 0x56
VK_X       = 0x58
VK_Z       = 0x5A
VK_F4      = 0x73
VK_RETURN  = 0x0D
VK_ESCAPE  = 0x1B
VK_TAB     = 0x09
VK_DELETE  = 0x2E
VK_SPACE   = 0x20

# SendInput 相关常量
_INPUT_KEYBOARD   = 1
_INPUT_MOUSE      = 0
_KEYEVENTF_KEYUP  = 0x0002
_MOUSEEVENTF_MOVE         = 0x0001
_MOUSEEVENTF_LEFTDOWN     = 0x0002
_MOUSEEVENTF_LEFTUP       = 0x0004
_MOUSEEVENTF_RIGHTDOWN    = 0x0008
_MOUSEEVENTF_RIGHTUP      = 0x0010
_MOUSEEVENTF_ABSOLUTE     = 0x8000

# Windows Messages
_WM_CLOSE = 0x0010

# Clipboard formats
_CF_UNICODETEXT = 13

# winreg hive 映射
_HIVE_MAP: Dict[str, int] = {}
if winreg:
    _HIVE_MAP = {
        'HKLM': winreg.HKEY_LOCAL_MACHINE,
        'HKCU': winreg.HKEY_CURRENT_USER,
        'HKCR': winreg.HKEY_CLASSES_ROOT,
        'HKU':  winreg.HKEY_USERS,
        'HKCC': winreg.HKEY_CURRENT_CONFIG,
    }
    _REG_TYPE_MAP: Dict[str, int] = {
        'REG_SZ':        winreg.REG_SZ,
        'REG_DWORD':     winreg.REG_DWORD,
        'REG_BINARY':    winreg.REG_BINARY,
        'REG_EXPAND_SZ': winreg.REG_EXPAND_SZ,
        'REG_MULTI_SZ':  winreg.REG_MULTI_SZ,
    }
else:
    _REG_TYPE_MAP = {}


def _require_windows(method_name: str) -> Tuple[bool, str]:
    """返回非 Windows 错误提示。"""
    return False, f"{method_name} 仅支持 Windows 平台（当前: {sys.platform}）"


class WindowsOperator:
    """
    Windows 底层操作：文件系统（真实路径）、注册表、进程管理、
    窗口控制、键鼠模拟、剪贴板。
    零外部依赖——全部使用 ctypes + winreg + subprocess + stdlib。
    """

    # ════════════════════════════════════════════════════════════════════════
    # 文件系统（真实权限，非沙箱）
    # ════════════════════════════════════════════════════════════════════════

    def read_file(self, path: str, encoding: str = 'utf-8') -> Tuple[bool, str]:
        """读取任意路径文件内容。"""
        try:
            with open(path, 'r', encoding=encoding, errors='replace') as f:
                return True, f.read()
        except Exception as e:
            return False, f"读取失败: {e}"

    def write_file(self, path: str, content: str,
                   encoding: str = 'utf-8') -> Tuple[bool, str]:
        """写入文件（自动创建目录）。"""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
            return True, f"已写入 {len(content)} 字符到 {path}"
        except Exception as e:
            return False, f"写入失败: {e}"

    def append_file(self, path: str, content: str,
                    encoding: str = 'utf-8') -> Tuple[bool, str]:
        """追加写入文件。"""
        try:
            with open(path, 'a', encoding=encoding) as f:
                f.write(content)
            return True, f"已追加 {len(content)} 字符到 {path}"
        except Exception as e:
            return False, f"追加失败: {e}"

    def delete_file(self, path: str) -> Tuple[bool, str]:
        """删除文件。"""
        try:
            os.remove(path)
            return True, f"已删除 {path}"
        except Exception as e:
            return False, f"删除失败: {e}"

    def list_dir(self, path: str) -> Tuple[bool, List[Dict]]:
        """列出目录内容（含文件大小和修改时间）。"""
        try:
            entries = []
            for name in os.listdir(path):
                full = os.path.join(path, name)
                try:
                    stat = os.stat(full)
                    entries.append({
                        "name": name,
                        "is_dir": os.path.isdir(full),
                        "size": stat.st_size,
                        "mtime": stat.st_mtime,
                    })
                except OSError:
                    entries.append({"name": name, "is_dir": False, "size": 0, "mtime": 0})
            return True, entries
        except Exception as e:
            return False, [{"error": str(e)}]  # type: ignore

    def copy_file(self, src: str, dst: str) -> Tuple[bool, str]:
        """复制文件（保留元数据）。"""
        try:
            shutil.copy2(src, dst)
            return True, f"已复制 {src} → {dst}"
        except Exception as e:
            return False, f"复制失败: {e}"

    def move_file(self, src: str, dst: str) -> Tuple[bool, str]:
        """移动/重命名文件。"""
        try:
            shutil.move(src, dst)
            return True, f"已移动 {src} → {dst}"
        except Exception as e:
            return False, f"移动失败: {e}"

    def make_dir(self, path: str) -> Tuple[bool, str]:
        """创建目录（含多层父目录）。"""
        try:
            os.makedirs(path, exist_ok=True)
            return True, f"目录已创建: {path}"
        except Exception as e:
            return False, f"创建目录失败: {e}"

    # ════════════════════════════════════════════════════════════════════════
    # 注册表（winreg stdlib）
    # ════════════════════════════════════════════════════════════════════════

    def reg_read(self, hive: str, key: str,
                 value_name: str) -> Tuple[bool, str]:
        """读取注册表值。hive: 'HKLM'/'HKCU'/'HKCR'/'HKU'/'HKCC'。"""
        if not winreg:
            return _require_windows("reg_read")
        root = _HIVE_MAP.get(hive.upper())
        if root is None:
            return False, f"未知 hive: {hive}"
        try:
            with winreg.OpenKey(root, key) as k:
                data, _ = winreg.QueryValueEx(k, value_name)
            return True, str(data)
        except FileNotFoundError:
            return False, f"键或值不存在: {hive}\\{key}\\{value_name}"
        except Exception as e:
            return False, f"注册表读取失败: {e}"

    def reg_write(self, hive: str, key: str, value_name: str,
                  data, reg_type: str = 'REG_SZ') -> Tuple[bool, str]:
        """写入注册表值（不存在则创建）。"""
        if not winreg:
            return _require_windows("reg_write")
        root = _HIVE_MAP.get(hive.upper())
        if root is None:
            return False, f"未知 hive: {hive}"
        rtype = _REG_TYPE_MAP.get(reg_type.upper(), winreg.REG_SZ)
        try:
            with winreg.CreateKey(root, key) as k:
                winreg.SetValueEx(k, value_name, 0, rtype, data)
            return True, f"已写入 {hive}\\{key}\\{value_name}"
        except Exception as e:
            return False, f"注册表写入失败: {e}"

    def reg_delete_value(self, hive: str, key: str,
                         value_name: str) -> Tuple[bool, str]:
        """删除注册表值。"""
        if not winreg:
            return _require_windows("reg_delete_value")
        root = _HIVE_MAP.get(hive.upper())
        if root is None:
            return False, f"未知 hive: {hive}"
        try:
            with winreg.OpenKey(root, key, 0, winreg.KEY_WRITE) as k:
                winreg.DeleteValue(k, value_name)
            return True, f"已删除 {hive}\\{key}\\{value_name}"
        except FileNotFoundError:
            return False, "值不存在"
        except Exception as e:
            return False, f"注册表删除失败: {e}"

    def reg_list_keys(self, hive: str, key: str) -> Tuple[bool, List[str]]:
        """列出注册表子键。"""
        if not winreg:
            ok, msg = _require_windows("reg_list_keys")
            return ok, [msg]
        root = _HIVE_MAP.get(hive.upper())
        if root is None:
            return False, [f"未知 hive: {hive}"]
        try:
            with winreg.OpenKey(root, key) as k:
                subkeys = []
                i = 0
                while True:
                    try:
                        subkeys.append(winreg.EnumKey(k, i))
                        i += 1
                    except OSError:
                        break
            return True, subkeys
        except Exception as e:
            return False, [f"注册表列键失败: {e}"]

    # ════════════════════════════════════════════════════════════════════════
    # 进程管理
    # ════════════════════════════════════════════════════════════════════════

    def run_command(self, cmd: str, timeout: int = 30,
                    cwd: str = None) -> Tuple[bool, str]:
        """执行 shell 命令（无沙箱限制），返回 (success, output)。"""
        try:
            result = subprocess.run(
                cmd, shell=True, cwd=cwd,
                capture_output=True, text=True,
                encoding='utf-8', errors='replace',
                timeout=timeout,
            )
            output = (result.stdout + result.stderr).strip()
            if result.returncode == 0:
                return True, output or "<无输出>"
            return False, output or f"退出码 {result.returncode}"
        except subprocess.TimeoutExpired:
            return False, f"命令超时（{timeout}s）"
        except Exception as e:
            return False, f"执行异常: {e}"

    def run_detached(self, cmd: str) -> Tuple[bool, int]:
        """
        在后台启动进程（不等待完成）。
        返回 (success, pid)。
        """
        try:
            flags = 0
            if _IS_WINDOWS:
                flags = subprocess.CREATE_NEW_PROCESS_GROUP
            proc = subprocess.Popen(
                cmd, shell=True,
                creationflags=flags,
            )
            return True, proc.pid
        except Exception as e:
            return False, -1

    def kill_process(self, pid: int) -> Tuple[bool, str]:
        """强制终止进程（通过 PID）。"""
        try:
            if _IS_WINDOWS:
                result = subprocess.run(
                    ['taskkill', '/F', '/PID', str(pid)],
                    capture_output=True, text=True, encoding='utf-8', timeout=10
                )
                if result.returncode == 0:
                    return True, f"进程 {pid} 已终止"
                return False, result.stdout.strip() or result.stderr.strip()
            else:
                os.kill(pid, 9)
                return True, f"进程 {pid} 已终止（SIGKILL）"
        except Exception as e:
            return False, f"终止失败: {e}"

    def list_processes(self) -> List[Dict]:
        """列出所有运行中的进程。"""
        try:
            if _IS_WINDOWS:
                result = subprocess.run(
                    ['tasklist', '/FO', 'CSV', '/NH'],
                    capture_output=True, text=True,
                    encoding='utf-8', errors='replace', timeout=15
                )
                procs = []
                for line in result.stdout.splitlines():
                    line = line.strip().strip('"')
                    if not line:
                        continue
                    parts = [p.strip('"') for p in line.split('","')]
                    if len(parts) >= 2:
                        procs.append({
                            "name": parts[0],
                            "pid": parts[1],
                            "mem": parts[4] if len(parts) > 4 else "",
                        })
                return procs
            else:
                result = subprocess.run(
                    ['ps', '-eo', 'pid,comm'],
                    capture_output=True, text=True, timeout=10
                )
                procs = []
                for line in result.stdout.splitlines()[1:]:
                    parts = line.split(None, 1)
                    if len(parts) == 2:
                        procs.append({"pid": parts[0], "name": parts[1]})
                return procs
        except Exception:
            return []

    def find_process(self, name: str) -> List[Dict]:
        """按名称过滤进程列表（大小写不敏感）。"""
        name_lower = name.lower()
        return [p for p in self.list_processes()
                if name_lower in p.get("name", "").lower()]

    # ════════════════════════════════════════════════════════════════════════
    # 窗口控制（ctypes user32）
    # ════════════════════════════════════════════════════════════════════════

    def get_foreground_window(self) -> Tuple[int, str]:
        """获取当前前台窗口句柄和标题。返回 (hwnd, title)。"""
        if not _IS_WINDOWS:
            return 0, "仅支持 Windows"
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            buf = ctypes.create_unicode_buffer(512)
            user32.GetWindowTextW(hwnd, buf, 512)
            return hwnd, buf.value
        except Exception as e:
            return 0, f"获取失败: {e}"

    def find_window(self, title: str) -> int:
        """按标题查找窗口句柄。未找到返回 0。"""
        if not _IS_WINDOWS:
            return 0
        try:
            return ctypes.windll.user32.FindWindowW(None, title)
        except Exception:
            return 0

    def set_foreground(self, hwnd: int) -> bool:
        """将指定窗口置于前台。"""
        if not _IS_WINDOWS:
            return False
        try:
            return bool(ctypes.windll.user32.SetForegroundWindow(hwnd))
        except Exception:
            return False

    def move_window(self, hwnd: int, x: int, y: int,
                    w: int, h: int) -> bool:
        """移动并调整窗口大小。"""
        if not _IS_WINDOWS:
            return False
        try:
            return bool(ctypes.windll.user32.MoveWindow(hwnd, x, y, w, h, True))
        except Exception:
            return False

    def close_window(self, hwnd: int) -> bool:
        """发送 WM_CLOSE 消息关闭窗口。"""
        if not _IS_WINDOWS:
            return False
        try:
            ctypes.windll.user32.PostMessageW(hwnd, _WM_CLOSE, 0, 0)
            return True
        except Exception:
            return False

    # ════════════════════════════════════════════════════════════════════════
    # 键鼠模拟（ctypes SendInput）
    # ════════════════════════════════════════════════════════════════════════

    def _build_keyboard_input(self, vk: int, flags: int = 0):
        """构建 KEYBDINPUT 结构体（用于 SendInput）。"""

        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ("wVk",         ctypes.c_ushort),
                ("wScan",       ctypes.c_ushort),
                ("dwFlags",     ctypes.c_ulong),
                ("time",        ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
            ]

        class INPUT(ctypes.Structure):
            class _INPUT(ctypes.Union):
                _fields_ = [("ki", KEYBDINPUT)]
            _anonymous_ = ("_input",)
            _fields_ = [("type", ctypes.c_ulong), ("_input", _INPUT)]

        inp = INPUT()
        inp.type = _INPUT_KEYBOARD
        inp.ki.wVk = vk
        inp.ki.wScan = 0
        inp.ki.dwFlags = flags
        inp.ki.time = 0
        inp.ki.dwExtraInfo = ctypes.cast(
            ctypes.pointer(ctypes.c_ulong(0)),
            ctypes.POINTER(ctypes.c_ulong)
        )
        return inp

    def send_key(self, vk_code: int, hold_ms: int = 50) -> None:
        """模拟按键（按下 + 抬起）。"""
        if not _IS_WINDOWS:
            return
        try:
            down = self._build_keyboard_input(vk_code, 0)
            up   = self._build_keyboard_input(vk_code, _KEYEVENTF_KEYUP)
            ctypes.windll.user32.SendInput(1, ctypes.byref(down), ctypes.sizeof(down))
            time.sleep(hold_ms / 1000.0)
            ctypes.windll.user32.SendInput(1, ctypes.byref(up), ctypes.sizeof(up))
        except Exception:
            pass

    def send_hotkey(self, *vk_codes: int) -> None:
        """模拟组合键（同时按下多个键，如 Ctrl+C）。"""
        if not _IS_WINDOWS or not vk_codes:
            return
        try:
            # 全部按下
            for vk in vk_codes:
                inp = self._build_keyboard_input(vk, 0)
                ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
            time.sleep(0.05)
            # 全部抬起（逆序）
            for vk in reversed(vk_codes):
                inp = self._build_keyboard_input(vk, _KEYEVENTF_KEYUP)
                ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
        except Exception:
            pass

    def mouse_move(self, x: int, y: int) -> None:
        """移动鼠标到绝对坐标 (x, y)。"""
        if not _IS_WINDOWS:
            return
        try:
            ctypes.windll.user32.SetCursorPos(x, y)
        except Exception:
            pass

    def mouse_click(self, x: int, y: int, button: str = 'left') -> None:
        """在坐标 (x, y) 处单击鼠标。button: 'left' | 'right'。"""
        if not _IS_WINDOWS:
            return
        try:
            user32 = ctypes.windll.user32
            user32.SetCursorPos(x, y)
            if button == 'right':
                user32.mouse_event(_MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
                time.sleep(0.05)
                user32.mouse_event(_MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
            else:
                user32.mouse_event(_MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                time.sleep(0.05)
                user32.mouse_event(_MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        except Exception:
            pass

    def type_string(self, text: str) -> None:
        """逐字符模拟键盘输入（使用 VkKeyScanW + SendInput）。"""
        if not _IS_WINDOWS:
            return
        try:
            user32 = ctypes.windll.user32
            for ch in text:
                vk_scan = user32.VkKeyScanW(ord(ch))
                if vk_scan == -1:
                    continue
                vk = vk_scan & 0xFF
                shift = (vk_scan >> 8) & 0xFF
                if shift & 1:  # Shift 键
                    self.send_key(VK_SHIFT, 0)
                    time.sleep(0.01)
                self.send_key(vk, 30)
                time.sleep(0.02)
        except Exception:
            pass

    # ════════════════════════════════════════════════════════════════════════
    # 剪贴板（ctypes OpenClipboard）
    # ════════════════════════════════════════════════════════════════════════

    def clipboard_get(self) -> str:
        """读取剪贴板文本内容。"""
        if not _IS_WINDOWS:
            return ""
        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            if not user32.OpenClipboard(None):
                return ""
            try:
                hdata = user32.GetClipboardData(_CF_UNICODETEXT)
                if not hdata:
                    return ""
                ptr = kernel32.GlobalLock(hdata)
                if not ptr:
                    return ""
                try:
                    return ctypes.wstring_at(ptr)
                finally:
                    kernel32.GlobalUnlock(hdata)
            finally:
                user32.CloseClipboard()
        except Exception:
            return ""

    def clipboard_set(self, text: str) -> bool:
        """设置剪贴板文本内容。"""
        if not _IS_WINDOWS:
            return False
        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            if not user32.OpenClipboard(None):
                return False
            try:
                user32.EmptyClipboard()
                # 分配全局内存
                encoded = (text + '\0').encode('utf-16-le')
                hdata = kernel32.GlobalAlloc(0x0002, len(encoded))  # GMEM_MOVEABLE
                if not hdata:
                    return False
                ptr = kernel32.GlobalLock(hdata)
                if not ptr:
                    kernel32.GlobalFree(hdata)
                    return False
                ctypes.memmove(ptr, encoded, len(encoded))
                kernel32.GlobalUnlock(hdata)
                user32.SetClipboardData(_CF_UNICODETEXT, hdata)
                return True
            finally:
                user32.CloseClipboard()
        except Exception:
            return False

    # ════════════════════════════════════════════════════════════════════════
    # 系统信息
    # ════════════════════════════════════════════════════════════════════════

    def get_system_info(self) -> Dict:
        """获取 Windows 系统信息（OS版本/CPU/内存/主机名）。"""
        info: Dict = {
            "platform": sys.platform,
            "python_version": sys.version,
            "hostname": platform.node(),
            "os": platform.system(),
            "os_version": platform.version(),
            "processor": platform.processor(),
            "architecture": platform.architecture()[0],
        }
        # 尝试从 systeminfo 获取更多信息（仅 Windows）
        if _IS_WINDOWS:
            try:
                result = subprocess.run(
                    ['systeminfo'],
                    capture_output=True, text=True,
                    encoding='utf-8', errors='replace', timeout=30
                )
                for line in result.stdout.splitlines():
                    if 'Total Physical Memory' in line or '总物理内存' in line:
                        info["total_ram"] = line.split(':', 1)[-1].strip()
                    elif 'Available Physical Memory' in line or '可用物理内存' in line:
                        info["free_ram"] = line.split(':', 1)[-1].strip()
            except Exception:
                pass
        return info

    def get_disk_info(self, path: str = 'C:\\') -> Dict:
        """获取磁盘使用信息。"""
        try:
            usage = shutil.disk_usage(path)
            return {
                "path": path,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "used_percent": round(usage.used / usage.total * 100, 1) if usage.total else 0,
            }
        except Exception as e:
            return {"error": str(e)}

    def get_env(self, key: str) -> str:
        """读取环境变量。"""
        return os.environ.get(key, "")

    def set_env(self, key: str, value: str) -> None:
        """设置环境变量（当前进程有效）。"""
        os.environ[key] = value
