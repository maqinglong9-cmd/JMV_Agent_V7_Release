"""JMV智伴 LLM 配置界面 - 纯 Kivy 实现（适配 Android + Windows）
无 ScrollView 版：移除 ScrollView 彻底解决 Android 触摸拦截问题。
动态渲染：每次只创建当前供应商的字段（3个），直接放在 BoxLayout 中，无需滚动。
供应商导航：用 ◀ / ▶ 按钮替换 Spinner，彻底规避 Android Spinner 触摸 BUG。
"""
import threading

# ── 颜色常量 ─────────────────────────────────────────────
C_BG       = (0.06, 0.08, 0.12, 1)
C_CARD     = (0.10, 0.14, 0.22, 1)
C_SECTION  = (0.09, 0.12, 0.18, 1)
C_INPUT_BG = (0.08, 0.11, 0.17, 1)
C_TEXT     = (0.90, 0.92, 0.95, 1)
C_SUBTEXT  = (0.55, 0.62, 0.75, 1)
C_GREEN    = (0.20, 0.75, 0.45, 1)
C_YELLOW   = (0.85, 0.70, 0.20, 1)
C_RED      = (0.80, 0.25, 0.25, 1)
C_BTN_SAVE = (0.18, 0.58, 0.32, 1)
C_BTN_TEST = (0.18, 0.28, 0.48, 1)

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.clock import Clock

from ui.responsive import (
    dp, font_body, font_small, font_large, font_btn, font_label,
    button_height, input_height, padding_h, padding_v,
    is_android, touch_target, spacing_normal
)
from ui.llm_config_data import (
    load_config, save_config, PROVIDERS, _PROVIDER_FIELDS, _DEFAULT_CONFIG, CONFIG_FILE
)


def _bg(widget, color):
    with widget.canvas.before:
        Color(*color)
        rect = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(pos=lambda *_: setattr(rect, 'pos', widget.pos))
    widget.bind(size=lambda *_: setattr(rect, 'size', widget.size))


def _card_bg(widget, color, radius=8):
    with widget.canvas.before:
        Color(*color)
        rect = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[radius])
    widget.bind(pos=lambda *_: setattr(rect, 'pos', widget.pos))
    widget.bind(size=lambda *_: setattr(rect, 'size', widget.size))


