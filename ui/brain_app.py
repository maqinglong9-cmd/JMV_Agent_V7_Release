"""Kivy App 主类 - 含中文字体注册、底部导航栏（脑感知/对话/设置）"""
import os
import sys
import threading

from kivy.app import App
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle

from ui.responsive import (
    dp, font_small, font_body, tab_bar_height, is_android
)


def _get_project_root() -> str:
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _font_cache_path() -> str:
    root = _get_project_root()
    workspace = os.path.join(root, 'jmv_workspace')
    os.makedirs(workspace, exist_ok=True)
    return os.path.join(workspace, 'font_cache.txt')


def _read_font_cache() -> str:
    try:
        p = _font_cache_path()
        if os.path.isfile(p):
            cached = open(p, encoding='utf-8').read().strip()
            if cached and os.path.isfile(cached):
                return cached
    except Exception:
        pass
    return ''


def _write_font_cache(path: str) -> None:
    try:
        with open(_font_cache_path(), 'w', encoding='utf-8') as f:
            f.write(path)
    except Exception:
        pass


def _register_cjk_font() -> str | None:
    project_root = _get_project_root()
    candidates = [
        _read_font_cache(),
        os.path.join(project_root, 'fonts', 'msyh.ttc'),
        r'C:\Windows\Fonts\msyh.ttc',
        r'C:\Windows\Fonts\msyhbd.ttc',
        r'C:\Windows\Fonts\simsun.ttc',
        r'C:\Windows\Fonts\simhei.ttf',
        r'C:\Windows\Fonts\simkai.ttf',
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/System/Library/Fonts/PingFang.ttc',
        '/Library/Fonts/Arial Unicode MS.ttf',
    ]
    seen: set = set()
    for path in candidates:
        if not path or path in seen:
            continue
        seen.add(path)
        if not os.path.isfile(path):
            continue
        try:
            LabelBase.register(name='Roboto', fn_regular=path)
            Logger.info(f'BrainAgentApp: CJK字体注册成功 → {path}')
            _write_font_cache(path)
            return path
        except Exception as e:
            Logger.warning(f'BrainAgentApp: 字体注册失败 {path}: {e}')
    Logger.warning('BrainAgentApp: 未找到CJK字体，中文可能显示方块')
    return None


# ── 颜色常量 ─────────────────────────────────────────────
C_TAB_BG     = (0.07, 0.09, 0.14, 1)
C_TAB_ACTIVE = (0.18, 0.62, 0.36, 1)
C_TAB_IDLE   = (0.12, 0.16, 0.26, 1)
C_TAB_TEXT   = (0.90, 0.92, 0.95, 1)
C_TAB_DIM    = (0.45, 0.52, 0.65, 1)


def _bg(widget, color):
    with widget.canvas.before:
        Color(*color)
        rect = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(pos=lambda *_: setattr(rect, 'pos', widget.pos))
    widget.bind(size=lambda *_: setattr(rect, 'size', widget.size))


TABS = [
    ('brain',    '🧠 脑感知'),
    ('chat',     '💬 对话'),
    ('settings', '⚙ 设置'),
]


class TabBar(BoxLayout):
    """底部三标签导航栏"""

    def __init__(self, on_switch, **kwargs):
        super().__init__(
            orientation='horizontal',
            size_hint_y=None,
            height=tab_bar_height(),
            **kwargs
        )
        _bg(self, C_TAB_BG)
        self._on_switch = on_switch
        self._btns: dict[str, Button] = {}

        for key, label in TABS:
            btn = Button(
                text=label,
                font_size=font_small(),
                background_normal='',
                background_color=C_TAB_IDLE,
                color=C_TAB_DIM,
            )
            btn.bind(on_press=lambda b, k=key: self._tap(k))
            self._btns[key] = btn
            self.add_widget(btn)

        self._set_active('brain')

    def _tap(self, key: str):
        self._set_active(key)
        self._on_switch(key)

    def _set_active(self, key: str):
        for k, btn in self._btns.items():
            if k == key:
                btn.background_color = C_TAB_ACTIVE
                btn.color = C_TAB_TEXT
            else:
                btn.background_color = C_TAB_IDLE
                btn.color = C_TAB_DIM

    def set_active(self, key: str):
        self._set_active(key)


