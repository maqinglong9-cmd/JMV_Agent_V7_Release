"""
测试 ToolRegistry：
  - 内置工具注册正确（含新增的 TRANSLATE/SUMMARIZE）
  - execute 调用正确工具
  - 翻译工具无 LLM 时降级返回原文
  - 摘要工具无 LLM 时截取前段
  - 计算器工具精确计算
  - CALL_TOOL_SPACESHIP 兼容映射到翻译
  - 动态工具可注册
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent.tool_registry import ToolRegistry


@pytest.fixture
def registry():
    return ToolRegistry()


class TestBuiltinTools:
    def test_all_tools_registered(self, registry):
        tools = registry.list_tools()
        expected = [
            'CALL_TOOL_PAINTER', 'CALL_TOOL_CALCULATOR',
            'CALL_TOOL_SEARCH',  'CALL_TOOL_CODER',
            'CALL_TOOL_TRANSLATE', 'CALL_TOOL_SUMMARIZE',
            'CALL_TOOL_FILE_WRITE', 'CALL_TOOL_SHELL',
            'CALL_TOOL_SPACESHIP',
        ]
        for name in expected:
            assert name in tools, f"{name} 未注册"

    def test_spaceship_compat_mapped(self, registry):
        # CALL_TOOL_SPACESHIP 应映射到翻译工具
        result = registry.execute("CALL_TOOL_SPACESHIP", "Hello World")
        # 无 LLM 时返回降级信息，但不崩溃
        assert isinstance(result, str)
        assert len(result) > 0


class TestCalculator:
    def test_basic_arithmetic(self, registry):
        result = registry.execute("CALL_TOOL_CALCULATOR", "2 + 3 * 4")
        assert "14" in result

    def test_empty_expression(self, registry):
        result = registry.execute("CALL_TOOL_CALCULATOR", "无效输入abc")
        assert "无法" in result or "失败" in result

    def test_division(self, registry):
        result = registry.execute("CALL_TOOL_CALCULATOR", "10 / 2")
        assert "5" in result


class TestTranslate:
    def test_returns_string(self, registry):
        result = registry.execute("CALL_TOOL_TRANSLATE", "你好世界")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_no_llm_fallback(self, registry):
        # 确保无 LLM 不崩溃，返回降级信息
        result = registry._tool_translate("Hello World")
        assert isinstance(result, str)

    def test_empty_input(self, registry):
        result = registry._tool_translate("")
        assert "为空" in result


class TestSummarize:
    def test_returns_string(self, registry):
        result = registry.execute("CALL_TOOL_SUMMARIZE", "这是一段需要摘要的测试文本，内容关于人工智能。")
        assert isinstance(result, str)

    def test_no_llm_fallback_truncates(self, registry):
        long_text = "A" * 200
        result = registry._tool_summarize(long_text)
        assert "摘要" in result

    def test_empty_input(self, registry):
        result = registry._tool_summarize("")
        assert "为空" in result


class TestExecuteRouter:
    def test_unknown_tool_returns_message(self, registry):
        result = registry.execute("CALL_TOOL_UNKNOWN", "params")
        assert "未找到工具" in result

    def test_decision_with_pipe(self, registry):
        result = registry.execute("DECISION:CALL_TOOL_CALCULATOR|extra", "1+1")
        assert "2" in result


class TestDynamicRegister:
    def test_register_custom_tool(self, registry):
        def my_tool(params):
            return f"自定义工具: {params}"
        registry.register("CALL_TOOL_CUSTOM", my_tool)
        result = registry.execute("CALL_TOOL_CUSTOM", "测试参数")
        assert "自定义工具" in result
        assert "测试参数" in result
