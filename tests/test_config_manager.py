from embedding.config_manager import EmbeddingConfig, load_embedding_config


class TestEmbeddingConfig:
    def test_defaults_have_paths(self):
        cfg = EmbeddingConfig()
        assert cfg.corpus_dir
        assert cfg.out_dir
        assert cfg.chroma_path
        assert cfg.cache_dir
        assert cfg.chunked_dir

    def test_defaults_have_embedding_params(self):
        cfg = EmbeddingConfig()
        assert cfg.default_model
        assert cfg.default_chunking
        assert cfg.text_type == "all"
        assert cfg.batch_size == 32

    def test_override_via_constructor(self):
        cfg = EmbeddingConfig(batch_size=64, text_type="original")
        assert cfg.batch_size == 64
        assert cfg.text_type == "original"

    def test_models_defaults_to_empty(self):
        cfg = EmbeddingConfig()
        assert cfg.models == []

    def test_cache_defaults(self):
        cfg = EmbeddingConfig()
        assert cfg.max_size_mb == 1024
        assert cfg.ttl_days == 30

    def test_metrics_file_default(self):
        cfg = EmbeddingConfig()
        assert "performance_metrics" in cfg.metrics_file


class TestLoadEmbeddingConfig:
    def test_load_from_yaml(self, tmp_path):
        cfg_file = tmp_path / "test.yaml"
        cfg_file.write_text("embedding:\n  batch_size: 128\n  text_type: original\n")
        cfg = load_embedding_config(str(cfg_file))
        assert cfg.batch_size == 128
        assert cfg.text_type == "original"

    def test_defaults_preserved_on_partial_load(self, tmp_path):
        cfg_file = tmp_path / "partial.yaml"
        cfg_file.write_text("embedding:\n  batch_size: 16\n")
        cfg = load_embedding_config(str(cfg_file))
        assert cfg.batch_size == 16
        assert cfg.text_type == "all"
        assert cfg.cache_batch_size == 50

    def test_cache_section_loaded(self, tmp_path):
        cfg_file = tmp_path / "cache.yaml"
        cfg_file.write_text("cache:\n  max_size_mb: 512\n  ttl_days: 7\n")
        cfg = load_embedding_config(str(cfg_file))
        assert cfg.max_size_mb == 512
        assert cfg.ttl_days == 7

    def test_missing_file_returns_defaults(self):
        cfg = load_embedding_config("/nonexistent/path.yaml")
        assert cfg.batch_size == 32
        assert cfg.text_type == "all"