class RootLayout(BoxLayout):
    """根布局：内容区 + 底部 TabBar"""

    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=0, **kwargs)

        from ui.main_screen import MainScreen
        from ui.chat_screen import ChatScreen
        from ui.llm_config_screen import LLMConfigScreen

        # 延迟初始化：先建内容容器
        self._content = BoxLayout()
        self.add_widget(self._content)

        self._tab_bar = TabBar(on_switch=self._switch_tab)
        self.add_widget(self._tab_bar)

        # 构建各屏幕（懒加载）
        self._screens: dict[str, BoxLayout] = {}
        self._active_key = ''

        # 先创建主屏（立即显示）
        self._main_screen = MainScreen(on_open_settings=self._open_settings)
        self._screens['brain'] = self._main_screen

        # 切换到主屏
        self._switch_tab('brain')

    def _get_screen(self, key: str) -> BoxLayout:
        if key not in self._screens:
            if key == 'chat':
                from ui.chat_screen import ChatScreen
                llm = getattr(self._main_screen.adapter, '_llm', None)
                self._screens['chat'] = ChatScreen(llm_client=llm)
            elif key == 'settings':
                from ui.llm_config_screen import LLMConfigScreen
                self._screens['settings'] = LLMConfigScreen(
                    on_saved=self._on_config_saved
                )
        return self._screens[key]

    def _switch_tab(self, key: str):
        if key == self._active_key:
            return
        self._active_key = key
        self._content.clear_widgets()
        screen = self._get_screen(key)
        self._content.add_widget(screen)
        self._tab_bar.set_active(key)

    def _open_settings(self):
        """从主屏的设置按钮跳转到设置页"""
        self._switch_tab('settings')
        self._tab_bar.set_active('settings')

    def _on_config_saved(self, config: dict):
        """配置保存后更新适配器和聊天 Agent"""
        self._main_screen.adapter.reload_llm()
        self._main_screen._refresh_llm_status()
        provider = self._main_screen.adapter.llm_provider
        connected = self._main_screen.adapter.llm_connected
        self._main_screen.log_viewer.append(
            f'[设置] 配置已更新 → {"✓ " + provider if connected else "本地模式"}'
        )
        # 同步更新聊天界面的 LLM 客户端
        if 'chat' in self._screens:
            llm = getattr(self._main_screen.adapter, '_llm', None)
            self._screens['chat'].set_llm(llm)


class BrainAgentApp(App):
    def build(self):
        font_path = _register_cjk_font()
        if not font_path:
            Logger.error('BrainAgentApp: CJK字体缺失！')

        self.title = 'JMV智伴 - 全脑感知系统'
        Window.clearcolor = (0.06, 0.08, 0.12, 1)
        Window.minimum_width = 360
        Window.minimum_height = 600
        # Android 软键盘：pan 模式整体平移界面，兼容性最佳，避免 below_target 在部分定制系统的布局错误
        if is_android():
            Window.softinput_mode = 'pan'

        try:
            root = RootLayout()
        except Exception as e:
            Logger.error(f'BrainAgentApp: 初始化失败: {e}')
            raise

        # 3 秒后后台静默检查更新
        Clock.schedule_once(
            lambda dt: self._background_update_check(root._main_screen), 3
        )
        return root

    def on_start(self):
        self._request_android_permissions()

    def _request_android_permissions(self):
        """Android 运行时权限申请（Android 6.0+ 危险权限必须动态申请）。"""
        if not is_android():
            return
        try:
            from android.permissions import request_permissions, Permission  # type: ignore
            request_permissions([
                Permission.INTERNET,
                Permission.CAMERA,
                Permission.RECORD_AUDIO,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.ACCESS_FINE_LOCATION,
                Permission.ACCESS_COARSE_LOCATION,
            ])
        except Exception as e:
            Logger.warning(f'BrainAgentApp: 权限申请失败（非 Android 环境）: {e}')

    def _background_update_check(self, main_screen):
        def _run():
            try:
                from updater.version_checker import check_for_update
                info = check_for_update()
                if info.get('has_update'):
                    Clock.schedule_once(
                        lambda dt: main_screen.log_viewer.append(
                            f'[升级] 发现新版本 {info["latest"]}，切换到"设置"页面可手动触发升级。'
                        ), 0
                    )
            except Exception as e:
                Logger.warning(f'BrainAgentApp: 后台版本检查失败: {e}')

        threading.Thread(target=_run, daemon=True).start()

    def on_stop(self):
        Logger.info('BrainAgentApp: 应用正常退出')
