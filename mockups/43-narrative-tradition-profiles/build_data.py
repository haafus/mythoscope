"""Narrative tradition profiles (mockup 43) — mockup 16 re-run on the data-driven facet.

Same idea as mockup 16 (cluster traditions by the genre balance of their corpus, plot on the
map), but the profile is the **16-dim narrative-cluster distribution** (mockup 41's taxonomy)
instead of Berezkin's 13 hand themes. Justified by mockup 42: the narrative profile is a strictly
better tradition descriptor (it subsumes the theme profile on the Jaccard-ΔR² test). This asks
whether the *better* descriptor also gives a sharper / more cross-continental tradition grouping.

Reports var-by-macro for BOTH profiles on the same working set, so the two are directly comparable.

Run:  python mockups/43-narrative-tradition-profiles/build_data.py
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
HERE = Path(__file__).resolve().parent
OUT = HERE / "data.js"
K = 8
MIN_MOTIFS = 30
PALETTE = ["#2f6fed", "#12a150", "#d97706", "#9151d8", "#0e9aa7", "#c2410c",
           "#e11d48", "#7d8b3a", "#0891b2", "#a3457e"]


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, MOCKS / rel)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def _sunflower(j, n):
    r = math.sqrt((j + 0.5) / n); a = j * math.pi * (3 - math.sqrt(5))
    return r * math.cos(a), r * math.sin(a)


def var_by_macro(X, macros):
    gm = X.mean(0); tot = ((X - gm) ** 2).sum()
    between = sum(len(X[macros == m]) * ((X[macros == m].mean(0) - gm) ** 2).sum() for m in set(macros))
    return round(100 * between / tot)


def _need(p, hint=""):
    """Fail with a clear message (not a raw traceback) when a required input is absent."""
    if not p.exists():
        raise SystemExit(f"\n✗ missing input: {p}" + (f"\n  → {hint}\n" if hint else "\n"))
    return p


def main():
    geo = _load("_geo.py", "geo")
    coords = geo.berezkin_coords()
    bz = json.loads(_need(ROOT / "outputs/motifs/berezkin.json",
                          "build the motif DB first: `mytho motifs`").read_text("utf-8"))
    T = bz["traditions"]
    tax = json.loads(_need(MOCKS / "41-theme-rederivation/narrative_taxonomy.json",
                           "run `python mockups/41-theme-rederivation/build_data.py` first"
                           ).read_text("utf-8"))
    NT = tax["motifs"]
    NAMES = [c["name"] for c in sorted(tax["clusters"], key=lambda c: c["l1"])]
    K1 = len(NAMES)

    narr = defaultdict(lambda: np.zeros(K1))
    theme = defaultdict(lambda: np.zeros(13))
    for r in bz["motifs"]:
        nt = NT.get(r["id"]); g = r.get("motif_group_num")
        for tid in (r.get("traditions") or []):
            if nt:
                narr[tid][nt["l1"]] += 1
            if g and 1 <= int(g) <= 13:
                theme[tid][int(g) - 1] += 1

    kept = [t for t, v in narr.items() if v.sum() >= MIN_MOTIFS]
    X = np.array([narr[t] / narr[t].sum() for t in kept])
    Xtheme = np.array([theme[t] / theme[t].sum() if theme[t].sum() else theme[t] for t in kept])

    def macro(t):
        ap = T[t].get("areal_path") or []
        return ap[0][1] if ap else "?"
    macros = np.array([macro(t) for t in kept])
    var_narr = var_by_macro(X, macros)
    var_theme = var_by_macro(Xtheme, macros)

    km = KMeans(n_clusters=K, random_state=0, n_init=10).fit(X)
    labels = km.labels_

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

    raw = [(i, *coord(t)) for i, t in enumerate(kept) if coord(t)]
    groups = defaultdict(list)
    for idx, lon, lat in raw:
        groups[(round(lon, 2), round(lat, 2))].append(idx)
    xy_by_i = {}
    for (lon, lat), members in groups.items():
        members.sort(key=lambda i: kept[i]); n = len(members); span = 1.1 * math.sqrt(n)
        for j, idx in enumerate(members):
            ox, oy = _sunflower(j, n)
            xy_by_i[idx] = (round(lon + ox * span * 1.35, 2), round(lat + oy * span, 2))
    points = [{"x": xy_by_i[i][0], "y": xy_by_i[i][1], "k": int(labels[i])}
              for i in range(len(kept)) if i in xy_by_i]

    natt = {t: int(narr[t].sum()) for t in kept}
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
            "top": [{"i": i, "name": NAMES[i], "v": round(float(mean[i]), 3)} for i in top],
            "regions": [{"name": m, "n": n} for m, n in regions if m != "?"],
            "examples": [T[t].get("name", "") for t in examples],
            "n_macro": len({m for m in macros[idx] if m != "?"}),
        })
    clusters.sort(key=lambda c: -c["n"])

    data = {"dims": NAMES, "k": K, "n_trad": len(kept), "min_motifs": MIN_MOTIFS,
            "var_by_macro": var_narr, "var_by_macro_theme": var_theme,
            "clusters": clusters, "points": points}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"{len(kept)} traditions profiled (16-dim narrative) · {K} clusters · {len(points)} placed")
    print(f"  var-by-macro: narrative {var_narr}%  vs  13-theme {var_theme}%  (lower = more geography-orthogonal)")
    for c in clusters:
        print(f"  [{c['id']}] n={c['n']:3} spans {c['n_macro']:2} macro-areas · top: "
              f"{', '.join(t['name'][:22] for t in c['top'][:2])}")


if __name__ == "__main__":
    main()
