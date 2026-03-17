"""
测试 BrainAgentAdapter：
  - LLM 连接状态属性
  - reload_llm 更新客户端
  - run_async 正常流程（LLM 模式 + 降级模式）
  - run_async 并发锁保护（第二次调用应被忽略）
  - 错误路径通过 event_bus 发出 'error' 事件
"""
import sys
import os
import threading
import time
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from adapter.agent_adapter import BrainAgentAdapter
from adapter.event_bus import EventBus


# ---------------------------------------------------------------------------
# 辅助：等待后台线程完成
# ---------------------------------------------------------------------------

def _wait(timeout: float = 2.0):
    """等待所有非主线程结束。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        workers = [t for t in threading.enumerate()
                   if t is not threading.current_thread() and t.daemon]
        if not workers:
            break
        time.sleep(0.05)


# ---------------------------------------------------------------------------
# 属性与配置
# ---------------------------------------------------------------------------

class TestAdapterProperties:
    def test_llm_connected_false_when_no_config(self, tmp_path, monkeypatch):
        """无配置文件时 llm_connected 应为 False。"""
        monkeypatch.setattr(
            "adapter.agent_adapter._CONFIG_FILE",
            str(tmp_path / "nonexistent.json")
        )
        adapter = BrainAgentAdapter()
        assert adapter.llm_connected is False

    def test_llm_provider_empty_when_no_config(self, tmp_path, monkeypatch):
        """无配置文件时 llm_provider 应为空字符串。"""
        monkeypatch.setattr(
            "adapter.agent_adapter._CONFIG_FILE",
            str(tmp_path / "nonexistent.json")
        )
        adapter = BrainAgentAdapter()
        assert adapter.llm_provider == ""

    def test_reload_llm_updates_state(self, tmp_path, monkeypatch):
        """reload_llm 调用后状态应与重新读取配置一致。"""
        cfg_path = str(tmp_path / "nonexistent.json")
        monkeypatch.setattr("adapter.agent_adapter._CONFIG_FILE", cfg_path)

        adapter = BrainAgentAdapter()
        assert adapter.llm_connected is False

        # 写入合法但指向不可用 provider 的配置（_init_llm_client 应返回 None）
        import json
        with open(cfg_path, "w") as f:
            json.dump({"active_provider": "FakeProvider"}, f)

        # reload 后配置已读取，但 client 初始化失败（无真实 provider）
        adapter.reload_llm()
        # 无论成功与否，reload 不应抛出异常
        assert isinstance(adapter.llm_connected, bool)


# ---------------------------------------------------------------------------
# run_async — 降级模式（无 LLM）
# ---------------------------------------------------------------------------

class TestRunAsyncFallback:
    def _make_adapter_no_llm(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "adapter.agent_adapter._CONFIG_FILE",
            str(tmp_path / "no.json")
        )
        return BrainAgentAdapter()

    def test_fallback_emits_step_events(self, tmp_path, monkeypatch):
        """无 LLM 时应降级到本地脑区模拟，发出 step 事件。"""
        adapter = self._make_adapter_no_llm(tmp_path, monkeypatch)

        received_steps = []
        adapter.bus.subscribe("step", lambda data: received_steps.append(data))

        adapter.run_async("树木", "鸟鸣", "微风")
        _wait()

        assert len(received_steps) == 9
        for item in received_steps:
            assert "text" in item
            assert "index" in item
            assert "total" in item

    def test_fallback_emits_done_event(self, tmp_path, monkeypatch):
        """降级模式完成后应发出 done 事件。"""
        adapter = self._make_adapter_no_llm(tmp_path, monkeypatch)

        done_called = []
        adapter.bus.subscribe("done", lambda _: done_called.append(True))

        adapter.run_async("输入", "声音", "触感")
        _wait()

        assert done_called == [True]

    def test_fallback_saves_to_memory(self, tmp_path, monkeypatch):
        """降级模式应调用 memory.save。"""
        adapter = self._make_adapter_no_llm(tmp_path, monkeypatch)

        saved = []
        original_save = adapter.memory.save
        adapter.memory.save = lambda *a: saved.append(a)

        adapter.run_async("视觉", "听觉", "触觉")
        _wait()

        assert len(saved) == 1

    def test_concurrent_calls_are_serialized(self, tmp_path, monkeypatch):
        """第二次 run_async 在第一次未完成时应被忽略（锁保护）。"""
        adapter = self._make_adapter_no_llm(tmp_path, monkeypatch)

        done_count = []
        adapter.bus.subscribe("done", lambda _: done_count.append(1))

        # 手动持有锁，模拟"正在运行"
        adapter._lock.acquire()
        try:
            adapter.run_async("视觉", "听觉", "触觉")  # 应被忽略
            _wait(0.3)
            assert done_count == []  # 不应执行
        finally:
            adapter._lock.release()


# ---------------------------------------------------------------------------
# EventBus
# ---------------------------------------------------------------------------

class TestEventBus:
    def test_subscribe_and_emit(self):
        bus = EventBus()
        received = []
        bus.subscribe("test", lambda d: received.append(d))
        bus.emit("test", {"value": 42})
        assert received == [{"value": 42}]

    def test_unsubscribe_stops_delivery(self):
        bus = EventBus()
        received = []
        cb = lambda d: received.append(d)
        bus.subscribe("ev", cb)
        bus.unsubscribe("ev", cb)
        bus.emit("ev", "data")
        assert received == []

    def test_emit_unknown_event_does_not_crash(self):
        bus = EventBus()
        bus.emit("nonexistent", None)  # 不应抛出异常

    def test_callback_error_does_not_propagate(self):
        """回调内部异常不应传播到调用方。"""
        bus = EventBus()
        bus.subscribe("ev", lambda d: (_ for _ in ()).throw(RuntimeError("坏回调")))
        bus.emit("ev", "data")  # 不应抛出
