"""Provider 注册表 —— 将所有供应商统一注册为可查询字典"""
from agent.providers.base import BaseLLMProvider
from agent.providers.openai_compat import OpenAICompatProvider, _COMPAT_TABLE
from agent.providers.gemini import GeminiProvider
from agent.providers.anthropic import AnthropicProvider
from agent.providers.ollama import OllamaProvider

# 从 OpenAI 兼容表构建基础注册表
PROVIDER_REGISTRY: dict = {
    name: OpenAICompatProvider(name) for name in _COMPAT_TABLE
}

# 添加使用自定义协议的供应商
PROVIDER_REGISTRY.update({
    'Gemini': GeminiProvider(),
    'Claude': AnthropicProvider(),
    'Ollama': OllamaProvider(),
})


def get_provider(name: str):
    """按名称获取 Provider 实例，不存在返回 None"""
    return PROVIDER_REGISTRY.get(name)


def list_providers() -> list:
    """返回所有已注册供应商名称列表"""
    return list(PROVIDER_REGISTRY.keys())
