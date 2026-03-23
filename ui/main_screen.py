"""主屏幕：全固定高度布局 - LogViewer 填满剩余空间"""
import os
import threading

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.graphics import Color, Rectangle

from ui.brain_dashboard import BrainDashboard
from ui.log_viewer import LogViewer
from ui.input_panel import InputPanel
from adapter.agent_adapter import BrainAgentAdapter
from ui.responsive import (
    dp, font_small, font_large, font_btn, font_label,
    button_height, header_height, section_height, mode_row_height,
    padding_h, is_android
)

C_BG      = (0.06, 0.08, 0.12, 1)
C_HEADER  = (0.10, 0.13, 0.20, 1)
C_SECTION = (0.09, 0.12, 0.17, 1)
C_GREEN   = (0.20, 0.75, 0.45, 1)
C_YELLOW  = (0.85, 0.70, 0.20, 1)
C_TEXT    = (0.90, 0.92, 0.95, 1)
C_SUBTEXT = (0.55, 0.60, 0.70, 1)


def _bg(widget, color):
    with widget.canvas.before:
        Color(*color)
        rect = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(pos=lambda *_: setattr(rect, 'pos', widget.pos))
    widget.bind(size=lambda *_: setattr(rect, 'size', widget.size))


class SectionLabel(BoxLayout):
    """带左侧色条的紧凑区块标题（24dp）"""

    def __init__(self, text, **kwargs):
        super().__init__(
            orientation='horizontal',
            size_hint_y=None,
            height=section_height(),
            spacing=0,
            **kwargs
        )
        bar = BoxLayout(size_hint_x=None, width=dp(3))
        with bar.canvas.before:
            Color(*C_GREEN)
            r = Rectangle(pos=bar.pos, size=bar.size)
        bar.bind(pos=lambda *_: setattr(r, 'pos', bar.pos))
        bar.bind(size=lambda *_: setattr(r, 'size', bar.size))

        lbl = Label(
            text=f'  {text}',
            font_size=font_label(),
            color=C_SUBTEXT,
            halign='left', valign='middle',
        )
        lbl.bind(size=lbl.setter('text_size'))
        self.add_widget(bar)
        self.add_widget(lbl)
        _bg(self, C_SECTION)


