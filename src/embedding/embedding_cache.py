import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np

from .cache_utils import get_cache_key, save_to_cache

logger = logging.getLogger(__name__)


class EmbeddingCache:
    def __init__(self, cache_dir: Path, cache_batch_size: int = 50, executor: ThreadPoolExecutor | None = None):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_batch_size = cache_batch_size
        self._owns_executor = executor is None
        self._executor = executor or ThreadPoolExecutor(max_workers=16)

    def _get_cache_key(self, text: str, model_name: str, chunking_strategy: Any) -> str:
        return get_cache_key(text, model_name, chunking_strategy)

    def _load_single(self, key: str) -> np.ndarray | None:
        cache_npy = self.cache_dir / f"{key}.npy"
        cache_json = self.cache_dir / f"{key}.json"
        if cache_npy.exists() and cache_json.exists():
            try:
                return np.load(cache_npy)
            except Exception:
                return None
        return None

    def _batch_load(self, cache_keys: list[str]) -> list[np.ndarray | None]:
        futures = [self._executor.submit(self._load_single, key) for key in cache_keys]
        return [f.result() for f in futures]

    def generate_embeddings(
        self,
        sentences: list[str],
        model: Any,
        model_name: str,
        model_dim: int,
        batch_size: int,
        chunking_strategy: Any,
        metrics: Any,
    ) -> np.ndarray:
        if not sentences:
            return np.array([])

        with metrics.track("generate_embeddings"):
            final_embeddings = np.empty((len(sentences), model_dim), dtype=np.float32)
            to_compute_indices: list[int] = []
            to_compute_text: list[str] = []

            for i in range(0, len(sentences), self.cache_batch_size):
                batch = sentences[i : i + self.cache_batch_size]
                cache_keys = [self._get_cache_key(text, model_name, chunking_strategy) for text in batch]
                cached = self._batch_load(cache_keys)

                for j, (text, emb) in enumerate(zip(batch, cached, strict=False)):
                    global_idx = i + j
                    if emb is not None:
                        final_embeddings[global_idx] = emb
                    else:
                        to_compute_indices.append(global_idx)
                        to_compute_text.append(text)

            if to_compute_text:
                for k in range(0, len(to_compute_text), batch_size):
                    batch_text = to_compute_text[k : k + batch_size]
                    batch_indices = to_compute_indices[k : k + batch_size]

                    computed = model.encode(
                        batch_text, batch_size=len(batch_text), show_progress_bar=False, normalize_embeddings=True
                    )

                    for idx, text, emb in zip(batch_indices, batch_text, computed, strict=False):
                        final_embeddings[idx] = emb
                        save_to_cache(text, emb, model_name, chunking_strategy, self.cache_dir)

            return final_embeddings

    def close(self) -> None:
        if self._owns_executor:
            self._executor.shutdown(wait=True, cancel_futures=True)
