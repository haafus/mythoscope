"""Shared resumable HTTP fetch-to-cache — the single caching layer for every remote
fetch in the project (both the motif sources and the corpus downloader).

Each URL is cached as a file; a non-empty cached file short-circuits the request
unless ``force``. This is what makes the builds cheap to re-run and safe to
interrupt: pages already fetched are reused, and a text that failed *processing*
last time is not re-fetched. The actual download lives in ``corpus.downloader``
(which owns ``requests``); it is imported lazily so importing this module doesn't
require the corpus HTTP extra.
"""

from __future__ import annotations

import hashlib
from pathlib import Path


def cache_path(base_dir: str | Path, url: str) -> Path:
    """A stable cache file for ``url`` under ``base_dir`` (hashed, so any URL is a
    safe filename). Use when there is no natural per-page name to key on."""
    return Path(base_dir) / hashlib.sha1(url.encode("utf-8")).hexdigest()


def fetch_to_cache(url: str, cache_file: str | Path, *, force: bool = False,
                   auth: tuple[str, str] | None = None) -> bytes:
    """Return the bytes for ``url``, reading/writing ``cache_file``.

    A non-empty cached file short-circuits the request unless ``force``. ``auth`` is
    an optional ``(user, password)`` for HTTP basic auth (e.g. mapsofmyths.com).
    """
    cache_file = Path(cache_file)
    if not force and cache_file.exists() and cache_file.stat().st_size > 0:
        return cache_file.read_bytes()

    from corpus.downloader import download_file  # lazy: requests lives in the corpus extra

    content = download_file(url, auth=auth)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_bytes(content)
    return content


def fetch_text(url: str, cache_file: str | Path, *, encoding: str = "utf-8",
               force: bool = False, auth: tuple[str, str] | None = None) -> str:
    return fetch_to_cache(url, cache_file, force=force, auth=auth).decode(encoding, errors="replace")
