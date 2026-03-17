"""
测试 LLMBrainCore 的 JSON 幻觉自愈机制。
重点验证 BUG 1 修复：空字段应触发自愈提示升级，而非直接返回 SUCCESS。
"""
import sys
import os
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# 工具：构造一个每次调用都返回预设值的假 LLM 客户端
# ---------------------------------------------------------------------------

class _FakeLLMClient:
    """按顺序逐一返回预设 (response, status) 元组。"""

    def __init__(self, responses: list):
        self._queue = list(responses)
        self.call_count = 0
        self.received_prompts = []

    def generate_content(self, system_prompt: str, user_prompt: str):
        self.call_count += 1
        self.received_prompts.append(system_prompt)
        if self._queue:
            return self._queue.pop(0)
        return None, "QUEUE_EMPTY"


def _make_brain(fake_client):
    from agent.llm_brain_core import LLMBrainCore
    core = LLMBrainCore.__new__(LLMBrainCore)
    core.llm_client = fake_client
    core._use_universal = False
    core.evolution_level = 1
    core.base_system_prompt = (
        "你是 JMV智伴，以 JSON 格式回复，包含 thought/action/reply 三个字段。"
    )
    return core


# ---------------------------------------------------------------------------
# 正常路径
# ---------------------------------------------------------------------------

class TestValidResponse:
    def test_valid_json_returns_success(self):
        payload = json.dumps({"thought": "需要画图", "action": "CALL_TOOL_PAINTER", "reply": "好的"})
        client = _FakeLLMClient([(payload, "SUCCESS")])
        core = _make_brain(client)

        result, status = core.process_with_healing("画一幅风景画")

        assert status == "SUCCESS"
        assert result["thought"] == "需要画图"
        assert result["action"] == "CALL_TOOL_PAINTER"
        assert result["reply"] == "好的"
        assert client.call_count == 1

    def test_action_none_is_valid(self):
        """action='NONE' 是合法值，不应触发自愈。"""
        payload = json.dumps({"thought": "无需操作", "action": "NONE", "reply": "明白"})
        client = _FakeLLMClient([(payload, "SUCCESS")])
        core = _make_brain(client)

        result, status = core.process_with_healing("你好")

        assert status == "SUCCESS"
        assert result["action"] == "NONE"
        assert client.call_count == 1


# ---------------------------------------------------------------------------
# BUG 1 修复验证：空字段触发自愈
# ---------------------------------------------------------------------------

class TestEmptyFieldTriggersHealing:
    def test_empty_thought_triggers_retry(self):
        """thought 为空 → 第1次返回 SUCCESS 但字段空 → 自愈升级 → 第2次返回正常值。"""
        bad_payload = json.dumps({"thought": "", "action": "NONE", "reply": "回复"})
        good_payload = json.dumps({"thought": "已修复思考", "action": "NONE", "reply": "好的"})
        client = _FakeLLMClient([
            (bad_payload, "SUCCESS"),
            (good_payload, "SUCCESS"),
        ])
        core = _make_brain(client)

        result, status = core.process_with_healing("测试")

        assert status == "SUCCESS"
        assert result["thought"] == "已修复思考"
        assert client.call_count == 2

    def test_empty_thought_escalates_system_prompt(self):
        """自愈时 system_prompt 应包含警告文本。"""
        bad_payload = json.dumps({"thought": "", "action": "NONE", "reply": "回复"})
        good_payload = json.dumps({"thought": "修复后思考", "action": "NONE", "reply": "好"})
        client = _FakeLLMClient([
            (bad_payload, "SUCCESS"),
            (good_payload, "SUCCESS"),
        ])
        core = _make_brain(client)
        core.process_with_healing("测试")

        # 第2次调用时，system_prompt 中应包含警告
        assert len(client.received_prompts) == 2
        assert "警告" in client.received_prompts[1] or "JSONDecodeError" in client.received_prompts[1] or "ValueError" in client.received_prompts[1]

    def test_empty_action_triggers_retry(self):
        """action 为空字符串 → 触发自愈。"""
        bad_payload = json.dumps({"thought": "思考内容", "action": "", "reply": "回复"})
        good_payload = json.dumps({"thought": "思考内容", "action": "NONE", "reply": "回复"})
        client = _FakeLLMClient([
            (bad_payload, "SUCCESS"),
            (good_payload, "SUCCESS"),
        ])
        core = _make_brain(client)

        result, status = core.process_with_healing("测试")

        assert status == "SUCCESS"
        assert result["action"] == "NONE"
        assert client.call_count == 2

    def test_all_empty_fields_exhaust_retries(self):
        """持续返回空字段应耗尽重试次数并返回 FATAL_ERROR。"""
        bad_payload = json.dumps({"thought": "", "action": "", "reply": ""})
        client = _FakeLLMClient([(bad_payload, "SUCCESS")] * 10)
        core = _make_brain(client)

        result, status = core.process_with_healing("测试")

        assert result is None
        assert "FATAL_ERROR" in status
        assert client.call_count == 5  # max_retries=5


# ---------------------------------------------------------------------------
# JSON 格式幻觉
# ---------------------------------------------------------------------------

class TestJsonHallucination:
    def test_invalid_json_triggers_healing(self):
        """非 JSON 响应 → 自愈升级 → 第2次返回正确 JSON。"""
        bad_response = "这是一段普通文本，不是JSON"
        good_payload = json.dumps({"thought": "思考", "action": "NONE", "reply": "好"})
        client = _FakeLLMClient([
            (bad_response, "SUCCESS"),
            (good_payload, "SUCCESS"),
        ])
        core = _make_brain(client)

        result, status = core.process_with_healing("测试")

        assert status == "SUCCESS"
        assert client.call_count == 2

    def test_missing_keys_triggers_healing(self):
        """缺少 reply 字段 → 触发自愈。"""
        bad_payload = json.dumps({"thought": "思考", "action": "NONE"})
        good_payload = json.dumps({"thought": "思考", "action": "NONE", "reply": "补充"})
        client = _FakeLLMClient([
            (bad_payload, "SUCCESS"),
            (good_payload, "SUCCESS"),
        ])
        core = _make_brain(client)

        result, status = core.process_with_healing("测试")

        assert status == "SUCCESS"
        assert result["reply"] == "补充"

    def test_markdown_wrapped_json_is_cleaned(self):
        """```json ... ``` 包裹的 JSON 应被清洗后成功解析。"""
        payload = "```json\n" + json.dumps({"thought": "ok", "action": "NONE", "reply": "ok"}) + "\n```"
        client = _FakeLLMClient([(payload, "SUCCESS")])
        core = _make_brain(client)

        result, status = core.process_with_healing("测试")

        assert status == "SUCCESS"


# ---------------------------------------------------------------------------
# 网络/鉴权错误
# ---------------------------------------------------------------------------

class TestNetworkErrors:
    def test_network_error_retries(self):
        """底层网络失败 → 重试 → 第2次成功。"""
        good_payload = json.dumps({"thought": "思考", "action": "NONE", "reply": "ok"})
        client = _FakeLLMClient([
            (None, "NETWORK_ERROR"),
            (good_payload, "SUCCESS"),
        ])
        core = _make_brain(client)

        result, status = core.process_with_healing("测试")

        assert status == "SUCCESS"
        assert client.call_count == 2

    def test_persistent_network_error_returns_fatal(self):
        """持续网络失败应返回 FATAL_ERROR。"""
        client = _FakeLLMClient([(None, "NETWORK_ERROR")] * 10)
        core = _make_brain(client)

        result, status = core.process_with_healing("测试")

        assert result is None
        assert "FATAL_ERROR" in status
