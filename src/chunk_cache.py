"""Content-addressed per-chunk cache (JSONL).

Resume is keyed by the hash of the chunk text, so it is order-independent and
robust to re-chunking. Each step keeps its own cache file (graphs and motif use
different chunks) — only the mechanism is shared, not the data.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def chunk_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def load_cache(path: Path) -> dict[str, Any]:
    """Read the cache into {hash: value}, skipping a torn final line after a crash."""
    cache: dict[str, Any] = {}
    if not path.exists():
        return cache
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as e:
        logger.warning("Could not read cache %s: %s", path, e)
        return cache
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
            cache[record["hash"]] = record["value"]
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
    return cache


def append_cache(path: Path, key: str, value: Any) -> None:
    """Append one chunk result as a JSON line (O(1), survives partial last line)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"hash": key, "value": value}, ensure_ascii=False) + "\n")


def clear_cache(path: Path) -> None:
    path.unlink(missing_ok=True)
