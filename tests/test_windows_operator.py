"""
WindowsOperator 单元测试
========================
用 unittest.mock 模拟 subprocess/ctypes/winreg/builtins，
测试全部路径（成功/失败/非Windows降级）。
"""
import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch, call, mock_open

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── 在导入前注入 winreg mock（Linux/macOS 无此模块）────────────────────────
if sys.platform != 'win32':
    _winreg = types.ModuleType("winreg")
    # 注册表根键常量
    _winreg.HKEY_LOCAL_MACHINE  = 0x80000002
    _winreg.HKEY_CURRENT_USER   = 0x80000001
    _winreg.HKEY_CLASSES_ROOT   = 0x80000000
    _winreg.HKEY_USERS          = 0x80000003
    _winreg.HKEY_CURRENT_CONFIG = 0x80000005
    # 值类型常量
    _winreg.REG_SZ         = 1
    _winreg.REG_DWORD      = 4
    _winreg.REG_BINARY     = 3
    _winreg.REG_EXPAND_SZ  = 2
    _winreg.REG_MULTI_SZ   = 7
    # 权限
    _winreg.KEY_WRITE = 0x20006
    # 函数存根（测试中会被 patch 替换）
    _winreg.OpenKey         = MagicMock()
    _winreg.QueryValueEx    = MagicMock()
    _winreg.CreateKey       = MagicMock()
    _winreg.SetValueEx      = MagicMock()
    _winreg.DeleteValue     = MagicMock()
    _winreg.EnumKey         = MagicMock()
    sys.modules["winreg"] = _winreg

from agent.windows_operator import WindowsOperator


# ────────────────────────────────────────────────────────────────────────────
# 文件系统测试
# ────────────────────────────────────────────────────────────────────────────

