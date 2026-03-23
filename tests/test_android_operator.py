"""
AndroidOperator 单元测试
========================
用 unittest.mock.patch 模拟所有 subprocess.run 调用，
无需真实 Android 设备即可覆盖全部路径。
"""
import os
import sys
import unittest
from unittest.mock import MagicMock, patch, call

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.android_operator import (
    AndroidOperator, _is_android, _KEYCODE_MAP,
    KEY_HOME, KEY_BACK, KEY_ENTER, KEY_POWER,
    KEY_VOLUME_UP, KEY_VOLUME_DOWN, KEY_MENU,
    KEY_DELETE, KEY_SPACE, KEY_DPAD_UP, KEY_DPAD_DOWN,
)


def _make_proc(returncode=0, stdout="", stderr=""):
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = stderr
    return m


class TestIsAndroid:
    def test_returns_bool(self):
        result = _is_android()
        assert isinstance(result, bool)

    def test_non_android_when_no_build_prop(self):
        with patch("os.path.exists", return_value=False):
            with patch("builtins.open", side_effect=OSError):
                assert _is_android() is False

    def test_android_when_build_prop_exists(self):
        with patch("os.path.exists", return_value=True):
            assert _is_android() is True


class TestKeyConstants:
    def test_key_home(self):
        assert KEY_HOME == 3

    def test_key_back(self):
        assert KEY_BACK == 4

    def test_key_enter(self):
        assert KEY_ENTER == 66

    def test_key_power(self):
        assert KEY_POWER == 26

    def test_key_volume_up(self):
        assert KEY_VOLUME_UP == 24

    def test_key_volume_down(self):
        assert KEY_VOLUME_DOWN == 25

    def test_key_menu(self):
        assert KEY_MENU == 82

    def test_key_delete(self):
        assert KEY_DELETE == 67

    def test_key_space(self):
        assert KEY_SPACE == 62

    def test_key_dpad_up(self):
        assert KEY_DPAD_UP == 19

    def test_key_dpad_down(self):
        assert KEY_DPAD_DOWN == 20

    def test_keycode_map_has_home(self):
        assert _KEYCODE_MAP["HOME"] == KEY_HOME

    def test_keycode_map_has_back(self):
        assert _KEYCODE_MAP["BACK"] == KEY_BACK

    def test_keycode_map_has_enter(self):
        assert _KEYCODE_MAP["ENTER"] == KEY_ENTER


class TestAndroidOperatorInit:
    def test_default_init(self):
        op = AndroidOperator()
        assert isinstance(op._on_android, bool)
        assert op._adb_device == ''

    def test_custom_device(self):
        op = AndroidOperator(adb_device='192.168.1.100:5555')
        assert op._adb_device == '192.168.1.100:5555'


class TestShellMethod:
    """测试 _shell() 内部方法。"""

    def _op(self):
        op = AndroidOperator()
        op._on_android = False  # 非 Android 模式，使用 adb
        return op

    def test_success_returns_true_and_output(self):
        op = self._op()
        with patch("subprocess.run", return_value=_make_proc(0, "output text")) as m:
            ok, out = op._shell("echo hello")
        assert ok is True
        assert "output text" in out

    def test_failure_returns_false(self):
        op = self._op()
        with patch("subprocess.run", return_value=_make_proc(1, "", "error msg")):
            ok, out = op._shell("bad cmd")
        assert ok is False

    def test_timeout_returns_false(self):
        import subprocess
        op = self._op()
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 10)):
            ok, out = op._shell("sleep 100")
        assert ok is False
        assert "超时" in out

    def test_file_not_found_returns_false(self):
        op = self._op()
        with patch("subprocess.run", side_effect=FileNotFoundError("adb not found")):
            ok, out = op._shell("any cmd")
        assert ok is False
        assert "命令未找到" in out

    def test_android_mode_uses_sh(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(0, "ok")) as m:
            op._shell("ls")
        args = m.call_args[0][0]
        assert args[0] == 'sh'
        assert args[1] == '-c'

    def test_non_android_uses_adb(self):
        op = AndroidOperator()
        op._on_android = False
        with patch("subprocess.run", return_value=_make_proc(0, "ok")) as m:
            op._shell("ls")
        args = m.call_args[0][0]
        assert 'adb' in args[0]
        assert 'shell' in args

    def test_custom_device_in_adb_args(self):
        op = AndroidOperator(adb_device='emulator-5554')
        op._on_android = False
        with patch("subprocess.run", return_value=_make_proc(0, "ok")) as m:
            op._shell("ls")
        args = m.call_args[0][0]
        assert '-s' in args
        assert 'emulator-5554' in args


