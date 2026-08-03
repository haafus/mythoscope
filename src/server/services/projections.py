"""Projection payloads, cached as pre-serialized bytes.

A projection file is up to ~8MB of JSON, and the old path paid for it three
times per request: ``json.load`` from disk (~27ms), FastAPI re-encoding the dict
it had just decoded (~28ms), and ``GZipMiddleware`` compressing the result
(~320ms at its default level 9). All of it under the GIL, so the endpoint sat at
a flat ~24 req/s no matter the concurrency — extra threads only queued.

None of that work depends on the request: the bytes change only when the file on
disk changes. So decode, encode and compress once, key the result on the file's
identity (mtime + size), and hand out the finished buffers. Measurements and the
before/after are in ``docs/deployment.md``.
"""

import gzip
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from projections import PROJECTION_KEYS
from settings import settings

# One entry per (model, method) actually requested. The large ones are ~8MB raw
# plus ~2MB gzipped; a handful of models stays well inside the ~370MB baseline.
# Bounded so an unexpected fan-out cannot grow without limit, and so superseded
# entries (same file, new mtime) are evicted rather than accumulating.
_CACHE_SIZE = 16

# Paid once per file, not per request, so buy the smallest payload available.
_GZIP_LEVEL = 9


@dataclass(frozen=True)
class ProjectionPayload:
    """A projection response, ready to send in either encoding."""

    body: bytes
    gzipped: bytes
    etag: str


@lru_cache(maxsize=_CACHE_SIZE)
def _build(path_str: str, method: str, mtime_ns: int, size: int) -> ProjectionPayload:
    # mtime_ns/size do not appear in the body — they are the cache key, so a file
    # replaced by `push-outputs` yields a new entry instead of a stale hit.
    data = json.loads(Path(path_str).read_bytes())
    data["method"] = method
    # Compact separators: the default encoder emits ", " / ": ", which is a few
    # hundred KB of whitespace on a payload this size.
    body = json.dumps(data, separators=(",", ":")).encode("utf-8")
    return ProjectionPayload(
        body=body,
        gzipped=gzip.compress(body, _GZIP_LEVEL),
        etag=f'"{mtime_ns:x}-{size:x}"',
    )


def load_projection(model_key: str, method: str) -> ProjectionPayload | None:
    """The cached payload for one projection, or None if there is no such file."""
    if method not in PROJECTION_KEYS:
        return None
    path = settings.projections_dir / model_key / f"{method}.json"
    try:
        stat = path.stat()
    except OSError:
        return None
    return _build(str(path), method, stat.st_mtime_ns, stat.st_size)