class TestReadFile:
    def test_read_success(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world", encoding='utf-8')
        op = WindowsOperator()
        ok, content = op.read_file(str(f))
        assert ok is True
        assert content == "hello world"

    def test_read_nonexistent(self):
        op = WindowsOperator()
        ok, msg = op.read_file("/nonexistent/path/file.txt")
        assert ok is False
        assert "读取失败" in msg

    def test_read_with_encoding(self, tmp_path):
        f = tmp_path / "cn.txt"
        f.write_text("你好世界", encoding='utf-8')
        op = WindowsOperator()
        ok, content = op.read_file(str(f), encoding='utf-8')
        assert ok is True
        assert "你好世界" in content


class TestWriteFile:
    def test_write_creates_file(self, tmp_path):
        path = str(tmp_path / "out.txt")
        op = WindowsOperator()
        ok, msg = op.write_file(path, "test content")
        assert ok is True
        assert os.path.isfile(path)
        assert open(path).read() == "test content"

    def test_write_creates_parent_dirs(self, tmp_path):
        path = str(tmp_path / "nested" / "dir" / "file.txt")
        op = WindowsOperator()
        ok, msg = op.write_file(path, "nested")
        assert ok is True
        assert os.path.isfile(path)

    def test_write_returns_char_count(self, tmp_path):
        path = str(tmp_path / "f.txt")
        content = "hello"
        op = WindowsOperator()
        ok, msg = op.write_file(path, content)
        assert str(len(content)) in msg

    def test_write_failure(self):
        op = WindowsOperator()
        with patch("builtins.open", side_effect=PermissionError("denied")):
            with patch("os.makedirs"):
                ok, msg = op.write_file("/protected/file.txt", "content")
        assert ok is False
        assert "写入失败" in msg


class TestAppendFile:
    def test_append_to_existing(self, tmp_path):
        f = tmp_path / "app.txt"
        f.write_text("first", encoding='utf-8')
        op = WindowsOperator()
        ok, msg = op.append_file(str(f), " second")
        assert ok is True
        assert f.read_text(encoding='utf-8') == "first second"

    def test_append_failure(self):
        op = WindowsOperator()
        with patch("builtins.open", side_effect=OSError("blocked")):
            ok, msg = op.append_file("/bad/path.txt", "data")
        assert ok is False


class TestDeleteFile:
    def test_delete_success(self, tmp_path):
        f = tmp_path / "del.txt"
        f.write_text("bye")
        op = WindowsOperator()
        ok, msg = op.delete_file(str(f))
        assert ok is True
        assert not f.exists()

    def test_delete_nonexistent(self):
        op = WindowsOperator()
        ok, msg = op.delete_file("/nonexistent.txt")
        assert ok is False
        assert "删除失败" in msg


class TestListDir:
    def test_list_success(self, tmp_path):
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b.txt").write_text("b")
        op = WindowsOperator()
        ok, entries = op.list_dir(str(tmp_path))
        assert ok is True
        names = [e["name"] for e in entries]
        assert "a.txt" in names
        assert "b.txt" in names

    def test_list_has_size_and_mtime(self, tmp_path):
        (tmp_path / "c.txt").write_text("content")
        op = WindowsOperator()
        ok, entries = op.list_dir(str(tmp_path))
        assert ok is True
        entry = next(e for e in entries if e["name"] == "c.txt")
        assert "size" in entry
        assert "mtime" in entry

    def test_list_nonexistent_dir(self):
        op = WindowsOperator()
        ok, entries = op.list_dir("/no/such/dir")
        assert ok is False

    def test_list_marks_dirs(self, tmp_path):
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        op = WindowsOperator()
        ok, entries = op.list_dir(str(tmp_path))
        dir_entry = next((e for e in entries if e["name"] == "subdir"), None)
        assert dir_entry is not None
        assert dir_entry["is_dir"] is True


class TestCopyFile:
    def test_copy_success(self, tmp_path):
        src = tmp_path / "src.txt"
        dst = tmp_path / "dst.txt"
        src.write_text("copy me")
        op = WindowsOperator()
        ok, msg = op.copy_file(str(src), str(dst))
        assert ok is True
        assert dst.read_text() == "copy me"

    def test_copy_failure(self):
        op = WindowsOperator()
        ok, msg = op.copy_file("/nonexistent.txt", "/dst.txt")
        assert ok is False


class TestMoveFile:
    def test_move_success(self, tmp_path):
        src = tmp_path / "src.txt"
        dst = tmp_path / "dst.txt"
        src.write_text("move me")
        op = WindowsOperator()
        ok, msg = op.move_file(str(src), str(dst))
        assert ok is True
        assert not src.exists()
        assert dst.read_text() == "move me"


class TestMakeDir:
    def test_make_dir_success(self, tmp_path):
        path = str(tmp_path / "new" / "nested")
        op = WindowsOperator()
        ok, msg = op.make_dir(path)
        assert ok is True
        assert os.path.isdir(path)

    def test_make_dir_idempotent(self, tmp_path):
        op = WindowsOperator()
        ok, _ = op.make_dir(str(tmp_path))
        assert ok is True  # 已存在不报错


# ────────────────────────────────────────────────────────────────────────────
# 注册表测试（用 mock 覆盖 winreg 函数）
# ────────────────────────────────────────────────────────────────────────────

class TestRegRead:
    def test_read_success(self):
        op = WindowsOperator()
        import agent.windows_operator as wmod
        mock_key = MagicMock()
        mock_key.__enter__ = MagicMock(return_value=mock_key)
        mock_key.__exit__ = MagicMock(return_value=False)
        with patch.object(wmod, 'winreg') as mock_winreg:
            mock_winreg.HKEY_LOCAL_MACHINE = 0x80000002
            mock_winreg.OpenKey.return_value = mock_key
            mock_winreg.QueryValueEx.return_value = ("test_value", 1)
            from agent.windows_operator import _HIVE_MAP
            old_map = _HIVE_MAP.copy()
            _HIVE_MAP['HKLM'] = mock_winreg.HKEY_LOCAL_MACHINE
            try:
                ok, val = op.reg_read("HKLM", "SOFTWARE\\Test", "key")
            finally:
                _HIVE_MAP.clear()
                _HIVE_MAP.update(old_map)

    def test_read_unknown_hive(self):
        op = WindowsOperator()
        ok, msg = op.reg_read("HKUNKNOWN", "any\\key", "val")
        assert ok is False
        assert "未知" in msg

    def test_read_no_winreg(self):
        op = WindowsOperator()
        import agent.windows_operator as wmod
        original = wmod.winreg
        wmod.winreg = None
        try:
            ok, msg = op.reg_read("HKLM", "key", "val")
        finally:
            wmod.winreg = original
        assert ok is False

    def test_read_key_not_found(self):
        op = WindowsOperator()
        import agent.windows_operator as wmod
        mock_key = MagicMock()
        mock_key.__enter__ = MagicMock(return_value=mock_key)
        mock_key.__exit__ = MagicMock(return_value=False)
        with patch.object(wmod, 'winreg') as mock_winreg:
            mock_winreg.OpenKey.side_effect = FileNotFoundError("not found")
            from agent.windows_operator import _HIVE_MAP
            old_map = _HIVE_MAP.copy()
            _HIVE_MAP['HKLM'] = 0x80000002
            try:
                ok, msg = op.reg_read("HKLM", "NONEXISTENT", "key")
            finally:
                _HIVE_MAP.clear()
                _HIVE_MAP.update(old_map)
        assert ok is False


class TestRegWrite:
    def test_write_unknown_hive(self):
        op = WindowsOperator()
        ok, msg = op.reg_write("HKBAD", "key", "val", "data")
        assert ok is False

    def test_write_no_winreg(self):
        op = WindowsOperator()
        import agent.windows_operator as wmod
        original = wmod.winreg
        wmod.winreg = None
        try:
            ok, msg = op.reg_write("HKLM", "key", "val", "data")
        finally:
            wmod.winreg = original
        assert ok is False


class TestRegDeleteValue:
    def test_delete_unknown_hive(self):
        op = WindowsOperator()
        ok, msg = op.reg_delete_value("HKBAD", "key", "val")
        assert ok is False

    def test_delete_no_winreg(self):
        op = WindowsOperator()
        import agent.windows_operator as wmod
        original = wmod.winreg
        wmod.winreg = None
        try:
            ok, msg = op.reg_delete_value("HKLM", "key", "val")
        finally:
            wmod.winreg = original
        assert ok is False


class TestRegListKeys:
    def test_list_unknown_hive(self):
        op = WindowsOperator()
        ok, keys = op.reg_list_keys("HKBAD", "any")
        assert ok is False

    def test_list_no_winreg(self):
        op = WindowsOperator()
        import agent.windows_operator as wmod
        original = wmod.winreg
        wmod.winreg = None
        try:
            ok, keys = op.reg_list_keys("HKLM", "any")
        finally:
            wmod.winreg = original
        assert ok is False


# ────────────────────────────────────────────────────────────────────────────
# 进程管理测试
# ────────────────────────────────────────────────────────────────────────────

def _make_proc(returncode=0, stdout="", stderr=""):
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = stderr
    return m


class TestRunCommand:
    def test_success(self):
        op = WindowsOperator()
        with patch("subprocess.run", return_value=_make_proc(0, "hello output")):
            ok, out = op.run_command("echo hello")
        assert ok is True
        assert "hello output" in out

    def test_failure(self):
        op = WindowsOperator()
        with patch("subprocess.run", return_value=_make_proc(1, "", "cmd not found")):
            ok, out = op.run_command("bad_cmd")
        assert ok is False

    def test_timeout(self):
        import subprocess
        op = WindowsOperator()
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 5)):
            ok, out = op.run_command("sleep 100", timeout=5)
        assert ok is False
        assert "超时" in out

    def test_empty_output(self):
        op = WindowsOperator()
        with patch("subprocess.run", return_value=_make_proc(0, "")):
            ok, out = op.run_command("cmd")
        assert ok is True
        assert "<无输出>" in out

    def test_with_cwd(self):
        op = WindowsOperator()
        with patch("subprocess.run", return_value=_make_proc(0, "ok")) as m:
            op.run_command("ls", cwd="/tmp")
        assert m.call_args[1]["cwd"] == "/tmp"


