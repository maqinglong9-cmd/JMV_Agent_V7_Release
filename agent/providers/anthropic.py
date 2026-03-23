"""Anthropic Claude Provider —— 使用 x-api-key 鉴权与 Messages API，支持自定义端点"""
from agent.providers.base import BaseLLMProvider

_DEFAULT_URL = 'https://api.anthropic.com/v1/messages'


class AnthropicProvider(BaseLLMProvider):
    name = 'Claude'

    def call(self, system: str, user: str, config: dict) -> tuple:
        api_key = config.get('claude_key', '')
        model = config.get('claude_model', 'claude-sonnet-4-6')
        # 自定义端点优先（可用于代理 Anthropic API）
        url = config.get('claude_endpoint', '').strip() or _DEFAULT_URL
        headers = {
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
        }
        payload = {
            'model': model,
            'system': system,
            'messages': [{'role': 'user', 'content': user}],
            'max_tokens': 1024,
        }
        res, status = self._post(url, headers, payload)
        if status == 'SUCCESS':
            try:
                return res['content'][0]['text'], 'SUCCESS'
            except (KeyError, IndexError, TypeError) as e:
                return None, f'PARSE_ERROR: {e}'
        return None, status
