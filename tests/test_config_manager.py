from settings import EmbeddingSettings, settings


class TestEmbeddingSettings:
    def test_defaults_have_embedding_params(self):
        emb = settings.embedding
        assert emb.chunk_size == 1024
        assert emb.chunk_overlap == 128
        assert emb.batch_size == 32

    def test_override_via_constructor(self):
        emb = EmbeddingSettings(batch_size=64)
        assert emb.batch_size == 64
