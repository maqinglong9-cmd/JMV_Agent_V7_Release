"""LLM 配置数据模块单元测试（使用 llm_config_data，无 Kivy 依赖）"""
import sys
import os
import json
import unittest.mock as mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestLoadConfig:
    def test_returns_dict(self):
        from ui.llm_config_data import load_config
        config = load_config()
        assert isinstance(config, dict)

    def test_has_required_keys(self):
        from ui.llm_config_data import load_config
        config = load_config()
        assert 'active_provider' in config
        assert 'gemini_model' in config
        assert 'ollama_endpoint' in config

    def test_default_provider_is_valid(self):
        from ui.llm_config_data import load_config, PROVIDERS
        config = load_config()
        assert config['active_provider'] in PROVIDERS

    def test_env_var_overrides_file(self, tmp_path, monkeypatch):
        """环境���量中的 API Key 应覆盖文件中的值"""
        from ui import llm_config_data as lcs
        cfg_path = str(tmp_path / 'test_config.json')
        with open(cfg_path, 'w') as f:
            json.dump({'gemini_key': 'from_file'}, f)
        monkeypatch.setenv('GEMINI_API_KEY', 'from_env')
        original = lcs.CONFIG_FILE
        lcs.CONFIG_FILE = cfg_path
        try:
            config = lcs.load_config()
            assert config.get('gemini_key') == 'from_env'
        finally:
            lcs.CONFIG_FILE = original
            monkeypatch.delenv('GEMINI_API_KEY', raising=False)

    def test_missing_file_uses_defaults(self, tmp_path):
        from ui import llm_config_data as lcs
        original = lcs.CONFIG_FILE
        lcs.CONFIG_FILE = str(tmp_path / 'nonexistent.json')
        try:
            config = lcs.load_config()
            assert config['active_provider'] in lcs.PROVIDERS
        finally:
            lcs.CONFIG_FILE = original

    def test_endpoint_fields_default_empty(self):
        """所有自定义端点字段默认为空字符串"""
        from ui.llm_config_data import _DEFAULT_CONFIG
        endpoint_fields = [k for k in _DEFAULT_CONFIG if k.endswith('_endpoint')
                           and not k.startswith('ollama')]
        assert len(endpoint_fields) > 0
        for field in endpoint_fields:
            assert _DEFAULT_CONFIG[field] == '', f'{field} 默认值应为空字符串'


class TestSaveConfig:
    def test_saves_to_file(self, tmp_path):
        from ui import llm_config_data as lcs
        original = lcs.CONFIG_FILE
        lcs.CONFIG_FILE = str(tmp_path / 'config.json')
        try:
            config = {
                'active_provider': 'Gemini',
                'gemini_key': 'test_key_123',
                'gemini_model': 'gemini-2.5-flash',
            }
            lcs.save_config(config)
            assert os.path.exists(lcs.CONFIG_FILE)
            with open(lcs.CONFIG_FILE, 'r') as f:
                saved = json.load(f)
            assert saved['active_provider'] == 'Gemini'
            assert saved['gemini_key'] == 'test_key_123'
        finally:
            lcs.CONFIG_FILE = original

    def test_api_key_persisted(self, tmp_path):
        """API Key 应写入文件"""
        from ui import llm_config_data as lcs
        original = lcs.CONFIG_FILE
        lcs.CONFIG_FILE = str(tmp_path / 'config.json')
        try:
            lcs.save_config({'active_provider': 'OpenAI', 'openai_key': 'sk-test'})
            with open(lcs.CONFIG_FILE, 'r') as f:
                saved = json.load(f)
            assert saved.get('openai_key') == 'sk-test'
        finally:
            lcs.CONFIG_FILE = original

    def test_save_sets_env_var(self, tmp_path, monkeypatch):
        from ui import llm_config_data as lcs
        original = lcs.CONFIG_FILE
        lcs.CONFIG_FILE = str(tmp_path / 'config.json')
        monkeypatch.delenv('GEMINI_API_KEY', raising=False)
        try:
            lcs.save_config({'active_provider': 'Gemini', 'gemini_key': 'env_test_key'})
            assert os.environ.get('GEMINI_API_KEY') == 'env_test_key'
        finally:
            lcs.CONFIG_FILE = original
            monkeypatch.delenv('GEMINI_API_KEY', raising=False)

    def test_custom_endpoint_saved(self, tmp_path):
        """自定义端点字段应被持久化"""
        from ui import llm_config_data as lcs
        original = lcs.CONFIG_FILE
        lcs.CONFIG_FILE = str(tmp_path / 'config.json')
        try:
            lcs.save_config({
                'active_provider': 'OpenAI',
                'openai_key': 'sk-test',
                'openai_endpoint': 'https://my-proxy.com/v1/chat/completions',
            })
            with open(lcs.CONFIG_FILE, 'r') as f:
                saved = json.load(f)
            assert saved.get('openai_endpoint') == 'https://my-proxy.com/v1/chat/completions'
        finally:
            lcs.CONFIG_FILE = original


