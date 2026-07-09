"""Generate glottolog_join.json — Berezkin tradition -> Glottolog languoid.

Produces the cached join that mockups 28 / 30 / 31 read. Strategy (validated in the
join-quality audit): **name-first, coordinate-fallback**, which fixes the wrong-neighbour
errors a pure nearest-coordinate match makes (e.g. Biloxi -> Siouan, not the nearest French
creole). Steps per tradition:

  1. exact match of the tradition's most-specific `language` level / name to a Glottolog
     language name (homonyms disambiguated by distance; rejected past `CAP` km);
  2. fuzzy name match among languages within `RADIUS` km (ratio >= `FUZZ`);
  3. nearest-coordinate fallback on the clean spoken-language set.

Pseudo-languoids (Sign Language, Bookkeeping, Unattested, …) are excluded — they are what a
naive rebuild mis-assigns. Quality is measured by **name-agreement** (does the assigned
language match the tradition's declared language), not km: the audit lifted it 14% -> 29% with
no change to the dominant-family dating (97% of dated motifs stable, 0 family flips).

Source: glottolog-cldf `languages.csv` (CC-BY), downloaded to a git-ignored snapshot.
Run:  python mockups/30-dated-phylogeny/build_join.py
"""
import csv
import difflib
import importlib.util
import json
import re
import urllib.request
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MOCKS = HERE.parent
SRC = HERE / "glottolog_languages.csv"          # git-ignored snapshot
OUT = HERE / "glottolog_join.json"
SRC_URL = "https://raw.githubusercontent.com/glottolog/glottolog-cldf/master/cldf/languages.csv"
CAP, RADIUS, FUZZ = 500.0, 700.0, 0.88
PSEUDO = {"Sign Language", "Bookkeeping", "Unattested", "Artificial Language",
          "Mixed Language", "Pidgin", "Speech Register", "Unclassifiable"}


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, MOCKS / rel)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", (s or "").lower())).strip()


def hav(lat, lon, la, lo):
    la1, la2 = np.radians(lat), np.radians(la)
    dla, dlo = np.radians(la - lat), np.radians(lo - lon)
    a = np.sin(dla / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin(dlo / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(a))


def main():
    if not SRC.exists():
        print(f"downloading {SRC_URL}")
        urllib.request.urlretrieve(SRC_URL, SRC)
    with open(SRC, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    by_gc = {r["ID"]: r for r in rows}

    def fam_name(r):
        if r.get("Is_Isolate") in ("True", "true", "1"):
            return "(isolate)"
        fid = r["Family_ID"]
        if fid and fid in by_gc:
            return by_gc[fid]["Name"]
        return r["Name"] if r["Level"] == "family" else "(isolate)"

    langs = []
    for r in rows:
        if r["Level"] != "language" or not r["Latitude"]:
            continue
        f = fam_name(r)
        if f in PSEUDO:
            continue
        r["_lat"] = float(r["Latitude"]); r["_lon"] = float(r["Longitude"])
        r["_fam"] = f; r["_nn"] = norm(r["Name"])
        langs.append(r)
    name_idx = {}
    for r in langs:
        name_idx.setdefault(r["_nn"], []).append(r)
    LAT = np.array([r["_lat"] for r in langs]); LON = np.array([r["_lon"] for r in langs])
    GN = [r["_nn"] for r in langs]

    geo = _load("_geo.py", "geo")
    coords = geo.berezkin_coords()
    with open(ROOT / "outputs" / "motifs" / "berezkin.json", encoding="utf-8") as f:
        T = json.load(f)["traditions"]

    def coord(tid):
        c = coords.get(tid)
        if isinstance(c, (list, tuple)) and len(c) == 2:
            return float(c[0]), float(c[1])
        ap = T[tid].get("areal_path") or []
        if len(ap) >= 2:
            cen = geo.SUBREGION.get(ap[1][1].upper())
            if cen:
                return float(cen[1]), float(cen[0])
        return None

    def cand_names(v):
        out = []
        lang = v.get("language") or []
        if lang:
            out.append(lang[-1])
        parts = v.get("name", "").split()
        if len(parts) > 1:
            out.append(" ".join(parts[1:]))
        out.append(v.get("name", ""))
        seen, uniq = set(), []
        for s in out:
            n = norm(s)
            if n and n not in seen:
                seen.add(n); uniq.append(n)
        return uniq

    join, method = {}, {"name": 0, "fuzzy": 0, "coord": 0}
    for tid, v in T.items():
        c = coord(tid)
        if c is None:
            continue
        lat, lon = c
        d = hav(lat, lon, LAT, LON)
        cands = cand_names(v)
        hit = None
        for nm in cands:                                       # 1. exact name
            if nm in name_idx:
                cc = name_idx[nm]; dd = [hav(lat, lon, r["_lat"], r["_lon"]) for r in cc]
                j = int(np.argmin(dd))
                if dd[j] <= CAP:
                    hit = (cc[j], dd[j], "name"); break
        if hit is None:                                        # 2. fuzzy within radius
            best = None
            for i in np.where(d < RADIUS)[0]:
                for cn in cands[:2]:
                    ratio = difflib.SequenceMatcher(None, GN[i], cn).ratio()
                    if ratio >= FUZZ and (best is None or ratio > best[0]):
                        best = (ratio, int(i))
            if best:
                i = best[1]; hit = (langs[i], float(d[i]), "fuzzy")
        if hit is None:                                        # 3. coordinate fallback
            j = int(np.argmin(d)); hit = (langs[j], float(d[j]), "coord")
        r, km, meth = hit
        method[meth] += 1
        join[tid] = {"gc": r["ID"], "gname": r["Name"], "gfam": r["_fam"],
                     "km": round(float(km)), "ofam": (v.get("language") or [""])[0]}

    OUT.write_text(json.dumps(join, ensure_ascii=False), encoding="utf-8")
    print(f"joined {len(join)} traditions -> {OUT.name}   method {method}")


if __name__ == "__main__":
    main()
