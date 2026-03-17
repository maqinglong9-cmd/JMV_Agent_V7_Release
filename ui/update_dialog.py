"""更新弹窗 UI - 显示版本信息、下载进度、确认/取消"""
import threading
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle

C_BG      = (0.08, 0.11, 0.17, 1)
C_BTN_OK  = (0.15, 0.55, 0.35, 1)
C_BTN_NO  = (0.28, 0.22, 0.22, 1)
C_TEXT    = (0.90, 0.92, 0.95, 1)
C_SUBTEXT = (0.55, 0.60, 0.70, 1)
C_GREEN   = (0.20, 0.75, 0.45, 1)
C_RED     = (0.80, 0.25, 0.25, 1)


def _bg(widget, color):
    with widget.canvas.before:
        Color(*color)
        rect = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(pos=lambda *_: setattr(rect, 'pos', widget.pos))
    widget.bind(size=lambda *_: setattr(rect, 'size', widget.size))


class UpdateDialog(Popup):
    """
    显示可用更新并提供下载/安装入口。

    参数:
      update_info  -- version_checker.check_for_update() 的返回值
      on_confirm   -- 用户点击"立即升级"时的回调，接受 update_info 作为参数
    """

    def __init__(self, update_info: dict, on_confirm, **kwargs):
        self._info       = update_info
        self._on_confirm = on_confirm
        self._cancelled  = False

        content = self._build_content()

        super().__init__(
            title='',
            content=content,
            size_hint=(0.92, None),
            height=360,
            auto_dismiss=False,
            separator_height=0,
            background='',
            background_color=(0, 0, 0, 0),
            **kwargs,
        )
        _bg(self, C_BG)

    def _build_content(self) -> BoxLayout:
        root = BoxLayout(orientation='vertical', padding=16, spacing=10)
        _bg(root, C_BG)

        # ── 标题 ────────────────────────────────────────────
        title = Label(
            text='[b]发现新版本[/b]',
            markup=True, font_size='16sp',
            color=C_TEXT,
            size_hint_y=None, height=32,
            halign='center', valign='middle',
        )
        title.bind(size=title.setter('text_size'))
        root.add_widget(title)

        # ── 版本号 ───────────────────────────────────────────
        ver_text = (
            f"当前版本：[color=#8899aa]{self._info['current']}[/color]    "
            f"最新版本：[color=#33cc77]{self._info['latest']}[/color]"
        )
        ver_lbl = Label(
            text=ver_text, markup=True, font_size='12sp',
            color=C_TEXT,
            size_hint_y=None, height=28,
            halign='center', valign='middle',
        )
        ver_lbl.bind(size=ver_lbl.setter('text_size'))
        root.add_widget(ver_lbl)

        # ── 更新日志 ─────────────────────────────────────────
        notes = self._info.get('release_notes') or '（无更新说明）'
        notes_lbl = Label(
            text=notes, font_size='12sp',
            color=C_SUBTEXT,
            halign='left', valign='top',
            text_size=(None, None),
        )
        notes_lbl.bind(size=notes_lbl.setter('text_size'))
        root.add_widget(notes_lbl)

        # ── 进度条（初始隐藏）───────────────────────────────
        self._progress = ProgressBar(
            max=100, value=0,
            size_hint_y=None, height=8,
            opacity=0,
        )
        root.add_widget(self._progress)

        # ── 状态文字 ─────────────────────────────────────────
        self._status_lbl = Label(
            text='', font_size='11sp',
            color=C_SUBTEXT,
            size_hint_y=None, height=22,
            halign='center', valign='middle',
        )
        self._status_lbl.bind(size=self._status_lbl.setter('text_size'))
        root.add_widget(self._status_lbl)

        # ── 按钮行 ───────────────────────────────────────────
        btn_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None, height=44, spacing=12,
        )

        self._cancel_btn = Button(
            text='暂不升级', font_size='13sp',
            background_normal='', background_color=C_BTN_NO,
            color=C_TEXT,
        )
        self._cancel_btn.bind(on_press=self._on_cancel)

        self._ok_btn = Button(
            text='立即升级', font_size='13sp',
            background_normal='', background_color=C_BTN_OK,
            color=C_TEXT,
        )
        self._ok_btn.bind(on_press=self._on_ok)

        btn_row.add_widget(self._cancel_btn)
        btn_row.add_widget(self._ok_btn)
        root.add_widget(btn_row)

        return root

    # ── 内部方法 ─────────────────────────────────────────────

    def _on_cancel(self, *_):
        self._cancelled = True
        self.dismiss()

    def _on_ok(self, *_):
        self._ok_btn.disabled    = True
        self._cancel_btn.disabled = True
        self._ok_btn.text        = '下载中...'
        self._progress.opacity   = 1
        self._status_lbl.text    = '正在准备下载...'

        threading.Thread(target=self._do_update, daemon=True).start()

    def _do_update(self):
        from updater import apply_update
        import sys, os

        platform = 'android' if (sys.platform == 'linux' and os.path.exists('/data/data')) else 'windows'
        assets   = self._info.get('assets', {})
        asset    = assets.get(platform)

        if not asset:
            Clock.schedule_once(lambda dt: self._set_error(f'平台 [{platform}] 无可用安装包'), 0)
            return

        url    = asset.get('url', '')
        sha256 = asset.get('sha256', '')

        def _progress(downloaded, total):
            if total > 0:
                pct = int(downloaded / total * 100)
                mb  = downloaded / 1_048_576
                Clock.schedule_once(lambda dt, p=pct, m=mb: self._set_progress(p, m), 0)

        try:
            apply_update(url, sha256, _progress)
            # apply_update 成功后进程已退出（Windows）或系统已接管（Android）
        except Exception as e:
            Clock.schedule_once(lambda dt, err=str(e): self._set_error(err), 0)

    def _set_progress(self, pct: int, mb: float):
        self._progress.value   = pct
        self._status_lbl.text  = f'已下载 {mb:.1f} MB  ({pct}%)'
        self._status_lbl.color = C_TEXT

    def _set_error(self, msg: str):
        self._status_lbl.text     = f'错误：{msg}'
        self._status_lbl.color    = C_RED
        self._ok_btn.disabled     = False
        self._cancel_btn.disabled = False
        self._ok_btn.text         = '重试'
        self._progress.opacity    = 0
