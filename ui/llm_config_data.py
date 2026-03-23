"""LLM 配置数据和持久化逻辑（无 Kivy 依赖，可在测试中直接导入）"""
import os
import json

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONFIG_FILE = os.path.join(_PROJECT_ROOT, 'jmv_compute_config.json')

# 全部 19 个云端供应商 + 1 个本地 Ollama
PROVIDERS = [
    # 国际
    'Gemini', 'OpenAI', 'Claude', 'DeepSeek', 'Mistral', 'Groq',
    'Yi', 'Grok', 'Perplexity', 'Together',
    # 国内
    'Qwen', 'ERNIE', 'Zhipu', 'Kimi', 'MiniMax', 'Doubao', 'Stepfun', 'Spark',
    # 本地
    'Ollama',
]

# (field_key, 显示标签, is_secret, hint_text)
# hint_text 用于输入框占位提示（含格式示例）
_PROVIDER_FIELDS = {
    'Gemini': [
        ('gemini_key',      'API Key',  True,  'AIzaSy... (Google AI Studio 获取)'),
        ('gemini_model',    '模型名称', False, 'gemini-2.5-flash'),
        ('gemini_endpoint', 'API端点',  False, '留空使用官方地址，填代理前缀如 https://your-proxy.com'),
    ],
    'OpenAI': [
        ('openai_key',      'API Key',  True,  'sk-... (platform.openai.com 获取)'),
        ('openai_model',    '模型名称', False, 'gpt-4o-mini'),
        ('openai_endpoint', 'API端点',  False, '留空使用官方地址，国内代理如 https://your-proxy.com/v1/chat/completions'),
    ],
    'Claude': [
        ('claude_key',      'API Key',  True,  'sk-ant-... (console.anthropic.com 获取)'),
        ('claude_model',    '模型名称', False, 'claude-sonnet-4-6'),
        ('claude_endpoint', 'API端点',  False, '留空使用官方地址，填代理如 https://your-proxy.com/v1/messages'),
    ],
    'DeepSeek': [
        ('deepseek_key',      'API Key',  True,  'sk-... (platform.deepseek.com 获取)'),
        ('deepseek_model',    '模型名称', False, 'deepseek-chat'),
        ('deepseek_endpoint', 'API端点',  False, '留空使用官方地址'),
    ],
    'Mistral': [
        ('mistral_key',      'API Key',  True,  '... (console.mistral.ai 获取)'),
        ('mistral_model',    '模型名称', False, 'mistral-large-latest'),
        ('mistral_endpoint', 'API端点',  False, '留空使用官方地址'),
    ],
    'Groq': [
        ('groq_key',      'API Key',  True,  'gsk_... (console.groq.com 获取)'),
        ('groq_model',    '模型名称', False, 'llama-3.3-70b-versatile'),
        ('groq_endpoint', 'API端点',  False, '留空使用官方地址'),
    ],
    'Yi': [
        ('yi_key',      'API Key',  True,  '... (platform.lingyiwanwu.com 获取)'),
        ('yi_model',    '模型名称', False, 'yi-lightning'),
        ('yi_endpoint', 'API端点',  False, '留空使用官方地址'),
    ],
    'Grok': [
        ('grok_key',      'API Key',  True,  '... (console.x.ai 获取)'),
        ('grok_model',    '模型名称', False, 'grok-2-latest'),
        ('grok_endpoint', 'API端点',  False, '留空使用官方地址'),
    ],
    'Perplexity': [
        ('perplexity_key',      'API Key',  True,  'pplx-... (perplexity.ai 获取)'),
        ('perplexity_model',    '模型名称', False, 'llama-3.1-sonar-large-128k-online'),
        ('perplexity_endpoint', 'API端点',  False, '留空使用官方地址'),
    ],
    'Together': [
        ('together_key',      'API Key',  True,  '... (api.together.ai 获取)'),
        ('together_model',    '模型名称', False, 'meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo'),
        ('together_endpoint', 'API端点',  False, '留空使用官方地址'),
    ],
    'Qwen': [
        ('qwen_key',      'API Key',  True,  'sk-... (dashscope.aliyun.com 获取)'),
        ('qwen_model',    '模型名称', False, 'qwen-turbo'),
        ('qwen_endpoint', 'API端点',  False, '留空使用官方地址'),
    ],
    'ERNIE': [
        ('ernie_key',      'API Key',  True,  '... (qianfan.cloud.baidu.com 获取)'),
        ('ernie_model',    '模型名称', False, 'ernie-4.5-turbo-128k'),
        ('ernie_endpoint', 'API端点',  False, '留空使用官方地址'),
    ],
    'Zhipu': [
        ('zhipu_key',      'API Key',  True,  '... (open.bigmodel.cn 获取)'),
        ('zhipu_model',    '模型名称', False, 'glm-4-flash'),
        ('zhipu_endpoint', 'API端点',  False, '留空使用官方地址'),
    ],
    'Kimi': [
        ('kimi_key',      'API Key',  True,  'sk-... (platform.moonshot.cn 获取)'),
        ('kimi_model',    '模型名称', False, 'moonshot-v1-8k'),
        ('kimi_endpoint', 'API端点',  False, '留空使用官方地址'),
    ],
    'MiniMax': [
        ('minimax_key',      'API Key',  True,  '... (api.minimax.chat 获取)'),
        ('minimax_model',    '模型名称', False, 'abab6.5s-chat'),
        ('minimax_endpoint', 'API端点',  False, '留空使用官方地址'),
    ],
    'Doubao': [
        ('doubao_key',      'API Key',  True,  '... (ark.cn-beijing.volces.com 获取)'),
        ('doubao_model',    '模型名称', False, 'doubao-pro-32k（填入 endpoint ID）'),
        ('doubao_endpoint', 'API端点',  False, '留空使用官方地址'),
    ],
    'Stepfun': [
        ('stepfun_key',      'API Key',  True,  '... (platform.stepfun.com 获取)'),
        ('stepfun_model',    '模型名称', False, 'step-1-8k'),
        ('stepfun_endpoint', 'API端点',  False, '留空使用官方地址'),
    ],
    'Spark': [
        ('spark_key',      'API Key',  True,  '... (xf-yun.com 开放平台获取)'),
        ('spark_model',    '模型名称', False, 'lite'),
        ('spark_endpoint', 'API端点',  False, '留空使用官方地址'),
    ],
    'Ollama': [
        ('ollama_endpoint', '接口地址', False, 'http://localhost:11434/api/generate'),
        ('ollama_model',    '模型名称', False, 'llama3'),
    ],
}

