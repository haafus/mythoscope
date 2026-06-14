import pytest

pytest.importorskip("torch")

from embedding.builder import normalize_text_type
from embedding.model_manager import BATCH_SIZE_THRESHOLDS, DEFAULT_BATCH_SIZE, get_optimal_batch_size


class TestGetOptimalBatchSize:
    def test_large_dim_returns_smallest_batch(self):
        assert get_optimal_batch_size(4096) == 8

    def test_medium_dim(self):
        assert get_optimal_batch_size(1024) == 16

    def test_small_dim_returns_default(self):
        assert get_optimal_batch_size(128) == DEFAULT_BATCH_SIZE

    def test_exact_threshold_boundary(self):
        for min_dim, expected_batch in BATCH_SIZE_THRESHOLDS:
            assert get_optimal_batch_size(min_dim) == expected_batch

    def test_one_below_threshold(self):
        assert get_optimal_batch_size(767) == 24


class TestNormalizeTextType:
    def test_both_becomes_all(self):
        assert normalize_text_type("both") == "all"

    def test_translation_becomes_translate(self):
        assert normalize_text_type("translation") == "translate"

    def test_passthrough(self):
        assert normalize_text_type("original") == "original"
        assert normalize_text_type("translate") == "translate"

    def test_none_returns_none(self):
        assert normalize_text_type(None) is None
