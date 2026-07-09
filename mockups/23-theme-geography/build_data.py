"""Theme × geography (mockup 23) — where the thematic blocks concentrate.

Visualises the theme × area signal that macro-area-facets.md only states in prose. Three
views over the Berezkin catalogue:

1. Heatmap — 13 theme groups × 12 macro-areas, coloured by **lift** (observed vs expected
   attestations under independence): where each block is over- or under-represented.
2. Cluster map — traditions **co-clustered with themes** (SpectralCoclustering on the
   tradition × 13-theme proportion matrix), each cluster drawn as filled footprint blobs
   (mockup-15 style) and labelled by its defining themes. This is the traditions × themes
   analogue of mockup 15's traditions × motifs biclusters.
3. Theme picker — per-tradition theme shares + coordinates, so the page can shade the map
   by any single theme group.

Run:  python mockups/23-theme-geography/build_data.py
"""
import importlib.util
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.cluster.hierarchy import leaves_list, linkage, optimal_leaf_ordering
from scipy.spatial import ConvexHull, QhullError
from scipy.spatial.distance import squareform
from sklearn.cluster import DBSCAN, SpectralCoclustering

ROOT = Path(__file__).resolve().parents[2]
MOCKS = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "data.js"
MIN_MOTIF = 30       # traditions with a stable theme profile
K = 7                # co-clusters
TN = {1: "Sun & Moon", 2: "Stars", 3: "Cosmogony", 4: "Origin of death", 5: "Origin of humans",
      6: "Origin of subsistence", 7: "Plants & animals", 8: "Monstrous beings", 9: "Protagonist identity",
      10: "Adventures", 11: "Tricks & competitions", 12: "Proper names", 13: "Formulae"}
GROUPS = list(range(1, 14))
CLUSTER_COL = ["#6a5aa6", "#3c8a5e", "#c05540", "#b28a3e", "#4f7d99", "#8f6b9e", "#4c8c88"]

_spec = importlib.util.spec_from_file_location("m21", MOCKS / "21-facet-population" / "build_data.py")
m21 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(m21)


