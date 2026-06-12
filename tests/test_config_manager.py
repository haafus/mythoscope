from embedding.config_manager import ConfigManager


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

    def test_merge_config(self):
        mgr = ConfigManager(config_path=None)
        mgr._merge_config(mgr._config, {"embedding": {"batch_size": 999}})
        assert mgr.get("embedding.batch_size") == 999

    def test_load_yaml(self, tmp_path):
        cfg = tmp_path / "test.yaml"
        cfg.write_text("embedding:\n  batch_size: 64\n")
        mgr = ConfigManager(config_path=str(cfg))
        assert mgr.get("embedding.batch_size") == 64

    def test_load_json(self, tmp_path):
        cfg = tmp_path / "test.json"
        cfg.write_text('{"embedding": {"batch_size": 128}}')
        mgr = ConfigManager(config_path=str(cfg))
        assert mgr.get("embedding.batch_size") == 128

    def test_defaults_preserved_after_partial_load(self, tmp_path):
        cfg = tmp_path / "partial.yaml"
        cfg.write_text("embedding:\n  batch_size: 16\n")
        mgr = ConfigManager(config_path=str(cfg))
        assert mgr.get("embedding.batch_size") == 16
        assert mgr.get("embedding.text_type") == "all"
        assert mgr.get("paths.corpus_dir") is not None
