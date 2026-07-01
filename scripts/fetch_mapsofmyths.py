#!/usr/bin/env python
"""Standalone refresh of the mapsofmyths.com enrichment data.

This is a thin wrapper around the pipeline step
``motifs.sources.mapsofmyths.refresh`` — the same code ``mytho motifs`` runs. It
fetches (with HTTP basic auth) the English names/definitions, per-motif taxonomy /
ATU & Thompson ids / attesting traditions, and the tradition catalogue into the
resumable raw cache (``outputs/motifs/raw/mapsofmyths/``), and rewrites the parsed
data files under ``outputs/motifs/`` (not committed).

Prefer running the pipeline (``MYTHO_MOTIFS__MAPSOFMYTHS_USER=… MYTHO_MOTIFS__MAPSOFMYTHS_PASS=… mytho motifs``);
use this script to refresh the enrichment cache without a full rebuild.

Usage:
    python scripts/fetch_mapsofmyths.py --user U --pass P [--force]
    MYTHO_MAPSOFMYTHS_USER=... MYTHO_MAPSOFMYTHS_PASS=... python scripts/fetch_mapsofmyths.py
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from motifs import store  # noqa: E402
from motifs.sources import mapsofmyths  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--user", default=os.environ.get("MYTHO_MAPSOFMYTHS_USER"))
    ap.add_argument("--pass", dest="password", default=os.environ.get("MYTHO_MAPSOFMYTHS_PASS"))
    ap.add_argument("--force", action="store_true", help="re-fetch pages already in the raw cache")
    args = ap.parse_args()
    if not (args.user and args.password):
        ap.error("provide --user/--pass (or MYTHO_MAPSOFMYTHS_USER / MYTHO_MAPSOFMYTHS_PASS)")
        return 2

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    counts = mapsofmyths.refresh(store.motifs_dir() / "raw", force=args.force,
                                 auth=(args.user, args.password))
    print(counts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
