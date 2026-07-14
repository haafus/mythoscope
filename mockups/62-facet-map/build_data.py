"""62 · Facet map — one world map, switch the tradition facet.

Colours the same set of Berezkin traditions on the world map by a chosen facet:
`area` (12, from areal_path), `family` (11, from language), or the dominant
`theme` group (13, argmax of the theme profile). `subsistence` is listed but has
no data source yet (needs a D-PLACE join) — it shows as a disabled facet so the
gap is visible rather than hidden. Reuses mockup 21's area/family functions and
mockup 16's coordinate resolution + jitter.

Run:  python mockups/62-facet-map/build_data.py
"""
import importlib.util
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import rankdata
from sklearn.cluster import KMeans

ROOT = Path(__file__).resolve().parents[2]
MOCKS = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "data.js"

K_CLUSTERS = 8  # tradition profile clusters (KMeans over the 16-dim narrative profile)

MIN_MOTIFS = 30  # below this a narrative profile is too noisy to call a dominant cluster

# Subsistence comes from D-PLACE (nearest society), reusing mockup 22's snapshot.
SUB_ORDER = ["forager", "pastoralist", "horticulturalist", "agrarian_state"]
SUB_LABEL = {"forager": "Foragers", "pastoralist": "Pastoralists",
             "horticulturalist": "Horticulturalists", "agrarian_state": "Agrarian states"}
MATCH_KM = 250.0  # a nearest-society join farther than this is dropped (too weak)

# One 16-colour qualitative ramp, sliced per facet (fixed order, never cycled).
RAMP = ["#2f6fed", "#12a150", "#d97706", "#9151d8", "#0e9aa7", "#c2410c",
        "#e11d48", "#7d8b3a", "#0891b2", "#a3457e", "#4338ca", "#65a30d",
        "#be123c", "#0f766e", "#7c3aed", "#b45309"]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _sunflower(j, n):
    r = math.sqrt((j + 0.5) / n)
    a = j * math.pi * (3 - math.sqrt(5))
    return r * math.cos(a), r * math.sin(a)


def _haversine(lat, lon, lats, lons):
    lat, lon = math.radians(lat), math.radians(lon)
    lats, lons = np.radians(lats), np.radians(lons)
    dlat, dlon = lats - lat, lons - lon
    h = np.sin(dlat / 2) ** 2 + math.cos(lat) * np.cos(lats) * np.sin(dlon / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(h))