class TestLaunchApp:
    def _op(self):
        op = AndroidOperator()
        op._on_android = True
        return op

    def test_launch_with_activity(self):
        op = self._op()
        with patch("subprocess.run", return_value=_make_proc(0, "Starting")) as m:
            ok, out = op.launch_app("com.example.app", ".MainActivity")
        assert ok is True
        cmd = m.call_args[0][0][2]
        assert "am start -n com.example.app/.MainActivity" == cmd

    def test_launch_without_activity_uses_monkey(self):
        op = self._op()
        with patch("subprocess.run", return_value=_make_proc(0, "Events injected")) as m:
            ok, out = op.launch_app("com.example.app")
        assert ok is True
        cmd = m.call_args[0][0][2]
        assert "monkey" in cmd
        assert "com.example.app" in cmd

    def test_launch_failure(self):
        op = self._op()
        with patch("subprocess.run", return_value=_make_proc(1, "", "Error")):
            ok, out = op.launch_app("com.bad.app")
        assert ok is False


class TestStopApp:
    def test_stop_success(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(0, "")) as m:
            ok, out = op.stop_app("com.example.app")
        assert ok is True
        cmd = m.call_args[0][0][2]
        assert "am force-stop com.example.app" == cmd

    def test_stop_failure(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(1, "", "not found")):
            ok, out = op.stop_app("com.bad.app")
        assert ok is False


class TestClearAppData:
    def test_clear_success(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(0, "Success")) as m:
            ok, out = op.clear_app_data("com.example.app")
        assert ok is True
        cmd = m.call_args[0][0][2]
        assert "pm clear com.example.app" == cmd


class TestInstallApk:
    def test_install_success(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(0, "Success")) as m:
            ok, out = op.install_apk("/sdcard/app.apk")
        assert ok is True
        cmd = m.call_args[0][0][2]
        assert "pm install -r /sdcard/app.apk" == cmd

    def test_install_failure(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(1, "", "INSTALL_FAILED")):
            ok, out = op.install_apk("/sdcard/bad.apk")
        assert ok is False


class TestUninstallApp:
    def test_uninstall_success(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(0, "Success")) as m:
            ok, out = op.uninstall_app("com.example.app")
        assert ok is True
        cmd = m.call_args[0][0][2]
        assert "pm uninstall com.example.app" == cmd


class TestListPackages:
    def _op(self):
        op = AndroidOperator()
        op._on_android = True
        return op

    def test_list_all(self):
        output = "package:com.example.one\npackage:com.example.two\npackage:com.other.app"
        op = self._op()
        with patch("subprocess.run", return_value=_make_proc(0, output)):
            pkgs = op.list_packages()
        assert "com.example.one" in pkgs
        assert "com.example.two" in pkgs
        assert "com.other.app" in pkgs

    def test_list_with_filter(self):
        output = "package:com.example.one\npackage:com.example.two\npackage:com.other.app"
        op = self._op()
        with patch("subprocess.run", return_value=_make_proc(0, output)):
            pkgs = op.list_packages("com.example")
        assert "com.example.one" in pkgs
        assert "com.example.two" in pkgs
        assert "com.other.app" not in pkgs

    def test_list_failure_returns_empty(self):
        op = self._op()
        with patch("subprocess.run", return_value=_make_proc(1, "", "error")):
            pkgs = op.list_packages()
        assert pkgs == []

    def test_list_empty_output(self):
        op = self._op()
        with patch("subprocess.run", return_value=_make_proc(0, "")):
            pkgs = op.list_packages()
        assert pkgs == []