def _geo():
    spec = importlib.util.spec_from_file_location("_geo", MOCKS / "_geo.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


# --- footprint blobs (multi-component: one contour per dense region, per mockup 15) ---
def _ring(cx, cy, r, n=18):
    return [[round(cx + r * math.cos(2 * math.pi * i / n), 2),
             round(cy + r * math.sin(2 * math.pi * i / n), 2)] for i in range(n)]


def _buffer_hull(pts, pad):
    c = pts.mean(axis=0)
    try:
        verts = pts[ConvexHull(pts).vertices]
    except (QhullError, ValueError):
        r = float(np.max(np.linalg.norm(pts - c, axis=1))) + pad if len(pts) else pad
        return _ring(c[0], c[1], max(r, pad))
    out = []
    for v in verts:
        d = v - c; n = np.linalg.norm(d) or 1.0
        p = c + d + (d / n) * pad
        out.append([round(float(p[0]), 2), round(float(p[1]), 2)])
    return out


def _chaikin(poly, iters=2):
    for _ in range(iters):
        out = []
        for i in range(len(poly)):
            a, b = poly[i], poly[(i + 1) % len(poly)]
            out.append([round(a[0] * 0.75 + b[0] * 0.25, 2), round(a[1] * 0.75 + b[1] * 0.25, 2)])
            out.append([round(a[0] * 0.25 + b[0] * 0.75, 2), round(a[1] * 0.25 + b[1] * 0.75, 2)])
        poly = out
    return poly


def cluster_blobs(points, eps=18.0, pad=3.0):
    """points: [{x:lon, y:lat}]. One smoothed contour PER dense DBSCAN component, so a
    globally-spread theme cluster shows several regional footprints, not one planet-hull."""
    if not points:
        return []
    P = np.array([[p["x"], p["y"]] for p in points], dtype=float)
    blobs = []
    if len(P) >= 3:
        labels = DBSCAN(eps=eps, min_samples=3).fit(P).labels_
    else:
        labels = np.array([-1] * len(P))
    for lab in sorted(set(labels)):
        grp = P[labels == lab]
        if lab == -1 or len(grp) < 3:
            continue
        blobs.append(_chaikin(_buffer_hull(grp, pad)))
    if not blobs:                       # nothing dense enough -> small ring at centroid
        blobs = [_chaikin(_ring(P[:, 0].mean(), P[:, 1].mean(), pad + 1))]
    return blobs


def main():
    geo = _geo()
    coords = geo.berezkin_coords()
    with open(ROOT / "outputs" / "motifs" / "berezkin.json", encoding="utf-8") as f:
        bz = json.load(f)
    T = bz["motifs"], bz["traditions"]
    motifs, trads = T
    area_of = {tid: m21.area_of(v.get("areal_path") or []) for tid, v in trads.items()}

    # per-tradition theme counts + theme x area contingency (attestation level)
    tcount = defaultdict(lambda: np.zeros(14))      # tid -> counts over groups 1..13
    cont = np.zeros((13, len(m21.AREAS12)))
    aidx = {a: i for i, a in enumerate(m21.AREAS12)}
    for r in motifs:
        g = int(r.get("motif_group_num") or 0)
        if not (1 <= g <= 13):
            continue
        for tid in (r.get("traditions") or []):
            if tid in trads:
                tcount[tid][g] += 1
                a = area_of.get(tid)
                if a in aidx:
                    cont[g - 1, aidx[a]] += 1

    # heatmap: lift = observed / expected under independence, + share within area
    row = cont.sum(1, keepdims=True); col = cont.sum(0, keepdims=True); N = cont.sum()
    expected = row @ col / N
    lift = np.divide(cont, expected, out=np.ones_like(cont), where=expected > 0)
    share_area = np.divide(cont, col, out=np.zeros_like(cont), where=col > 0)   # theme share within area
    heat = {"areas": m21.AREAS12, "groups": [{"g": g, "name": TN[g]} for g in GROUPS],
            "lift": [[round(float(lift[i, j]), 2) for j in range(len(m21.AREAS12))] for i in range(13)],
            "share": [[round(float(100 * share_area[i, j])) for j in range(len(m21.AREAS12))] for i in range(13)]}

    # tradition x theme proportion matrix (>= MIN_MOTIF, with coords)
    tids, rows, pts_all = [], [], []
    for tid, cnt in tcount.items():
        tot = cnt[1:].sum()
        c = coords.get(tid)
        if tot >= MIN_MOTIF and isinstance(c, (list, tuple)) and len(c) == 2:
            tids.append(tid); rows.append(cnt[1:] / tot)
            pts_all.append({"x": round(float(c[1]), 2), "y": round(float(c[0]), 2)})
    M = np.array(rows)

    # co-cluster traditions x themes
    model = SpectralCoclustering(n_clusters=K, random_state=0)
    model.fit(M + 1e-9)
    rlab = model.row_labels_
    # order clusters by size, remap to contiguous ids
    order = [k for k, _ in Counter(rlab).most_common()]
    remap = {k: i for i, k in enumerate(order)}
    clusters, points = [], []
    for i in range(len(tids)):
        points.append({"x": pts_all[i]["x"], "y": pts_all[i]["y"], "k": remap[rlab[i]]})
    for k in order:
        members = [i for i in range(len(tids)) if rlab[i] == k]
        col_themes = [g for gi, g in enumerate(GROUPS) if model.columns_[k][gi]]
        mean_share = M[members].mean(0)
        top = sorted(GROUPS, key=lambda g: -mean_share[g - 1])[:3]
        areas = Counter(area_of.get(tids[i]) for i in members if area_of.get(tids[i]))
        cpts = [pts_all[i] for i in members]
        clusters.append({
            "id": remap[k], "n": len(members), "color": CLUSTER_COL[remap[k] % len(CLUSTER_COL)],
            "themes": [TN[g] for g in (col_themes or top)][:3],
            "top": [{"name": TN[g], "pct": round(float(100 * mean_share[g - 1]))} for g in top],
            "areas": [{"name": a, "n": n} for a, n in areas.most_common(3)],
            "blobs": cluster_blobs(cpts)})
    clusters.sort(key=lambda c: c["id"])

    # theme picker: per-tradition share vector + coords
    pick = [{"x": pts_all[i]["x"], "y": pts_all[i]["y"],
             "s": [round(float(M[i, g - 1]), 3) for g in GROUPS]} for i in range(len(tids))]

    # theme co-occurrence: correlation of theme shares across traditions, on the CLR
    # transform so the constant-sum (compositional) closure doesn't make the dominant
    # blocks spuriously anti-correlate with everything. Rows/cols are SERIATED (hierarchical
    # clustering + optimal leaf ordering) so co-occurring blocks sit adjacent.
    L = np.log(M + 0.005); L = L - L.mean(1, keepdims=True)
    corr = np.corrcoef(L.T)
    dist = squareform(np.clip(1 - corr, 0, 2), checks=False)
    Z = optimal_leaf_ordering(linkage(dist, method="average"), dist)
    seri = list(leaves_list(Z))                         # order over 0..12
    cooc = {"order": [GROUPS[i] for i in seri],
            "groups": [{"g": GROUPS[i], "name": TN[GROUPS[i]]} for i in seri],
            "m": [[round(float(corr[seri[i], seri[j]]), 2) for j in range(13)] for i in range(13)]}

    data = {"heat": heat, "cooc": cooc, "clusters": clusters, "points": points, "pick": pick,
            "groups": [{"g": g, "name": TN[g]} for g in GROUPS], "n_trad": len(tids),
            "n_area": len(m21.AREAS12)}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"{len(tids)} traditions profiled · {K} co-clusters · heatmap 13x{len(m21.AREAS12)}")
    for c in clusters:
        print(f"  cluster {c['id']}: n={c['n']:3} themes={c['themes']} areas={[a['name'] for a in c['areas']]}")
    # a couple of headline lifts
    b_eur = lift[9, aidx["Europe"]]; b_meso = lift[9, aidx["Mesoamerica & Andes"]]
    print(f"  Adventures lift: Europe {b_eur:.2f} vs Mesoamerica-Andes {b_meso:.2f}")


if __name__ == "__main__":
    main()
