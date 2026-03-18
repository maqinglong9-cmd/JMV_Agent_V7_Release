"""Ollama 本地 LLM Provider —— 通过 /api/generate 接口调用"""
from agent.providers.base import BaseLLMProvider


class OllamaProvider(BaseLLMProvider):
    name = 'Ollama'

    def call(self, system: str, user: str, config: dict) -> tuple:
        endpoint = config.get('ollama_endpoint', 'http://localhost:11434/api/generate')
        model = config.get('ollama_model', 'llama3')
        payload = {
            'model': model,
            'system': system,
            'prompt': user,
            'stream': False,
        }
        res, status = self._post(endpoint, {'Content-Type': 'application/json'}, payload)
        if status == 'SUCCESS':
            try:
                return res.get('response', ''), 'SUCCESS'
            except AttributeError as e:
                return None, f'PARSE_ERROR: {e}'
        return None, status