class TestGetAppInfo:
    def test_extracts_version(self):
        op = AndroidOperator()
        op._on_android = True
        dumpsys_output = "versionName=2.3.1\nversionCode=231\ncodePath=/data/app/com.ex.app"
        with patch("subprocess.run", return_value=_make_proc(0, dumpsys_output)):
            info = op.get_app_info("com.ex.app")
        assert info["version"] == "2.3.1"
        assert info["version_code"] == "231"
        assert info["install_path"] == "/data/app/com.ex.app"

    def test_failure_returns_error_dict(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(1, "", "not found")):
            info = op.get_app_info("com.bad.app")
        assert "error" in info


class TestTap:
    def test_tap_sends_correct_command(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(0, "")) as m:
            ok, _ = op.tap(100, 200)
        assert ok is True
        cmd = m.call_args[0][0][2]
        assert cmd == "input tap 100 200"

    def test_tap_failure(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(1, "", "error")):
            ok, _ = op.tap(0, 0)
        assert ok is False


class TestSwipe:
    def test_swipe_command(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(0, "")) as m:
            ok, _ = op.swipe(0, 0, 500, 500, 300)
        cmd = m.call_args[0][0][2]
        assert cmd == "input swipe 0 0 500 500 300"

    def test_swipe_default_duration(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(0, "")) as m:
            op.swipe(10, 20, 30, 40)
        cmd = m.call_args[0][0][2]
        assert "300" in cmd  # 默认 300ms


class TestTypeText:
    def test_type_simple_text(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(0, "")) as m:
            ok, _ = op.type_text("hello")
        assert ok is True
        cmd = m.call_args[0][0][2]
        assert "input text" in cmd

    def test_type_chinese_text(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(0, "")) as m:
            ok, _ = op.type_text("你好")
        assert ok is True
        cmd = m.call_args[0][0][2]
        assert "input text" in cmd

    def test_type_special_chars(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(0, "")) as m:
            ok, _ = op.type_text("hello world")
        assert ok is True


class TestPressKey:
    def test_press_key_int(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(0, "")) as m:
            ok, _ = op.press_key(KEY_HOME)
        cmd = m.call_args[0][0][2]
        assert cmd == f"input keyevent {KEY_HOME}"

    def test_press_key_string(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(0, "")) as m:
            ok, _ = op.press_key("HOME")
        cmd = m.call_args[0][0][2]
        assert str(KEY_HOME) in cmd

    def test_press_key_string_case_insensitive(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(0, "")) as m:
            ok, _ = op.press_key("back")
        cmd = m.call_args[0][0][2]
        assert str(KEY_BACK) in cmd


class TestLongPress:
    def test_long_press_command(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(0, "")) as m:
            ok, _ = op.long_press(100, 200, 1000)
        cmd = m.call_args[0][0][2]
        # long_press 用 swipe x y x y dur 实现
        assert cmd == "input swipe 100 200 100 200 1000"


class TestScreenshot:
    def test_screenshot_default_path(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(0, "")) as m:
            ok, path = op.screenshot()
        assert ok is True
        assert path == '/sdcard/jmv_screenshot.png'

    def test_screenshot_custom_path(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(0, "")) as m:
            ok, path = op.screenshot('/sdcard/myshot.png')
        assert ok is True
        assert path == '/sdcard/myshot.png'

    def test_screenshot_failure(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(1, "", "error")):
            ok, out = op.screenshot()
        assert ok is False


class TestGetUiHierarchy:
    def test_returns_xml(self):
        op = AndroidOperator()
        op._on_android = True
        xml = '<?xml version="1.0"?><hierarchy><node /></hierarchy>'
        with patch("subprocess.run", return_value=_make_proc(0, xml)):
            ok, out = op.get_ui_hierarchy()
        assert ok is True
        assert "hierarchy" in out

    def test_failure(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(1, "", "uiautomator not found")):
            ok, out = op.get_ui_hierarchy()
        assert ok is False


