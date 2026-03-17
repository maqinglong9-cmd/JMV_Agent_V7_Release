"""LLM 配置数据和持久化逻辑（无 Kivy 依赖，可在测试中直接导入）"""
import os
import json

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONFIG_FILE = os.path.join(_PROJECT_ROOT, 'jmv_compute_config.json')

PROVIDERS = ['Gemini', 'OpenAI', 'Claude', 'DeepSeek', 'Ollama']

_PROVIDER_FIELDS = {
    'Gemini':   [('gemini_key',    'API Key',  True),  ('gemini_model',   '模型名称', False)],
    'OpenAI':   [('openai_key',    'API Key',  True),  ('openai_model',   '模型名称', False)],
    'Claude':   [('claude_key',    'API Key',  True),  ('claude_model',   '模型名称', False)],
    'DeepSeek': [('deepseek_key',  'API Key',  True),  ('deepseek_model', '模型名称', False)],
    'Ollama':   [('ollama_endpoint','接口地址', False), ('ollama_model',   '模型名称', False)],
}

_DEFAULT_CONFIG = {
    'active_provider': 'Gemini',
    'gemini_model':    'gemini-2.5-flash',
    'openai_model':    'gpt-3.5-turbo',
    'claude_model':    'claude-sonnet-4-6',
    'deepseek_model':  'deepseek-chat',
    'ollama_endpoint': 'http://localhost:11434/api/generate',
    'ollama_model':    'llama3',
    'gemini_key':      '',
    'openai_key':      '',
    'claude_key':      '',
    'deepseek_key':    '',
}

_ENV_KEY_MAP = {
    'gemini_key':   'GEMINI_API_KEY',
    'openai_key':   'OPENAI_API_KEY',
    'claude_key':   'ANTHROPIC_API_KEY',
    'deepseek_key': 'DEEPSEEK_API_KEY',
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
    """保存配置到本地 JSON（包含 API Key）并同步写入环境变量"""
    try:
        config_dir = os.path.dirname(CONFIG_FILE)
        if config_dir:
            os.makedirs(config_dir, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        for field, env_var in _ENV_KEY_MAP.items():
            val = config.get(field, '')
            if val:
                os.environ[env_var] = val
    except Exception as e:
        print(f'[Config] 保存失败: {e}')
