"""Facet showdown (mockup 42) — do the data-driven narrative clusters beat Berezkin's 13 hand
themes as a tradition facet? Empirical head-to-head on two established metrics:

  * TEST A (mockup 32) — unique contribution ΔR²: predict pairwise tradition motif-set Jaccard
    from {area, family, subsistence} ± a theme facet. Δ = R²(with) − R²(without) = the variance
    ONLY that facet explains. Also the subsumption test: each facet's unique Δ when BOTH are in.
  * TEST B (mockup 23) — theme × area signal: Cramér's V and mean top-area share of the theme
    labels over motif attestations. Higher = sharper areal concentration.

Compares three theme facets on the same working set: Berezkin's **13 hand themes**, the
**16 narrative clusters**, and the **61 narrative sub-themes** (from narrative_taxonomy.json).
Reproduces mockup 32's published theme ΔR² = 0.125 exactly, so the comparison is faithful.

Run:  python mockups/42-facet-showdown/build_data.py
"""
import importlib.util
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MOCKS = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
OUT = HERE / "data.js"
MATCH_KM, MIN_MOTIF = 600.0, 15


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, MOCKS / rel)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def haversine(lat1, lon1, lat2, lon2):
    r1, r2 = np.radians(lat1), np.radians(lat2)
    dlat, dlon = np.radians(lat2 - lat1), np.radians(lon2 - lon1)
    a = np.sin(dlat / 2) ** 2 + np.cos(r1) * np.cos(r2) * np.sin(dlon / 2) ** 2
    return 6371 * 2 * np.arcsin(np.sqrt(a))


def cramers_v(x, y):
    xs = {v: i for i, v in enumerate(sorted(set(x)))}
    ys = {v: i for i, v in enumerate(sorted(set(y)))}
    tab = np.zeros((len(xs), len(ys)))
    for a, b in zip(x, y, strict=True):
        tab[xs[a], ys[b]] += 1
    n = tab.sum(); r, c = tab.shape
    exp = tab.sum(1, keepdims=True) @ tab.sum(0, keepdims=True) / n
    chi2 = ((tab - exp) ** 2 / np.where(exp > 0, exp, 1)).sum()
    return float(np.sqrt((chi2 / n) / max(1, min(r - 1, c - 1))))


def mean_max_share(lab, area):
    tot = 0.0; labs = set(lab)
    for L in labs:
        aa = area[lab == L]
        tot += max((aa == a).mean() for a in set(aa))
    return tot / len(labs)


