#!/usr/bin/env python
"""Fetch English motif names + definitions from mapsofmyths.com.

mapsofmyths.com is the sister site of areasofmyths.com (the Berezkin & Duvakin
catalogue): same motif ids, but it carries an English name and an English
definition for (almost) every motif. Its ``/motifs_full`` page lists them all as
Drupal nodes. Under the catalogue's CC BY-NC-SA 4.0 licence this data can be used
for non-commercial purposes with attribution.

This writes ``src/motifs/data/mapsofmyths_en.json`` (a tracked data file), which
the Berezkin source (``motifs/sources/berezkin.py``) reads to attach ``name_eng``
and ``definition_eng`` to each motif — so the build itself needs no credentials.

Usage:
    MYTHO_MAPSOFMYTHS_USER=... MYTHO_MAPSOFMYTHS_PASS=... python scripts/fetch_mapsofmyths.py
    python scripts/fetch_mapsofmyths.py --user U --pass P
    python scripts/fetch_mapsofmyths.py --html path/to/motifs_full.html   # parse a local copy
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

BASE = "http://mapsofmyths.com"
OUT = Path(__file__).resolve().parents[1] / "src" / "motifs" / "data" / "mapsofmyths_en.json"


def _field(node, name: str) -> str:
    el = node.find("div", class_=f"field-name-{name}")
    if not el:
        return ""
    item = el.find("div", class_="field-item")
    return " ".join(item.get_text(" ", strip=True).split()) if item else ""


def parse(html: str) -> dict[str, dict]:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    out: dict[str, dict] = {}
    for node in soup.find_all("div", class_=lambda c: c and "node-motif" in c):
        h2 = node.find("h2")
        if not h2:
            continue
        # ids are case-insensitive in the catalogue (A7B == a7b); normalise upper.
        mid = h2.get_text(strip=True).upper()
        name, desc = _field(node, "field-name-eng"), _field(node, "body")
        if name or desc:
            out[mid] = {"name_eng": name, "definition_eng": desc}
    return out


def fetch(user: str, password: str) -> str:
    import requests

    resp = requests.get(f"{BASE}/motifs_full", auth=(user, password), timeout=120)
    resp.raise_for_status()
    return resp.text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--user", default=os.environ.get("MYTHO_MAPSOFMYTHS_USER"))
    ap.add_argument("--pass", dest="password", default=os.environ.get("MYTHO_MAPSOFMYTHS_PASS"))
    ap.add_argument("--html", help="parse a local motifs_full.html instead of fetching")
    args = ap.parse_args()

    if args.html:
        html = Path(args.html).read_text(encoding="utf-8")
    elif args.user and args.password:
        html = fetch(args.user, args.password)
    else:
        ap.error("provide --html, or --user/--pass (or MYTHO_MAPSOFMYTHS_USER/PASS)")
        return 2

    motifs = parse(html)
    if not motifs:
        print("No motifs parsed — page layout may have changed.", file=sys.stderr)
        return 1
    payload = {
        "source": "mapsofmyths.com",
        "license": "CC BY-NC-SA 4.0",
        "attribution": "Yu.E. Berezkin, E.N. Duvakin. The Electronic Analytic "
                       "Catalogue of Folklore and Mythology Motifs",
        "motifs": motifs,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"Wrote {len(motifs)} English motif entries to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
