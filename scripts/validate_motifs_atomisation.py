#!/usr/bin/env python3
"""Validate the motifs atomisation — the deterministic core must survive the refactor byte-for-byte.

An orchestration change (splitting the ``build_motifs`` monolith into per-source / crosswalk /
parallels / meta stages, ``docs/proposals/motifs-atomisation.md``) MUST NOT change the data. This
guard rebuilds motifs **from the pinned raw cache** (offline, deterministic — no re-fetch) and
canon-hashes the deterministic core: ``berezkin / tmi / atu / crosswalk / parallels .json``.
``meta.json`` is excluded (its ``built_at`` + degradation state are per-build).

Flow:
    python scripts/validate_motifs_atomisation.py snapshot   # BEFORE the change → writes baseline
    # ...make the atomisation changes...
    python scripts/validate_motifs_atomisation.py assert     # AFTER  → exits non-zero on any drift

Rebuild goes through the driver scoped to motifs (``build(..., force=True)``), so the same command
works before the split (one ``motifs`` stage) and after (the ``motifs:*`` stages). Requires a
populated ``outputs/motifs/raw/`` — run ``scripts/fetch_motifs_raw.py`` first.

No credentials needed: the core files carry enrichment (``berezkin.json``: ``name_rus`` /
``tmi_refs`` / ``motif_group`` / ``traditions``), and with a populated raw cache the enrichment
re-derives offline (mapsofmyths gates creds on the network, not the step), so the rebuild is a
clean function of (code + raw).

The baseline lives at ``outputs/motifs/.golden-core.json`` (gitignored, beside the store).
"""

from __future__ import annotations

import hashlib
import json
import sys

CORE = ["berezkin", "tmi", "atu", "crosswalk", "parallels"]


def _baseline_path():
    from motifs import store
    return store.motifs_dir() / ".golden-core.json"


def _rebuild_from_cache() -> None:
    """Rebuild the motifs stage(s) from the raw cache. Deletes every fp sidecar first: the driver's
    ``actual()`` short-circuits on a matching fp, so without this the "rebuild" is a silent no-op.
    With the gates gone every stage reads ``missing`` and rebuilds from the cache — offline
    (``force=False`` never re-fetches), hence deterministic. Prefix-scoped, so it spans the monolith
    (``motifs``) and the atomised stages (``motifs:*``)."""
    from motifs import store
    from pipeline import build, build_pipeline

    for fp in store.motifs_dir().glob(".fp*"):  # coarse .fp + per-stage .fp.<stage> → force a rebuild
        fp.unlink()
    motifs = [s for s in build_pipeline() if s.name == "motifs" or s.name.startswith("motifs")]
    if not motifs:
        raise SystemExit("no motifs stage in the pipeline")
    build(motifs, targets={s.name for s in motifs})


def _hash_core() -> dict[str, str]:
    from motifs import store

    out: dict[str, str] = {}
    for name in CORE:
        path = store.motifs_dir() / f"{name}.json"
        data = json.loads(path.read_text("utf-8"))
        canon = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
        out[name] = hashlib.blake2b(canon, digest_size=16).hexdigest()
    return out


def main(argv: list[str]) -> int:
    mode = argv[1] if len(argv) > 1 else ""

    if mode == "snapshot":
        _rebuild_from_cache()
        digests = _hash_core()
        _baseline_path().write_text(json.dumps(digests, indent=2), "utf-8")
        print(f"snapshot → {_baseline_path()}")
        for k, v in digests.items():
            print(f"  {k:<10} {v}")
        return 0

    if mode == "assert":
        bp = _baseline_path()
        if not bp.exists():
            print("no baseline — run `snapshot` first", file=sys.stderr)
            return 2
        before = json.loads(bp.read_text("utf-8"))
        _rebuild_from_cache()
        after = _hash_core()
        drift = [k for k in CORE if before.get(k) != after.get(k)]
        for k in CORE:
            print(f"  {'DRIFT' if k in drift else 'ok':<5} {k}")
        if drift:
            print(f"\nFAIL: {len(drift)} core file(s) drifted: {drift}", file=sys.stderr)
            return 1
        print("\nPASS: deterministic core byte-identical.")
        return 0

    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
