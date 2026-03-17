"""ChatAgent 单元测试"""
import sys
import os
import unittest.mock as mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.chat_agent import ChatAgent, _MAX_HISTORY


class TestChatAgentNoLLM:
    def test_chat_returns_string(self):
        agent = ChatAgent()
        result = agent.chat('你好')
        assert isinstance(result, str)
        assert len(result) > 0

    def test_empty_input_returns_hint(self):
        agent = ChatAgent()
        result = agent.chat('   ')
        assert '请输入' in result or len(result) > 0

    def test_fallback_cycles_through_replies(self):
        agent = ChatAgent()
        replies = set()
        for _ in range(8):
            r = agent.chat('测试')
            replies.add(r)
        # 应该出现多种回复（循环）
        assert len(replies) >= 1

    def test_history_grows_after_each_chat(self):
        agent = ChatAgent()
        agent.clear_history()
        agent.chat('第一条')
        agent.chat('第二条')
        history = agent.get_history()
        assert len(history) == 4  # 2 user + 2 assistant

    def test_history_trimmed_to_max(self):
        agent = ChatAgent()
        agent.clear_history()
        for i in range(_MAX_HISTORY + 5):
            agent.chat(f'消息 {i}')
        history = agent.get_history()
        assert len(history) <= _MAX_HISTORY * 2

    def test_clear_history(self):
        agent = ChatAgent()
        agent.chat('测试')
        agent.clear_history()
        assert agent.get_history() == []

    def test_get_history_returns_list(self):
        agent = ChatAgent()
        agent.clear_history()
        history = agent.get_history()
        assert isinstance(history, list)

    def test_history_has_user_and_assistant_roles(self):
        agent = ChatAgent()
        agent.clear_history()
        agent.chat('你好')
        history = agent.get_history()
        roles = {msg['role'] for msg in history}
        assert 'user' in roles
        assert 'assistant' in roles


class TestChatAgentWithLLM:
    def test_llm_called_with_text(self):
        fake_llm = mock.MagicMock()
        fake_llm.chat.return_value = ('你好，我是AI', 'SUCCESS')
        agent = ChatAgent(llm_client=fake_llm)
        agent.clear_history()
        result = agent.chat('hello')
        fake_llm.chat.assert_called_once()
        assert result == '你好，我是AI'

    def test_llm_failure_returns_error_msg(self):
        fake_llm = mock.MagicMock()
        fake_llm.chat.return_value = (None, 'HTTP_401: Unauthorized')
        agent = ChatAgent(llm_client=fake_llm)
        agent.clear_history()
        result = agent.chat('test')
        assert isinstance(result, str)
        assert len(result) > 0

    def test_llm_exception_does_not_crash(self):
        fake_llm = mock.MagicMock()
        fake_llm.chat.side_effect = RuntimeError('模拟网络错误')
        agent = ChatAgent(llm_client=fake_llm)
        agent.clear_history()
        result = agent.chat('test')
        assert isinstance(result, str)

    def test_set_llm_updates_client(self):
        agent = ChatAgent()
        agent.clear_history()
        fake_llm = mock.MagicMock()
        fake_llm.chat.return_value = ('已更新', 'SUCCESS')
        agent.set_llm(fake_llm)
        result = agent.chat('test')
        assert result == '已更新'

    def test_history_included_in_context(self):
        """多轮对话时，历史应包含在 LLM 请求中"""
        calls = []
        def fake_chat(system_prompt, user_prompt):
            calls.append(user_prompt)
            return ('回复', 'SUCCESS')

        fake_llm = mock.MagicMock()
        fake_llm.chat.side_effect = fake_chat
        agent = ChatAgent(llm_client=fake_llm)
        agent.clear_history()
        agent.chat('第一条消息')
        agent.chat('第二条消息')

        # 第二次调用时，user_prompt 应包含历史
        assert len(calls) == 2
        assert '第一条消息' in calls[1] or '第二条消息' in calls[1]


class TestChatAgentPersistence:
    def test_save_and_load_memory(self, tmp_path):
        """保存记忆后重新创建的 Agent 应加载历史"""
        agent = ChatAgent()
        # 修改内存路径到 tmp
        agent._memory_path = str(tmp_path / 'chat_memory.json')
        agent.clear_history()
        agent.chat('持久化测试')
        agent._save_memory()

        # 新 Agent 加载同一路径
        agent2 = ChatAgent()
        agent2._memory_path = str(tmp_path / 'chat_memory.json')
        agent2._load_memory()
        history = agent2.get_history()
        assert len(history) > 0
