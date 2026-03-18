"""JMV智伴 LLM 配置界面 - 纯 Kivy 实现（适配 Android + Windows）
无任何 Tkinter 依赖，可在 Android 上正常运行。
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
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
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
    """API Key 输入行，带显示/隐藏按钮"""

    def __init__(self, label_text, field_key, is_secret=False, **kwargs):
        super().__init__(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(4),
            **kwargs
        )
        self.field_key = field_key
        self.is_secret = is_secret
        self._hidden = is_secret
        self.height = dp(80) if is_android() else dp(68)

        # 标签行
        lbl_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None, height=dp(24)
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
        input_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=input_height(),
            spacing=dp(6),
        )
        self.ti = TextInput(
            hint_text='请输入...' if not is_secret else '请输入 API Key...',
            multiline=False,
            font_size=font_body(),
            foreground_color=(0.88, 0.92, 0.96, 1),
            background_color=C_INPUT_BG,
            hint_text_color=(0.40, 0.48, 0.62, 0.8),
            cursor_color=(*C_GREEN[:3], 1),
            padding=[dp(10), dp(10)],
            password=is_secret,
        )
        input_row.add_widget(self.ti)

        if is_secret:
            self._eye_btn = Button(
                text='👁',
                font_size=font_body(),
                size_hint_x=None,
                width=touch_target(),
                background_normal='',
                background_color=C_SECTION,
                color=C_SUBTEXT,
            )
            self._eye_btn.bind(on_press=self._toggle_visibility)
            input_row.add_widget(self._eye_btn)

        self.add_widget(input_row)

    def _toggle_visibility(self, _):
        self._hidden = not self._hidden
        self.ti.password = self._hidden
        self._eye_btn.color = C_SUBTEXT if self._hidden else C_GREEN

    @property
    def text(self) -> str:
        return self.ti.text.strip()

    @text.setter
    def text(self, val: str):
        self.ti.text = val or ''


class SectionHeader(BoxLayout):
    """带色条的区块标题"""

    def __init__(self, title, **kwargs):
        super().__init__(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(36),
            **kwargs
        )
        bar = BoxLayout(size_hint_x=None, width=dp(3))
        with bar.canvas.before:
            Color(*C_GREEN)
            r = Rectangle(pos=bar.pos, size=bar.size)
        bar.bind(pos=lambda *_: setattr(r, 'pos', bar.pos))
        bar.bind(size=lambda *_: setattr(r, 'size', bar.size))

        lbl = Label(
            text=f'  {title}',
            font_size=font_label(),
            color=C_SUBTEXT,
            bold=True,
            halign='left', valign='middle',
        )
        lbl.bind(size=lbl.setter('text_size'))
        self.add_widget(bar)
        self.add_widget(lbl)
        _bg(self, C_SECTION)


class LLMConfigScreen(BoxLayout):
    """全屏 LLM 配置界面（纯 Kivy，无 Tkinter 依赖）"""

    def __init__(self, on_saved=None, **kwargs):
        super().__init__(orientation='vertical', spacing=0, **kwargs)
        self._on_saved = on_saved
        self._config = load_config()
        self._fields: dict[str, KeyField] = {}
        self._provider_sections: dict[str, BoxLayout] = {}
        _bg(self, C_BG)
        self._build_ui()

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

        # ── 可滚动内容区 ────────────────────────────────
        scroll = ScrollView(do_scroll_x=False)
        content = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(8),
            padding=[padding_h(), padding_v(), padding_h(), padding_v()],
        )
        content.bind(minimum_height=content.setter('height'))
        _bg(content, C_BG)

        # ── 供应商选择 ──────────────────────────────────
        content.add_widget(SectionHeader('选择 AI 供应商'))

        provider_card = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(56),
            padding=[dp(8), dp(6)],
        )
        _card_bg(provider_card, C_CARD)

        provider_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(44),
            spacing=dp(8),
        )
        prov_lbl = Label(
            text='当前供应商:',
            font_size=font_body(),
            color=C_TEXT,
            size_hint_x=None,
            width=dp(90),
            halign='left', valign='middle',
        )
        prov_lbl.bind(size=prov_lbl.setter('text_size'))

        self._provider_spinner = Spinner(
            text=self._config.get('active_provider', 'Gemini'),
            values=PROVIDERS,
            font_size=font_body(),
            background_normal='',
            background_color=(0.18, 0.24, 0.36, 1),
            color=C_TEXT,
            size_hint_x=1,
            height=dp(44),
        )
        self._provider_spinner.bind(text=self._on_provider_change)

        provider_row.add_widget(prov_lbl)
        provider_row.add_widget(self._provider_spinner)
        provider_card.add_widget(provider_row)
        content.add_widget(provider_card)

        # ── 各供应商配置区（动态显示/隐藏）────────────────
        for provider, fields in _PROVIDER_FIELDS.items():
            section = BoxLayout(
                orientation='vertical',
                size_hint_y=None,
                spacing=dp(6),
                padding=[dp(8), dp(6)],
            )
            _card_bg(section, C_CARD)

            for field_key, label_text, is_secret in fields:
                kf = KeyField(
                    label_text=f'{provider} {label_text}',
                    field_key=field_key,
                    is_secret=is_secret,
                )
                kf.text = self._config.get(field_key, '')
                section.add_widget(kf)
                self._fields[field_key] = kf

            # 计算总高度
            section.height = len(fields) * (dp(80) if is_android() else dp(68)) + dp(12)
            self._provider_sections[provider] = section
            content.add_widget(section)

        scroll.add_widget(content)
        self.add_widget(scroll)

        # ── 底部按钮区 ──────────────────────────────────
        btn_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=button_height() + dp(16),
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

        # 初始化显示
        self._on_provider_change(None, self._config.get('active_provider', 'Gemini'))

    def _on_provider_change(self, spinner, provider):
        """切换供应商时显示/隐藏对应配置区"""
        for prov, section in self._provider_sections.items():
            section.opacity = 1 if prov == provider else 0
            section.height = (
                (len(_PROVIDER_FIELDS[prov]) * (dp(80) if is_android() else dp(68)) + dp(12))
                if prov == provider else 0
            )

    def _collect_config(self) -> dict:
        """从 UI 控件收集当前配置"""
        config = dict(self._config)
        config['active_provider'] = self._provider_spinner.text
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
        """后台测试 LLM 连接"""
        self._set_status('⏳ 连接中...', C_YELLOW)
        config = self._collect_config()

        def _run():
            try:
                from agent.universal_llm_client import UniversalLLMClient
                client = UniversalLLMClient(config)
                resp, status = client.chat(
                    '你是测试节点，只回复 JMV_CORE_ONLINE。',
                    '链路测试'
                )
                if status == 'SUCCESS' and resp:
                    msg = f'✓ 已连接 {config["active_provider"]}'
                    color = C_GREEN
                else:
                    msg = f'✗ 连接失败: {status}'
                    color = C_RED
            except Exception as e:
                msg = f'✗ 异常: {e}'
                color = C_RED
            Clock.schedule_once(lambda dt: self._set_status(msg, color), 0)

        threading.Thread(target=_run, daemon=True).start()
