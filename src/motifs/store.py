"""Filesystem layout for the motif database and read helpers.

The build step writes per-index JSON plus a cross-walk and a meta manifest; the
server reads them back. Read helpers cache parsed JSON in module state so the
(potentially large) files are loaded at most once per process.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from json_utils import load_json_optional
from settings import settings

logger = logging.getLogger(__name__)


def motifs_dir() -> Path:
    return Path(settings.motifs_dir)


def raw_dir() -> Path:
    return motifs_dir() / "raw"


# Output file for each index plus the cross-walk and manifest.
INDEX_FILES = {
    "berezkin": "berezkin.json",
    "tmi": "tmi.json",
    "atu": "atu.json",
}
CROSSWALK_FILE = "crosswalk.json"
META_FILE = "meta.json"


def index_path(index: str) -> Path:
    return motifs_dir() / INDEX_FILES[index]


def crosswalk_path() -> Path:
    return motifs_dir() / CROSSWALK_FILE


def meta_path() -> Path:
    return motifs_dir() / META_FILE


# ---------------------------------------------------------------------------
# Read side (server) — cached per process
# ---------------------------------------------------------------------------

_cache: dict[str, Any] = {}


def clear_cache() -> None:
    _cache.clear()


def _load_cached(key: str, path: Path) -> Any:
    if key not in _cache:
        _cache[key] = load_json_optional(path)
    return _cache[key]


def load_index(index: str) -> dict | None:
    """Load one index file (``{"motifs"/"types": [...], ...}``) or None."""
    if index not in INDEX_FILES:
        return None
    return _load_cached(f"index:{index}", index_path(index))


def load_crosswalk() -> dict:
    return _load_cached("crosswalk", crosswalk_path()) or {}


def load_meta() -> dict:
    return _load_cached("meta", meta_path()) or {}


def is_built() -> bool:
    return meta_path().exists()
