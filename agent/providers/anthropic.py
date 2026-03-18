"""Anthropic Claude Provider —— 使用 x-api-key 鉴权与 Messages API"""
from agent.providers.base import BaseLLMProvider


class AnthropicProvider(BaseLLMProvider):
    name = 'Claude'

    def call(self, system: str, user: str, config: dict) -> tuple:
        api_key = config.get('claude_key', '')
        model = config.get('claude_model', 'claude-sonnet-4-6')
        url = 'https://api.anthropic.com/v1/messages'
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
