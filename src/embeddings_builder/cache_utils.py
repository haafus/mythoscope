import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


def get_cache_key(text: str, model_name: str, chunking_strategy: Any) -> str:
    key_str = (
        f"{text}|{model_name}|{chunking_strategy.name}|{chunking_strategy.chunk_size}|{chunking_strategy.chunk_overlap}"
    )
    return hashlib.md5(key_str.encode("utf-8")).hexdigest()


def save_to_cache(
    text: str, embedding: np.ndarray, model_name: str, chunking_strategy: Any, cache_dir: Path, key: str | None = None
) -> bool:
    try:
        if key is None:
            key = get_cache_key(text, model_name, chunking_strategy)
        cache_dir.mkdir(parents=True, exist_ok=True)
        np.save(cache_dir / f"{key}.npy", embedding)
        metadata = {
            "text": text,
            "model_name": model_name,
            "chunking_name": chunking_strategy.name,
            "chunk_size": chunking_strategy.chunk_size,
            "chunk_overlap": chunking_strategy.chunk_overlap,
        }
        with open(cache_dir / f"{key}.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Failed to save to cache: {e}")
        return False


def load_from_cache(
    text: str, model_name: str, chunking_strategy: Any, cache_dir: Path, key: str | None = None
) -> np.ndarray | None:
    try:
        if key is None:
            key = get_cache_key(text, model_name, chunking_strategy)
        npy_file = cache_dir / f"{key}.npy"
        json_file = cache_dir / f"{key}.json"

        if not npy_file.exists() or not json_file.exists():
            return None

        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)

        if (
            data.get("text") == text
            and data.get("model_name") == model_name
            and data.get("chunking_name") == chunking_strategy.name
        ):
            result: np.ndarray = np.load(npy_file)
            return result
        else:
            logger.warning(f"Cache mismatch for key: {key}")
            return None
    except Exception as e:
        logger.error(f"Failed to load from cache: {e}")
        return None


def cleanup_cache(cache_dir: Path, max_size_mb: int = 1024, ttl_days: int = 30) -> int:
    if not cache_dir.exists():
        return 0

    removed = 0
    current_time = datetime.now()
    cutoff_time = current_time - timedelta(days=ttl_days)
    total_size = 0

    for json_file in cache_dir.glob("*.json"):
        if json_file.name == ".checksums.json":
            continue
        npy_file = cache_dir / f"{json_file.stem}.npy"
        if not npy_file.exists():
            json_file.unlink()
            removed += 1
            logger.info(f"Removed orphaned cache JSON: {json_file.name}")

    cache_files = list(cache_dir.glob("*.npy"))
    for cache_file in cache_files:
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        json_file = cache_dir / f"{cache_file.stem}.json"

        if mtime < cutoff_time:
            cache_file.unlink()
            if json_file.exists():
                json_file.unlink()
            removed += 1
            logger.info(f"Removed expired cache: {cache_file.name}")
        else:
            total_size += cache_file.stat().st_size
            if json_file.exists():
                total_size += json_file.stat().st_size

    max_size_bytes = max_size_mb * 1024 * 1024
    if total_size > max_size_bytes:
        cache_files = sorted([f for f in cache_dir.glob("*.npy") if f.exists()], key=lambda f: f.stat().st_mtime)
        for cache_file in cache_files:
            if total_size <= max_size_bytes:
                break
            json_file = cache_dir / f"{cache_file.stem}.json"

            file_size = cache_file.stat().st_size
            cache_file.unlink()
            total_size -= file_size

            if json_file.exists():
                total_size -= json_file.stat().st_size
                json_file.unlink()

            removed += 1
            logger.info(f"Removed cache file to enforce size limit: {cache_file.name}")

    return removed
