"""Document identity — `document_id = blake2b(normalize(locator))` (D1, data-model §5).

The id anchors on the document's upstream **locator** (its URL or `sources/` path), not its
title or content, so it survives a rename *and* a text edit. The normalization pass folds
only cosmetic edits to the locator (RFC-3986 case/percent/port/fragment rules) — it never
merges two genuinely distinct sources — and is **frozen once ids are minted** (changing it
is a migration, not a hot edit). This same value is the raw-archive key after the §6 re-key.
"""

from __future__ import annotations

import posixpath
import re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from .utils import content_fingerprint

# RFC-3986 unreserved set: %-encodings of these decode to the same document (%7E ≡ ~).
_UNRESERVED = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
)
_DEFAULT_PORT = {"http": 80, "https": 443}


def _decode_unreserved(s: str) -> str:
    def repl(m: re.Match) -> str:
        ch = chr(int(m.group(1), 16))
        return ch if ch in _UNRESERVED else m.group(0)  # keep reserved %-encodings verbatim

    return re.sub(r"%([0-9A-Fa-f]{2})", repl, s)


def _normalize_web(url: str) -> str:
    p = urlsplit(url)
    scheme = p.scheme.lower()
    host = (p.hostname or "").lower()  # scheme + host are case-insensitive
    port = p.port
    netloc = host if (port is None or port == _DEFAULT_PORT.get(scheme)) else f"{host}:{port}"
    path = _decode_unreserved(p.path)  # path CASE kept (case-sensitive)
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]  # collapse a single trailing slash
    # query kept verbatim (it can select a real resource); fragment dropped (never names a doc)
    return urlunsplit((scheme, netloc, path, p.query, ""))


def _normalize_local(url: str) -> str:
    # A sources/ file: the path relative to sources/, POSIX-normalized, case preserved.
    path = url[len("file:"):] if url.startswith("file:") else url
    path = path.strip().replace("\\", "/").lstrip("/")
    return posixpath.normpath(path)


def normalize_locator(url: str) -> str:
    """Canonicalize a locator so cosmetic re-typings map to one id without merging distinct
    sources. Web (`http`/`https`) and local (`file:` / bare path) follow the two rules above."""
    url = (url or "").strip()
    scheme = urlsplit(url).scheme.lower()
    if scheme in ("http", "https"):
        return _normalize_web(url)
    return _normalize_local(url)


def document_id(url: str) -> str:
    """The stable `document_id` (D1): blake2b of the normalized locator, 32 hex."""
    return content_fingerprint(normalize_locator(url).encode("utf-8"))


def corpus_raw_path(raw_dir: str | Path, url: str) -> Path:
    """The corpus raw-archive path for a locator: ``<raw_dir>/<document_id>``. The archive is
    keyed by ``document_id = blake2b(locator)`` (D1) — one value for identity + archive key.
    The old ``sha1(url)`` key is retired by the one-off ``scripts/rekey_raw.py`` re-key (§6)."""
    return Path(raw_dir) / document_id(url)
