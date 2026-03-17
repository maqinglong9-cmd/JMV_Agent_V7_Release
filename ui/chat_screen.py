"""对话屏幕 - 气泡式多轮聊天 UI"""
import threading

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.clock import Clock

from ui.responsive import (
    dp, font_body, font_small, font_large, font_btn, font_hint,
    button_height, input_height, padding_h, padding_v,
    is_android, spacing_normal
)

C_BG         = (0.06, 0.08, 0.12, 1)
C_HEADER     = (0.10, 0.13, 0.20, 1)
C_USER_BG    = (0.18, 0.42, 0.28, 1)
C_BOT_BG     = (0.12, 0.16, 0.26, 1)
C_TEXT       = (0.90, 0.92, 0.95, 1)
C_SUBTEXT    = (0.55, 0.62, 0.75, 1)
C_INPUT_BG   = (0.08, 0.11, 0.17, 1)
C_SEND_BTN   = (0.18, 0.62, 0.36, 1)
C_SEND_DIS   = (0.20, 0.26, 0.36, 1)
C_CLEAR_BTN  = (0.22, 0.16, 0.16, 1)
C_GREEN      = (0.20, 0.75, 0.45, 1)


def _bg(widget, color):
    with widget.canvas.before:
        Color(*color)
        rect = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(pos=lambda *_: setattr(rect, 'pos', widget.pos))
    widget.bind(size=lambda *_: setattr(rect, 'size', widget.size))


def _bubble_bg(widget, color, radius=12):
    with widget.canvas.before:
        Color(*color)
        rect = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[radius])
    widget.bind(pos=lambda *_: setattr(rect, 'pos', widget.pos))
    widget.bind(size=lambda *_: setattr(rect, 'size', widget.size))


class MessageBubble(BoxLayout):
    """单条消息气泡"""

    def __init__(self, text: str, is_user: bool, **kwargs):
        super().__init__(
            orientation='horizontal',
            size_hint_y=None,
            padding=[dp(8), dp(4)],
            spacing=dp(6),
            **kwargs
        )
        self.is_user = is_user

        # 气泡容器
        bubble = BoxLayout(
            orientation='vertical',
            size_hint_x=0.78 if is_android() else 0.72,
            size_hint_y=None,
            padding=[dp(10), dp(8)],
        )
        _bubble_bg(bubble, C_USER_BG if is_user else C_BOT_BG, radius=12)

        lbl = Label(
            text=text,
            font_size=font_body(),
            color=C_TEXT,
            halign='right' if is_user else 'left',
            valign='top',
            markup=False,
            size_hint_y=None,
        )

        def _update_size(instance, width):
            instance.text_size = (width - dp(4), None)
            instance.texture_update()
            h = max(instance.texture_size[1] + dp(4), dp(24))
            instance.height = h
            bubble.height = h + dp(16)
            self.height = bubble.height + dp(8)

        lbl.bind(width=_update_size)
        bubble.add_widget(lbl)
        bubble.bind(minimum_height=bubble.setter('height'))

        spacer = Label(size_hint_x=1)  # 推到对应侧

        if is_user:
            self.add_widget(spacer)
            self.add_widget(bubble)
        else:
            self.add_widget(bubble)
            self.add_widget(spacer)

        self.height = dp(60)  # 初始高度，后续由 lbl 绑定更新


class TypingIndicator(BoxLayout):
    """AI 正在输入动画指示器"""

    def __init__(self, **kwargs):
        super().__init__(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            padding=[dp(8), dp(4)],
        )
        bubble = BoxLayout(
            size_hint_x=None, width=dp(80),
            size_hint_y=None, height=dp(32),
            padding=[dp(10), dp(6)],
        )
        _bubble_bg(bubble, C_BOT_BG, radius=12)

        self._lbl = Label(
            text='AI ●●●',
            font_size=font_small(),
            color=C_SUBTEXT,
        )
        bubble.add_widget(self._lbl)
        self.add_widget(bubble)
        self.add_widget(Label())  # spacer

        self._dots = 1
        Clock.schedule_interval(self._animate, 0.5)

    def _animate(self, dt):
        self._dots = (self._dots % 3) + 1
        self._lbl.text = 'AI ' + '●' * self._dots + '○' * (3 - self._dots)

    def dismiss(self):
        Clock.unschedule(self._animate)


