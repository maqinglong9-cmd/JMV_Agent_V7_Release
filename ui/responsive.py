"""响应式设计工具模块 - dp/sp 单位换算、屏幕断点、触摸目标尺寸"""
import sys
import os


def is_android() -> bool:
    """检测是否运行在 Android 平台"""
    return sys.platform == 'linux' and os.path.exists('/data/data')


def dp(val: float) -> float:
    """密度无关像素（density-independent pixels）"""
    try:
        from kivy.metrics import dp as _dp
        return _dp(val)
    except Exception:
        return float(val)


def sp(val: float) -> float:
    """缩放无关像素（scale-independent pixels），用于字体大小"""
    try:
        from kivy.metrics import sp as _sp
        return _sp(val)
    except Exception:
        return float(val)


def screen_width() -> float:
    try:
        from kivy.core.window import Window
        return Window.width
    except Exception:
        return 480.0


def screen_height() -> float:
    try:
        from kivy.core.window import Window
        return Window.height
    except Exception:
        return 800.0


def is_small_screen() -> bool:
    """宽度 < dp(400) 视为小屏手机"""
    return screen_width() < dp(400)


def is_large_screen() -> bool:
    """宽度 > dp(720) 视为平板/桌面"""
    return screen_width() > dp(720)


def touch_target() -> float:
    """Material Design 最小触摸目标：手机 48dp，桌面 40dp"""
    return dp(48) if is_android() else dp(40)


def button_height() -> float:
    return dp(52) if is_android() else dp(44)


def input_height() -> float:
    return dp(52) if is_android() else dp(42)


def header_height() -> float:
    return dp(52)


def tab_bar_height() -> float:
    return dp(56) if is_android() else dp(48)


def section_label_height() -> float:
    return dp(32) if is_android() else dp(26)


def compact_brain_height() -> float:
    """脑区仪表盘紧凑高度"""
    return dp(88)


def section_height() -> float:
    """区块标题栏高度（紧凑版）"""
    return dp(24)


def tool_row_height() -> float:
    """工具栏行高"""
    return dp(40)


def mode_row_height() -> float:
    """模式选择行高"""
    return dp(40)


def padding_h() -> float:
    return dp(16) if is_android() else dp(10)


def padding_v() -> float:
    return dp(12) if is_android() else dp(6)


def font_body() -> str:
    return '14sp' if is_android() else '12sp'


def font_small() -> str:
    return '12sp' if is_android() else '10sp'


def font_large() -> str:
    return '18sp' if is_android() else '16sp'


def font_title() -> str:
    return '22sp' if is_android() else '18sp'


def font_hint() -> str:
    return '13sp' if is_android() else '11sp'


def font_btn() -> str:
    return '15sp' if is_android() else '13sp'


def font_label() -> str:
    return '13sp' if is_android() else '11sp'


def spacing_normal() -> float:
    return dp(8) if is_android() else dp(6)


def spacing_small() -> float:
    return dp(4) if is_android() else dp(3)
