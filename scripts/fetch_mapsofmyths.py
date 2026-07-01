#!/usr/bin/env python
"""Fetch Berezkin enrichment data from mapsofmyths.com (sister site of the
areasofmyths.com catalogue: same motif ids, CC BY-NC-SA 4.0, use with attribution).

It writes three tracked data files under ``src/motifs/data/`` that the Berezkin
source (``motifs/sources/berezkin.py``) reads at build time — so the build itself
needs no credentials:

* ``mapsofmyths_en.json``       — id -> English name + definition (from /motifs_full)
* ``mapsofmyths_nodes.json``    — id -> motif type/group, ATU & Thompson ids, and the
                                  areal ids of the traditions attesting the motif
                                  (from every /node/N motif page)
* ``mapsofmyths_traditions.json`` — the 1046 traditions with names (En/Ru), the named
                                  4-level areal hierarchy, and language family
                                  (from /traditions_full)

Usage:
    MYTHO_MAPSOFMYTHS_USER=... MYTHO_MAPSOFMYTHS_PASS=... python scripts/fetch_mapsofmyths.py
    python scripts/fetch_mapsofmyths.py --user U --pass P [--workers 16] [--only en,nodes,traditions]

Fetching every node page (~3400) takes a few minutes; ``--only en`` refreshes just
the fast English file.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = "http://mapsofmyths.com"
DATA = Path(__file__).resolve().parents[1] / "src" / "motifs" / "data"
_LICENSE = "CC BY-NC-SA 4.0"
_ATTRIB = ("Yu.E. Berezkin, E.N. Duvakin. The Electronic Analytic Catalogue of "
           "Folklore and Mythology Motifs")


def _soup(html: str):
    from bs4 import BeautifulSoup

    return BeautifulSoup(html, "html.parser")


def _field(node, name: str) -> str:
    el = node.find("div", class_=f"field-name-{name}")
    item = el.find("div", class_="field-item") if el else None
    return " ".join(item.get_text(" ", strip=True).split()) if item else ""


# --- session with basic auth + retry ---------------------------------------

def _make_session(user: str, password: str):
    import requests

    s = requests.Session()
    s.auth = (user, password)
    return s


def _get(session, path: str, retries: int = 3) -> str:
    last = None
    for _ in range(retries):
        try:
            r = session.get(BASE + path, timeout=90)
            r.raise_for_status()
            return r.text
        except Exception as exc:  # transient network / proxy hiccup
            last = exc
            time.sleep(1)
    raise RuntimeError(f"GET {path} failed: {last}")


# --- parsers ---------------------------------------------------------------

def parse_motifs_full(html: str) -> dict[str, dict]:
    """id -> {name_eng, definition_eng, href} from the /motifs_full listing."""
    out: dict[str, dict] = {}
    for node in _soup(html).find_all("div", class_=lambda c: c and "node-motif" in c):
        h2, a = node.find("h2"), node.find("a", href=True)
        if not h2:
            continue
        out[h2.get_text(strip=True).upper()] = {
            "name_eng": _field(node, "field-name-eng"),
            "definition_eng": _field(node, "body"),
            "href": a["href"] if a else "",
        }
    return out


def parse_motif_node(html: str) -> dict:
    """Type/group, ATU & Thompson ids, and attesting-tradition areal ids."""
    soup = _soup(html)
    group = _field(soup, "field-motif-group")
    traditions: list[str] = []
    table = soup.find("table")
    if table:
        for row in table.find_all("tr"):
            cells = [" ".join(td.get_text(" ", strip=True).split()) for td in row.find_all("td")]
            if len(cells) >= 2 and re.match(r"^[\d.]+$", cells[0]):
                traditions.append(cells[0])
    return {
        "type": _field(soup, "field-motif-type"),
        "group_num": group.split()[0] if group else "",
        "group": group,
        "atu": _field(soup, "field-atu-id"),
        "tmi": _field(soup, "field-stith-thompson-id"),
        "traditions": traditions,
    }


def parse_traditions_full(html: str) -> dict[str, dict]:
    """areal_id -> {name, name_rus, areal_path:[[id,name]], language:[...]}."""
    out: dict[str, dict] = {}
    rows = _soup(html).find("div", class_="view-content").find_all(
        "div", class_=lambda c: c and "views-row" in c)
    for r in rows:
        aid_el = r.find("div", class_="field-name-field-areal-id")
        aid = aid_el.find("div", class_="field-item").get_text(strip=True) if aid_el else ""
        if not aid:
            continue
        name = " ".join(r.find("h2").get_text(" ", strip=True).split()) if r.find("h2") else ""
        # named areal levels (shs-hierarchy list of taxonomy links), broadest first
        areal = r.find("div", class_="field-name-field-areal")
        levels = [" ".join(a.get_text(" ", strip=True).split())
                  for a in areal.select("ul.shs-hierarchy li a")] if areal else []
        # pair each level name with its areal-id prefix (5 / 5.1 / 5.1.3 ...)
        parts = aid.split(".")
        path = [[".".join(parts[: i + 1]), lvl] for i, lvl in enumerate(levels)]
        lang = r.find("div", class_="field-name-field-language-hierarchy")
        language = [" ".join(a.get_text(" ", strip=True).split())
                    for a in lang.find_all("a")] if lang else []
        out[aid] = {
            "name": name,
            "name_rus": _field(r, "body"),
            "areal_path": path,
            "language": language,
        }
    return out


# --- orchestration ---------------------------------------------------------

def _write(name: str, payload: dict) -> None:
    path = DATA / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"  wrote {name} ({round(path.stat().st_size / 1024)} KB)")


def run(session, steps: set[str], workers: int) -> None:
    english = {}
    if {"en", "nodes"} & steps:
        print("Fetching /motifs_full …")
        english = parse_motifs_full(_get(session, "/motifs_full"))
        print(f"  {len(english)} motifs")

    if "en" in steps:
        _write("mapsofmyths_en.json", {
            "source": "mapsofmyths.com", "license": _LICENSE, "attribution": _ATTRIB,
            "motifs": {k: {"name_eng": v["name_eng"], "definition_eng": v["definition_eng"]}
                       for k, v in english.items()},
        })

    if "nodes" in steps:
        targets = [(mid, v["href"]) for mid, v in english.items() if v["href"]]
        print(f"Fetching {len(targets)} motif node pages (type/group, ATU/TMI, traditions) …")

        def one(mh):
            mid, href = mh
            try:
                return mid, parse_motif_node(_get(session, href))
            except Exception:
                return mid, None

        nodes, done = {}, 0
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for mid, rec in pool.map(one, targets):
                done += 1
                if rec:
                    nodes[mid] = rec
                if done % 500 == 0:
                    print(f"  {done}/{len(targets)}", flush=True)
        _write("mapsofmyths_nodes.json", {
            "source": "mapsofmyths.com", "license": _LICENSE, "attribution": _ATTRIB,
            "motifs": nodes,
        })

    if "traditions" in steps:
        print("Fetching /traditions_full …")
        trads = parse_traditions_full(_get(session, "/traditions_full"))
        print(f"  {len(trads)} traditions")
        _write("mapsofmyths_traditions.json", {
            "source": "mapsofmyths.com", "license": _LICENSE, "attribution": _ATTRIB,
            "traditions": trads,
        })


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--user", default=os.environ.get("MYTHO_MAPSOFMYTHS_USER"))
    ap.add_argument("--pass", dest="password", default=os.environ.get("MYTHO_MAPSOFMYTHS_PASS"))
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--only", default="en,nodes,traditions",
                    help="comma list of steps to run (en, nodes, traditions)")
    args = ap.parse_args()
    if not (args.user and args.password):
        ap.error("provide --user/--pass (or MYTHO_MAPSOFMYTHS_USER / MYTHO_MAPSOFMYTHS_PASS)")
        return 2
    steps = {s.strip() for s in args.only.split(",") if s.strip()}
    run(_make_session(args.user, args.password), steps, args.workers)
    return 0


if __name__ == "__main__":
    sys.exit(main())