class KeyField(BoxLayout):
    """API Key / 端点 / 模型输入行，带显示/隐藏按钮（仅密钥字段）"""

    def __init__(self, label_text, field_key, is_secret=False, hint_text='', on_paste=None, **kwargs):
        # Android 用更高的行高，确保触摸目标足够大
        fh = dp(96) if is_android() else dp(74)
        super().__init__(
            orientation='vertical',
            size_hint_y=None,
            height=fh,
            spacing=dp(4),
            **kwargs
        )
        self.field_key = field_key
        self.is_secret = is_secret
        self._hidden = is_secret
        self._on_paste = on_paste  # 粘贴成功后的回调（供父级自动保存）

        # 标签行
        lbl_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None, height=dp(26)
        )
        lbl = Label(
            text=label_text,
            font_size=font_label(),
            color=C_SUBTEXT,
            halign='left', valign='middle',
        )
        lbl.bind(size=lbl.setter('text_size'))
        lbl_row.add_widget(lbl)
        self.add_widget(lbl_row)

        # 输入行
        ih = dp(56) if is_android() else input_height()
        input_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=ih,
            spacing=dp(6),
        )
        _default_hint = '点击此处输入 API Key...' if is_secret else '点击此处输入...'
        self.ti = TextInput(
            hint_text=hint_text or _default_hint,
            multiline=False,
            font_size=font_body(),
            foreground_color=(0.88, 0.92, 0.96, 1),
            background_normal='',
            background_color=C_INPUT_BG,
            hint_text_color=(0.40, 0.48, 0.62, 0.8),
            cursor_color=(*C_GREEN[:3], 1),
            padding=[dp(12), dp(14)],
            password=is_secret,
            input_type='text',
            write_tab=False,
            size_hint_x=1,
        )
        input_row.add_widget(self.ti)

        if is_secret:
            eye_size = dp(58) if is_android() else touch_target()
            self._eye_btn = Button(
                text='👁',
                font_size=font_body(),
                size_hint_x=None,
                width=eye_size,
                background_normal='',
                background_color=C_SECTION,
                color=C_SUBTEXT,
            )
            self._eye_btn.bind(on_press=self._toggle_visibility)
            input_row.add_widget(self._eye_btn)

            # Android 上 password 字段无法通过长按菜单粘贴，提供专用粘贴按钮
            if is_android():
                paste_btn = Button(
                    text='📋',
                    font_size=font_body(),
                    size_hint_x=None,
                    width=dp(58),
                    background_normal='',
                    background_color=(0.14, 0.20, 0.34, 1),
                    color=C_SUBTEXT,
                )
                paste_btn.bind(on_press=self._paste_from_clipboard)
                input_row.add_widget(paste_btn)

        self.add_widget(input_row)

    def on_touch_down(self, touch):
        """Android: 点击 KeyField 任意位置都聚焦到输入框。
        只在触摸点不在 TextInput 自身范围内时才调度延迟聚焦，
        避免与 TextInput 的自然获焦冲突，防止 IME 双重初始化导致输入失败。
        """
        if self.collide_point(*touch.pos):
            if not (self.is_secret and
                    hasattr(self, '_eye_btn') and
                    self._eye_btn.collide_point(*touch.pos)):
                # 仅当触摸点不在 TextInput 自身上时才延迟设焦，
                # 触摸在 TextInput 上时让其自然获焦，避免双重 focus 干扰 IME
                if not self.ti.collide_point(*touch.pos):
                    Clock.schedule_once(lambda dt: setattr(self.ti, 'focus', True), 0.15)
        return super().on_touch_down(touch)

    def _toggle_visibility(self, _):
        self._hidden = not self._hidden
        self.ti.password = self._hidden
        self._eye_btn.color = C_SUBTEXT if self._hidden else C_GREEN

    def _paste_from_clipboard(self, _):
        """Android 专用：从系统剪贴板粘贴到 API Key 输入框。
        粘贴后临时明文显示 2 秒，让用户确认内容，然后自动恢复密码模式。
        同时通过 on_paste 回调通知父级自动保存配置，避免用户忘记按保存。
        """
        try:
            from kivy.core.clipboard import Clipboard
            text = Clipboard.paste()
            if text:
                stripped = text.strip()
                if not stripped:
                    return
                self.ti.text = stripped
                self.ti.focus = True
                # 临时明文显示：让用户能看到粘贴内容是否正确
                if self.is_secret and self._hidden:
                    self.ti.password = False
                    self._eye_btn.color = C_GREEN
                    Clock.schedule_once(self._restore_password_mode, 2.0)
                # 通知父级自动保存（解决用户忘记按保存导致 401 的问题）
                if self._on_paste:
                    Clock.schedule_once(lambda dt: self._on_paste(), 0.1)
        except Exception as e:
            from kivy.logger import Logger
            Logger.warning(f'KeyField: 粘贴失败（可能是 Android 剪贴板权限限制）: {e}')

    def _restore_password_mode(self, dt):
        """2 秒后恢复密码遮掩模式"""
        if self.is_secret:
            self.ti.password = True
            self._hidden = True
            self._eye_btn.color = C_SUBTEXT

    @property
    def text(self) -> str:
        return self.ti.text.strip()

    @text.setter
    def text(self, val: str):
        self.ti.text = val or ''


