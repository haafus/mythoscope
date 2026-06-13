import json

import numpy as np
import pytest

from embedding.embedding_cache import EmbeddingCache


class TestLoadSingle:
    def test_returns_array_when_both_files_exist(self, tmp_path):
        cache = EmbeddingCache(tmp_path, cache_batch_size=10)
        try:
            emb = np.array([1.0, 2.0, 3.0], dtype=np.float32)
            np.save(tmp_path / "abc123.npy", emb)
            with open(tmp_path / "abc123.json", "w") as f:
                json.dump({"text": "hello"}, f)

            result = cache._load_single("abc123")
            np.testing.assert_array_equal(result, emb)
        finally:
            cache.close()

    def test_returns_none_when_npy_missing(self, tmp_path):
        cache = EmbeddingCache(tmp_path, cache_batch_size=10)
        try:
            with open(tmp_path / "abc123.json", "w") as f:
                json.dump({"text": "hello"}, f)

            assert cache._load_single("abc123") is None
        finally:
            cache.close()

    def test_returns_none_when_json_missing(self, tmp_path):
        cache = EmbeddingCache(tmp_path, cache_batch_size=10)
        try:
            np.save(tmp_path / "abc123.npy", np.array([1.0]))
            assert cache._load_single("abc123") is None
        finally:
            cache.close()

    def test_returns_none_for_nonexistent_key(self, tmp_path):
        cache = EmbeddingCache(tmp_path, cache_batch_size=10)
        try:
            assert cache._load_single("nonexistent") is None
        finally:
            cache.close()


class TestBatchLoad:
    def test_loads_multiple_keys(self, tmp_path):
        cache = EmbeddingCache(tmp_path, cache_batch_size=10)
        try:
            for i in range(3):
                np.save(tmp_path / f"key{i}.npy", np.array([float(i)]))
                with open(tmp_path / f"key{i}.json", "w") as f:
                    json.dump({"i": i}, f)

            results = cache._batch_load(["key0", "key1", "key2"])
            assert len(results) == 3
            for i, r in enumerate(results):
                assert r is not None
                np.testing.assert_array_equal(r, np.array([float(i)]))
        finally:
            cache.close()

    def test_returns_none_for_missing(self, tmp_path):
        cache = EmbeddingCache(tmp_path, cache_batch_size=10)
        try:
            np.save(tmp_path / "exists.npy", np.array([1.0]))
            with open(tmp_path / "exists.json", "w") as f:
                json.dump({}, f)

            results = cache._batch_load(["exists", "missing"])
            assert results[0] is not None
            assert results[1] is None
        finally:
            cache.close()


class TestCacheDir:
    def test_creates_cache_dir(self, tmp_path):
        cache_dir = tmp_path / "new" / "nested" / "cache"
        cache = EmbeddingCache(cache_dir, cache_batch_size=10)
        try:
            assert cache_dir.exists()
        finally:
            cache.close()
