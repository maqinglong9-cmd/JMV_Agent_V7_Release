"""Windows 系统托盘图标（ctypes Shell_NotifyIcon，零依赖）
双击托盘图标 → 显示窗口；右键 → 退出。
在独立后台线程中运行 Win32 消息循环。
"""
import sys
import threading
import ctypes
import ctypes.wintypes as wt

_IS_WINDOWS = sys.platform == 'win32'

# ── Win32 常量 ────────────────────────────────────────────────────────────────
WM_USER          = 0x0400
_WM_TRAYICON     = WM_USER + 20
NIM_ADD          = 0
NIM_DELETE       = 2
NIF_MESSAGE      = 1
NIF_ICON         = 2
NIF_TIP          = 4
WM_LBUTTONDBLCLK = 0x0203
WM_RBUTTONUP     = 0x0205
WM_DESTROY       = 0x0002
WM_QUIT          = 0x0012
IDI_APPLICATION  = 32512
CS_HREDRAW       = 2
CS_VREDRAW       = 1
COLOR_WINDOW     = 5
WS_OVERLAPPED    = 0


class TrayIcon:
    """
    Windows 系统托盘图标。
    - 双击：调用 on_show 回调（显示主窗口）
    - 右键：调用 on_quit 回调（退出应用）
    非 Windows 平台：所有方法静默忽略。
    """

    def __init__(self, tooltip: str = 'JMV智伴',
                 on_show=None, on_quit=None):
        self._tooltip = tooltip[:127]
        self._on_show = on_show
        self._on_quit = on_quit
        self._hwnd = None
        self._thread = None

    def start(self):
        """启动托盘图标（后台线程）。"""
        if not _IS_WINDOWS:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """移除托盘图标并停止消息循环。"""
        if _IS_WINDOWS and self._hwnd:
            try:
                ctypes.windll.user32.PostMessageW(self._hwnd, WM_QUIT, 0, 0)
            except Exception:
                pass

    def _run(self):
        try:
            self._message_loop()
        except Exception:
            pass

    def _message_loop(self):
        user32  = ctypes.windll.user32
        shell32 = ctypes.windll.shell32
        kernel32 = ctypes.windll.kernel32

        WNDPROC = ctypes.WINFUNCTYPE(
            ctypes.c_long, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM
        )

        def _wnd_proc(hwnd, msg, wparam, lparam):
            if msg == _WM_TRAYICON:
                if lparam == WM_LBUTTONDBLCLK and self._on_show:
                    self._on_show()
                elif lparam == WM_RBUTTONUP and self._on_quit:
                    self._on_quit()
            elif msg == WM_DESTROY:
                user32.PostQuitMessage(0)
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        wnd_proc_cb = WNDPROC(_wnd_proc)

        class WNDCLASSEX(ctypes.Structure):
            _fields_ = [
                ('cbSize',        wt.UINT),
                ('style',         wt.UINT),
                ('lpfnWndProc',   WNDPROC),
                ('cbClsExtra',    ctypes.c_int),
                ('cbWndExtra',    ctypes.c_int),
                ('hInstance',     wt.HINSTANCE),
                ('hIcon',         wt.HICON),
                ('hCursor',       wt.HANDLE),
                ('hbrBackground', wt.HBRUSH),
                ('lpszMenuName',  wt.LPCWSTR),
                ('lpszClassName', wt.LPCWSTR),
                ('hIconSm',       wt.HICON),
            ]

        class NOTIFYICONDATA(ctypes.Structure):
            _fields_ = [
                ('cbSize',          wt.DWORD),
                ('hWnd',            wt.HWND),
                ('uID',             wt.UINT),
                ('uFlags',          wt.UINT),
                ('uCallbackMessage',wt.UINT),
                ('hIcon',           wt.HICON),
                ('szTip',           wt.WCHAR * 128),
            ]

        hinstance  = kernel32.GetModuleHandleW(None)
        class_name = 'JMVTrayWnd'

        wc = WNDCLASSEX()
        wc.cbSize        = ctypes.sizeof(WNDCLASSEX)
        wc.style         = CS_HREDRAW | CS_VREDRAW
        wc.lpfnWndProc   = wnd_proc_cb
        wc.hInstance     = hinstance
        wc.hIcon         = user32.LoadIconW(None, IDI_APPLICATION)
        wc.hCursor       = user32.LoadCursorW(None, IDI_APPLICATION)
        wc.hbrBackground = COLOR_WINDOW + 1
        wc.lpszClassName = class_name
        user32.RegisterClassExW(ctypes.byref(wc))

        hwnd = user32.CreateWindowExW(
            0, class_name, 'JMV Tray',
            WS_OVERLAPPED, 0, 0, 1, 1,
            None, None, hinstance, None
        )
        self._hwnd = hwnd

        nid = NOTIFYICONDATA()
        nid.cbSize          = ctypes.sizeof(NOTIFYICONDATA)
        nid.hWnd            = hwnd
        nid.uID             = 1
        nid.uFlags          = NIF_MESSAGE | NIF_ICON | NIF_TIP
        nid.uCallbackMessage = _WM_TRAYICON
        nid.hIcon           = user32.LoadIconW(None, IDI_APPLICATION)
        nid.szTip           = self._tooltip
        shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid))

        msg = wt.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid))
