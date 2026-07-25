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


# --- lenient content validators (validate-before-commit, fetch-and-refresh §4) --------------
# Each gates *adopt*: a fresh reply must pass before it can overwrite the pinned copy. They are
# deliberately lenient — reject only clearly-broken replies (empty / wrong content-type / a plain
# error stub), never a real payload, so a genuine upstream change is never falsely kept-pinned.
# Catching a *structured* HTML error page served with 200 needs a per-source parser (deferred).

def valid_html(content: bytes) -> bool:
    """Non-empty and carrying markup — rejects an empty body or a plain-text/binary error stub."""
    return bool(content.strip()) and b"<" in content[:4096]


def valid_csv(content: bytes) -> bool:
    """Decodable non-markup text with a comma-bearing header + at least one row — rejects the
    common failure of a CSV endpoint returning an HTML error page."""
    if not content.strip() or content[:64].lstrip().lower().startswith((b"<!doctype", b"<html", b"<?xml")):
        return False
    lines = [ln for ln in content.decode("utf-8", errors="replace").splitlines() if ln.strip()]
    return len(lines) >= 2 and "," in lines[0]


def valid_json(content: bytes) -> bool:
    """Parses as JSON — for the POST marker replies (a truncated/HTML reply fails here)."""
    import json
    try:
        json.loads(content)
        return True
    except Exception:
        return False


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
