"""零依赖多供应商 LLM 路由客户端（模块化 providers 架构）"""


class UniversalLLMClient:
    """统一 LLM 调用入口，根据配置路由到对应的 Provider 模块"""

    def __init__(self, config: dict):
        self.config = config
        self._provider_name = config.get('active_provider', 'Gemini')

    def chat(self, system_prompt: str, user_prompt: str) -> tuple:
        """
        路由到对应供应商并调用。
        返回 (response_text, status_str)，status_str == 'SUCCESS' 表示成功。
        """
        from agent.providers import get_provider
        provider = get_provider(self._provider_name)
        if provider is None:
            return None, f'UNKNOWN_PROVIDER: {self._provider_name}'
        return provider.call(system_prompt, user_prompt, self.config)
