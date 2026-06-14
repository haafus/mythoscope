from settings import EmbeddingSettings, settings


class TestEmbeddingSettings:
    def test_defaults_have_embedding_params(self):
        emb = settings.embedding
        assert emb.models
        assert emb.default_chunking
        assert emb.batch_size == 32

    def test_override_via_constructor(self):
        emb = EmbeddingSettings(batch_size=64)
        assert emb.batch_size == 64

    def test_models_defaults(self):
        emb = EmbeddingSettings()
        assert len(emb.models) == 5
        assert "BAAI/bge-m3" in emb.models

    def test_metrics_file_default(self):
        emb = EmbeddingSettings()
        assert "performance_metrics" in emb.metrics_file

    def test_settings_embedding_is_embedding_settings(self):
        assert isinstance(settings.embedding, EmbeddingSettings)