class TestGetScreenSize:
    def test_parses_size(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(0, "Physical size: 1080x1920")):
            w, h = op.get_screen_size()
        assert w == 1080
        assert h == 1920

    def test_failure_returns_zero(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(1, "", "error")):
            w, h = op.get_screen_size()
        assert w == 0
        assert h == 0


class TestGetSystemInfo:
    def test_contains_expected_keys(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(0, "Pixel 6")) as m:
            info = op.get_system_info()
        assert isinstance(info, dict)

    def test_extracts_model(self):
        op = AndroidOperator()
        op._on_android = True
        call_count = [0]

        def side_effect(args, **kwargs):
            call_count[0] += 1
            cmd = args[-1] if isinstance(args, list) else ""
            if "ro.product.model" in cmd:
                return _make_proc(0, "Pixel 6")
            elif "ro.build.version.release" in cmd:
                return _make_proc(0, "13")
            elif "ro.product.manufacturer" in cmd:
                return _make_proc(0, "Google")
            elif "meminfo" in cmd:
                return _make_proc(0, "MemTotal: 8GB")
            elif "dumpsys battery" in cmd:
                return _make_proc(0, "  level: 85")
            return _make_proc(0, "")

        with patch("subprocess.run", side_effect=side_effect):
            info = op.get_system_info()
        assert info.get("model") == "Pixel 6"
        assert info.get("android_version") == "13"

    def test_extracts_battery_level(self):
        op = AndroidOperator()
        op._on_android = True

        def side_effect(args, **kwargs):
            cmd = args[-1] if isinstance(args, list) else ""
            if "battery" in cmd:
                return _make_proc(0, "  level: 72")
            return _make_proc(0, "")

        with patch("subprocess.run", side_effect=side_effect):
            info = op.get_system_info()
        assert info.get("battery_level") == 72


class TestSetSetting:
    def test_set_global_setting(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(0, "")) as m:
            ok, _ = op.set_setting("global", "airplane_mode_on", "1")
        cmd = m.call_args[0][0][2]
        assert cmd == "settings put global airplane_mode_on 1"

    def test_set_system_setting(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(0, "")) as m:
            op.set_setting("system", "screen_brightness", "128")
        cmd = m.call_args[0][0][2]
        assert "settings put system" in cmd


class TestGetSetting:
    def test_get_returns_value(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(0, "1")):
            val = op.get_setting("global", "airplane_mode_on")
        assert val == "1"

    def test_get_failure_returns_empty(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(1, "", "error")):
            val = op.get_setting("global", "no_such_key")
        assert val == ""


class TestSendBroadcast:
    def test_basic_broadcast(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(0, "Broadcast completed")) as m:
            ok, _ = op.send_broadcast("android.intent.action.TEST")
        assert ok is True
        cmd = m.call_args[0][0][2]
        assert "am broadcast -a android.intent.action.TEST" == cmd

    def test_broadcast_with_string_extra(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(0, "ok")) as m:
            op.send_broadcast("com.test.ACTION", {"key": "val"})
        cmd = m.call_args[0][0][2]
        assert "--es key" in cmd

    def test_broadcast_with_int_extra(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(0, "ok")) as m:
            op.send_broadcast("com.test.ACTION", {"count": 5})
        cmd = m.call_args[0][0][2]
        assert "--ei count 5" in cmd

    def test_broadcast_with_bool_extra(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(0, "ok")) as m:
            op.send_broadcast("com.test.ACTION", {"flag": True})
        cmd = m.call_args[0][0][2]
        assert "--ez flag true" in cmd


class TestStartService:
    def test_start_service_command(self):
        op = AndroidOperator()
        op._on_android = True
        with patch("subprocess.run", return_value=_make_proc(0, "")) as m:
            ok, _ = op.start_service("com.example", ".MyService")
        assert ok is True
        cmd = m.call_args[0][0][2]
        assert "am startservice -n com.example/.MyService" == cmd
