#!/usr/bin/env python3
"""Fetch a full motifs raw snapshot — wholesale re-scrape of every source into ``outputs/motifs/raw/``.

The motifs raw cache (areasofmyths / mapsofmyths / Trilogy CSVs / Wikidata / Ashliman / folkmasa)
is gitignored and never exported, so a fresh build environment has none. A populated ``raw/`` is
the **prerequisite** for validating the motifs atomisation offline: with it the split builds
deterministically and is golden-diffable (see ``docs/proposals/motifs-atomisation.md``). This
script forces a full re-fetch (``build_motifs(force=True)``), then rebuilds the indexes from it.

Credentials: mapsofmyths enrichment needs HTTP basic auth — set ``MAPSOFMYTHS_AUTH=user:pass`` in
the env before running, else that step is skipped (the catalogue still builds, minus enrichment).

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
    from motifs.build_motifs import build_motifs

    build_motifs(force=True)  # force → re-fetch every source into raw/, then rebuild indexes

    raw = store.motifs_dir() / "raw"
    meta = store.load_meta()
    print(f"\nraw cache: {raw}")
    print("counts:", meta.get("counts"))
    print("fetch_outcomes:", meta.get("fetch_outcomes"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
