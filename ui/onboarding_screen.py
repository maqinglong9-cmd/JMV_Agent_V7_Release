"""首次启动引导页（3步：欢迎 → 配置LLM → 开始使用）"""
import os

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle

from ui.responsive import dp, font_large, font_body, font_btn, button_height, padding_h

_FLAG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'jmv_workspace', 'onboarding_done.flag'
)

C_BG      = (0.06, 0.08, 0.12, 1)
C_CARD    = (0.10, 0.13, 0.20, 1)
C_GREEN   = (0.18, 0.62, 0.36, 1)
C_TEXT    = (0.90, 0.92, 0.95, 1)
C_SUBTEXT = (0.55, 0.62, 0.75, 1)

_STEPS = [
    (
        '🧠 欢迎使用 JMV智伴',
        '全脑感知 AI 助手\n\n'
        '• 多模态感知（视觉/听觉/触觉）\n'
        '• 20+ LLM 供应商支持\n'
        '• Android + Windows 双平台\n'
        '• 底层操作能力（文件/进程/UI）',
    ),
    (
        '⚙ 配置 LLM 供应商',
        '点击底部"设置"标签页\n\n'
        '选择你的 AI 供应商并填入 API Key：\n'
        '• 国际：Gemini / OpenAI / Claude\n'
        '• 国内：通义千问 / 文心 / 智谱\n'
        '• 本地：Ollama（无需 API Key）',
    ),
    (
        '🚀 开始使用',
        '一切就绪！\n\n'
        '• 脑感知页：输入任务，AI 自动路由\n'
        '• 对话页：多轮自然语言对话\n'
        '• 设置页：随时切换 LLM 供应商\n\n'
        '祝你使用愉快！',
    ),
]


def is_onboarding_done() -> bool:
    """检查是否已完成首次引导。"""
    return os.path.isfile(_FLAG_FILE)


def mark_onboarding_done():
    """标记引导已完成（写入标志文件）。"""
    try:
        os.makedirs(os.path.dirname(_FLAG_FILE), exist_ok=True)
        with open(_FLAG_FILE, 'w') as f:
            f.write('done')
    except Exception:
        pass


def _bg(widget, color):
    with widget.canvas.before:
        Color(*color)
        rect = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(pos=lambda *_: setattr(rect, 'pos', widget.pos))
    widget.bind(size=lambda *_: setattr(rect, 'size', widget.size))


class OnboardingScreen(BoxLayout):
    """首次启动引导页，完成后调用 on_done 回调。"""

    def __init__(self, on_done=None, **kwargs):
        super().__init__(orientation='vertical', spacing=0, **kwargs)
        _bg(self, C_BG)
        self._on_done = on_done
        self._step = 0
        self._build()

    def _build(self):
        self.clear_widgets()
        title_text, body_text = _STEPS[self._step]
        total = len(_STEPS)

        # 进度指示条
        progress_row = BoxLayout(
            size_hint_y=None, height=dp(36),
            padding=[padding_h(), dp(8)],
            spacing=dp(6),
        )
        _bg(progress_row, C_CARD)
        for i in range(total):
            dot = Label(
                text='●' if i == self._step else '○',
                font_size='14sp',
                color=(0.18, 0.62, 0.36, 1) if i == self._step else (*C_SUBTEXT[:3], 1),
                size_hint_x=None, width=dp(24),
            )
            progress_row.add_widget(dot)
        progress_row.add_widget(Label())
        progress_row.add_widget(Label(
            text=f'{self._step + 1} / {total}',
            font_size='12sp',
            color=C_SUBTEXT,
            size_hint_x=None, width=dp(48),
        ))
        self.add_widget(progress_row)

        # 内容区
        content = BoxLayout(
            orientation='vertical',
            padding=[dp(24), dp(28)],
            spacing=dp(18),
        )
        _bg(content, C_BG)

        title_lbl = Label(
            text=title_text,
            font_size=font_large(),
            bold=True,
            color=C_TEXT,
            halign='center', valign='middle',
            size_hint_y=None, height=dp(60),
        )
        title_lbl.bind(size=title_lbl.setter('text_size'))

        body_lbl = Label(
            text=body_text,
            font_size=font_body(),
            color=C_SUBTEXT,
            halign='left', valign='top',
            size_hint_y=1,
        )
        body_lbl.bind(size=body_lbl.setter('text_size'))

        content.add_widget(title_lbl)
        content.add_widget(body_lbl)
        self.add_widget(content)

        # 按钮区
        btn_row = BoxLayout(
            size_hint_y=None,
            height=button_height() + dp(24),
            padding=[padding_h(), dp(12)],
            spacing=dp(12),
        )
        _bg(btn_row, C_CARD)

        if self._step > 0:
            back_btn = Button(
                text='← 上一步',
                font_size=font_btn(),
                background_normal='',
                background_color=(0.15, 0.20, 0.30, 1),
                color=C_SUBTEXT,
                size_hint_x=0.35,
            )
            back_btn.bind(on_press=lambda _: self._prev())
            btn_row.add_widget(back_btn)

        is_last = self._step == total - 1
        next_btn = Button(
            text='开始使用 ✓' if is_last else '下一步 →',
            font_size=font_btn(),
            bold=True,
            background_normal='',
            background_color=C_GREEN,
            color=C_TEXT,
        )
        next_btn.bind(on_press=lambda _: self._next())
        btn_row.add_widget(next_btn)
        self.add_widget(btn_row)

    def _next(self):
        if self._step < len(_STEPS) - 1:
            self._step += 1
            self._build()
        else:
            mark_onboarding_done()
            if self._on_done:
                self._on_done()

    def _prev(self):
        if self._step > 0:
            self._step -= 1
            self._build()
