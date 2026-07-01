"""Resumable HTTP fetch-to-cache used by the motif sources.

Each URL is cached as a file under ``outputs/motifs/raw/``; a cached file is
returned without a network call unless ``force`` is set. This is what makes the
build cheap to re-run and safe to interrupt: pages already fetched are skipped.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def fetch_to_cache(url: str, cache_file: Path, *, force: bool = False,
                   auth: tuple[str, str] | None = None) -> bytes:
    """Return the bytes for ``url``, reading/writing ``cache_file``.

    A non-empty cached file short-circuits the request unless ``force``. ``auth`` is
    an optional ``(user, password)`` for HTTP basic auth (e.g. mapsofmyths.com).
    """
    if not force and cache_file.exists() and cache_file.stat().st_size > 0:
        return cache_file.read_bytes()

    from corpus.downloader import download_file  # lazy: requests lives in the corpus extra

    content = download_file(url, auth=auth)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_bytes(content)
    return content


def fetch_text(url: str, cache_file: Path, *, encoding: str = "utf-8", force: bool = False,
               auth: tuple[str, str] | None = None) -> str:
    return fetch_to_cache(url, cache_file, force=force, auth=auth).decode(encoding, errors="replace")
