"""Motif map explorer (mockup 40) — pick a motif, see its traditions drawn and its clusters
outlined on the map, alongside a depth-ranked list.

Two views over the same corpus:

  * a **depth-ranked list** of every motif (deep/broad -> local), each row carrying a compact
    12-area **footprint** sparkline (where it is attested) — the "depth x geography" table;
  * a **map**: selecting a motif plots its attesting traditions as points and outlines each
    geographic **cluster** with a smoothed contour (DBSCAN groups; strays stay bare). Works on
    the *whole* corpus (breadth proxy, mockup 17), not only the datable descent minority (31).

Motif depth proxy = breadth (# attesting traditions, mockup 17): deep >= 85th pct, areal 50-85th,
local < 50th — the same tiers as mockup 39. Cluster hulls reuse mockup 15's buffered-Chaikin
contour; the map re-centres on the selected motif's region (mockup 31) so a Pacific-diffusion
motif is not torn by the Atlantic seam.

Run:  python mockups/40-motif-map-explorer/build_data.py
"""
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.spatial import ConvexHull, QhullError
from sklearn.cluster import DBSCAN

ROOT = Path(__file__).resolve().parents[2]
MOCKS = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
OUT = HERE / "data.js"
MIN_PLACED = 4          # a motif needs this many locatable traditions to be worth mapping
EPS, PAD = 22.0, 3.2    # DBSCAN cluster radius (deg) · hull buffer (deg)


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, MOCKS / rel)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


# --- cluster contour helpers (from mockup 15, adapted to return one hull per cluster) ------- #
def _ring(cx, cy, r, n=12):
    return [[round(cx + r * math.cos(2 * math.pi * i / n), 2),
             round(cy + r * math.sin(2 * math.pi * i / n), 2)] for i in range(n)]


def _buffer_hull(pts, pad):
    c = pts.mean(axis=0)
    try:
        verts = pts[ConvexHull(pts).vertices]
    except (QhullError, ValueError):
        r = float(np.max(np.linalg.norm(pts - c, axis=1))) + pad
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


def _unwrap_lon(P):
    """Unwrap longitudes around their circular mean so a seam-straddling group is contiguous."""
    lon = P[:, 0]
    mx = math.degrees(math.atan2(np.mean(np.sin(np.radians(lon))), np.mean(np.cos(np.radians(lon)))))
    P = P.copy()
    P[:, 0] = mx + ((lon - mx + 180) % 360) - 180
    return P


def cluster_points_and_hulls(pts):
    """pts: list of (lon, lat). Returns (labelled_points, hulls). DBSCAN groups nearby
    traditions; each dense group gets its own smoothed contour, strays (label -1) stay bare."""
    P = np.array(pts, float)
    if len(P) >= 2:
        labels = DBSCAN(eps=EPS, min_samples=2).fit(_unwrap_lon(P)).labels_
    else:
        labels = np.array([-1] * len(P))
    hulls = []
    for lab in sorted(set(labels) - {-1}):
        grp = P[labels == lab]
        if len(grp) < 2:
            continue
        ring = _chaikin(_buffer_hull(_unwrap_lon(grp), PAD), iters=1)   # unwrap around this cluster's own mean
        hulls.append({"k": int(lab), "ring": [[round(float(x), 1), round(float(y), 1)] for x, y in ring]})
    labelled = [[round(float(lo), 1), round(float(la), 1), int(lab)] for (lo, la), lab in zip(pts, labels, strict=True)]
    return labelled, hulls


GROUPS = {1: "Солнце/Луна", 2: "Звёзды", 3: "Космогония", 4: "Смерть", 5: "Происх. людей",
          6: "Культура", 7: "Флора/фауна", 8: "Чудовища", 9: "Отождествления",
          10: "Приключения", 11: "Трюки/обман", 12: "Имена", 13: "Формулы"}


def main():
    geo = _load("_geo.py", "geo")
    m21 = _load("21-facet-population/build_data.py", "m21")
    with open(ROOT / "outputs" / "motifs" / "berezkin.json", encoding="utf-8") as f:
        bz = json.load(f)
    T, motifs = bz["traditions"], bz["motifs"]
    coords = geo.berezkin_coords()
    AREAS = m21.AREAS12
    area_ix = {a: i for i, a in enumerate(AREAS)}

    def coord(t):
        c = coords.get(t)
        if isinstance(c, (list, tuple)) and len(c) == 2:
            return float(c[1]), float(c[0])            # -> (lon, lat)
        ap = T[t].get("areal_path") or []
        if len(ap) >= 2:
            cen = geo.SUBREGION.get(ap[1][1].upper())
            if cen:
                return float(cen[0]), float(cen[1])
        return None

    breadth = {r["id"]: len(r.get("traditions") or []) for r in motifs}
    bvals = np.array(list(breadth.values()))
    p50, p85 = int(np.percentile(bvals, 50)), int(np.percentile(bvals, 85))

    def tier(b):
        return "deep" if b >= p85 else "areal" if b >= p50 else "local"

    out = []
    for r in motifs:
        trads = r.get("traditions") or []
        pts = [coord(t) for t in trads]
        pts = [p for p in pts if p]
        if len(pts) < MIN_PLACED:
            continue
        # de-duplicate identical points (many traditions share a subregion centroid)
        seen, upts = set(), []
        for p in pts:
            key = (round(p[0], 1), round(p[1], 1))
            if key not in seen:
                seen.add(key); upts.append(p)
        labelled, hulls = cluster_points_and_hulls(upts)
        fp = [0] * len(AREAS)
        for t in trads:
            a = m21.area_of(T[t].get("areal_path") or [])
            if a in area_ix:
                fp[area_ix[a]] += 1
        b = breadth[r["id"]]
        out.append({
            "c": r["id"], "name": r.get("name", r["id"]), "ru": (r.get("name_rus") or "").strip(),
            "b": b, "tier": tier(b), "g": int(r.get("motif_group_num") or 0),
            "np": len(upts), "nc": len(hulls), "fp": fp,
            "pts": labelled, "hulls": hulls,
        })

    out.sort(key=lambda m: -m["b"])
    tier_n = Counter(m["tier"] for m in out)
    data = {
        "n": len(out), "n_motif_total": len(motifs), "p50": p50, "p85": p85,
        "min_placed": MIN_PLACED, "areas": AREAS, "groups": GROUPS,
        "tier_n": {k: tier_n.get(k, 0) for k in ("deep", "areal", "local")},
        "motifs": out,
    }
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False,
                                                 separators=(",", ":")) + ";", encoding="utf-8")
    print(f"{len(out)} mappable motifs (>= {MIN_PLACED} placed traditions) of {len(motifs)} total")
    print(f"  depth tiers: deep {tier_n['deep']} · areal {tier_n['areal']} · local {tier_n['local']}"
          f"  (breadth >= {p85} deep, < {p50} local)")
    print(f"  multi-cluster motifs: {sum(1 for m in out if m['nc'] >= 2)}"
          f" · data.js ~{OUT.stat().st_size // 1024}KB")


if __name__ == "__main__":
    main()
