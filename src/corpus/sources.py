"""Source acquisition helpers — dispatch by URL scheme.

A corpus item keeps a single ``url`` field; its scheme decides how the bytes are
obtained: ``http(s)://`` is downloaded (via the shared fetch-cache), while
``file:`` (or a bare relative path) is read from a local file **confined under
``settings.sources_dir``**. The scheme itself is the source type, so nothing else
in the metadata records it.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import unquote, urlparse

WEB_SCHEMES = ("http", "https")
# A bare relative path (no scheme) is treated as a local file, same as ``file:``.
FILE_SCHEMES = ("file", "")


def source_scheme(url: str) -> str:
    """Lowercased URL scheme (``""`` for a bare path)."""
    return urlparse(url or "").scheme.lower()


def is_file_source(url: str) -> bool:
    """True for a non-empty local (``file:`` / bare-path) source."""
    return bool(url) and source_scheme(url) in FILE_SCHEMES


def resolve_local_path(url: str, root: str | Path) -> Path:
    """Map a ``file:`` URL (or bare relative path) to a real path confined under
    ``root``. Raises ``ValueError`` on an absolute path, a remote host, or any path
    that escapes ``root`` (traversal guard)."""
    parsed = urlparse(url)
    if parsed.scheme not in FILE_SCHEMES:
        raise ValueError(f"Not a local file source: {url!r}")
    if parsed.netloc and parsed.netloc.lower() != "localhost":
        raise ValueError(f"Remote file host is not allowed: {url!r}")

    rel = unquote(parsed.path if parsed.scheme == "file" else url)
    p = Path(rel)
    if p.is_absolute():
        raise ValueError(f"Absolute file paths are not allowed: {url!r}")

    root = Path(root).resolve()
    full = (root / p).resolve()
    if not full.is_relative_to(root):
        raise ValueError(f"File path escapes sources_dir: {url!r}")
    return full


def read_local(url: str, root: str | Path) -> bytes:
    """Read the bytes of a local ``file:`` source, confined under ``root``."""
    path = resolve_local_path(url, root)
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {path}")
    return path.read_bytes()


def read_local_to_cache(url: str, cache_file: str | Path, root: str | Path) -> bytes:
    """Read a local source and snapshot it into the raw cache (for parity with the
    HTTP path and reproducibility), returning the bytes. Always re-reads the source
    so on-disk edits are picked up."""
    data = read_local(url, root)
    cache_file = Path(cache_file)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_bytes(data)
    return data


def file_source_unchanged(url: str, cache_file: str | Path, root: str | Path) -> bool:
    """True if the local ``file:`` source still matches the raw-cache snapshot from
    the previous build (content hash unchanged). Used to skip re-extraction of
    unmodified files without storing a separate hash in the metadata. Any error
    (missing snapshot, missing/unreadable source) is treated as "changed"."""
    cache_file = Path(cache_file)
    if not cache_file.exists():
        return False
    try:
        current = read_local(url, root)
    except (OSError, ValueError):
        return False
    return hashlib.md5(current).digest() == hashlib.md5(cache_file.read_bytes()).digest()
