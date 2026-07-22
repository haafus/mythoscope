"""Motif-source view onto the shared fetch-to-cache (see top-level ``fetch_cache``).

Kept as a thin re-export so the sources can ``from .fetch import fetch_text`` while
the one caching implementation is shared with the corpus downloader.
"""

from __future__ import annotations

from fetch_cache import (  # noqa: F401
    FetchRejected,
    cache_path,
    fetch_text,
    fetch_to_cache,
    read_pinned,
)
