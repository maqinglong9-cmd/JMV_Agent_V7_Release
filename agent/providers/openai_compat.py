"""OpenAI 兼容接口通用 Provider —— 支持 16 个供应商"""
from agent.providers.base import BaseLLMProvider

# 供应商名称 → (接口URL, key字段, model字段, 默认模型)
_COMPAT_TABLE: dict = {
    # ── 国际供应商 ──────────────────────────────────────────
    'OpenAI': (
        'https://api.openai.com/v1/chat/completions',
        'openai_key', 'openai_model', 'gpt-4o-mini',
    ),
    'DeepSeek': (
        'https://api.deepseek.com/v1/chat/completions',
        'deepseek_key', 'deepseek_model', 'deepseek-chat',
    ),
    'Mistral': (
        'https://api.mistral.ai/v1/chat/completions',
        'mistral_key', 'mistral_model', 'mistral-large-latest',
    ),
    'Groq': (
        'https://api.groq.com/openai/v1/chat/completions',
        'groq_key', 'groq_model', 'llama-3.3-70b-versatile',
    ),
    'Yi': (
        'https://api.lingyiwanwu.com/v1/chat/completions',
        'yi_key', 'yi_model', 'yi-lightning',
    ),
    'Grok': (
        'https://api.x.ai/v1/chat/completions',
        'grok_key', 'grok_model', 'grok-2-latest',
    ),
    'Perplexity': (
        'https://api.perplexity.ai/chat/completions',
        'perplexity_key', 'perplexity_model', 'llama-3.1-sonar-large-128k-online',
    ),
    'Together': (
        'https://api.together.xyz/v1/chat/completions',
        'together_key', 'together_model', 'meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo',
    ),
    # ── 国内供应商 ──────────────────────────────────────────
    'Qwen': (
        'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
        'qwen_key', 'qwen_model', 'qwen-turbo',
    ),
    'Zhipu': (
        'https://open.bigmodel.cn/api/paas/v4/chat/completions',
        'zhipu_key', 'zhipu_model', 'glm-4-flash',
    ),
    'Kimi': (
        'https://api.moonshot.cn/v1/chat/completions',
        'kimi_key', 'kimi_model', 'moonshot-v1-8k',
    ),
    'Doubao': (
        'https://ark.cn-beijing.volces.com/api/v3/chat/completions',
        'doubao_key', 'doubao_model', 'doubao-pro-32k',
    ),
    'Stepfun': (
        'https://api.stepfun.com/v1/chat/completions',
        'stepfun_key', 'stepfun_model', 'step-1-8k',
    ),
    'ERNIE': (
        'https://qianfan.baidubce.com/v2/chat/completions',
        'ernie_key', 'ernie_model', 'ernie-4.5-turbo-128k',
    ),
    'MiniMax': (
        'https://api.minimax.chat/v1/chat/completions',
        'minimax_key', 'minimax_model', 'abab6.5s-chat',
    ),
    'Spark': (
        'https://spark-api-open.xf-yun.com/v1/chat/completions',
        'spark_key', 'spark_model', 'lite',
    ),
}


class OpenAICompatProvider(BaseLLMProvider):
    """支持 OpenAI 兼容接口的通用 Provider（Bearer token 鉴权）"""

    def __init__(self, provider_name: str):
        entry = _COMPAT_TABLE[provider_name]
        self.name = provider_name
        self._url = entry[0]
        self._key_field = entry[1]
        self._model_field = entry[2]
        self._default_model = entry[3]

    def call(self, system: str, user: str, config: dict) -> tuple:
        api_key = config.get(self._key_field, '')
        model = config.get(self._model_field, self._default_model)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        }
        payload = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': user},
            ],
        }
        res, status = self._post(self._url, headers, payload)
        if status == 'SUCCESS':
            try:
                return res['choices'][0]['message']['content'], 'SUCCESS'
            except (KeyError, IndexError, TypeError) as e:
                return None, f'PARSE_ERROR: {e}'
        return None, status