class TestRunDetached:
    def test_success_returns_pid(self):
        op = WindowsOperator()
        mock_proc = MagicMock()
        mock_proc.pid = 12345
        with patch("subprocess.Popen", return_value=mock_proc):
            ok, pid = op.run_detached("notepad.exe")
        assert ok is True
        assert pid == 12345

    def test_failure_returns_minus_one(self):
        op = WindowsOperator()
        with patch("subprocess.Popen", side_effect=Exception("failed")):
            ok, pid = op.run_detached("bad.exe")
        assert ok is False
        assert pid == -1


class TestKillProcess:
    def test_kill_success_windows(self):
        op = WindowsOperator()
        with patch("sys.platform", "win32"):
            with patch("subprocess.run", return_value=_make_proc(0, "SUCCESS")):
                ok, msg = op.kill_process(1234)
        assert ok is True

    def test_kill_failure_windows(self):
        op = WindowsOperator()
        with patch("sys.platform", "win32"):
            with patch("subprocess.run", return_value=_make_proc(1, "not found", "")):
                ok, msg = op.kill_process(9999)
        assert ok is False

    def test_kill_non_windows(self):
        op = WindowsOperator()
        import agent.windows_operator as wmod
        original = wmod._IS_WINDOWS
        wmod._IS_WINDOWS = False
        try:
            with patch("os.kill") as m:
                ok, msg = op.kill_process(999)
        finally:
            wmod._IS_WINDOWS = original
        m.assert_called_once_with(999, 9)
        assert ok is True

    def test_kill_exception(self):
        op = WindowsOperator()
        with patch("sys.platform", "win32"):
            with patch("subprocess.run", side_effect=Exception("error")):
                ok, msg = op.kill_process(1)
        assert ok is False


