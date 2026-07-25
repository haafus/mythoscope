#!/usr/bin/env python3
"""Fetch a full motifs raw snapshot into ``outputs/motifs/raw/`` — populate a fresh build env.

The motifs raw cache (areasofmyths / mapsofmyths / Trilogy CSVs / Wikidata / Ashliman / folkmasa)
is gitignored and never exported, so a fresh build environment has none. A populated ``raw/`` is
the **prerequisite** for validating the motifs atomisation offline: with it the split builds
deterministically and is golden-diffable (see ``docs/proposals/motifs-atomisation.md``).

This drives the atomised ``motifs:*`` pipeline stages: on an empty cache each source **acquires on
miss** (fetches every page it needs), so a plain build lands the whole snapshot. To force a re-fetch
of an *already-populated* cache, use ``mytho refresh motifs --apply`` (the networked re-check path).

Credentials: mapsofmyths enrichment needs HTTP basic auth — set ``MAPSOFMYTHS_AUTH=user:pass`` in
the env before running, else that source is skipped (the catalogue still builds, minus enrichment).

Usage (repo root, ``pip install -e ".[all]"``):
    MAPSOFMYTHS_AUTH=user:pass python scripts/fetch_motifs_raw.py
    # optional: MYTHO_MOTIFS__MAX_WORKERS=10  concurrent detail-page fetches
"""

from __future__ import annotations

import os
import sys


def main() -> int:
    if not os.environ.get("MAPSOFMYTHS_AUTH"):
        print("warning: MAPSOFMYTHS_AUTH unset — mapsofmyths enrichment will be skipped "
              "(catalogue still builds, minus English names / traditions).", file=sys.stderr)

    from motifs import store
    from pipeline import build, build_pipeline

    motifs = [s for s in build_pipeline() if s.name.startswith("motifs")]
    build(motifs, targets={s.name for s in motifs})   # cold cache → each stage acquires on miss

    raw = store.motifs_dir() / "raw"
    meta = store.load_meta()
    print(f"\nraw cache: {raw}")
    print("counts:", meta.get("counts"))
    print("fetch_outcomes:", meta.get("fetch_outcomes"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
