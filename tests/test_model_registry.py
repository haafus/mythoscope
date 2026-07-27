import pytest

from model_registry import (
    active_embedding_models,
    list_embedding_aliases,
    list_llm_providers,
    resolve_embedding_model,
    resolve_llm_provider,
)


class TestResolveEmbeddingModel:
    def test_resolves_alias(self):
        assert resolve_embedding_model("bge-m3") == "BAAI/bge-m3"

    def test_passes_through_full_name(self):
        assert resolve_embedding_model("BAAI/bge-m3") == "BAAI/bge-m3"

    def test_passes_through_unknown(self):
        assert resolve_embedding_model("some/unknown-model") == "some/unknown-model"


class TestResolveLLMProvider:
    def test_resolves_known_provider(self):
        result = resolve_llm_provider("gpt4o-mini")
        assert result["model"] == "gpt-4o-mini"
        assert "openai" in result["base_url"]

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="not found"):
            resolve_llm_provider("nonexistent-model")


class TestListFunctions:
    def test_list_llm_providers_returns_active_only(self):
        providers = list_llm_providers()
        assert "gpt4o-mini" in providers
        assert "gemini25-flash" in providers
        assert "qwen3-8b" not in providers

    def test_inactive_llm_raises(self):
        with pytest.raises(ValueError, match="not found"):
            resolve_llm_provider("qwen3-8b")

    def test_list_embedding_aliases(self):
        aliases = list_embedding_aliases()
        # Only bge-m3 is active (config/models.json); labse et al. are inactive.
        assert aliases["bge-m3"] == "BAAI/bge-m3"
        assert "labse" not in aliases

    def test_active_embedding_models(self):
        models = active_embedding_models()
        assert models == ["BAAI/bge-m3"]

    def test_inactive_embedding_passes_through(self):
        # Inactive aliases are not resolved — they pass through unchanged.
        assert resolve_embedding_model("labse") == "labse"
        assert resolve_embedding_model("qwen-4b") == "qwen-4b"
        assert resolve_embedding_model("story-emb") == "story-emb"
