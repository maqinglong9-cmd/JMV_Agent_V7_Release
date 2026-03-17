"""脑区状态仪表盘：8 个脑区卡片，激活时高亮（紧凑固定高度 88dp）"""
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle

REGIONS = [
    "额叶", "顶叶", "颞叶", "枕叶",
    "丘脑", "下丘脑", "小脑", "脑干"
]

C_IDLE        = (0.12, 0.15, 0.22, 1)
C_ACTIVE      = (0.15, 0.65, 0.40, 1)
C_TEXT_IDLE   = (0.55, 0.60, 0.68, 1)
C_TEXT_ACTIVE = (0.92, 1.00, 0.95, 1)


class RegionCard(Label):
    """单个脑区卡片（纯 Label，背景用 canvas）"""

    def __init__(self, region_name, **kwargs):
        from ui.responsive import dp
        super().__init__(
            text=region_name,
            font_size='13sp',
            bold=True,
            color=C_TEXT_IDLE,
            halign='center',
            valign='middle',
            size_hint=(1, 1),
            **kwargs
        )
        self.region_name = region_name
        self._active = False
        self.bind(size=self.setter('text_size'))
        self._draw_bg(C_IDLE)

    def _draw_bg(self, color):
        from ui.responsive import dp
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*color)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(6)])
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *_):
        self._rect.pos  = self.pos
        self._rect.size = self.size

    def set_active(self, active: bool):
        if self._active == active:
            return
        self._active = active
        if active:
            self._draw_bg(C_ACTIVE)
            self.color = C_TEXT_ACTIVE
        else:
            self._draw_bg(C_IDLE)
            self.color = C_TEXT_IDLE


class BrainDashboard(GridLayout):
    def __init__(self, **kwargs):
        from ui.responsive import dp, compact_brain_height
        super().__init__(
            cols=4,
            spacing=dp(2),
            padding=[dp(4), dp(2), dp(4), dp(2)],
            size_hint_y=None,
            height=compact_brain_height(),
            **kwargs
        )
        self.cards = {}
        for name in REGIONS:
            card = RegionCard(name)
            self.cards[name] = card
            self.add_widget(card)

    def activate_region(self, region_name: str):
        """根据日志文字精确或宽松匹配并高亮脑区"""
        for name, card in self.cards.items():
            if f'[{name}' in region_name or f'({name}' in region_name:
                card.set_active(True)
                return
        for name, card in self.cards.items():
            if name in region_name:
                card.set_active(True)
                return

    def reset_all(self):
        for card in self.cards.values():
            card.set_active(False)
