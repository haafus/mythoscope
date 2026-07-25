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


# The raw files/dirs each source's build consumes, relative to the raw dir — for its per-source
# fingerprint (the granular replacements for the one coarse fp above). The trilogy CSVs are split
# between TMI (tmi.csv) and ATU (atu_*.csv); the union covers the whole raw cache, no overlap.
_SOURCE_RAW = {
    "berezkin": ["berezkin", "mapsofmyths"],
    "tmi": ["trilogy/tmi.csv", "mellmann", "folkmasa_bibliography.html"],
    "atu": ["trilogy/atu_combos.csv", "trilogy/atu_df.csv", "trilogy/atu_seq.csv", "wikidata", "ashliman"],
}


def source_fingerprint(source: str) -> str:
    """Per-source offline staleness key: a blake2b of just that source's raw files + config + algo.
    Isolating each source's raw (see ``_SOURCE_RAW``) is what lets a ``motifs:source:*`` stage go
    stale independently — a change under one source's patterns never moves another's fp."""
    h = hashlib.blake2b(digest_size=16)
    h.update(f"algo={MOTIFS_ALGO_VERSION}|source={source}".encode())

    cfg = settings.config_dir / "motifs.json"
    h.update(b"|config=")
    h.update(cfg.read_bytes() if cfg.exists() else b"none")

    raw = store.raw_dir()
    for pattern in _SOURCE_RAW.get(source, []):
        base = raw / pattern
        members = [base] if base.is_file() else (base.rglob("*") if base.exists() else [])
        for f in sorted(p for p in members if p.is_file()):
            h.update(f"|{f.relative_to(raw)}=".encode())
            h.update(f.read_bytes())
    return h.hexdigest()