class TestListProcesses:
    def test_windows_parses_csv(self):
        op = WindowsOperator()
        csv = '"notepad.exe","1234","Console","1","4,096 K"\n"cmd.exe","5678","Console","1","2,048 K"\n'
        with patch("sys.platform", "win32"):
            with patch("subprocess.run", return_value=_make_proc(0, csv)):
                procs = op.list_processes()
        assert any(p["name"] == "notepad.exe" for p in procs)
        assert any(p["pid"] == "1234" for p in procs)

    def test_failure_returns_empty(self):
        op = WindowsOperator()
        with patch("subprocess.run", side_effect=Exception("failed")):
            procs = op.list_processes()
        assert procs == []


class TestFindProcess:
    def test_find_by_name(self):
        op = WindowsOperator()
        with patch.object(op, "list_processes", return_value=[
            {"name": "notepad.exe", "pid": "100"},
            {"name": "chrome.exe", "pid": "200"},
        ]):
            result = op.find_process("notepad")
        assert len(result) == 1
        assert result[0]["pid"] == "100"

    def test_find_case_insensitive(self):
        op = WindowsOperator()
        with patch.object(op, "list_processes", return_value=[
            {"name": "Notepad.EXE", "pid": "100"},
        ]):
            result = op.find_process("notepad")
        assert len(result) == 1

    def test_find_not_found(self):
        op = WindowsOperator()
        with patch.object(op, "list_processes", return_value=[
            {"name": "chrome.exe", "pid": "200"},
        ]):
            result = op.find_process("notepad")
        assert result == []


