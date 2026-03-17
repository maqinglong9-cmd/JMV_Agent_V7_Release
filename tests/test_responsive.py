"""ui.responsive 单元测试"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestIsAndroid:
    def test_not_android_on_windows(self):
        import unittest.mock as mock
        with mock.patch('sys.platform', 'win32'):
            from ui import responsive
            with mock.patch.object(responsive.sys, 'platform', 'win32'):
                result = responsive.is_android()
        assert result is False

    def test_android_requires_both_conditions(self):
        import unittest.mock as mock
        from ui import responsive
        with mock.patch.object(responsive.sys, 'platform', 'linux'), \
             mock.patch('os.path.exists', return_value=False):
            result = responsive.is_android()
        assert result is False

    def test_android_detected_with_data_dir(self):
        import unittest.mock as mock
        from ui import responsive
        with mock.patch.object(responsive.sys, 'platform', 'linux'), \
             mock.patch('os.path.exists', return_value=True):
            result = responsive.is_android()
        assert result is True


class TestFontFunctions:
    def test_font_body_returns_string(self):
        from ui.responsive import font_body
        result = font_body()
        assert isinstance(result, str)
        assert 'sp' in result

    def test_font_small_smaller_or_equal_to_body(self):
        from ui.responsive import font_small, font_body
        small_val = int(font_small().replace('sp', ''))
        body_val  = int(font_body().replace('sp', ''))
        assert small_val <= body_val

    def test_font_large_larger_than_body(self):
        from ui.responsive import font_large, font_body
        large_val = int(font_large().replace('sp', ''))
        body_val  = int(font_body().replace('sp', ''))
        assert large_val > body_val

    def test_font_title_largest(self):
        from ui.responsive import font_title, font_large
        title_val = int(font_title().replace('sp', ''))
        large_val = int(font_large().replace('sp', ''))
        assert title_val >= large_val


class TestDpSp:
    def test_dp_returns_float(self):
        from ui.responsive import dp
        result = dp(16)
        assert isinstance(result, (int, float))
        assert result > 0

    def test_sp_returns_float(self):
        from ui.responsive import sp
        result = sp(12)
        assert isinstance(result, (int, float))
        assert result > 0

    def test_dp_proportional(self):
        from ui.responsive import dp
        assert dp(32) > dp(16)

    def test_sp_proportional(self):
        from ui.responsive import sp
        assert sp(24) > sp(12)


class TestLayoutHelpers:
    def test_button_height_positive(self):
        from ui.responsive import button_height
        assert button_height() > 0

    def test_input_height_positive(self):
        from ui.responsive import input_height
        assert input_height() > 0

    def test_header_height_larger_than_button(self):
        from ui.responsive import header_height, button_height
        assert header_height() >= button_height()

    def test_touch_target_minimum(self):
        from ui.responsive import touch_target, dp
        assert touch_target() >= dp(36)

    def test_tab_bar_height_positive(self):
        from ui.responsive import tab_bar_height
        assert tab_bar_height() > 0

    def test_compact_brain_height_positive(self):
        from ui.responsive import compact_brain_height
        assert compact_brain_height() > 0

    def test_section_height_smaller_than_section_label_height(self):
        from ui.responsive import section_height, section_label_height
        # 新紧凑版应该 <= 旧版高度
        assert section_height() <= section_label_height()

    def test_tool_row_height_positive(self):
        from ui.responsive import tool_row_height
        assert tool_row_height() > 0

    def test_mode_row_height_positive(self):
        from ui.responsive import mode_row_height
        assert mode_row_height() > 0

    def test_header_height_equals_52dp(self):
        from ui.responsive import header_height, dp
        assert header_height() == dp(52)

    def test_total_fixed_height_fits_phone(self):
        """验证固定高度总计不超过 640dp（标准手机屏幕）"""
        from ui.responsive import (
            header_height, mode_row_height, section_height,
            compact_brain_height, dp, tab_bar_height, tool_row_height, button_height
        )
        # Header + ModeRow + 2*SectionLabel + Brain + Progress + Input(base) + TabBar
        total = (
            header_height()         # 52
            + mode_row_height()     # 40
            + section_height() * 2  # 24*2 = 48
            + compact_brain_height()# 88
            + dp(4)                 # progress bar
            + dp(52) + tool_row_height() + button_height()  # input panel base 144
            + tab_bar_height()      # 56
        )
        assert total <= dp(500), f'固定高度总计 {total} > 500dp，LogViewer 无空间'