class LLMConfigScreen(BoxLayout):
    """全屏 LLM 配置界面
    - 无 ScrollView：避免 Android 触摸拦截
    - 用 ◀ / ▶ 按钮导航供应商，避免 Android Spinner BUG
    - 动态渲染：只创建当前供应商的字段（最多 3 个）
    """

    def __init__(self, on_saved=None, **kwargs):
        super().__init__(orientation='vertical', spacing=0, **kwargs)
        self._on_saved = on_saved
        self._config = load_config()
        self._fields: dict[str, KeyField] = {}
        self._provider_idx = self._get_provider_idx(
            self._config.get('active_provider', 'Gemini')
        )
        _bg(self, C_BG)
        self._build_ui()

    def _get_provider_idx(self, provider: str) -> int:
        try:
            return PROVIDERS.index(provider)
        except ValueError:
            return 0

    @property
    def _active_provider(self) -> str:
        return PROVIDERS[self._provider_idx]

    def _build_ui(self):
        # ── 标题栏 ─────────────────────────────────────
        header = BoxLayout(
            size_hint_y=None,
            height=dp(56),
            padding=[padding_h(), dp(8)],
        )
        _bg(header, (0.10, 0.13, 0.20, 1))
        title_lbl = Label(
            text='⚙ 算力引擎配置',
            font_size=font_large(),
            bold=True,
            color=C_TEXT,
            halign='left', valign='middle',
        )
        title_lbl.bind(size=title_lbl.setter('text_size'))
        header.add_widget(title_lbl)
        self.add_widget(header)

        # ── 供应商导航栏（◀ 名称 ▶）─────────────────────
        # 用按钮替换 Spinner，彻底解决 Android Spinner 触摸问题
        nav_h = dp(60) if is_android() else dp(52)
        nav_bar = BoxLayout(
            size_hint_y=None,
            height=nav_h,
            padding=[padding_h(), dp(6)],
            spacing=dp(8),
        )
        _bg(nav_bar, (0.10, 0.14, 0.22, 1))

        prov_lbl = Label(
            text='供应商:',
            font_size=font_body(),
            color=C_TEXT,
            size_hint_x=None,
            width=dp(64),
            halign='left', valign='middle',
        )
        prov_lbl.bind(size=prov_lbl.setter('text_size'))

        nav_btn_w = dp(56) if is_android() else dp(44)
        nav_btn_h = dp(48) if is_android() else dp(40)

        prev_btn = Button(
            text='◀',
            font_size=font_btn(),
            size_hint_x=None,
            width=nav_btn_w,
            height=nav_btn_h,
            background_normal='',
            background_color=(0.18, 0.24, 0.36, 1),
            color=C_TEXT,
        )
        prev_btn.bind(on_press=lambda _: self._prev_provider())

        self._provider_name_lbl = Label(
            text=self._active_provider,
            font_size=font_btn(),
            bold=True,
            color=C_GREEN,
            halign='center', valign='middle',
        )
        self._provider_name_lbl.bind(
            size=self._provider_name_lbl.setter('text_size')
        )

        next_btn = Button(
            text='▶',
            font_size=font_btn(),
            size_hint_x=None,
            width=nav_btn_w,
            height=nav_btn_h,
            background_normal='',
            background_color=(0.18, 0.24, 0.36, 1),
            color=C_TEXT,
        )
        next_btn.bind(on_press=lambda _: self._next_provider())

        # 页码指示（如 3/19）
        self._page_lbl = Label(
            text=self._page_text(),
            font_size=font_small(),
            color=C_SUBTEXT,
            size_hint_x=None,
            width=dp(36),
            halign='center', valign='middle',
        )
        self._page_lbl.bind(size=self._page_lbl.setter('text_size'))

        nav_bar.add_widget(prov_lbl)
        nav_bar.add_widget(prev_btn)
        nav_bar.add_widget(self._provider_name_lbl)
        nav_bar.add_widget(next_btn)
        nav_bar.add_widget(self._page_lbl)
        self.add_widget(nav_bar)

        # ── 字段区（无 ScrollView，直接 BoxLayout）─────
        # 最多 3 个字段，Android 上每个 ~96dp，加 padding 约 320dp，
        # 任何手机屏幕都容得下，不需要滚动。
        self._content = BoxLayout(
            orientation='vertical',
            size_hint_y=1,          # 填满剩余空间
            spacing=dp(12),
            padding=[padding_h(), dp(12), padding_h(), dp(8)],
        )
        _bg(self._content, C_BG)
        self.add_widget(self._content)

        # ── 底部按钮区 ──────────────────────────────────
        btn_bar_h = button_height() + dp(16)
        btn_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=btn_bar_h,
            spacing=dp(8),
            padding=[padding_h(), dp(8)],
        )
        _bg(btn_row, (0.08, 0.10, 0.16, 1))

        self._status_lbl = Label(
            text='',
            font_size=font_small(),
            color=C_GREEN,
            halign='left', valign='middle',
        )
        self._status_lbl.bind(size=self._status_lbl.setter('text_size'))

        test_btn = Button(
            text='🔌 测试连接',
            font_size=font_btn(),
            size_hint_x=None,
            width=dp(120),
            height=button_height(),
            background_normal='',
            background_color=C_BTN_TEST,
            color=C_TEXT,
        )
        test_btn.bind(on_press=lambda _: self._test_connection())

        save_btn = Button(
            text='💾 保存配置',
            font_size=font_btn(),
            size_hint_x=None,
            width=dp(120),
            height=button_height(),
            background_normal='',
            background_color=C_BTN_SAVE,
            color=C_TEXT,
        )
        save_btn.bind(on_press=lambda _: self._save())

        btn_row.add_widget(self._status_lbl)
        btn_row.add_widget(test_btn)
        btn_row.add_widget(save_btn)
        self.add_widget(btn_row)

        # 渲染初始供应商的字段
        self._render_provider_fields(self._active_provider)

    # ── 供应商导航 ──────────────────────────────────────

    def _page_text(self) -> str:
        return f'{self._provider_idx + 1}/{len(PROVIDERS)}'

    def _prev_provider(self):
        self._switch_to((self._provider_idx - 1) % len(PROVIDERS))

    def _next_provider(self):
        self._switch_to((self._provider_idx + 1) % len(PROVIDERS))

    def _switch_to(self, idx: int):
        if idx == self._provider_idx:
            return
        # 保存当前字段值
        for field_key, kf in self._fields.items():
            self._config[field_key] = kf.text
        self._provider_idx = idx
        self._provider_name_lbl.text = self._active_provider
        self._page_lbl.text = self._page_text()
        self._render_provider_fields(self._active_provider)

    # ── 字段渲染 ────────────────────────────────────────

    def _render_provider_fields(self, provider: str):
        """销毁旧字段，只创建当前供应商的字段"""
        self._content.clear_widgets()
        self._fields.clear()

        fields = _PROVIDER_FIELDS.get(provider, [])
        if not fields:
            lbl = Label(
                text=f'[{provider}] 暂无可配置字段',
                font_size=font_body(),
                color=C_SUBTEXT,
            )
            self._content.add_widget(lbl)
            return

        # 供应商标题（小标注）
        sec_title = Label(
            text=f'[{provider}] 配置',
            font_size=font_label(),
            color=C_GREEN,
            bold=True,
            halign='left', valign='middle',
            size_hint_y=None,
            height=dp(28),
        )
        sec_title.bind(size=sec_title.setter('text_size'))
        self._content.add_widget(sec_title)

        for field_entry in fields:
            if len(field_entry) == 4:
                field_key, label_text, is_secret, hint_text = field_entry
            else:
                field_key, label_text, is_secret = field_entry
                hint_text = ''

            kf = KeyField(
                label_text=label_text,
                field_key=field_key,
                is_secret=is_secret,
                hint_text=hint_text,
                on_paste=self._auto_save_after_paste,
            )
            kf.text = self._config.get(field_key, '')
            self._content.add_widget(kf)
            self._fields[field_key] = kf

        # 底部填充（让字段不会撑到屏幕最底）
        self._content.add_widget(BoxLayout())  # spacer

    # ── 配置收集 / 保存 / 测试 ──────────────────────────

    def _auto_save_after_paste(self):
        """粘贴 API Key 后自动保存配置，防止用户忘记按保存导致 HTTP 401。"""
        self._save()
        self._set_status('✓ Key 已粘贴并自动保存', C_GREEN)

    def _collect_config(self) -> dict:
        config = dict(self._config)
        config['active_provider'] = self._active_provider
        for field_key, kf in self._fields.items():
            config[field_key] = kf.text
        return config

    def _save(self):
        config = self._collect_config()
        save_config(config)
        self._config = config
        self._set_status('✓ 配置已保存', C_GREEN)
        if self._on_saved:
            self._on_saved(config)

    def _set_status(self, msg: str, color=None):
        self._status_lbl.text = msg
        if color:
            self._status_lbl.color = color
        Clock.schedule_once(lambda dt: setattr(self._status_lbl, 'text', ''), 4)

    def _test_connection(self):
        config = self._collect_config()
        provider = config.get('active_provider', 'Gemini')
        self._set_status(f'⏳ 正在连接 {provider}...', C_YELLOW)

        def _run():
            try:
                from agent.universal_llm_client import UniversalLLMClient
                client = UniversalLLMClient(config)
                resp, status = client.chat(
                    '你是测试节点，只回复 JMV_CORE_ONLINE。',
                    '链路测试'
                )
                if status == 'SUCCESS' and resp:
                    msg = f'✓ 已连接 {provider}'
                    color = C_GREEN
                else:
                    msg = f'✗ {provider} 失败: {status}'
                    color = C_RED
            except Exception as e:
                msg = f'✗ 异常: {e}'
                color = C_RED
            Clock.schedule_once(lambda dt: self._set_status(msg, color), 0)

        threading.Thread(target=_run, daemon=True).start()