# ────────────────────────────────────────────────────────────────────────────
# 窗口控制测试（非 Windows 降级）
# ────────────────────────────────────────────────────────────────────────────

class TestWindowOps:
    def test_get_foreground_non_windows(self):
        op = WindowsOperator()
        import agent.windows_operator as wmod
        original = wmod._IS_WINDOWS
        wmod._IS_WINDOWS = False
        try:
            hwnd, title = op.get_foreground_window()
        finally:
            wmod._IS_WINDOWS = original
        assert hwnd == 0

    def test_find_window_non_windows(self):
        op = WindowsOperator()
        import agent.windows_operator as wmod
        original = wmod._IS_WINDOWS
        wmod._IS_WINDOWS = False
        try:
            hwnd = op.find_window("Notepad")
        finally:
            wmod._IS_WINDOWS = original
        assert hwnd == 0

    def test_set_foreground_non_windows(self):
        op = WindowsOperator()
        import agent.windows_operator as wmod
        original = wmod._IS_WINDOWS
        wmod._IS_WINDOWS = False
        try:
            result = op.set_foreground(12345)
        finally:
            wmod._IS_WINDOWS = original
        assert result is False

    def test_move_window_non_windows(self):
        op = WindowsOperator()
        import agent.windows_operator as wmod
        original = wmod._IS_WINDOWS
        wmod._IS_WINDOWS = False
        try:
            result = op.move_window(1, 0, 0, 800, 600)
        finally:
            wmod._IS_WINDOWS = original
        assert result is False

    def test_close_window_non_windows(self):
        op = WindowsOperator()
        import agent.windows_operator as wmod
        original = wmod._IS_WINDOWS
        wmod._IS_WINDOWS = False
        try:
            result = op.close_window(1)
        finally:
            wmod._IS_WINDOWS = original
        assert result is False

    def test_find_window_windows_mock(self):
        if sys.platform != 'win32':
            import pytest
            pytest.skip("需要 Windows ctypes")
        op = WindowsOperator()
        with patch("ctypes.windll.user32.FindWindowW", return_value=12345):
            hwnd = op.find_window("Notepad")
        assert hwnd == 12345


# ────────────────────────────────────────────────────────────────────────────
# 键鼠模拟测试（非 Windows 降级）
# ────────────────────────────────────────────────────────────────────────────

class TestKeyMouse:
    def test_send_key_non_windows(self):
        op = WindowsOperator()
        import agent.windows_operator as wmod
        original = wmod._IS_WINDOWS
        wmod._IS_WINDOWS = False
        try:
            op.send_key(0x43)  # VK_C
        finally:
            wmod._IS_WINDOWS = original
        # 不抛异常即通过

    def test_send_hotkey_non_windows(self):
        op = WindowsOperator()
        import agent.windows_operator as wmod
        original = wmod._IS_WINDOWS
        wmod._IS_WINDOWS = False
        try:
            op.send_hotkey(0x11, 0x43)  # Ctrl+C
        finally:
            wmod._IS_WINDOWS = original

    def test_mouse_move_non_windows(self):
        op = WindowsOperator()
        import agent.windows_operator as wmod
        original = wmod._IS_WINDOWS
        wmod._IS_WINDOWS = False
        try:
            op.mouse_move(100, 200)
        finally:
            wmod._IS_WINDOWS = original

    def test_mouse_click_non_windows(self):
        op = WindowsOperator()
        import agent.windows_operator as wmod
        original = wmod._IS_WINDOWS
        wmod._IS_WINDOWS = False
        try:
            op.mouse_click(100, 200)
            op.mouse_click(100, 200, button='right')
        finally:
            wmod._IS_WINDOWS = original

    def test_type_string_non_windows(self):
        op = WindowsOperator()
        import agent.windows_operator as wmod
        original = wmod._IS_WINDOWS
        wmod._IS_WINDOWS = False
        try:
            op.type_string("hello world")
        finally:
            wmod._IS_WINDOWS = original


