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
        """环境变量中的 API Key 应覆盖文件中的值"""
        from ui import llm_config_data as lcs
        # 创建一个临时配置文件
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
        """API Key 现在应该写入文件（不再只存在 env vars）"""
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


class TestProviders:
    def test_all_providers_defined(self):
        from ui.llm_config_data import PROVIDERS, _PROVIDER_FIELDS
        for prov in PROVIDERS:
            assert prov in _PROVIDER_FIELDS

    def test_provider_fields_structure(self):
        from ui.llm_config_data import _PROVIDER_FIELDS
        for prov, fields in _PROVIDER_FIELDS.items():
            assert isinstance(fields, list)
            assert len(fields) >= 1
            for field_key, label, is_secret in fields:
                assert isinstance(field_key, str)
                assert isinstance(label, str)
                assert isinstance(is_secret, bool)

    def test_all_default_models_present(self):
        from ui.llm_config_data import _DEFAULT_CONFIG
        assert 'gemini_model' in _DEFAULT_CONFIG
        assert 'openai_model' in _DEFAULT_CONFIG
        assert 'claude_model' in _DEFAULT_CONFIG
        assert 'deepseek_model' in _DEFAULT_CONFIG
        assert 'ollama_model' in _DEFAULT_CONFIG
