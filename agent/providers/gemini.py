"""Google Gemini Provider —— 使用自定义 generateContent 格式，支持自定义端点前缀"""
from agent.providers.base import BaseLLMProvider

_DEFAULT_ENDPOINT_PREFIX = 'https://generativelanguage.googleapis.com'


class GeminiProvider(BaseLLMProvider):
    name = 'Gemini'

    def call(self, system: str, user: str, config: dict) -> tuple:
        api_key = config.get('gemini_key', '')
        model = config.get('gemini_model', 'gemini-2.5-flash')
        # 自定义端点前缀优先（可用于代理 Gemini API）
        prefix = config.get('gemini_endpoint', '').strip().rstrip('/') or _DEFAULT_ENDPOINT_PREFIX
        url = f'{prefix}/v1beta/models/{model}:generateContent?key={api_key}'
        payload = {
            'system_instruction': {'parts': [{'text': system}]},
            'contents': [{'parts': [{'text': user}]}],
        }
        res, status = self._post(url, {'Content-Type': 'application/json'}, payload)
        if status == 'SUCCESS':
            try:
                return res['candidates'][0]['content']['parts'][0]['text'], 'SUCCESS'
            except (KeyError, IndexError, TypeError) as e:
                return None, f'PARSE_ERROR: {e}'
        return None, status
