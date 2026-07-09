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
DEEP_ANCHORS = {"C6i1", "A47", "B4", "A10", "C10", "D4A"}           # earth-diver / sun-egg / flood / theft-of-fire
SHALLOW_ANCHORS = {"B88", "K8aa", "K27z2", "H7c1"}                  # Job / Jonah / jataka / cunning-into-paradise
# disjunction-weighted variant: reward cross-clade + barrier-spanning + fragmented,
# penalise raw prevalence (the fix for the prevalence confound of PC1).
DISJ_W = {"n_trad": -1.0, "n_macro": -0.5, "n_lang": 1.0, "spread": 0.5,
          "fragments": 0.8, "set_span": 1.0, "xindex": 0.0}
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
    def scale(a):
        return 100 * (a - a.min()) / (np.ptp(a) or 1)
    score = scale(pc)

    # disjunction-weighted variant (explicit weights, prevalence de-emphasised)
    disj = Z @ np.array([DISJ_W[f] for f in FEATURES])
    disj = scale(disj)

    def percentile(a):
        order = a.argsort()
        rank = np.empty(len(a)); rank[order] = np.arange(len(a))
        return 100 * rank / (len(a) - 1)
    pct_s, pct_d = percentile(score), percentile(disj)

    def enrich(i):
        r = mids[i]
        return {"c": r["id"], "n": r.get("name", ""),
                "s": round(float(score[i]), 1), "d": round(float(disj[i]), 1),
                "g": int(r.get("motif_group_num") or 0),
                "nt": int(F[i, 0]), "nm": int(F[i, 1]), "nl": int(F[i, 2]),
                "fr": int(F[i, 4]), "ss": int(F[i, 5])}

    order = np.argsort(-score)
    deepest = [enrich(int(i)) for i in order[:25]]
    shallowest = [enrich(int(i)) for i in order[-25:][::-1]]

    hist, edges = np.histogram(score, bins=20, range=(0, 100))

    anchors = {"deep": [enrich(idx[c]) for c in DEEP_ANCHORS if c in idx],
               "shallow": [enrich(idx[c]) for c in SHALLOW_ANCHORS if c in idx]}

    # PC1 → disjunction movers: biggest percentile gains (rise) and losses (fall)
    delta = pct_d - pct_s
    mv = np.argsort(-delta)
    movers = {"risers": [enrich(int(i)) for i in mv[:12]],
              "fallers": [enrich(int(i)) for i in mv[-12:][::-1]]}

    # validation: adventure/trick endemism under BOTH scores
    def endemism(vals):
        e, eo, bo = [], [], []
        for i, r in enumerate(mids):
            if str(r.get("motif_group_num")) not in ("10", "11"):
                continue
            ms = {macro(t) for t in (r.get("traditions") or [])}
            inA, inE = bool(ms & NEW_WORLD), bool(ms & EURO)
            (e if inA and not inE else eo if inE and not inA else bo if inA and inE else []).append(vals[i])
        m = lambda x: round(float(np.mean(x)), 1) if x else 0.0
        return {"endemic_amer": {"n": len(e), "mean": m(e)},
                "euro_only": {"n": len(eo), "mean": m(eo)},
                "both": {"n": len(bo), "mean": m(bo)}}
    valid = {"pc1": endemism(score), "disj": endemism(disj)}

    corr = {f: round(float(np.corrcoef(F[:, j], score)[0, 1]), 2) for j, f in enumerate(FEATURES)}
    corr_d = {f: round(float(np.corrcoef(F[:, j], disj)[0, 1]), 2) for j, f in enumerate(FEATURES)}

    data = {"n_motifs": len(mids), "min_trad": MIN_TRAD, "features": FEATURES,
            "corr": corr, "corr_disj": corr_d, "disj_w": DISJ_W,
            "hist": [int(h) for h in hist], "edges": [round(float(e), 1) for e in edges],
            "deepest": deepest, "shallowest": shallowest, "movers": movers,
            "anchors": anchors, "valid": valid}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";",
                   encoding="utf-8")
    print(f"{len(mids)} motifs scored · data.js ~{OUT.stat().st_size // 1024}KB")
    print(f"  endemism (endemic-Amer vs Euro-only):  PC1 {valid['pc1']['endemic_amer']['mean']} vs "
          f"{valid['pc1']['euro_only']['mean']}   disj {valid['disj']['endemic_amer']['mean']} vs "
          f"{valid['disj']['euro_only']['mean']}")
    print("  top risers under disjunction weighting:",
          [f"{m['c']}({m['s']:.0f}->{m['d']:.0f})" for m in movers["risers"][:6]])
    print("  top fallers:", [f"{m['c']}({m['s']:.0f}->{m['d']:.0f})" for m in movers["fallers"][:6]])


if __name__ == "__main__":
    main()
