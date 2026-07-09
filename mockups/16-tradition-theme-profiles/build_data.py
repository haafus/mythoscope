"""Tradition thematic-profile clustering (mockup 16).

Each Berezkin tradition has a 13-dim `theme_profile`: the proportion of its attested
motifs falling in each of Berezkin's 13 thematic groups. This clusters traditions by
that profile alone (no geography, no language) and plots the clusters on the world map
— testing whether the genre balance of a tradition's corpus is a signal, and whether it
groups cultures across geography (see docs/motifs/proposals/macro-area-facets.md).

Run:  python mockups/16-tradition-theme-profiles/build_data.py
"""
import importlib.util
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from sklearn.cluster import KMeans

ROOT = Path(__file__).resolve().parents[2]
MOCKS = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "data.js"

K = 8            # clusters
MIN_MOTIFS = 30  # traditions with fewer attested motifs are too noisy to profile
PALETTE = ["#2f6fed", "#12a150", "#d97706", "#9151d8", "#0e9aa7", "#c2410c",
           "#e11d48", "#7d8b3a", "#0891b2", "#a3457e"]
THEMES = ["Sun & Moon", "Stars & constellations", "Cosmogony & elements",
          "Origin of death", "Origin of humans", "Origin of subsistence",
          "Plants & animals", "Monstrous beings", "Protagonist identity",
          "Adventures", "Tricks & competitions", "Proper names", "Formulae"]


def _geo():
    spec = importlib.util.spec_from_file_location("_geo", MOCKS / "_geo.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _sunflower(j, n):
    r = math.sqrt((j + 0.5) / n)
    a = j * math.pi * (3 - math.sqrt(5))
    return r * math.cos(a), r * math.sin(a)


def main():
    geo = _geo()
    coords = geo.berezkin_coords()   # areal_id -> [lat, lon], from tradition-coords.json
    with open(ROOT / "outputs" / "motifs" / "berezkin.json", encoding="utf-8") as f:
        bz = json.load(f)
    T = bz["traditions"]

    # per-tradition 13-dim theme counts
    prof = defaultdict(lambda: np.zeros(13))
    for r in bz["motifs"]:
        g = r.get("motif_group_num")
        if not g:
            continue
        gi = int(g) - 1
        if not 0 <= gi < 13:
            continue
        for tid in (r.get("traditions") or []):
            prof[tid][gi] += 1

    kept = [t for t, v in prof.items() if v.sum() >= MIN_MOTIFS]
    X = np.array([prof[t] / prof[t].sum() for t in kept])

    # variance in theme-profile explained by macro-area (the signal statistic)
    def macro(t):
        ap = T[t].get("areal_path") or []
        return ap[0][1] if ap else "?"
    macros = np.array([macro(t) for t in kept])
    gm = X.mean(0)
    tot = ((X - gm) ** 2).sum()
    between = sum(len(X[macros == m]) * ((X[macros == m].mean(0) - gm) ** 2).sum()
                 for m in set(macros))
    var_by_macro = round(100 * between / tot)

    km = KMeans(n_clusters=K, random_state=0, n_init=10).fit(X)
    labels = km.labels_

    # resolve a coordinate per tradition: real coord, else areal-subregion centroid
    def coord(t):
        c = coords.get(t)
        if isinstance(c, (list, tuple)) and len(c) == 2:
            return float(c[1]), float(c[0])   # [lat,lon] -> (lon,lat)
        ap = T[t].get("areal_path") or []
        if len(ap) >= 2:
            cen = geo.SUBREGION.get(ap[1][1].upper())
            if cen:
                return float(cen[0]), float(cen[1])
        return None

    # points, spread within a shared base coordinate so nothing piles up
    raw = []
    for i, t in enumerate(kept):
        xy = coord(t)
        if xy:
            raw.append((i, xy[0], xy[1]))
    groups = defaultdict(list)
    for idx, lon, lat in raw:
        groups[(round(lon, 2), round(lat, 2))].append(idx)
    xy_by_i = {}
    for (lon, lat), members in groups.items():
        members.sort(key=lambda i: kept[i])
        n = len(members)
        span = 1.1 * math.sqrt(n)
        for j, idx in enumerate(members):
            ox, oy = _sunflower(j, n)
            xy_by_i[idx] = (round(lon + ox * span * 1.35, 2), round(lat + oy * span, 2))

    points = [{"x": xy_by_i[i][0], "y": xy_by_i[i][1], "k": int(labels[i])}
              for i in range(len(kept)) if i in xy_by_i]

    # per-cluster summary
    natt = {t: int(prof[t].sum()) for t in kept}
    clusters = []
    for c in range(K):
        idx = np.where(labels == c)[0]
        mean = X[idx].mean(0)
        top = [int(i) for i in mean.argsort()[::-1][:4]]
        regions = Counter(macros[idx]).most_common(4)
        examples = sorted((kept[i] for i in idx), key=lambda t: -natt[t])[:8]
        clusters.append({
            "id": c, "color": PALETTE[c % len(PALETTE)], "n": len(idx),
            "profile": [round(float(v), 3) for v in mean],
            "top": [{"i": i, "name": THEMES[i], "v": round(float(mean[i]), 3)} for i in top],
            "regions": [{"name": m, "n": n} for m, n in regions if m != "?"],
            "examples": [T[t].get("name", "") for t in examples],
        })
    clusters.sort(key=lambda c: -c["n"])

    data = {"themes": THEMES, "k": K, "n_trad": len(kept),
            "min_motifs": MIN_MOTIFS, "var_by_macro": var_by_macro,
            "clusters": clusters, "points": points}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";",
                   encoding="utf-8")
    placed = len(points)
    print(f"{len(kept)} traditions profiled · {K} clusters · {placed} placed · "
          f"var-by-macro {var_by_macro}% · data.js ~{OUT.stat().st_size // 1024}KB")


if __name__ == "__main__":
    main()
