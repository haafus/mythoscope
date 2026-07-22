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
import os
import tempfile
from collections.abc import Callable
from pathlib import Path


class FetchRejected(Exception):
    """A freshly-downloaded response failed ``validate`` — so it was **not** committed
    to the cache (the live copy, if any, is left untouched). Distinct from a transport
    error: the bytes arrived but are unhealthy. The caller decides whether to serve a
    pinned copy or skip."""


def cache_path(base_dir: str | Path, url: str) -> Path:
    """A stable cache file for ``url`` under ``base_dir`` (hashed, so any URL is a
    safe filename). Use when there is no natural per-page name to key on."""
    return Path(base_dir) / hashlib.sha1(url.encode("utf-8")).hexdigest()


def commit_bytes(cache_file: str | Path, content: bytes) -> None:
    """Atomically write ``content`` to ``cache_file`` (validate-before-commit staging):
    stage to a UNIQUE ``.partial`` sibling, then ``os.replace``. A crash mid-write leaves
    only an inert ``.partial``, never a half-written live file. Shared by the fetch layer
    and ``refresh`` so both adopt bytes the same atomic way (fetch-and-refresh §3)."""
    cache_file = Path(cache_file)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=cache_file.parent, prefix=cache_file.name + ".", suffix=".partial")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content)
        os.replace(tmp, cache_file)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def read_pinned(cache_file: str | Path, *, encoding: str = "utf-8") -> str | None:
    """The pinned cached **text** if a non-empty copy exists, else ``None``. The shared
    serve-pinned primitive: when a fresh fetch is rejected or unavailable, a source falls
    back to the last good copy through this one place (same existence + encoding rule)."""
    cache_file = Path(cache_file)
    if cache_file.exists() and cache_file.stat().st_size > 0:
        return cache_file.read_text(encoding=encoding, errors="replace")
    return None


def fetch_to_cache(url: str, cache_file: str | Path, *, force: bool = False,
                   auth: tuple[str, str] | None = None,
                   validate: Callable[[bytes], bool] | None = None) -> bytes:
    """Return the bytes for ``url``, reading/writing ``cache_file``.

    A non-empty cached file short-circuits the request unless ``force``. ``auth`` is
    an optional ``(user, password)`` for HTTP basic auth (e.g. mapsofmyths.com).

    **Validate before commit.** When ``validate`` is given it runs on the freshly
    downloaded bytes *before* they touch the live cache: if it returns falsy the bytes
    are discarded and :class:`FetchRejected` is raised — the live copy is never
    overwritten with an unhealthy reply. The write itself is atomic (staged to a
    ``.partial`` sibling, then ``os.replace``), so a crash mid-write can never leave a
    half-written cache. A *transport* failure (``download_file`` raising) propagates
    unchanged — it happens before any write, so the live copy is likewise untouched.
    """
    cache_file = Path(cache_file)
    if not force and cache_file.exists() and cache_file.stat().st_size > 0:
        return cache_file.read_bytes()

    from corpus.downloader import download_file  # lazy: requests lives in the corpus extra

    content = download_file(url, auth=auth)      # transport failure raises here — never touches the cache
    if validate is not None and not validate(content):
        raise FetchRejected(url)                 # unhealthy reply: do not commit, keep the live copy

    # Stage to a UNIQUE temp in the same dir (so concurrent fetches of the same URL never
    # share a staging path), then os.replace atomically. `.partial` keeps it out of exports.
    commit_bytes(cache_file, content)
    return content


def fetch_text(url: str, cache_file: str | Path, *, encoding: str = "utf-8",
               force: bool = False, auth: tuple[str, str] | None = None,
               validate: Callable[[bytes], bool] | None = None) -> str:
    return fetch_to_cache(url, cache_file, force=force, auth=auth,
                          validate=validate).decode(encoding, errors="replace")