class TestProviders:
    def test_all_providers_defined(self):
        from ui.llm_config_data import PROVIDERS, _PROVIDER_FIELDS
        for prov in PROVIDERS:
            assert prov in _PROVIDER_FIELDS

    def test_provider_fields_structure(self):
        """每个供应商字段支持 3 元组或 4 元组（含 hint_text）"""
        from ui.llm_config_data import _PROVIDER_FIELDS
        for prov, fields in _PROVIDER_FIELDS.items():
            assert isinstance(fields, list)
            assert len(fields) >= 1
            for field_entry in fields:
                assert len(field_entry) in (3, 4), \
                    f'{prov} 字段应为 3 或 4 元组'
                field_key, label, is_secret = field_entry[0], field_entry[1], field_entry[2]
                assert isinstance(field_key, str)
                assert isinstance(label, str)
                assert isinstance(is_secret, bool)
                if len(field_entry) == 4:
                    assert isinstance(field_entry[3], str), 'hint_text 应为字符串'

    def test_all_default_models_present(self):
        from ui.llm_config_data import _DEFAULT_CONFIG
        assert 'gemini_model' in _DEFAULT_CONFIG
        assert 'openai_model' in _DEFAULT_CONFIG
        assert 'claude_model' in _DEFAULT_CONFIG
        assert 'deepseek_model' in _DEFAULT_CONFIG
        assert 'ollama_model' in _DEFAULT_CONFIG

    def test_cloud_providers_have_endpoint_fields(self):
        """云端供应商（非 Ollama）应在 _DEFAULT_CONFIG 中有对应端点字段"""
        from ui.llm_config_data import _DEFAULT_CONFIG, PROVIDERS
        cloud_providers = [p for p in PROVIDERS if p != 'Ollama']
        for prov in cloud_providers:
            endpoint_key = f'{prov.lower()}_endpoint'
            assert endpoint_key in _DEFAULT_CONFIG, \
                f'{prov} 缺少端点字段 {endpoint_key}'

    def test_endpoint_fields_in_provider_fields(self):
        """主要供应商（Gemini/OpenAI/Claude/DeepSeek）应在 _PROVIDER_FIELDS 中包含端点字段"""
        from ui.llm_config_data import _PROVIDER_FIELDS
        key_providers = ['Gemini', 'OpenAI', 'Claude', 'DeepSeek']
        for prov in key_providers:
            fields = _PROVIDER_FIELDS[prov]
            field_keys = [f[0] for f in fields]
            endpoint_key = f'{prov.lower()}_endpoint'
            assert endpoint_key in field_keys, \
                f'{prov} 的 _PROVIDER_FIELDS 中缺少端点字段 {endpoint_key}'

    def test_hint_text_present_for_key_fields(self):
        """API Key 字段应有 hint_text（格式提示）"""
        from ui.llm_config_data import _PROVIDER_FIELDS
        for prov, fields in _PROVIDER_FIELDS.items():
            for field_entry in fields:
                if len(field_entry) == 4 and field_entry[2]:  # is_secret=True
                    hint = field_entry[3]
                    assert len(hint) > 0, f'{prov} 的 API Key 字段缺少 hint_text'
