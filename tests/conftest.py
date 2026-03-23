"""
pytest 全局配置：mock Kivy 模块，使测试无需安装 Kivy/SDL2 即可运行。
必须在任何 import 之前执行，因此放在 conftest.py 最顶层。
"""
import sys
import types

# ---- mock kivy 顶层包 ----
_kivy = types.ModuleType("kivy")
sys.modules["kivy"] = _kivy

# kivy.clock
_clock_mod = types.ModuleType("kivy.clock")


class _FakeClock:
    @staticmethod
    def schedule_once(callback, delay=0):
        """测试中立即同步执行回调，消除异步延迟。"""
        callback(delay)


_clock_mod.Clock = _FakeClock()
sys.modules["kivy.clock"] = _clock_mod
_kivy.clock = _clock_mod

# kivy.logger
_logger_mod = types.ModuleType("kivy.logger")


class _FakeLogger:
    @staticmethod
    def error(*args, **kwargs):
        pass

    @staticmethod
    def warning(*args, **kwargs):
        pass

    @staticmethod
    def info(*args, **kwargs):
        pass


_logger_mod.Logger = _FakeLogger()
sys.modules["kivy.logger"] = _logger_mod
_kivy.logger = _logger_mod

# kivy.app
_app_mod = types.ModuleType("kivy.app")


class _FakeApp:
    pass


_app_mod.App = _FakeApp
sys.modules["kivy.app"] = _app_mod

# kivy.uix.*  常用控件
for _uix_name in [
    "kivy.uix",
    "kivy.uix.boxlayout",
    "kivy.uix.label",
    "kivy.uix.button",
    "kivy.uix.textinput",
    "kivy.uix.scrollview",
    "kivy.uix.gridlayout",
    "kivy.uix.widget",
    "kivy.uix.popup",
    "kivy.uix.floatlayout",
    "kivy.uix.spinner",
]:
    _mod = types.ModuleType(_uix_name)
    for _cls in ["BoxLayout", "Label", "Button", "TextInput",
                 "ScrollView", "GridLayout", "Widget", "Popup", "FloatLayout",
                 "Spinner", "SpinnerOption"]:
        setattr(_mod, _cls, type(_cls, (), {}))
    sys.modules[_uix_name] = _mod

# kivy.graphics
_graphics_mod = types.ModuleType("kivy.graphics")


class _FakeInstruction:
    def __init__(self, *args, **kwargs):
        pass

    def bind(self, **kwargs):
        pass


for _gfx_cls in ["Color", "Rectangle", "RoundedRectangle", "Line", "Ellipse"]:
    setattr(_graphics_mod, _gfx_cls, _FakeInstruction)
sys.modules["kivy.graphics"] = _graphics_mod
_kivy.graphics = _graphics_mod

# kivy.properties
_props_mod = types.ModuleType("kivy.properties")
for _prop in ["StringProperty", "BooleanProperty", "NumericProperty",
              "ListProperty", "ObjectProperty", "DictProperty"]:
    setattr(_props_mod, _prop, lambda *a, **kw: None)
sys.modules["kivy.properties"] = _props_mod
