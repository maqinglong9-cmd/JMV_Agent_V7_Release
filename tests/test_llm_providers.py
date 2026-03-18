"""LLM Provider 模块化架构单元测试"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestProviderBase:
    def test_base_provider_exists(self):
        from agent.providers.base import BaseLLMProvider
        assert BaseLLMProvider is not None

    def test_base_provider_raises_not_implemented(self):
        from agent.providers.base import BaseLLMProvider
        import pytest
        p = BaseLLMProvider()
        with pytest.raises(NotImplementedError):
            p.call("sys", "user", {})


class TestOpenAICompatProvider:
    def test_all_compat_providers_importable(self):
        from agent.providers.openai_compat import _COMPAT_TABLE
        assert len(_COMPAT_TABLE) >= 16

    def test_compat_table_structure(self):
        from agent.providers.openai_compat import _COMPAT_TABLE
        for name, entry in _COMPAT_TABLE.items():
            assert len(entry) == 4, f"{name} entry should have 4 elements"
            url, key_field, model_field, default_model = entry
            assert url.startswith('http'), f"{name} URL should start with http"
            assert isinstance(key_field, str)
            assert isinstance(model_field, str)
            assert isinstance(default_model, str)

    def test_provider_instantiation(self):
        from agent.providers.openai_compat import OpenAICompatProvider
        p = OpenAICompatProvider('OpenAI')
        assert p.name == 'OpenAI'
        assert 'openai.com' in p._url

    def test_deepseek_provider(self):
        from agent.providers.openai_compat import OpenAICompatProvider
        p = OpenAICompatProvider('DeepSeek')
        assert 'deepseek' in p._url.lower()
        assert p._key_field == 'deepseek_key'

    def test_groq_provider(self):
        from agent.providers.openai_compat import OpenAICompatProvider
        p = OpenAICompatProvider('Groq')
        assert 'groq' in p._url.lower()

    def test_domestic_providers_present(self):
        from agent.providers.openai_compat import _COMPAT_TABLE
        domestic = ['Qwen', 'Zhipu', 'Kimi', 'Doubao', 'Stepfun', 'ERNIE', 'MiniMax', 'Spark']
        for name in domestic:
            assert name in _COMPAT_TABLE, f"Domestic provider {name} missing"


class TestGeminiProvider:
    def test_provider_name(self):
        from agent.providers.gemini import GeminiProvider
        p = GeminiProvider()
        assert p.name == 'Gemini'

    def test_url_construction(self):
        """Gemini URL 应基于 model 和 key 动态构建"""
        from agent.providers.gemini import GeminiProvider
        import unittest.mock as mock
        p = GeminiProvider()
        # 验证接口在无效 key 下会被调用（网络错误是预期的）
        with mock.patch.object(p, '_post', return_value=(None, 'NETWORK_ERROR: test')):
            result, status = p.call('sys', 'user', {'gemini_key': 'test', 'gemini_model': 'gemini-2.5-flash'})
        assert result is None
        assert status != 'SUCCESS'


class TestAnthropicProvider:
    def test_provider_name(self):
        from agent.providers.anthropic import AnthropicProvider
        p = AnthropicProvider()
        assert p.name == 'Claude'

    def test_uses_correct_headers(self):
        from agent.providers.anthropic import AnthropicProvider
        import unittest.mock as mock
        p = AnthropicProvider()
        captured = {}

        def fake_post(url, headers, payload, timeout=30):
            captured['headers'] = headers
            return None, 'NETWORK_ERROR: test'

        with mock.patch.object(p, '_post', side_effect=fake_post):
            p.call('sys', 'user', {'claude_key': 'sk-test'})
        assert 'x-api-key' in captured.get('headers', {})
        assert 'anthropic-version' in captured.get('headers', {})


class TestOllamaProvider:
    def test_provider_name(self):
        from agent.providers.ollama import OllamaProvider
        p = OllamaProvider()
        assert p.name == 'Ollama'

    def test_payload_format(self):
        from agent.providers.ollama import OllamaProvider
        import unittest.mock as mock
        p = OllamaProvider()
        captured = {}

        def fake_post(url, headers, payload, timeout=30):
            captured['payload'] = payload
            return {'response': 'test response'}, 'SUCCESS'

        with mock.patch.object(p, '_post', side_effect=fake_post):
            result, status = p.call('sys', 'user', {'ollama_model': 'llama3'})
        assert status == 'SUCCESS'
        assert result == 'test response'
        assert captured['payload']['stream'] is False
        assert captured['payload']['model'] == 'llama3'


class TestRegistry:
    def test_registry_has_all_providers(self):
        from agent.providers.registry import PROVIDER_REGISTRY
        expected = [
            'OpenAI', 'Claude', 'Gemini', 'DeepSeek', 'Mistral', 'Groq',
            'Yi', 'Grok', 'Perplexity', 'Together',
            'Qwen', 'ERNIE', 'Zhipu', 'Kimi', 'MiniMax', 'Doubao', 'Stepfun', 'Spark',
            'Ollama',
        ]
        for name in expected:
            assert name in PROVIDER_REGISTRY, f"Provider {name} missing from registry"

    def test_get_provider_returns_correct_type(self):
        from agent.providers.registry import get_provider
        from agent.providers.base import BaseLLMProvider
        for name in ['OpenAI', 'Claude', 'Gemini', 'DeepSeek', 'Ollama']:
            p = get_provider(name)
            assert p is not None
            assert isinstance(p, BaseLLMProvider)

    def test_get_unknown_provider_returns_none(self):
        from agent.providers.registry import get_provider
        assert get_provider('NonExistent') is None

    def test_list_providers(self):
        from agent.providers.registry import list_providers
        providers = list_providers()
        assert len(providers) >= 19
        assert 'Gemini' in providers
        assert 'Ollama' in providers


class TestUniversalLLMClient:
    def test_routes_to_provider(self):
        from agent.universal_llm_client import UniversalLLMClient
        import unittest.mock as mock

        config = {'active_provider': 'OpenAI', 'openai_key': 'test', 'openai_model': 'gpt-4o-mini'}
        client = UniversalLLMClient(config)

        with mock.patch('agent.providers.openai_compat.OpenAICompatProvider.call',
                        return_value=('hello', 'SUCCESS')):
            result, status = client.chat('sys', 'user')
        assert status == 'SUCCESS'
        assert result == 'hello'

    def test_unknown_provider_returns_error(self):
        from agent.universal_llm_client import UniversalLLMClient
        client = UniversalLLMClient({'active_provider': 'Unknown123'})
        result, status = client.chat('sys', 'user')
        assert result is None
        assert 'UNKNOWN_PROVIDER' in status

    def test_default_provider_is_gemini(self):
        from agent.universal_llm_client import UniversalLLMClient
        client = UniversalLLMClient({})
        assert client._provider_name == 'Gemini'

    def test_gemini_mock_call(self):
        from agent.universal_llm_client import UniversalLLMClient
        import unittest.mock as mock

        config = {'active_provider': 'Gemini', 'gemini_key': 'test'}
        client = UniversalLLMClient(config)

        with mock.patch('agent.providers.gemini.GeminiProvider.call',
                        return_value=('gemini response', 'SUCCESS')):
            result, status = client.chat('sys', 'user')
        assert result == 'gemini response'