def main():
    geo = _load("_geo", MOCKS / "_geo.py")
    f21 = _load("_f21", MOCKS / "21-facet-population" / "build_data.py")
    coords = geo.berezkin_coords()

    with open(ROOT / "outputs" / "motifs" / "berezkin.json", encoding="utf-8") as f:
        bz = json.load(f)
    T = bz["traditions"]

    # Data-driven narrative clusters (mockup 41): each motif → one of 16 named clusters.
    # The dominant theme (Berezkin's 13) is uninformative — "Adventures" swamps everything —
    # so the theme facet uses the balanced narrative clusters instead.
    with open(MOCKS / "41-theme-rederivation" / "narrative_taxonomy.json", encoding="utf-8") as f:
        tax = json.load(f)
    NT = tax["motifs"]
    NARR = [c["name"] for c in sorted(tax["clusters"], key=lambda c: c["l1"])]

    # per-tradition narrative-cluster counts → dominant cluster
    prof = defaultdict(lambda: np.zeros(len(NARR)))
    for r in bz["motifs"]:
        nt = NT.get(r["id"])
        if nt:
            for tid in (r.get("traditions") or []):
                prof[tid][nt["l1"]] += 1

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

    # D-PLACE societies (id, name, lat, lon, subsistence bucket) — mockup 22's snapshot.
    with open(MOCKS / "22-subsistence-external" / "dplace_subsistence.json", encoding="utf-8") as f:
        dp = json.load(f)
    dp_lat = np.array([s["lat"] for s in dp])
    dp_lon = np.array([s["lon"] for s in dp])
    dp_sub = [s["s"] for s in dp]

    area_ix = {a: i for i, a in enumerate(f21.AREAS12)}
    fam_ix = {a: i for i, a in enumerate(f21.FAMILIES11)}
    sub_ix = {s: i for i, s in enumerate(SUB_ORDER)}

    recs = []  # [tid, lon, lat, area_idx, fam_idx, narr_cluster, sub_idx]  (-1 = no value)
    prof_rows, prof_tids = [], []   # narrative profiles of placed, well-attested traditions
    for t, v in T.items():
        xy = coord(t)
        if not xy:
            continue
        lon, lat = xy
        ap = v.get("areal_path") or []
        area = f21.area_of(ap)
        lang0 = (v.get("language") or [None])[0]
        family, _ = f21.family_of(lang0, area)
        d = _haversine(lat, lon, dp_lat, dp_lon)
        j = int(np.argmin(d))
        sub = sub_ix[dp_sub[j]] if d[j] <= MATCH_KM else -1
        recs.append([t, lon, lat, area_ix.get(area, -1), fam_ix.get(family, -1), -1, sub])
        p = prof.get(t)
        if p is not None and p.sum() >= MIN_MOTIFS:
            prof_rows.append(p / p.sum())
            prof_tids.append(t)

    # Cluster the traditions by their narrative profile (mockup 43's move), then colour
    # each tradition by its profile cluster — not by a single dominant motif group.
    X = np.array(prof_rows)
    labels = KMeans(n_clusters=K_CLUSTERS, random_state=0, n_init=10).fit(X).labels_
    sizes = [int((labels == c).sum()) for c in range(K_CLUSTERS)]
    order = sorted(range(K_CLUSTERS), key=lambda c: -sizes[c])   # biggest cluster first
    remap = {c: i for i, c in enumerate(order)}
    # Name a cluster by what it over-represents vs the global mean (its *distinctive*
    # complexes), not its biggest dims — those are shared across clusters and don't separate them.
    gm = X.mean(0)
    cluster_names = [" · ".join(NARR[k] for k in (X[labels == c].mean(0) - gm).argsort()[::-1][:2])
                     for c in order]
    tid_cluster = {t: remap[int(labels[i])] for i, t in enumerate(prof_tids)}
    for r in recs:
        r[5] = tid_cluster.get(r[0], -1)

    # spread points sharing a base coordinate so nothing piles up (mockup 16 recipe)
    groups = defaultdict(list)
    for i, r in enumerate(recs):
        groups[(round(r[1], 2), round(r[2], 2))].append(i)
    xy_by_i = {}
    for (lon, lat), members in groups.items():
        members.sort(key=lambda i: recs[i][0])
        n = len(members)
        span = 1.1 * math.sqrt(n)
        for j, i in enumerate(members):
            ox, oy = _sunflower(j, n)
            xy_by_i[i] = (round(lon + ox * span * 1.35, 2), round(lat + oy * span, 2))

    # Motif diversity (mockup 52): β-turnover (γ/α) per macro-area, broadcast to its traditions.
    # Continuous, not categorical: α (per-tradition richness) tracks cataloguing effort; β does not.
    tmot = defaultdict(set)
    for k, m in enumerate(bz["motifs"]):
        for t in (m.get("traditions") or []):
            tmot[t].add(k)

    def _macro(t):
        ap = T[t].get("areal_path") or []
        return ap[0][1] if ap and ap[0] else None

    by_macro = defaultdict(list)
    for r in recs:
        if len(tmot[r[0]]) >= 15:
            by_macro[_macro(r[0])].append(r[0])
    area_beta = {}
    for a, ts in by_macro.items():
        if a is None or len(ts) < 8:
            continue
        alpha = float(np.mean([len(tmot[t]) for t in ts]))
        area_beta[a] = len(set().union(*[tmot[t] for t in ts])) / alpha
    tid_beta = {r[0]: area_beta[_macro(r[0])] for r in recs if _macro(r[0]) in area_beta}

    # Tradition depth = mean depth-rank of its motifs. Motif depth = breadth (# attesting
    # traditions, mockup 17); breadth is heavy-tailed, so a raw mean is distorted by the few
    # pan-global motifs. Rank-transform each motif's breadth to a 0–1 percentile first, then
    # average over the tradition: bounded, robust, and uses every motif (not just a top tier).
    breadth = np.array([len(m.get("traditions") or []) for m in bz["motifs"]])
    rank = (rankdata(breadth, method="average") - 1) / (len(breadth) - 1)   # 0..1 depth percentile
    tid_depth = {}
    for r in recs:
        ms = list(tmot[r[0]])
        if len(ms) >= 8:
            tid_depth[r[0]] = float(np.mean([rank[k] for k in ms]))

    # Histogram-equalize the depth for the map: colour by a tradition's depth *rank* among all
    # traditions (0–1), so the concentrated middle of the distribution spreads across the full
    # ramp instead of collapsing to one shade. Raw values are kept for the legend range.
    srt = sorted(tid_depth, key=lambda t: tid_depth[t])
    depth_eq = {t: i / (len(srt) - 1) for i, t in enumerate(srt)} if len(srt) > 1 else {}

    points = [{"x": xy_by_i[i][0], "y": xy_by_i[i][1],
               "a": r[3], "f": r[4], "n": r[5], "s": r[6],
               "d": round(tid_beta[r[0]], 3) if r[0] in tid_beta else None,
               "p": round(depth_eq[r[0]], 3) if r[0] in depth_eq else None}
              for i, r in enumerate(recs)]

    def facet(label, cats, key, colors=None):
        counts = Counter(p[key] for p in points if p[key] >= 0)
        return {
            "label": label,
            "cats": [{"name": c, "color": (colors or RAMP)[i % len(colors or RAMP)],
                      "n": counts.get(i, 0)}
                     for i, c in enumerate(cats)],
        }

    # forager · pastoralist · horticulturalist · agrarian_state — a jewel/earth set:
    # slate-blue / terracotta / teal-green / plum. Contrasting but not flat primaries.
    sub_colors = ["#3f6f9e", "#cc7a33", "#2f8f6b", "#9c4576"]
    betas = list(tid_beta.values())
    depths = list(tid_depth.values())
    facets = {
        "area": facet(f"Area · {len(f21.AREAS12)}", f21.AREAS12, "a"),
        "family": facet(f"Family · {len(f21.FAMILIES11)}", f21.FAMILIES11, "f"),
        "narrative": facet(f"Narrative profile cluster · {K_CLUSTERS}", cluster_names, "n"),
        "subsistence": facet("Subsistence · 4",
                             [SUB_LABEL[s] for s in SUB_ORDER], "s", sub_colors),
        "diversity": {
            "label": "Motif diversity · β-turnover",
            "kind": "continuous", "key": "d", "unit": "β = γ/α",
            "min": round(min(betas), 2), "max": round(max(betas), 2),
            # mockup 52's blue→red β scale, blue end softened (lighter, less saturated).
            "ramp": ["#83a4c6", "#e65a46"],
            "note": "β-turnover (γ/α) per macro-area (mockup 52): low = homogeneous shared stock "
                    "(diffusion belt), high = internally divergent. α richness is effort-confounded; β is not.",
        },
        "depth": {
            "label": "Tradition depth · mean rank",
            "kind": "continuous", "key": "p", "unit": "перцентиль среди традиций",
            "min": 0, "max": 1,
            # high-contrast light→dark (YlOrRd): shallow = pale, deep = dark red.
            "ramp": ["#ffffcc", "#fed976", "#feb24c", "#fd8d3c", "#f03b20", "#bd0026"],
            "note": f"mean depth-rank of a tradition's motifs (each motif's breadth, mockup 17, as a "
                    f"0–1 percentile, averaged), then histogram-equalized for contrast — colour = rank "
                    f"among traditions (raw mean-rank {min(depths):.2f}–{max(depths):.2f}). Deep = older/broader stock.",
        },
    }
    facets["subsistence"]["note"] = f"nearest D-PLACE society ≤ {MATCH_KM:.0f} km (mockup 22)"

    data = {"facets": facets,
            "order": ["area", "family", "narrative", "subsistence", "diversity", "depth"],
            "points": points, "n": len(points), "min_motifs": MIN_MOTIFS}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";",
                   encoding="utf-8")
    n_narr = sum(1 for p in points if p["n"] >= 0)
    print(f"{len(points)} placed · {n_narr} narrative-clustered · {len(tid_beta)} β-diversity "
          f"· {len(tid_depth)} depth (mean-rank {min(depths):.2f}–{max(depths):.2f})")


if __name__ == "__main__":
    main()
