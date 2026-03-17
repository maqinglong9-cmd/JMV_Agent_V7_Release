"""步骤日志滚动显示（含时间戳 + 颜色分级）"""
import time
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle

C_LOG_BG    = (0.07, 0.09, 0.14, 1)
C_STEP      = (0.75, 0.95, 0.78, 1)   # 普通步骤：浅绿
C_SYSTEM    = (0.55, 0.75, 0.95, 1)   # [系统] 消息：浅蓝
C_ERROR     = (0.95, 0.55, 0.50, 1)   # 错误：浅红
C_SUCCESS   = (0.55, 0.95, 0.70, 1)   # 完成：亮绿
C_TIMESTAMP = (0.30, 0.38, 0.52, 1)   # 时间戳：暗色


def _pick_color(text: str):
    if text.startswith('✓') or text.startswith('[完成]'):
        return C_SUCCESS
    if text.startswith('✗') or text.startswith('[错误]') or '错误' in text[:6]:
        return C_ERROR
    if text.startswith('[系统]') or text.startswith('[设置]'):
        return C_SYSTEM
    return C_STEP


class LogViewer(ScrollView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.do_scroll_x = False
        self.bar_width = 4
        self.bar_color = (0.25, 0.35, 0.55, 0.8)
        self.bar_inactive_color = (0.15, 0.20, 0.35, 0.5)

        self._container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=2,
            padding=[10, 6],
        )
        self._container.bind(minimum_height=self._container.setter('height'))

        # 背景
        with self._container.canvas.before:
            Color(*C_LOG_BG)
            self._bg_rect = Rectangle(
                pos=self._container.pos,
                size=self._container.size
            )
        self._container.bind(
            pos=lambda *_: setattr(self._bg_rect, 'pos', self._container.pos),
            size=lambda *_: setattr(self._bg_rect, 'size', self._container.size),
        )

        # 空状态提示
        self._empty_lbl = Label(
            text='等待感知输入...',
            font_size='12sp',
            color=(0.30, 0.38, 0.52, 0.8),
            halign='center', valign='middle',
            size_hint=(1, 1),
        )
        self._empty_lbl.bind(size=self._empty_lbl.setter('text_size'))
        self._container.add_widget(self._empty_lbl)

        self.add_widget(self._container)

    def append(self, text: str):
        ts = time.strftime('%H:%M:%S')
        color = _pick_color(text)

        from ui.responsive import is_android, dp
        _row_h  = dp(26) if is_android() else 22
        _ts_w   = dp(68) if is_android() else 60
        _ts_fs  = '11sp' if is_android() else '10sp'
        _msg_fs = '13sp' if is_android() else '12sp'

        row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=_row_h,
            spacing=6,
        )

        # 时间戳
        ts_lbl = Label(
            text=ts,
            font_size=_ts_fs,
            color=C_TIMESTAMP,
            size_hint_x=None, width=_ts_w,
            halign='right', valign='middle',
        )
        ts_lbl.bind(size=ts_lbl.setter('text_size'))

        # 日志内容
        msg_lbl = Label(
            text=text,
            font_size=_msg_fs,
            color=color,
            halign='left', valign='top',
            size_hint_y=None,
        )

        def _update_msg(instance, value):
            instance.text_size = (value - 8, None)
            instance.texture_update()
            h = max(instance.texture_size[1] + 6, 22)
            instance.height = h
            row.height = h

        msg_lbl.bind(width=_update_msg)

        # 首次添加时移除空状态提示
        if self._empty_lbl and self._empty_lbl.parent:
            self._container.remove_widget(self._empty_lbl)

        row.add_widget(ts_lbl)
        row.add_widget(msg_lbl)
        self._container.add_widget(row)

        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: setattr(self, 'scroll_y', 0), 0.05)

    def clear(self):
        self._container.clear_widgets()
        self._container.add_widget(self._empty_lbl)
