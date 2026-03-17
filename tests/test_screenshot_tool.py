"""screenshot_tool 单元测试（平台无关部分）"""
import sys
import os
import struct

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCaptureScreenToPpm:
    def test_non_windows_returns_error(self):
        """非 Windows 平台应返回 ERROR，不崩溃"""
        import unittest.mock as mock
        with mock.patch('sys.platform', 'linux'):
            from agent import screenshot_tool
            with mock.patch.object(screenshot_tool, 'sys') as m:
                m.platform = 'linux'
                path, status = screenshot_tool.capture_screen_to_ppm()
            assert "ERROR" in status
            assert path == ""

    def test_ppm_file_format_valid(self, tmp_path):
        """若平台为 Windows 且截图成功，PPM 文件应符合 P6 格式"""
        if sys.platform != 'win32':
            import pytest
            pytest.skip("仅在 Windows 上执行实际截图")

        from agent.screenshot_tool import capture_screen_to_ppm
        out = str(tmp_path / "test.ppm")
        path, status = capture_screen_to_ppm(output_path=out, scale=0.1)
        assert status == "SUCCESS"
        assert os.path.isfile(path)
        with open(path, 'rb') as f:
            header = f.read(64)
        assert header.startswith(b'P6\n')

    def test_ppm_pixel_data_length(self, tmp_path):
        """PPM 文件像素数据长度应等于 width * height * 3"""
        if sys.platform != 'win32':
            import pytest
            pytest.skip("仅在 Windows 上执行实际截图")

        from agent.screenshot_tool import capture_screen_to_ppm
        out = str(tmp_path / "test2.ppm")
        path, status = capture_screen_to_ppm(output_path=out, scale=0.05)
        assert status == "SUCCESS"
        with open(path, 'rb') as f:
            raw = f.read()
        lines = raw.split(b'\n', 3)
        # lines[0]=P6, lines[1]=W H, lines[2]=255, lines[3]=pixels
        assert lines[0] == b'P6'
        w, h = map(int, lines[1].split())
        pixel_data = lines[3]
        assert len(pixel_data) == w * h * 3


class TestCaptureAndAnalyze:
    def test_returns_two_strings(self):
        """capture_and_analyze 必须返回 (str, str) 元组，不崩溃"""
        if sys.platform != 'win32':
            import pytest
            pytest.skip("仅在 Windows 上执行实际截图")

        from agent.screenshot_tool import capture_and_analyze
        desc, status = capture_and_analyze()
        assert isinstance(desc, str)
        assert isinstance(status, str)

    def test_non_windows_returns_error_tuple(self):
        """非 Windows 返回 ERROR tuple，函数签名一致"""
        import unittest.mock as mock
        from agent import screenshot_tool
        with mock.patch.object(screenshot_tool, 'capture_screen_to_ppm',
                               return_value=("", "ERROR: 截图失败")):
            desc, status = screenshot_tool.capture_and_analyze()
        assert "ERROR" in status or "截图失败" in desc