def main():
    geo = _load("_geo.py", "geo")
    m21 = _load("21-facet-population/build_data.py", "m21")
    coords = geo.berezkin_coords()
    bz = json.loads((ROOT / "outputs/motifs/berezkin.json").read_text("utf-8"))
    T, motifs = bz["traditions"], bz["motifs"]
    tax = json.loads((MOCKS / "41-theme-rederivation/narrative_taxonomy.json").read_text("utf-8"))
    NT = tax["motifs"]
    subbase, acc = {}, 0
    for c in tax["clusters"]:
        subbase[c["l1"]] = acc; acc += len(c["subs"])
    K1, KSUB = len(tax["clusters"]), acc

    dp = json.loads((MOCKS / "22-subsistence-external/dplace_subsistence.json").read_text("utf-8"))
    dlat, dlon = np.array([d["lat"] for d in dp]), np.array([d["lon"] for d in dp])

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

    sub_of = {}
    for tid in T:
        c = coord(tid)
        if c is None:
            continue
        d = haversine(c[0], c[1], dlat, dlon); j = int(np.argmin(d))
        if float(d[j]) <= MATCH_KM:
            sub_of[tid] = dp[j]["s"]

    trad_motifs = defaultdict(set)
    theme_cnt = defaultdict(lambda: np.zeros(13))
    narr_cnt = defaultdict(lambda: np.zeros(K1))
    sub_cnt = defaultdict(lambda: np.zeros(KSUB))
    for mi, r in enumerate(motifs):
        g = int(r.get("motif_group_num") or 0); nt = NT.get(r["id"])
        for t in (r.get("traditions") or []):
            if t in T:
                trad_motifs[t].add(mi)
                if 1 <= g <= 13:
                    theme_cnt[t][g - 1] += 1
                if nt:
                    narr_cnt[t][nt["l1"]] += 1
                    sub_cnt[t][subbase[nt["l1"]] + nt["l2"]] += 1

    rows, meta = [], []
    for tid, v in T.items():
        ap = v.get("areal_path") or []
        area = m21.area_of(ap); lang0 = (v.get("language") or [None])[0]
        fam, _ = m21.family_of(lang0, area); sub = sub_of.get(tid)
        if area and fam and sub and len(trad_motifs.get(tid, ())) >= MIN_MOTIF:
            rows.append(tid); meta.append((area, fam, sub))
    N, Mn = len(rows), len(motifs)
    area_arr = np.array([m[0] for m in meta]); fam_arr = np.array([m[1] for m in meta])
    sub_arr = np.array([m[2] for m in meta])
    P = np.zeros((N, Mn), np.float32)
    theme = np.zeros((N, 13)); narr = np.zeros((N, K1)); nsub = np.zeros((N, KSUB))
    for i, tid in enumerate(rows):
        for mi in trad_motifs[tid]:
            P[i, mi] = 1.0
        for src, dst in ((theme_cnt, theme), (narr_cnt, narr), (sub_cnt, nsub)):
            tc = src[tid]; dst[i] = tc / tc.sum() if tc.sum() > 0 else tc

    inter = P @ P.T; size = P.sum(1); union = size[:, None] + size[None, :] - inter
    jac = inter / np.where(union > 0, union, 1)
    iu = np.triu_indices(N, 1); y = jac[iu]; sstot = ((y - y.mean()) ** 2).sum()

    def cosmat(prof):
        pn = prof / (np.linalg.norm(prof, axis=1, keepdims=True) + 1e-9)
        return (pn @ pn.T)[iu]

    same = {"area": (area_arr[:, None] == area_arr[None, :]).astype(float)[iu],
            "family": (fam_arr[:, None] == fam_arr[None, :]).astype(float)[iu],
            "subsistence": (sub_arr[:, None] == sub_arr[None, :]).astype(float)[iu],
            "theme": cosmat(theme), "narr": cosmat(narr), "sub": cosmat(nsub)}

    def r2(keys):
        X = np.column_stack([np.ones_like(y)] + [same[k] for k in keys])
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        return float(1 - ((y - X @ beta) ** 2).sum() / sstot)

    base = ["area", "family", "subsistence"]
    r0 = r2(base)
    FAC = [("theme", "13 тем Берёзкина", 13), ("narr", "16 нарративных кластеров", K1),
           ("sub", "61 нарративная под-тема", KSUB)]
    facets = []
    for key, label, n in FAC:
        full = r2(base + [key])
        facets.append({"key": key, "label": label, "n": n, "alone": round(r2([key]), 4),
                       "delta": round(full - r0, 4), "full": round(full, 4),
                       "residual": round(1 - full, 4)})
    full_both = r2(base + ["theme", "narr"])
    subsumption = {"full_both": round(full_both, 4),
                   "theme_given_narr": round(full_both - r2(base + ["narr"]), 4),
                   "narr_given_theme": round(full_both - r2(base + ["theme"]), 4)}

    # ---- TEST B: theme x area over attestations ----
    ai, ni, si, tg = [], [], [], []
    for r in motifs:
        g = int(r.get("motif_group_num") or 0); nt = NT.get(r["id"])
        for t in (r.get("traditions") or []):
            a = m21.area_of(T[t].get("areal_path") or []) if t in T else None
            if a and nt:
                ai.append(a); ni.append(nt["l1"]); si.append(subbase[nt["l1"]] + nt["l2"])
                tg.append(g if 1 <= g <= 13 else -1)
    ai = np.array(ai); ni = np.array(ni); si = np.array(si); tg = np.array(tg); ok = tg > 0
    testB = [{"label": "13 тем", "n": 13, "cv": round(cramers_v(tg[ok], ai[ok]), 3),
              "share": round(mean_max_share(tg[ok], ai[ok]), 3)},
             {"label": "16 кластеров", "n": K1, "cv": round(cramers_v(ni, ai), 3),
              "share": round(mean_max_share(ni, ai), 3)},
             {"label": "61 под-тема", "n": KSUB, "cv": round(cramers_v(si, ai), 3),
              "share": round(mean_max_share(si, ai), 3)}]

    data = {"n_trad": N, "n_pairs": len(iu[0]), "n_att": int(ok.sum()), "base_r2": round(r0, 4),
            "facets": facets, "subsumption": subsumption, "testB": testB}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"{N} traditions · {len(iu[0])} pairs · base R²(area+fam+subs)={r0:.4f}")
    print("TEST A  ΔR² (unique contribution):")
    for f in facets:
        print(f"  {f['label']:26} alone {f['alone']:.3f}  Δ {f['delta']:.3f}  "
              f"full {f['full']:.3f}  residual {f['residual']:.3f}")
    print(f"  subsumption (both in): theme|narr {subsumption['theme_given_narr']:.3f}  "
          f"narr|theme {subsumption['narr_given_theme']:.3f}")
    print("TEST B  theme × area:")
    for b in testB:
        print(f"  {b['label']:14} Cramér's V {b['cv']:.3f}  top-area share {b['share']:.3f}")


if __name__ == "__main__":
    main()
