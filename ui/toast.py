"""Toast 通知组件 - 屏幕底部短暂显示后自动消失（Kivy，零依赖）"""
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label


def show_toast(message: str, duration: float = 3.0):
    """在屏幕底部显示 Toast 通知，duration 秒后自动消失。"""
    try:
        toast = _Toast(message, duration)
        Window.add_widget(toast)
    except Exception:
        pass  # 非 Kivy 环境静默忽略


class _Toast(FloatLayout):
    """内部 Toast 实现：圆角背景 + 淡入淡出动画。"""

    def __init__(self, message: str, duration: float, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        w = min(Window.width * 0.82, 400)
        h = 48
        self.size = (w, h)
        self.pos = ((Window.width - w) / 2, Window.height * 0.10)
        self.opacity = 0

        with self.canvas.before:
            Color(0.08, 0.10, 0.16, 0.92)
            self._rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[10]
            )
        self.bind(
            pos=lambda *_: setattr(self._rect, 'pos', self.pos),
            size=lambda *_: setattr(self._rect, 'size', self.size),
        )

        lbl = Label(
            text=message,
            font_size='13sp',
            color=(0.92, 0.94, 0.97, 1),
            halign='center',
            valign='middle',
            size_hint=(1, 1),
        )
        lbl.bind(size=lbl.setter('text_size'))
        self.add_widget(lbl)

        # 淡入
        Clock.schedule_once(self._fade_in, 0)
        # 淡出
        Clock.schedule_once(self._fade_out, duration)

    def _fade_in(self, dt):
        try:
            from kivy.animation import Animation
            Animation(opacity=1, duration=0.25).start(self)
        except Exception:
            self.opacity = 1

    def _fade_out(self, dt):
        try:
            from kivy.animation import Animation
            anim = Animation(opacity=0, duration=0.3)
            anim.bind(on_complete=lambda *_: self._remove())
            anim.start(self)
        except Exception:
            self._remove()

    def _remove(self):
        try:
            Window.remove_widget(self)
        except Exception:
            pass
