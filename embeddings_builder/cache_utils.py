import pickle
import hashlib
import logging
from pathlib import Path
from typing import Optional, Any
import numpy as np

logger = logging.getLogger(__name__)


def get_cache_key(text: str, model_name: str, chunking_strategy: Any) -> str:
    """Generate cache key for text and parameters"""
    key_str = f"{text}|{model_name}|{chunking_strategy.name}|{chunking_strategy.chunk_size}|{chunking_strategy.chunk_overlap}"
    return hashlib.md5(key_str.encode('utf-8')).hexdigest()


def save_to_cache(
        text: str,
        embedding: np.ndarray,
        model_name: str,
        chunking_strategy: Any,
        cache_dir: Path,
        key: Optional[str] = None
) -> bool:
    """Save embedding to cache"""
    try:
        if key is None:
            key = get_cache_key(text, model_name, chunking_strategy)

        cache_file = cache_dir / f"{key}.pkl"
        cache_dir.mkdir(parents=True, exist_ok=True)

        with open(cache_file, 'wb') as f:
            pickle.dump({
                'embedding': embedding,
                'text': text,
                'model_name': model_name,
                'chunking_name': chunking_strategy.name,
                'chunk_size': chunking_strategy.chunk_size,
                'chunk_overlap': chunking_strategy.chunk_overlap
            }, f, protocol=pickle.HIGHEST_PROTOCOL)

        return True
    except Exception as e:
        logger.error(f"Failed to save to cache: {e}")
        return False


def load_from_cache(
        text: str,
        model_name: str,
        chunking_strategy: Any,
        cache_dir: Path,
        key: Optional[str] = None
) -> Optional[np.ndarray]:
    """Load embedding from cache"""
    try:
        if key is None:
            key = get_cache_key(text, model_name, chunking_strategy)

        cache_file = cache_dir / f"{key}.pkl"

        if not cache_file.exists():
            return None

        with open(cache_file, 'rb') as f:
            data = pickle.load(f)

        # Validate cache integrity
        if (data['text'] == text and
                data['model_name'] == model_name and
                data['chunking_name'] == chunking_strategy.name):
            return data['embedding']
        else:
            logger.warning(f"Cache mismatch for key: {key}")
            return None
    except Exception as e:
        logger.error(f"Failed to load from cache: {e}")
        return None


def cleanup_cache(cache_dir: Path, max_size_mb: int = 1024, ttl_days: int = 30) -> int:
    """Clean old cache files and enforce size limit"""
    from datetime import datetime, timedelta

    if not cache_dir.exists():
        return 0

    removed = 0
    current_time = datetime.now()
    cutoff_time = current_time - timedelta(days=ttl_days)
    total_size = 0

    # First pass: remove expired files and calculate total size
    cache_files = list(cache_dir.glob("*.pkl"))

    for cache_file in cache_files:
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        if mtime < cutoff_time:
            cache_file.unlink()
            removed += 1
            logger.info(f"Removed expired cache: {cache_file.name}")
        else:
            total_size += cache_file.stat().st_size

    # Second pass: remove oldest files if exceeding size limit
    max_size_bytes = max_size_mb * 1024 * 1024
    if total_size > max_size_bytes:
        # Sort by modification time (oldest first)
        cache_files = sorted(
            [f for f in cache_dir.glob("*.pkl") if f.exists()],
            key=lambda f: f.stat().st_mtime
        )

        for cache_file in cache_files:
            if total_size <= max_size_bytes:
                break
            file_size = cache_file.stat().st_size
            cache_file.unlink()
            total_size -= file_size
            removed += 1
            logger.info(f"Removed cache file to enforce size limit: {cache_file.name}")

    return removed