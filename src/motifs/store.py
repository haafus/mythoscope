"""Filesystem layout for the motif database and read helpers.

The build step writes per-index JSON plus a cross-walk and a meta manifest; the
server reads them back. Read helpers cache parsed JSON in module state so the
(potentially large) files are loaded at most once per process.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

from json_utils import load_json_optional
from settings import settings

logger = logging.getLogger(__name__)

# Committed data shipped with the package (precomputed artefacts that are expensive
# to regenerate, e.g. the BGE-M3 semantic parallels). Copied into the (git-ignored)
# outputs dir on first read so the running app needs neither the model nor its deps.
DATA_DIR = Path(__file__).resolve().parent / "data"


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
PARALLELS_FILE = "parallels.json"
SEMANTIC_PARALLELS_FILE = "semantic_parallels.json"
META_FILE = "meta.json"


def index_path(index: str) -> Path:
    return motifs_dir() / INDEX_FILES[index]


def crosswalk_path() -> Path:
    return motifs_dir() / CROSSWALK_FILE


def parallels_path() -> Path:
    return motifs_dir() / PARALLELS_FILE


def semantic_parallels_path() -> Path:
    return motifs_dir() / SEMANTIC_PARALLELS_FILE


def meta_path() -> Path:
    return motifs_dir() / META_FILE


def enrichment_path(source: str) -> Path:
    """Per-source enrichment summary sidecar (skip status + counts) — the meta aggregator reads
    these instead of the monolith's in-memory dict once the sources are separate stages."""
    return motifs_dir() / f"{source}.enrichment.json"


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


def cached(key: str, factory) -> Any:
    """Memoize a derived value in the per-process cache (reset by ``clear_cache``)."""
    if key not in _cache:
        _cache[key] = factory()
    return _cache[key]


def load_index(index: str) -> dict | None:
    """Load one index file (``{"motifs"/"types": [...], ...}``) or None."""
    if index not in INDEX_FILES:
        return None
    return _load_cached(f"index:{index}", index_path(index))


def load_crosswalk() -> dict:
    return _load_cached("crosswalk", crosswalk_path()) or {}


def load_parallels() -> dict:
    return _load_cached("parallels", parallels_path()) or {}


def load_semantic_parallels() -> dict:
    dst = semantic_parallels_path()
    if not dst.exists():
        src = DATA_DIR / SEMANTIC_PARALLELS_FILE   # committed precomputed copy
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            logger.info("Copied committed %s into %s", SEMANTIC_PARALLELS_FILE, dst.parent)
    return _load_cached("semantic_parallels", dst) or {}


def copy_semantic_parallels() -> dict | None:
    """Copy the committed precomputed semantic-parallels file into outputs (always, so
    a build serves the current version) and return its contents, or ``None`` if the
    committed file is absent. Unlike ``load_semantic_parallels`` this is unconditional."""
    src = DATA_DIR / SEMANTIC_PARALLELS_FILE
    if not src.exists():
        return None
    dst = semantic_parallels_path()
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return load_json_optional(dst) or {}


def load_meta() -> dict:
    return _load_cached("meta", meta_path()) or {}


def is_built() -> bool:
    return meta_path().exists()
