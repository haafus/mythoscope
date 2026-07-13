from model_registry import embedding_config, humanize_label, model_name_for_key, valid_key


class TestModelNameForKey:
    def test_active_variant(self):
        assert model_name_for_key("bge-m3") == "BAAI/bge-m3"

    def test_inactive_variant(self):
        assert model_name_for_key("qwen-4b") == "Qwen/Qwen3-Embedding-4B"

    def test_unknown_key_returns_key(self):
        assert model_name_for_key("unknown-model") == "unknown-model"


class TestEmbeddingConfig:
    def test_plain_variant(self):
        cfg = embedding_config("bge-m3")
        assert cfg["key"] == "bge-m3"
        assert cfg["model"] == "BAAI/bge-m3"
        assert cfg["preprocess_prompt"] is None
        assert cfg["query_prefix"] == ""

    def test_preprocess_variant(self):
        cfg = embedding_config("bge-m3-summary")
        assert cfg["key"] == "bge-m3-summary"
        assert cfg["model"] == "BAAI/bge-m3"
        assert cfg["preprocess_prompt"] == "summary"
        assert cfg["label"] == "BGE-M3 · summary"

    def test_inline_prefix_present(self):
        assert embedding_config("story-emb")["query_prefix"].startswith("Instruct:")

    def test_label_generated_when_absent(self):
        assert embedding_config("bge-m3")["label"] == "Bge · M3"


class TestKeyHelpers:
    def test_humanize(self):
        assert humanize_label("bge-m3-summary") == "Bge · M3 · Summary"

    def test_valid_key(self):
        assert valid_key("bge-m3-summary")
        assert not valid_key("BGE/M3")
        assert not valid_key("ab")
