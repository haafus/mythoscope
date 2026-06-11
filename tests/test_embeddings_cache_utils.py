from unittest.mock import MagicMock

from embeddings_builder.cache_utils import get_cache_key


class TestGetCacheKey:
    def _make_strategy(self, name="paragraph", chunk_size=1024, chunk_overlap=128):
        strategy = MagicMock()
        strategy.name = name
        strategy.chunk_size = chunk_size
        strategy.chunk_overlap = chunk_overlap
        return strategy

    def test_returns_string(self):
        key = get_cache_key("hello", "model-a", self._make_strategy())
        assert isinstance(key, str)
        assert len(key) > 0

    def test_deterministic(self):
        s = self._make_strategy()
        k1 = get_cache_key("text", "model", s)
        k2 = get_cache_key("text", "model", s)
        assert k1 == k2

    def test_different_text_different_key(self):
        s = self._make_strategy()
        k1 = get_cache_key("aaa", "model", s)
        k2 = get_cache_key("bbb", "model", s)
        assert k1 != k2

    def test_different_model_different_key(self):
        s = self._make_strategy()
        k1 = get_cache_key("text", "model-a", s)
        k2 = get_cache_key("text", "model-b", s)
        assert k1 != k2

    def test_different_strategy_different_key(self):
        k1 = get_cache_key("text", "model", self._make_strategy(name="sentence"))
        k2 = get_cache_key("text", "model", self._make_strategy(name="paragraph"))
        assert k1 != k2