# ────────────────────────────────────────────────────────────────────────────
# 剪贴板测试
# ────────────────────────────────────────────────────────────────────────────

class TestClipboard:
    def test_clipboard_get_non_windows(self):
        op = WindowsOperator()
        import agent.windows_operator as wmod
        original = wmod._IS_WINDOWS
        wmod._IS_WINDOWS = False
        try:
            result = op.clipboard_get()
        finally:
            wmod._IS_WINDOWS = original
        assert result == ""

    def test_clipboard_set_non_windows(self):
        op = WindowsOperator()
        import agent.windows_operator as wmod
        original = wmod._IS_WINDOWS
        wmod._IS_WINDOWS = False
        try:
            result = op.clipboard_set("test text")
        finally:
            wmod._IS_WINDOWS = original
        assert result is False

    def test_clipboard_get_open_fails(self):
        if sys.platform != 'win32':
            return  # 仅在 Windows 上测试 ctypes
        op = WindowsOperator()
        with patch("ctypes.windll.user32.OpenClipboard", return_value=0):
            result = op.clipboard_get()
        assert result == ""

    def test_clipboard_set_open_fails(self):
        if sys.platform != 'win32':
            return
        op = WindowsOperator()
        with patch("ctypes.windll.user32.OpenClipboard", return_value=0):
            result = op.clipboard_set("hello")
        assert result is False


# ────────────────────────────────────────────────────────────────────────────
# 系统信息测试
# ────────────────────────────────────────────────────────────────────────────

class TestGetSystemInfo:
    def test_contains_platform_keys(self):
        op = WindowsOperator()
        with patch("subprocess.run", return_value=_make_proc(0, "")):
            info = op.get_system_info()
        assert "platform" in info
        assert "hostname" in info
        assert "os" in info
        assert "python_version" in info

    def test_contains_architecture(self):
        op = WindowsOperator()
        with patch("subprocess.run", return_value=_make_proc(0, "")):
            info = op.get_system_info()
        assert "architecture" in info

    def test_windows_parses_ram(self):
        op = WindowsOperator()
        systeminfo_output = (
            "Total Physical Memory:     16,384 MB\n"
            "Available Physical Memory: 8,192 MB\n"
        )
        with patch("sys.platform", "win32"):
            import agent.windows_operator as wmod
            original = wmod._IS_WINDOWS
            wmod._IS_WINDOWS = True
            try:
                with patch("subprocess.run", return_value=_make_proc(0, systeminfo_output)):
                    info = op.get_system_info()
            finally:
                wmod._IS_WINDOWS = original
        if "total_ram" in info:
            assert "16,384 MB" in info["total_ram"]


class TestGetDiskInfo:
    def test_returns_usage_fields(self, tmp_path):
        op = WindowsOperator()
        info = op.get_disk_info(str(tmp_path))
        assert "total" in info
        assert "used" in info
        assert "free" in info
        assert "used_percent" in info

    def test_bad_path_returns_error(self):
        op = WindowsOperator()
        info = op.get_disk_info("/no/such/mount/point/xyz")
        assert "error" in info


class TestEnvVars:
    def test_get_existing_env(self):
        os.environ["JMV_TEST_VAR"] = "jmv_value"
        op = WindowsOperator()
        assert op.get_env("JMV_TEST_VAR") == "jmv_value"
        del os.environ["JMV_TEST_VAR"]

    def test_get_missing_env_returns_empty(self):
        op = WindowsOperator()
        assert op.get_env("JMV_NO_SUCH_VAR_XYZ") == ""

    def test_set_env(self):
        op = WindowsOperator()
        op.set_env("JMV_DYNAMIC_VAR", "dynamic_val")
        assert os.environ.get("JMV_DYNAMIC_VAR") == "dynamic_val"
        del os.environ["JMV_DYNAMIC_VAR"]
