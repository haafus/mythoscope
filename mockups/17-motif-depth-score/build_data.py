"""Motif depth-score prototype (mockup 17) — Method A of the stratum proposal.

Estimates each Berezkin motif's time-depth from the SHAPE of its areal distribution
alone (no Berezkin stratum labels): prevalence, geographic spread, spatial
fragmentation, language-family span, and cross-continental set span are combined into
one depth score (PCA PC1, oriented so a few uncontroversial deep anchors score high).
It is a first heuristic, deliberately un-bias-corrected — a sanity check that the
distributional signal exists, not a finished dating. See
docs/motifs/proposals/stratum-derivation.md (Method A).

Run:  python mockups/17-motif-depth-score/build_data.py
"""
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
MOCKS = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "data.js"

MIN_TRAD = 3     # need a distribution to date a motif
NEW_WORLD = {"NORTH AMERICA: NORTH AND WEST", "PLAINS AND SOUTHEAST",
             "MEXICO – CENTRAL ANDES", "EASTERN SOUTH AMERICA",
             "SOUTHERN SOUTH AMERICA", "BERINGIA"}
INDO_PACIFIC = {"OCEANIA", "AUSTRALIA"}
EURO = {"WESTERN EUROPE, NORTH AFRICA", "NORTHERN AND EASTERN EUROPE"}
# uncontroversial anchors to orient the axis (direction only, not training)
DEEP_ANCHORS = {"A11C", "C6i1", "A47", "B4", "A10", "C10"}          # celestial / earth-diver / flood
SHALLOW_ANCHORS = {"B88", "K8aa", "M182", "K27z2", "H7c1"}          # Job / Jonah / tar-baby / jataka / cunning-into-paradise
FEATURES = ["n_trad", "n_macro", "n_lang", "spread", "fragments", "set_span", "xindex"]


def _geo():
    spec = importlib.util.spec_from_file_location("_geo", MOCKS / "_geo.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _hav(a, b):
    la1, lo1, la2, lo2 = map(math.radians, [a[1], a[0], b[1], b[0]])
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371 * math.asin(min(1, math.sqrt(h)))


def megaset(macro):
    if macro in NEW_WORLD:
        return "NW"
    if macro in INDO_PACIFIC:
        return "IP"
    return "CONT"


def main():
    geo = _geo()
    coords = geo.berezkin_coords()
    with open(ROOT / "outputs" / "motifs" / "berezkin.json", encoding="utf-8") as f:
        bz = json.load(f)
    T = bz["traditions"]

    def macro(t):
        ap = T[t].get("areal_path") or []
        return ap[0][1] if ap else None

    def lang(t):
        lg = T[t].get("language") or []
        return lg[0] if lg else None

    def coord(t):
        c = coords.get(t)
        if isinstance(c, (list, tuple)) and len(c) == 2:
            return float(c[1]), float(c[0])
        ap = T[t].get("areal_path") or []
        if len(ap) >= 2:
            cen = geo.SUBREGION.get(ap[1][1].upper())
            if cen:
                return float(cen[0]), float(cen[1])
        return None

    rows, mids = [], []
    for r in bz["motifs"]:
        tids = r.get("traditions") or []
        if len(tids) < MIN_TRAD:
            continue
        macros = [macro(t) for t in tids if macro(t)]
        langs = {lang(t) for t in tids if lang(t)}
        pts = [coord(t) for t in tids]
        pts = [p for p in pts if p]
        # spread = mean great-circle distance to centroid; fragments via DBSCAN
        if len(pts) >= 2:
            cen = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
            spread = sum(_hav(p, cen) for p in pts) / len(pts)
            rad = np.radians([[p[1], p[0]] for p in pts])
            frags = len(set(DBSCAN(eps=0.35, min_samples=1, metric="haversine").fit(rad).labels_))
        else:
            spread, frags = 0.0, 1
        sets = {megaset(m) for m in macros}
        xindex = 1 + (1 if r.get("atu_refs") else 0)
        rows.append([len(tids), len(set(macros)), len(langs), spread, frags, len(sets), xindex])
        mids.append(r)

    F = np.array(rows, dtype=float)
    Z = StandardScaler().fit_transform(F)
    pc = PCA(n_components=1).fit_transform(Z).ravel()

    # orient: deep anchors should score high
    codes = [r["id"] for r in mids]
    idx = {c: i for i, c in enumerate(codes)}
    da = [pc[idx[c]] for c in DEEP_ANCHORS if c in idx]
    sa = [pc[idx[c]] for c in SHALLOW_ANCHORS if c in idx]
    if da and sa and np.mean(da) < np.mean(sa):
        pc = -pc
    # scale to 0..100
    score = 100 * (pc - pc.min()) / (np.ptp(pc) or 1)

    def enrich(i):
        r = mids[i]
        return {"c": r["id"], "n": r.get("name", ""),
                "s": round(float(score[i]), 1), "g": int(r.get("motif_group_num") or 0),
                "nt": int(F[i, 0]), "nm": int(F[i, 1]), "nl": int(F[i, 2]),
                "fr": int(F[i, 4]), "ss": int(F[i, 5])}

    order = np.argsort(-score)
    deepest = [enrich(int(i)) for i in order[:25]]
    shallowest = [enrich(int(i)) for i in order[-25:][::-1]]

    # histogram
    hist, edges = np.histogram(score, bins=20, range=(0, 100))

    # anchors
    anchors = {"deep": [enrich(idx[c]) for c in DEEP_ANCHORS if c in idx],
               "shallow": [enrich(idx[c]) for c in SHALLOW_ANCHORS if c in idx]}

    # validation: adventure/trick endemism — New-World-endemic vs Europe-only
    endemic, euro_only, both = [], [], []
    for i, r in enumerate(mids):
        if str(r.get("motif_group_num")) not in ("10", "11"):
            continue
        ms = {macro(t) for t in (r.get("traditions") or [])}
        inA, inE = bool(ms & NEW_WORLD), bool(ms & EURO)
        if inA and not inE:
            endemic.append(score[i])
        elif inE and not inA:
            euro_only.append(score[i])
        elif inA and inE:
            both.append(score[i])
    valid = {
        "endemic_amer": {"n": len(endemic), "mean": round(float(np.mean(endemic)), 1)},
        "euro_only": {"n": len(euro_only), "mean": round(float(np.mean(euro_only)), 1)},
        "both": {"n": len(both), "mean": round(float(np.mean(both)), 1)},
    }

    # feature ↔ score correlation, to show what drives depth
    corr = {f: round(float(np.corrcoef(F[:, j], score)[0, 1]), 2) for j, f in enumerate(FEATURES)}

    data = {"n_motifs": len(mids), "min_trad": MIN_TRAD, "features": FEATURES,
            "corr": corr, "hist": [int(h) for h in hist],
            "edges": [round(float(e), 1) for e in edges],
            "deepest": deepest, "shallowest": shallowest,
            "anchors": anchors, "valid": valid}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";",
                   encoding="utf-8")
    print(f"{len(mids)} motifs scored · endemic-Amer adv mean {valid['endemic_amer']['mean']} "
          f"vs Euro-only {valid['euro_only']['mean']} · data.js ~{OUT.stat().st_size // 1024}KB")
    print("  feature↔score corr:", corr)


if __name__ == "__main__":
    main()
