import hashlib
import pickle
from pathlib import Path
from typing import Optional

import numpy as np

from .chunking import ChunkingStrategy


def _get_cache_key(text: str, model_name: str, chunking: ChunkingStrategy) -> str:
    key_str = f"{text}|{model_name}|{chunking.name}|{chunking.chunk_size}|{chunking.chunk_overlap}"
    return hashlib.md5(key_str.encode('utf-8')).hexdigest()


def load_from_cache(text: str, model_name: str, chunking: ChunkingStrategy, cache_dir: Path) -> Optional[np.ndarray]:
    cache_key = _get_cache_key(text, model_name, chunking)
    cache_file = cache_dir / f"{cache_key}.pkl"
    if cache_file.exists():
        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except (pickle.UnpicklingError, EOFError):
            cache_file.unlink()
    return None


def save_to_cache(text: str, embeddings: np.ndarray, model_name: str, chunking: ChunkingStrategy, cache_dir: Path):
    cache_key = _get_cache_key(text, model_name, chunking)
    cache_file = cache_dir / f"{cache_key}.pkl"
    with open(cache_file, 'wb') as f:
        pickle.dump(embeddings, f)