class LLMStatusDot(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(
            orientation='horizontal',
            size_hint_x=None,
            width=dp(110),
            spacing=dp(4),
            **kwargs
        )
        self._dot = Label(
            text='●', font_size=font_small(),
            size_hint_x=None, width=dp(14),
            color=C_YELLOW,
        )
        self._txt = Label(
            text='算力: 未连接',
            font_size=font_small(),
            color=C_SUBTEXT,
            halign='left', valign='middle',
        )
        self._txt.bind(size=self._txt.setter('text_size'))
        self.add_widget(self._dot)
        self.add_widget(self._txt)

    def set_status(self, connected: bool, provider: str = ''):
        if connected:
            self._dot.color = C_GREEN
            self._txt.text = f'算力: {provider}'
        else:
            self._dot.color = C_YELLOW
            self._txt.text = '算力: 本地'


class HeaderBar(BoxLayout):
    def __init__(self, on_settings, on_check_update, **kwargs):
        super().__init__(
            orientation='horizontal',
            size_hint_y=None,
            height=header_height(),
            padding=[padding_h(), dp(4)],
            spacing=dp(6),
            **kwargs
        )
        _bg(self, C_HEADER)

        title = Label(
            text='JMV智伴',
            font_size=font_large(),
            bold=True, color=C_TEXT,
            size_hint_x=None, width=dp(80),
            halign='left', valign='middle',
        )
        title.bind(size=title.setter('text_size'))

        self.status_dot = LLMStatusDot()

        self.update_btn = Button(
            text='↑ 更新',
            font_size=font_small(),
            size_hint_x=None, width=dp(60),
            background_normal='',
            background_color=(0.12, 0.28, 0.20, 1),
            color=C_TEXT,
        )
        self.update_btn.bind(on_press=lambda _: on_check_update())

        self.settings_btn = Button(
            text='⚙ 设置',
            font_size=font_small(),
            size_hint_x=None, width=dp(60),
            background_normal='',
            background_color=(0.15, 0.20, 0.32, 1),
            color=C_TEXT,
        )
        self.settings_btn.bind(on_press=lambda _: on_settings())

        self.add_widget(title)
        self.add_widget(Label())  # spacer
        self.add_widget(self.status_dot)
        self.add_widget(self.update_btn)
        self.add_widget(self.settings_btn)


class MainScreen(BoxLayout):
    """主感知屏幕（全固定高度，LogViewer 填满剩余）"""

    def __init__(self, on_open_settings=None, **kwargs):
        super().__init__(orientation='vertical', spacing=0, **kwargs)
        _bg(self, C_BG)

        self._on_open_settings = on_open_settings
        self.adapter = BrainAgentAdapter()
        self.adapter.bus.subscribe('step',  self._on_step)
        self.adapter.bus.subscribe('done',  self._on_done)
        self.adapter.bus.subscribe('error', self._on_error)
        self._last_steps: list = []

        # ── 顶部标题栏 52dp ──────────────────────────────
        self.header = HeaderBar(
            on_settings=self._open_settings,
            on_check_update=self._check_update,
        )
        self.add_widget(self.header)

        # ── Agent 模式行 40dp ─────────────────────────────
        self.add_widget(self._build_mode_row())

        # ── 脑区区块标题 24dp ─────────────────────────────
        self.add_widget(SectionLabel('任务分析'))

        # ── 脑区仪表盘 88dp ───────────────────────────────
        self.dashboard = BrainDashboard()
        self.add_widget(self.dashboard)

        # ── 进度条 4dp ───────────────────────────────────
        self.progress = ProgressBar(
            max=100, value=0,
            size_hint_y=None, height=dp(4),
        )
        self.add_widget(self.progress)

        # ── 日志区块标题 24dp ─────────────────────────────
        self.add_widget(SectionLabel('执行日志'))

        # ── 日志区（填满剩余空间）────────────────────────
        self.log_viewer = LogViewer(size_hint_y=1)
        self.add_widget(self.log_viewer)

        # ── 输入面板（自管理高度）────────────────────────
        self.input_panel = InputPanel(
            on_run_callback=self._on_run,
            llm_getter=lambda: self.adapter._llm,
            on_evolve=self._trigger_evolution,
            on_cleanup=self._cleanup_workspace,
        )
        self.add_widget(self.input_panel)

        self._refresh_llm_status()

    # ── Agent 模式选择 ───────────────────────────────────

    def _build_mode_row(self) -> BoxLayout:
        from adapter.agent_router import AGENT_MODES
        row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None, height=mode_row_height(),
            spacing=dp(3), padding=[padding_h(), dp(4)],
        )
        _bg(row, (0.08, 0.10, 0.16, 1))

        self._mode_btns = {}
        for mode_key, mode_name in AGENT_MODES.items():
            btn = Button(
                text=mode_name,
                font_size=font_small(),
                background_normal='',
                background_color=(0.18, 0.24, 0.36, 1),
                color=C_SUBTEXT,
                size_hint_x=1,
            )
            btn.bind(on_press=lambda b, k=mode_key: self._switch_mode(k))
            self._mode_btns[mode_key] = btn
            row.add_widget(btn)

        self._highlight_mode('basic')
        return row

    def _switch_mode(self, mode_key: str) -> None:
        self.adapter.set_agent_mode(mode_key)
        self._highlight_mode(mode_key)
        from adapter.agent_router import AGENT_MODES
        self.log_viewer.append(f'[系统] Agent → {AGENT_MODES[mode_key]}')

    def _highlight_mode(self, active_key: str) -> None:
        for key, btn in self._mode_btns.items():
            if key == active_key:
                btn.background_color = (0.15, 0.48, 0.28, 1)
                btn.color = C_TEXT
            else:
                btn.background_color = (0.18, 0.24, 0.36, 1)
                btn.color = C_SUBTEXT

    # ── LLM 状态 ─────────────────────────────────────────

    def _refresh_llm_status(self):
        self.header.status_dot.set_status(
            self.adapter.llm_connected, self.adapter.llm_provider
        )

    # ── 设置 ─────────────────────────────────────────────

    def _open_settings(self):
        if callable(self._on_open_settings):
            self._on_open_settings()
        else:
            self.log_viewer.append('[系统] 请点击底部"⚙ 设置"标签配置。')

    # ── 感知流程 ─────────────────────────────────────────

    def _on_run(self, visual, audio, tactile):
        self.log_viewer.clear()
        self.dashboard.reset_all()
        self.progress.value = 0
        self._last_steps = []
        mode = self.adapter.llm_provider if self.adapter.llm_connected else '本地模拟'
        self.log_viewer.append(f'[系统] 启动感知（{mode}）')
        self.log_viewer.append(f'  视觉 → {visual[:60]}')
        if audio and audio != '无听觉输入':
            self.log_viewer.append(f'  听觉 → {audio[:60]}')
        self.adapter.run_async(visual, audio, tactile)

    def _on_step(self, payload):
        if not isinstance(payload, dict):
            return
        text  = payload.get('text', '')
        index = payload.get('index', 0)
        total = max(payload.get('total', 9), 1)
        self.log_viewer.append(f'• {text}')
        self.dashboard.activate_region(text)
        self.progress.value = int((index + 1) / total * 100)
        self._last_steps.append(text)

    def _on_done(self, _):
        self.progress.value = 100
        self.dashboard.reset_all()
        self.log_viewer.append('✓ 任务执行完成，已写入长期记忆。')
        self.input_panel.enable()
        if self.input_panel.voice_enabled and self._last_steps:
            from agent.voice_output import speak_async
            speak_async(self._last_steps[-1])

    def _on_error(self, err: str):
        self.progress.value = 0
        self.log_viewer.append(f'✗ 错误：{err}')
        self.input_panel.enable()

    # ── AI 自我进化 ──────────────────────────────────────

    def _trigger_evolution(self):
        evolution = getattr(self.adapter, 'evolution', None)
        if not evolution:
            self.log_viewer.append('[进化] 引擎未初始化。')
            return

        def _run():
            from kivy.clock import Clock

            def _log(msg):
                Clock.schedule_once(
                    lambda dt: self.log_viewer.append(f'[进化] {msg}'), 0
                )

            stats = evolution.get_evolution_stats()
            Clock.schedule_once(lambda dt: self.log_viewer.append(
                f'[进化] v{stats["current_version"]} | '
                f'交互:{stats["total_interactions"]} | '
                f'规则:{stats["learned_rules"]}'
            ), 0)

            llm = getattr(self.adapter, '_llm', None)
            patch = evolution.analyze_failures(llm_client=llm, progress_cb=_log)

            if patch.get('new_rules') or patch.get('patch_version'):
                _log('发现改进项，正在应用...')
                applied = evolution.apply_patch(patch, progress_cb=_log)
                _log('✓ 进化完成。' if applied else '无有效改进。')
            else:
                _log('分析完成，暂无需要改进的项目。')

        threading.Thread(target=_run, daemon=True).start()

    # ── 版本更新 ─────────────────────────────────────────

    def _check_update(self):
        self.header.update_btn.disabled = True
        self.header.update_btn.text = '检查中...'
        self.log_viewer.append('[升级] 正在检查新版本...')

        def _run():
            from updater.version_checker import check_for_update
            from kivy.clock import Clock
            info = check_for_update()
            Clock.schedule_once(lambda dt: self._on_update_result(info), 0)

        threading.Thread(target=_run, daemon=True).start()

    def _on_update_result(self, info: dict):
        self.header.update_btn.disabled = False
        self.header.update_btn.text = '↑ 更新'

        if info.get('error'):
            self.log_viewer.append(f'[升级] 检查失败：{info["error"]}')
            return
        if not info.get('has_update'):
            self.log_viewer.append(f'[升级] 当前已是最新版本 {info.get("current", "")}')
            return

        self.log_viewer.append(
            f'[升级] 发现新版本 {info["latest"]}（当前 {info["current"]}）'
        )
        from ui.update_dialog import UpdateDialog
        UpdateDialog(info, on_confirm=None).open()

    # ── 工作区清理 ───────────────────────────────────────

    def _cleanup_workspace(self):
        self.log_viewer.append('[清理] 开始工作区清理...')

        def _run():
            from kivy.clock import Clock
            try:
                workspace = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'jmv_workspace'
                )
                if not os.path.isdir(workspace):
                    Clock.schedule_once(lambda dt:
                        self.log_viewer.append('[清理] 工作区目录不存在。'), 0)
                    return

                files = sorted(
                    [os.path.join(workspace, f) for f in os.listdir(workspace)
                     if os.path.isfile(os.path.join(workspace, f))],
                    key=os.path.getmtime
                )
                KEEP_ALWAYS = {'metacognition_rules.json', 'font_cache.txt', 'dynamic_tools.py'}
                to_delete = [
                    f for f in files[:-10]
                    if os.path.basename(f) not in KEEP_ALWAYS
                ]
                deleted, freed = 0, 0
                for f in to_delete:
                    try:
                        freed += os.path.getsize(f)
                        os.remove(f)
                        deleted += 1
                    except Exception:
                        pass

                msg = f'[清理] 删除 {deleted} 个旧文件，释放 {freed // 1024} KB'
                Clock.schedule_once(lambda dt: self.log_viewer.append(msg), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt:
                    self.log_viewer.append(f'[清理] 失败: {e}'), 0)

        threading.Thread(target=_run, daemon=True).start()
