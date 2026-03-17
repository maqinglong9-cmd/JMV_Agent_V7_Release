"""
测试 version.py 版本工具函数：
  - parse_version 正确解析版本字符串
  - is_newer 正确比较版本号
  - 边界情况处理
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from version import parse_version, is_newer, __version__


class TestParseVersion:
    def test_basic(self):
        assert parse_version("1.2.3") == (1, 2, 3)

    def test_single_digit(self):
        assert parse_version("1.0.0") == (1, 0, 0)

    def test_large_numbers(self):
        assert parse_version("10.20.30") == (10, 20, 30)

    def test_invalid_returns_zeros(self):
        assert parse_version("invalid") == (0, 0, 0)

    def test_empty_returns_zeros(self):
        assert parse_version("") == (0, 0, 0)

    def test_strips_whitespace(self):
        assert parse_version("  1.2.3  ") == (1, 2, 3)


class TestIsNewer:
    def test_newer_patch(self):
        assert is_newer("1.1.1", "1.1.0") is True

    def test_newer_minor(self):
        assert is_newer("1.2.0", "1.1.9") is True

    def test_newer_major(self):
        assert is_newer("2.0.0", "1.9.9") is True

    def test_same_version(self):
        assert is_newer("1.1.0", "1.1.0") is False

    def test_older_version(self):
        assert is_newer("1.0.0", "1.1.0") is False

    def test_current_version_not_newer(self):
        # 当前版本不应该比自身更新
        assert is_newer(__version__, __version__) is False


class TestCurrentVersion:
    def test_version_format(self):
        """版本号格式必须是 X.Y.Z"""
        parts = __version__.split(".")
        assert len(parts) == 3
        for part in parts:
            assert part.isdigit(), f"版本号部分 '{part}' 不是数字"
