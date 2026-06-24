"""Unit tests for EmbeddingEncoder model loading (cache-first behavior)."""

from embeddings import model_manager
from embeddings.model_manager import EmbeddingEncoder


class _FakeModel:
    device = "cpu"


def _patch(monkeypatch, loader):
    monkeypatch.setattr(model_manager, "resolve_embedding_model", lambda n: n)
    monkeypatch.setattr(model_manager, "SentenceTransformer", loader)


def test_load_uses_cache_without_network(monkeypatch):
    """A cached model loads with local_files_only=True and never hits the network."""
    calls = []

    def loader(name, **kwargs):
        calls.append(kwargs.get("local_files_only", False))
        return _FakeModel()

    _patch(monkeypatch, loader)
    EmbeddingEncoder().load("cached-model")

    assert calls == [True]  # only the cache-only attempt, no network fallback


def test_load_falls_back_to_hub_when_not_cached(monkeypatch):
    """If the cache-only attempt raises OSError, fall back to a normal load."""
    calls = []

    def loader(name, **kwargs):
        local_only = kwargs.get("local_files_only", False)
        calls.append(local_only)
        if local_only:
            raise OSError("model not found in cache")
        return _FakeModel()

    _patch(monkeypatch, loader)
    EmbeddingEncoder().load("uncached-model")

    assert calls == [True, False]  # tried cache first, then downloaded