_DEFAULT_CONFIG = {
    'active_provider':  'Gemini',
    # 模型默认值
    'gemini_model':     'gemini-2.5-flash',
    'openai_model':     'gpt-4o-mini',
    'claude_model':     'claude-sonnet-4-6',
    'deepseek_model':   'deepseek-chat',
    'mistral_model':    'mistral-large-latest',
    'groq_model':       'llama-3.3-70b-versatile',
    'yi_model':         'yi-lightning',
    'grok_model':       'grok-2-latest',
    'perplexity_model': 'llama-3.1-sonar-large-128k-online',
    'together_model':   'meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo',
    'qwen_model':       'qwen-turbo',
    'ernie_model':      'ernie-4.5-turbo-128k',
    'zhipu_model':      'glm-4-flash',
    'kimi_model':       'moonshot-v1-8k',
    'minimax_model':    'abab6.5s-chat',
    'doubao_model':     'doubao-pro-32k',
    'stepfun_model':    'step-1-8k',
    'spark_model':      'lite',
    'ollama_endpoint':  'http://localhost:11434/api/generate',
    'ollama_model':     'llama3',
    # API Key 默认为空
    'gemini_key':       '',
    'openai_key':       '',
    'claude_key':       '',
    'deepseek_key':     '',
    'mistral_key':      '',
    'groq_key':         '',
    'yi_key':           '',
    'grok_key':         '',
    'perplexity_key':   '',
    'together_key':     '',
    'qwen_key':         '',
    'ernie_key':        '',
    'zhipu_key':        '',
    'kimi_key':         '',
    'minimax_key':      '',
    'doubao_key':       '',
    'stepfun_key':      '',
    'spark_key':        '',
    # 自定义端点（留空使用官方地址）
    'gemini_endpoint':     '',
    'openai_endpoint':     '',
    'claude_endpoint':     '',
    'deepseek_endpoint':   '',
    'mistral_endpoint':    '',
    'groq_endpoint':       '',
    'yi_endpoint':         '',
    'grok_endpoint':       '',
    'perplexity_endpoint': '',
    'together_endpoint':   '',
    'qwen_endpoint':       '',
    'ernie_endpoint':      '',
    'zhipu_endpoint':      '',
    'kimi_endpoint':       '',
    'minimax_endpoint':    '',
    'doubao_endpoint':     '',
    'stepfun_endpoint':    '',
    'spark_endpoint':      '',
}

_ENV_KEY_MAP = {
    'gemini_key':     'GEMINI_API_KEY',
    'openai_key':     'OPENAI_API_KEY',
    'claude_key':     'ANTHROPIC_API_KEY',
    'deepseek_key':   'DEEPSEEK_API_KEY',
    'mistral_key':    'MISTRAL_API_KEY',
    'groq_key':       'GROQ_API_KEY',
    'yi_key':         'YI_API_KEY',
    'grok_key':       'GROK_API_KEY',
    'perplexity_key': 'PERPLEXITY_API_KEY',
    'together_key':   'TOGETHER_API_KEY',
    'qwen_key':       'DASHSCOPE_API_KEY',
    'ernie_key':      'QIANFAN_API_KEY',
    'zhipu_key':      'ZHIPU_API_KEY',
    'kimi_key':       'MOONSHOT_API_KEY',
    'minimax_key':    'MINIMAX_API_KEY',
    'doubao_key':     'ARK_API_KEY',
    'stepfun_key':    'STEPFUN_API_KEY',
    'spark_key':      'SPARK_API_KEY',
}


def load_config() -> dict:
    """读取 LLM 配置（文件 + 环境变量 API Key）"""
    config = dict(_DEFAULT_CONFIG)
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
            config.update(saved)
    except Exception:
        pass
    # 环境变量中的 Key 优先级更高
    for field, env_var in _ENV_KEY_MAP.items():
        val = os.environ.get(env_var, '')
        if val:
            config[field] = val
    return config


def save_config(config: dict) -> None:
    """保存配置到本地 JSON（含 API Key）并同步写入环境变量"""
    try:
        config_dir = os.path.dirname(CONFIG_FILE)
        if config_dir:
            os.makedirs(config_dir, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        # 同步写入环境变量，方便其他进程/模块读取
        for field, env_var in _ENV_KEY_MAP.items():
            val = config.get(field, '')
            if val:
                os.environ[env_var] = val
    except Exception as e:
        print(f'[Config] 保存失败: {e}')
