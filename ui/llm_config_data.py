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

_PROVIDER_FIELDS = {
    'Gemini':     [('gemini_key',      'API Key',   True),  ('gemini_model',     '模型名称', False)],
    'OpenAI':     [('openai_key',      'API Key',   True),  ('openai_model',     '模型名称', False)],
    'Claude':     [('claude_key',      'API Key',   True),  ('claude_model',     '模型名称', False)],
    'DeepSeek':   [('deepseek_key',    'API Key',   True),  ('deepseek_model',   '模型名称', False)],
    'Mistral':    [('mistral_key',     'API Key',   True),  ('mistral_model',    '模型名称', False)],
    'Groq':       [('groq_key',        'API Key',   True),  ('groq_model',       '模型名称', False)],
    'Yi':         [('yi_key',          'API Key',   True),  ('yi_model',         '模型名称', False)],
    'Grok':       [('grok_key',        'API Key',   True),  ('grok_model',       '模型名称', False)],
    'Perplexity': [('perplexity_key',  'API Key',   True),  ('perplexity_model', '模型名称', False)],
    'Together':   [('together_key',    'API Key',   True),  ('together_model',   '模型名称', False)],
    'Qwen':       [('qwen_key',        'API Key',   True),  ('qwen_model',       '模型名称', False)],
    'ERNIE':      [('ernie_key',       'API Key',   True),  ('ernie_model',      '模型名称', False)],
    'Zhipu':      [('zhipu_key',       'API Key',   True),  ('zhipu_model',      '模型名称', False)],
    'Kimi':       [('kimi_key',        'API Key',   True),  ('kimi_model',       '模型名称', False)],
    'MiniMax':    [('minimax_key',     'API Key',   True),  ('minimax_model',    '模型名称', False)],
    'Doubao':     [('doubao_key',      'API Key',   True),  ('doubao_model',     '模型名称', False)],
    'Stepfun':    [('stepfun_key',     'API Key',   True),  ('stepfun_model',    '模型名称', False)],
    'Spark':      [('spark_key',       'API Key',   True),  ('spark_model',      '模型名称', False)],
    'Ollama':     [('ollama_endpoint', '接口地址',  False), ('ollama_model',     '模型名称', False)],
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
