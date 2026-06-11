from importlib import import_module

ConfigManager = import_module("02_embed.config_manager").ConfigManager


class TestConfigManager:
    def test_default_config_has_paths(self):
        mgr = ConfigManager(config_path=None)
        assert mgr.get("paths.corpus_dir") is not None
        assert mgr.get("paths.out_dir") is not None

    def test_get_nested_key(self):
        mgr = ConfigManager(config_path=None)
        assert mgr.get("embedding.default_chunking") is not None

    def test_get_missing_key_returns_default(self):
        mgr = ConfigManager(config_path=None)
        assert mgr.get("nonexistent.key", "fallback") == "fallback"

    def test_set_and_get(self):
        mgr = ConfigManager(config_path=None)
        mgr.set("custom.key", "value123")
        assert mgr.get("custom.key") == "value123"

    def test_set_nested(self):
        mgr = ConfigManager(config_path=None)
        mgr.set("a.b.c", 42)
        assert mgr.get("a.b.c") == 42

    def test_get_all(self):
        mgr = ConfigManager(config_path=None)
        all_config = mgr.get_all()
        assert isinstance(all_config, dict)
        assert "paths" in all_config
        assert "embedding" in all_config

    def test_validate_returns_list(self):
        mgr = ConfigManager(config_path=None)
        issues = mgr.validate()
        assert isinstance(issues, list)

    def test_save_and_load_yaml(self, tmp_path):
        mgr = ConfigManager(config_path=None)
        mgr.set("test_key", "test_value")
        save_path = str(tmp_path / "config.yaml")
        mgr.save(save_path)

        mgr2 = ConfigManager(config_path=save_path)
        assert mgr2.get("test_key") == "test_value"

    def test_save_and_load_json(self, tmp_path):
        mgr = ConfigManager(config_path=None)
        mgr.set("test_key", "json_value")
        save_path = str(tmp_path / "config.json")
        mgr.save(save_path)

        mgr2 = ConfigManager(config_path=save_path)
        assert mgr2.get("test_key") == "json_value"

    def test_merge_config(self):
        mgr = ConfigManager(config_path=None)
        mgr._merge_config(mgr._config, {"embedding": {"batch_size": 999}})
        assert mgr.get("embedding.batch_size") == 999