class ChatScreen(BoxLayout):
    """完整对话屏幕"""

    def __init__(self, llm_client=None, **kwargs):
        super().__init__(orientation='vertical', spacing=0, **kwargs)
        _bg(self, C_BG)

        from agent.chat_agent import ChatAgent
        self._agent = ChatAgent(llm_client)
        self._typing_indicator = None

        self._build_ui()
        self._load_history()

    def set_llm(self, client) -> None:
        """更新 LLM 客户端（切换配置后调用）"""
        self._agent.set_llm(client)

    # ── UI 构建 ──────────────────────────────────────────

    def _build_ui(self):
        # 标题栏
        header = BoxLayout(
            size_hint_y=None,
            height=dp(52),
            padding=[padding_h(), dp(8)],
            spacing=dp(8),
        )
        _bg(header, C_HEADER)

        title = Label(
            text='💬 AI 对话',
            font_size=font_large(),
            bold=True,
            color=C_TEXT,
            halign='left', valign='middle',
        )
        title.bind(size=title.setter('text_size'))

        clear_btn = Button(
            text='🗑 清空',
            font_size=font_small(),
            size_hint_x=None,
            width=dp(72),
            background_normal='',
            background_color=C_CLEAR_BTN,
            color=(0.85, 0.65, 0.65, 1),
        )
        clear_btn.bind(on_press=lambda _: self._clear_chat())

        header.add_widget(title)
        header.add_widget(Label())  # spacer
        header.add_widget(clear_btn)
        self.add_widget(header)

        # 消息滚动区
        self._scroll = ScrollView(do_scroll_x=False)
        self._msg_list = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(4),
            padding=[dp(6), dp(8)],
        )
        self._msg_list.bind(minimum_height=self._msg_list.setter('height'))
        _bg(self._msg_list, C_BG)
        self._scroll.add_widget(self._msg_list)
        self.add_widget(self._scroll)

        # 欢迎消息
        self._add_bot_msg('你好！我是 JMV智伴。有什么我可以帮你的吗？')

        # 输入区
        input_area = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=input_height() + dp(20),
            spacing=dp(8),
            padding=[padding_h(), dp(8)],
        )
        _bg(input_area, (0.08, 0.10, 0.16, 1))

        self._input = TextInput(
            hint_text='输入消息...',
            multiline=False,
            font_size=font_body(),
            foreground_color=(0.88, 0.92, 0.96, 1),
            background_color=C_INPUT_BG,
            hint_text_color=(0.40, 0.48, 0.62, 0.8),
            cursor_color=(*C_GREEN[:3], 1),
            padding=[dp(10), dp(10)],
        )
        self._input.bind(on_text_validate=self._on_send)

        self._send_btn = Button(
            text='发送 ➤',
            font_size=font_btn(),
            size_hint_x=None,
            width=dp(80),
            height=input_height(),
            background_normal='',
            background_color=C_SEND_BTN,
            color=C_TEXT,
            bold=True,
        )
        self._send_btn.bind(on_press=self._on_send)

        input_area.add_widget(self._input)
        input_area.add_widget(self._send_btn)
        self.add_widget(input_area)

    # ── 消息操作 ─────────────────────────────────────────

    def _add_bot_msg(self, text: str):
        bubble = MessageBubble(text=text, is_user=False)
        self._msg_list.add_widget(bubble)
        self._scroll_to_bottom()

    def _add_user_msg(self, text: str):
        bubble = MessageBubble(text=text, is_user=True)
        self._msg_list.add_widget(bubble)
        self._scroll_to_bottom()

    def _show_typing(self):
        if self._typing_indicator:
            return
        self._typing_indicator = TypingIndicator()
        self._msg_list.add_widget(self._typing_indicator)
        self._scroll_to_bottom()

    def _hide_typing(self):
        if self._typing_indicator:
            self._typing_indicator.dismiss()
            self._msg_list.remove_widget(self._typing_indicator)
            self._typing_indicator = None

    def _scroll_to_bottom(self):
        Clock.schedule_once(lambda dt: setattr(self._scroll, 'scroll_y', 0), 0.1)

    def _on_send(self, _):
        text = self._input.text.strip()
        if not text:
            return
        self._input.text = ''
        self._send_btn.disabled = True
        self._send_btn.background_color = C_SEND_DIS
        self._add_user_msg(text)
        self._show_typing()

        def _worker():
            reply = self._agent.chat(text)
            Clock.schedule_once(lambda dt: self._on_reply(reply), 0)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_reply(self, reply: str):
        self._hide_typing()
        self._add_bot_msg(reply)
        self._send_btn.disabled = False
        self._send_btn.background_color = C_SEND_BTN

    def _clear_chat(self):
        self._msg_list.clear_widgets()
        self._agent.clear_history()
        self._add_bot_msg('对话已清空。有什么新的问题吗？')

    def _load_history(self):
        """加载历史对话到 UI"""
        history = self._agent.get_history()
        if not history:
            return
        # 清空欢迎消息重新加载
        self._msg_list.clear_widgets()
        for msg in history[-40:]:  # 最多显示最近 20 轮
            if msg['role'] == 'user':
                self._add_user_msg(msg['content'])
            else:
                self._add_bot_msg(msg['content'])
