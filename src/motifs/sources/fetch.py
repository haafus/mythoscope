"""Motif-source view onto the shared fetch-to-cache (see top-level ``fetch_cache``).

Kept as a thin re-export so the sources can ``from .fetch import fetch_text`` while
the one caching implementation is shared with the corpus downloader.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from fetch_cache import (  # noqa: F401
    FetchRejected,
    cache_path,
    fetch_text,
    fetch_to_cache,
    read_pinned,
)
from settings import settings

from ..refresh import Fetchable


def raw_dir() -> Path:
    return Path(settings.motifs_dir) / "raw"


def walk_fetchables(subdir: str, base: str, *, exclude: set[str] = frozenset(),
                    auth: tuple[str, str] | None = None,
                    validate: Callable[[bytes], bool] | None = None) -> list[Fetchable]:
    """Enumerate a flat scraped dir: every pinned file under ``raw/<subdir>`` → a Fetchable at
    ``base/<name>`` (the tail rule). ``.absent`` known-404 markers and ``exclude`` names are
    skipped. Used by the fan-out sources whose page set *is* whatever they have pinned."""
    root = raw_dir() / subdir
    if not root.exists():
        return []
    out = []
    for f in sorted(p for p in root.iterdir() if p.is_file()):
        if f.name in exclude or f.name.endswith(".absent"):
            continue
        out.append(Fetchable(f"{subdir}/{f.name}", f"{base.rstrip('/')}/{f.name}", f,
                             auth=auth, validate=validate))
    return out
