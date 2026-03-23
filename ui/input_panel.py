"""智能输入面板：固定 144dp（SmartInput 52 + Tools 40 + Run 52）
专家模式展开时自动增高到 248dp（3×52 + 40 + 52）。
工具栏内含：截图、语音、AI进化、清理工作区。
"""
import threading

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle, Rectangle

from ui.responsive import (
    dp, font_body, font_small, font_btn, font_hint, font_label,
    button_height, input_height, tool_row_height, padding_h, is_android
)

C_ROW_BG  = (0.10, 0.13, 0.20, 1)
C_LABEL   = (0.55, 0.65, 0.80, 1)
C_HINT    = (0.35, 0.42, 0.55, 1)
C_BTN_RUN = (0.18, 0.68, 0.40, 1)
C_BTN_DIS = (0.22, 0.28, 0.38, 1)
C_BTN_TOO = (0.14, 0.22, 0.34, 1)
C_COUNT   = (0.40, 0.50, 0.62, 1)
C_TEXT    = (0.90, 0.92, 0.95, 1)
C_SUBTEXT = (0.55, 0.62, 0.75, 1)
C_GREEN   = (0.20, 0.75, 0.45, 1)
MAX_LEN   = 300

# 固定高度常量
_H_INPUT = dp(52)   # SmartInput / 每个专家行
_H_TOOLS = dp(40)   # 工具栏
_H_RUN   = dp(52)   # 运行按钮
_H_BASE  = _H_INPUT + _H_TOOLS + _H_RUN          # 144dp（智能模式）
_H_EXP   = _H_INPUT * 3 + _H_TOOLS + _H_RUN      # 248dp（专家模式）


def _rounded_bg(widget, color, radius=8):
    with widget.canvas.before:
        Color(*color)
        r = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[radius])
    widget.bind(pos=lambda *_: setattr(r, 'pos', widget.pos))
    widget.bind(size=lambda *_: setattr(r, 'size', widget.size))


def _bg(widget, color):
    with widget.canvas.before:
        Color(*color)
        rect = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(pos=lambda *_: setattr(rect, 'pos', widget.pos))
    widget.bind(size=lambda *_: setattr(rect, 'size', widget.size))


class InputRow(BoxLayout):
    """专家模式：单通道输入框"""

    def __init__(self, icon, label_text, hint, **kwargs):
        super().__init__(
            orientation='horizontal',
            size_hint_y=None,
            height=_H_INPUT,
            spacing=dp(6),
            padding=[dp(6), dp(3)],
            **kwargs
        )
        _rounded_bg(self, C_ROW_BG, radius=6)

        lbl = Label(
            text=f'{icon} {label_text}',
            font_size='11sp',
            color=C_LABEL,
            size_hint_x=None, width=dp(62),
            halign='right', valign='middle',
        )
        lbl.bind(size=lbl.setter('text_size'))

        self.ti = TextInput(
            hint_text=hint,
            multiline=False,
            font_size=font_body(),
            foreground_color=(0.88, 0.92, 0.96, 1),
            background_color=(0.08, 0.11, 0.17, 1),
            hint_text_color=(*C_HINT[:3], 0.6),
            cursor_color=(*C_GREEN[:3], 1),
            padding=[dp(8), dp(8)],
        )

        self.count_lbl = Label(
            text=f'0/{MAX_LEN}',
            font_size=font_small(),
            color=C_COUNT,
            size_hint_x=None, width=dp(48),
            halign='right', valign='middle',
        )
        self.count_lbl.bind(size=self.count_lbl.setter('text_size'))
        self.ti.bind(text=self._update_count)

        self.add_widget(lbl)
        self.add_widget(self.ti)
        self.add_widget(self.count_lbl)

    def _update_count(self, instance, value):
        n = len(value)
        self.count_lbl.text = f'{n}/{MAX_LEN}'
        self.count_lbl.color = (0.85, 0.35, 0.25, 1) if n >= MAX_LEN else C_COUNT

    @property
    def text(self) -> str:
        return self.ti.text


