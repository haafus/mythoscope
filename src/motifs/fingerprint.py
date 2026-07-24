"""Coarse input fingerprint for the motifs stage — its offline staleness key.

Motifs is still a monolith (a granular per-source split is deferred, pipeline §2.2), so this is
one coarse fp over everything a build consumes offline: the pinned raw scrape cache plus the
motifs config, with a manual ``MOTIFS_ALGO_VERSION`` covering anything content-hashing misses
(the bundled trilogy CSVs, parsing/derivation logic). It lets ``build_motifs`` skip the whole
re-parse/re-derive when nothing changed, instead of running it every build.
"""

from __future__ import annotations

import hashlib

from settings import settings

from . import store

# Bump when the parse/derivation logic, the crosswalk/parallels algorithm, or the bundled
# trilogy dataset changes in a way the raw cache + config below do not capture.
MOTIFS_ALGO_VERSION = 1


def motifs_fingerprint() -> str:
    """One hash of the raw scrape cache + config + algo version (a running blake2b)."""
    h = hashlib.blake2b(digest_size=16)
    h.update(f"algo={MOTIFS_ALGO_VERSION}".encode())

    cfg = settings.config_dir / "motifs.json"
    h.update(b"|config=")
    h.update(cfg.read_bytes() if cfg.exists() else b"none")

    raw = store.raw_dir()
    if raw.exists():
        for f in sorted(p for p in raw.rglob("*") if p.is_file()):
            h.update(f"|{f.relative_to(raw)}=".encode())
            h.update(f.read_bytes())
    return h.hexdigest()
