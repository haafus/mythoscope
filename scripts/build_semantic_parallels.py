#!/usr/bin/env python3
"""Precompute the BGE-M3 semantic-parallel suggestion layer, offline.

This is deliberately NOT part of ``mytho motifs`` — the model is ~2 GB and CPU
inference is slow. It embeds every motif (see ``motifs.semantic_parallels``) and
writes the committed ``src/motifs/data/semantic_parallels.json``; the running app
copies that into ``outputs/motifs/`` on first read (``store.load_semantic_parallels``),
so it needs neither the model nor ``sentence-transformers``.

Needs a built motif DB (``outputs/motifs/*.json``) and ``sentence-transformers``.
Embeddings cache to ``outputs/motifs/raw/bge_m3.npy`` (first run is the slow one).

Run: ``python scripts/build_semantic_parallels.py``
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from json_utils import save_json  # noqa: E402
from motifs import semantic_parallels  # noqa: E402

OUT = ROOT / "src" / "motifs" / "data" / "semantic_parallels.json"


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    data = semantic_parallels.build()
    if data is None:
        print("Skipped: sentence-transformers unavailable or no motif DB built.")
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    save_json(OUT, data)
    c = data["counts"]
    print(f"Wrote {OUT.relative_to(ROOT)} — {c['pairs']} pairs "
          f"({c['novel_only']} new beyond lexical, {c['also_lexical']} overlap).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