# ── LLM 文本拆分提示词 ─────────────────────────────────────
_SPLIT_SYSTEM = """你是感觉输入分析器。将用户描述的场景拆分为三个感知通道，每行一个，格式严格如下：
视觉：...
听觉：...
触觉：...
每项50字以内，不要多余解释，不要序号，不要冒号之外的标点。"""


def _split_with_llm(text: str, client) -> tuple:
    """用 LLM 将自然语言拆分为三路感觉输入，失败时全部填入视觉"""
    try:
        resp, status = client.chat(_SPLIT_SYSTEM, f'场景描述：{text}')
        if status != 'SUCCESS' or not resp:
            return text[:MAX_LEN], '', ''
        lines = {
            line.split('：', 1)[0].strip(): line.split('：', 1)[1].strip()
            for line in resp.strip().splitlines()
            if '：' in line
        }
        return (
            lines.get('视觉', text[:MAX_LEN])[:MAX_LEN],
            lines.get('听觉', '')[:MAX_LEN],
            lines.get('触觉', '')[:MAX_LEN],
        )
    except Exception:
        return text[:MAX_LEN], '', ''


class InputPanel(BoxLayout):
    """固定高度输入面板：智能144dp / 专家248dp（自管理高度）"""

    def __init__(self, on_run_callback, llm_getter=None,
                 on_evolve=None, on_cleanup=None, **kwargs):
        kwargs.setdefault('size_hint_y', None)
        super().__init__(
            orientation='vertical',
            spacing=0,
            padding=0,
            **kwargs
        )
        self._on_run        = on_run_callback
        self._llm_getter    = llm_getter
        self._on_evolve     = on_evolve
        self._on_cleanup    = on_cleanup
        self._voice_enabled = False
        self._expert_mode   = False

        _bg(self, (0.07, 0.09, 0.14, 1))
        self._build_ui()
        self._apply_mode()

    # ── 构建 UI ──────────────────────────────────────────

    def _build_ui(self):
        # ── 专家三通道（默认隐藏）───────────────────────
        self.visual_row  = InputRow('👁', '视觉', '例：前方红灯闪烁')
        self.audio_row   = InputRow('👂', '听觉', '例：刺耳的喇叭声')
        self.tactile_row = InputRow('✋', '触觉', '例：方向盘粗糙触感')
        self.add_widget(self.visual_row)
        self.add_widget(self.audio_row)
        self.add_widget(self.tactile_row)

        # ── 智能单行输入 dp(52) ──────────────────────────
        self._smart_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None, height=_H_INPUT,
            spacing=dp(4),
            padding=[dp(6), dp(3)],
        )
        _rounded_bg(self._smart_row, C_ROW_BG, radius=6)

        # 模式切换小按钮（左侧 36dp）
        self._mode_btn = Button(
            text='🎯',
            font_size=font_small(),
            size_hint_x=None, width=dp(36),
            background_normal='',
            background_color=(0.15, 0.28, 0.20, 1),
            color=C_GREEN,
        )
        self._mode_btn.bind(on_press=self._toggle_mode)

        self._smart_input = TextInput(
            hint_text='输入你的任务或问题，AI 自动理解并执行...',
            multiline=False,
            font_size=font_body(),
            foreground_color=(0.88, 0.92, 0.96, 1),
            background_color=(0.08, 0.11, 0.17, 1),
            hint_text_color=(*C_HINT[:3], 0.6),
            cursor_color=(*C_GREEN[:3], 1),
            padding=[dp(8), dp(8)],
        )
        self._smart_input.bind(on_text_validate=lambda _: self._on_press(None))

        self._smart_row.add_widget(self._mode_btn)
        self._smart_row.add_widget(self._smart_input)
        self.add_widget(self._smart_row)

        # ── 工具栏 dp(40) ────────────────────────────────
        tool_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None, height=_H_TOOLS,
            spacing=dp(4),
            padding=[dp(6), dp(4)],
        )
        _bg(tool_row, (0.08, 0.10, 0.16, 1))

        self._screenshot_btn = Button(
            text='📷',
            font_size=font_small(),
            size_hint_x=None, width=dp(44),
            background_normal='',
            background_color=C_BTN_TOO,
            color=(0.75, 0.85, 0.95, 1),
        )
        self._screenshot_btn.bind(on_press=self._on_screenshot)

        self._voice_btn = Button(
            text='🔇',
            font_size=font_small(),
            size_hint_x=None, width=dp(44),
            background_normal='',
            background_color=(0.20, 0.18, 0.26, 1),
            color=(0.65, 0.65, 0.75, 1),
        )
        self._voice_btn.bind(on_press=self._toggle_voice)

        tool_row.add_widget(self._screenshot_btn)
        tool_row.add_widget(self._voice_btn)
        tool_row.add_widget(Label())  # spacer

        if self._on_evolve:
            self._evo_btn = Button(
                text='🧬',
                font_size=font_small(),
                size_hint_x=None, width=dp(44),
                background_normal='',
                background_color=(0.12, 0.22, 0.16, 1),
                color=(0.60, 1.0, 0.70, 1),
            )
            self._evo_btn.bind(on_press=self._on_evo_press)
            tool_row.add_widget(self._evo_btn)

        if self._on_cleanup:
            self._cleanup_btn = Button(
                text='🗑',
                font_size=font_small(),
                size_hint_x=None, width=dp(44),
                background_normal='',
                background_color=(0.22, 0.14, 0.14, 1),
                color=(0.85, 0.65, 0.65, 1),
            )
            self._cleanup_btn.bind(on_press=lambda _: self._on_cleanup())
            tool_row.add_widget(self._cleanup_btn)

        self.add_widget(tool_row)

        # ── 运行按钮 dp(52) ──────────────────────────────
        self.run_btn = Button(
            text='▶  执行任务',
            size_hint_y=None, height=_H_RUN,
            background_normal='',
            background_color=C_BTN_RUN,
            color=(0.95, 1.0, 0.97, 1),
            font_size=font_btn(),
            bold=True,
        )
        self.run_btn.bind(on_press=self._on_press)
        self.add_widget(self.run_btn)

    # ── 模式切换 ─────────────────────────────────────────

    def _toggle_mode(self, _):
        self._expert_mode = not self._expert_mode
        self._apply_mode()

    def _apply_mode(self):
        if self._expert_mode:
            self._mode_btn.text             = '🔬'
            self._mode_btn.background_color = (0.24, 0.18, 0.10, 1)
            self._mode_btn.color            = (0.90, 0.70, 0.30, 1)
            self.visual_row.height   = _H_INPUT
            self.visual_row.opacity  = 1
            self.audio_row.height    = _H_INPUT
            self.audio_row.opacity   = 1
            self.tactile_row.height  = _H_INPUT
            self.tactile_row.opacity = 1
            self._smart_row.height   = 0
            self._smart_row.opacity  = 0
            self.height = _H_EXP
        else:
            self._mode_btn.text             = '🎯'
            self._mode_btn.background_color = (0.15, 0.28, 0.20, 1)
            self._mode_btn.color            = C_GREEN
            self.visual_row.height   = 0
            self.visual_row.opacity  = 0
            self.audio_row.height    = 0
            self.audio_row.opacity   = 0
            self.tactile_row.height  = 0
            self.tactile_row.opacity = 0
            self._smart_row.height   = _H_INPUT
            self._smart_row.opacity  = 1
            self.height = _H_BASE

    # ── 事件处理 ─────────────────────────────────────────

    def _on_press(self, _):
        if self._expert_mode:
            visual  = self.visual_row.text.strip()[:MAX_LEN]
            audio   = self.audio_row.text.strip()[:MAX_LEN]
            tactile = self.tactile_row.text.strip()[:MAX_LEN]
            if not any([visual, audio, tactile]):
                self._show_hint('⚠ 请填写至少一项感觉输入')
                return
            self._start_run(
                visual  or '无视觉输入',
                audio   or '无听觉输入',
                tactile or '无触觉输入',
            )
        else:
            text = self._smart_input.text.strip()
            if not text:
                self._show_hint('⚠ 请输入场景描述')
                return
            self._start_run_smart(text)

    def _start_run_smart(self, text: str):
        llm = self._get_llm()
        if llm:
            self.run_btn.disabled = True
            self.run_btn.background_color = C_BTN_DIS
            self.run_btn.text = '🧠 AI 分析中...'

            def _worker():
                v, a, t = _split_with_llm(text, llm)
                from kivy.clock import Clock
                Clock.schedule_once(lambda dt: self._after_split(v, a, t), 0)

            threading.Thread(target=_worker, daemon=True).start()
        else:
            self._start_run(text, '无听觉输入', '无触觉输入')

    def _after_split(self, visual: str, audio: str, tactile: str):
        self.run_btn.disabled = False
        self.run_btn.background_color = C_BTN_RUN
        self.run_btn.text = '▶  执行任务'
        self._start_run(visual, audio, tactile)

    def _start_run(self, visual: str, audio: str, tactile: str):
        self.run_btn.disabled = True
        self.run_btn.background_color = C_BTN_DIS
        self._on_run(visual, audio, tactile)

    def _get_llm(self):
        if callable(self._llm_getter):
            return self._llm_getter()
        return None

    def _on_screenshot(self, _):
        self._screenshot_btn.disabled = True

        def _run():
            from agent.screenshot_tool import capture_and_analyze
            from kivy.clock import Clock
            desc, status = capture_and_analyze()

            def _update(dt):
                if 'ERROR' not in status:
                    if self._expert_mode:
                        self.visual_row.ti.text = desc[:MAX_LEN]
                    else:
                        self._smart_input.text = desc[:MAX_LEN]
                self._screenshot_btn.disabled = False

            Clock.schedule_once(_update, 0)

        threading.Thread(target=_run, daemon=True).start()

    def _toggle_voice(self, _):
        self._voice_enabled = not self._voice_enabled
        if self._voice_enabled:
            self._voice_btn.text             = '🔊'
            self._voice_btn.background_color = (0.12, 0.30, 0.18, 1)
            self._voice_btn.color            = (0.60, 1.0, 0.70, 1)
        else:
            self._voice_btn.text             = '🔇'
            self._voice_btn.background_color = (0.20, 0.18, 0.26, 1)
            self._voice_btn.color            = (0.65, 0.65, 0.75, 1)

    def _on_evo_press(self, _):
        if not self._on_evolve:
            return
        self._evo_btn.disabled = True
        self._evo_btn.text = '⏳'

        def _run():
            try:
                self._on_evolve()
            finally:
                from kivy.clock import Clock
                Clock.schedule_once(lambda dt: self._reset_evo_btn(), 0)

        threading.Thread(target=_run, daemon=True).start()

    def _reset_evo_btn(self):
        self._evo_btn.disabled = False
        self._evo_btn.text = '🧬'

    @property
    def voice_enabled(self) -> bool:
        return self._voice_enabled

    def _show_hint(self, msg: str):
        from kivy.clock import Clock
        orig_text  = self.run_btn.text
        orig_color = list(self.run_btn.background_color)
        self.run_btn.text = msg
        self.run_btn.background_color = (0.70, 0.35, 0.10, 1)
        Clock.schedule_once(lambda dt: (
            setattr(self.run_btn, 'text', orig_text),
            setattr(self.run_btn, 'background_color', orig_color),
        ), 2)

    def enable(self):
        self.run_btn.disabled = False
        self.run_btn.background_color = C_BTN_RUN
        self.run_btn.text = '▶  执行任务'
