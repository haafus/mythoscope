"""Effort-correction sweep (mockup 24, roadmap M24) — do the theme findings survive?

Alternative-hypothesis #1 (synthesis §4): our theme signals could be artifacts of catalogue
density. This re-runs four headline findings **raw vs coverage-weighted** (one shared weight
w(t) = min(2, median/a(t)), _bias.py — every tradition contributes comparably instead of the
738-motif corpora dominating) and reports, per finding, survives / weakens / flips.

Findings swept:
  A · theme_profile variance explained by macro-area (mockup 16, raw 38%)
  B · subsistence × theme Category-A gradient (mockup 22)
  C · theme × area lift (mockup 23)
  D · theme co-occurrence A/B blocks (mockup 23, CLR correlation)

Run:  python mockups/24-bias-sweep/build_data.py
"""
import importlib.util
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MOCKS = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "data.js"
MIN_MOTIF = 30
MATCH_KM = 250.0
TN = {1: "Sun & Moon", 2: "Stars", 3: "Cosmogony", 4: "Origin of death", 5: "Origin of humans",
      6: "Origin of subsistence", 7: "Plants & animals", 8: "Monstrous beings", 9: "Protagonist identity",
      10: "Adventures", 11: "Tricks & competitions", 12: "Proper names", 13: "Formulae"}
GROUPS = list(range(1, 14))
CATA = set(range(1, 10))
SUB_ORDER = ["forager", "pastoralist", "horticulturalist", "agrarian_state"]
SUB_LAB = {"forager": "Foragers", "pastoralist": "Pastoralists",
           "horticulturalist": "Horticulturalists", "agrarian_state": "Agrarian states"}


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, MOCKS / rel)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def _need(p, hint=""):
    """Fail with a clear message (not a raw traceback) when a required input is absent."""
    if not p.exists():
        raise SystemExit(f"\n✗ missing input: {p}" + (f"\n  → {hint}\n" if hint else "\n"))
    return p


def w_eta2(X, groups, w):
    """Weighted multivariate eta^2 = between-group SS / total SS (fraction of theme-profile
    variance explained by the grouping)."""
    w = np.asarray(w, float); W = w.sum()
    mean = (X * w[:, None]).sum(0) / W
    sst = (w[:, None] * (X - mean) ** 2).sum()
    ssw = 0.0
    for g in set(groups):
        idx = [i for i, gg in enumerate(groups) if gg == g]
        if not idx:
            continue
        wi = w[idx]; Wi = wi.sum()
        mi = (X[idx] * wi[:, None]).sum(0) / Wi
        ssw += (wi[:, None] * (X[idx] - mi) ** 2).sum()
    return float(1 - ssw / sst) if sst > 0 else 0.0


def w_corr(a, b, w):
    w = np.asarray(w, float); W = w.sum()
    ma = (a * w).sum() / W; mb = (b * w).sum() / W
    cov = (w * (a - ma) * (b - mb)).sum() / W
    va = (w * (a - ma) ** 2).sum() / W; vb = (w * (b - mb) ** 2).sum() / W
    return float(cov / np.sqrt(va * vb)) if va > 0 and vb > 0 else 0.0


def main():
    bias = _load("_bias.py", "_bias")
    m21 = _load("21-facet-population/build_data.py", "m21")
    geo = _load("_geo.py", "_geo")
    coords = geo.berezkin_coords()
    with open(_need(ROOT / "outputs" / "motifs" / "berezkin.json",
                    "build the motif DB first: `mytho motifs`"), encoding="utf-8") as f:
        bz = json.load(f)
    T = bz["traditions"]; motifs = bz["motifs"]
    w_t, med = bias.coverage_weights(motifs, T)
    area_of = {tid: m21.area_of(v.get("areal_path") or []) for tid, v in T.items()}

    # per-tradition theme counts + Category-A share
    tc = defaultdict(lambda: np.zeros(14))
    cont_raw = np.zeros((13, len(m21.AREAS12))); cont_w = np.zeros((13, len(m21.AREAS12)))
    aidx = {a: i for i, a in enumerate(m21.AREAS12)}
    for r in motifs:
        g = int(r.get("motif_group_num") or 0)
        if not (1 <= g <= 13):
            continue
        for tid in (r.get("traditions") or []):
            if tid not in T:
                continue
            tc[tid][g] += 1
            a = area_of.get(tid)
            if a in aidx:
                cont_raw[g - 1, aidx[a]] += 1
                cont_w[g - 1, aidx[a]] += w_t.get(tid, 1.0)

    # tradition-level matrix (>= MIN_MOTIF)
    tids, X, wv, areas = [], [], [], []
    for tid, cnt in tc.items():
        tot = cnt[1:].sum()
        if tot >= MIN_MOTIF:
            tids.append(tid); X.append(cnt[1:] / tot)
            wv.append(w_t.get(tid, 1.0)); areas.append(area_of.get(tid))
    X = np.array(X); wv = np.array(wv)
    ashare = np.array([tc[t][1:10].sum() / tc[t][1:].sum() for t in tids])

    # ---- A · theme_profile variance by macro-area ----
    keep = [i for i, a in enumerate(areas) if a]
    Xa, ga, wa = X[keep], [areas[i] for i in keep], wv[keep]
    A_raw = w_eta2(Xa, ga, np.ones(len(keep)))
    A_w = w_eta2(Xa, ga, wa)

    # ---- B · subsistence x theme (nearest D-PLACE, as mockup 22) ----
    dp = json.loads(_need(MOCKS / "22-subsistence-external" / "dplace_subsistence.json",
                          "run `python mockups/22-subsistence-external/build_data.py` first"
                          ).read_text(encoding="utf-8"))
    dlat = np.array([d["lat"] for d in dp]); dlon = np.array([d["lon"] for d in dp])

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

    def hav(la, lo, la2, lo2):
        r1, r2 = np.radians(la), np.radians(la2)
        dla, dlo = np.radians(la2 - la), np.radians(lo2 - lo)
        h = np.sin(dla / 2) ** 2 + np.cos(r1) * np.cos(r2) * np.sin(dlo / 2) ** 2
        return 6371.0 * 2 * np.arcsin(np.sqrt(h))

    sub_of = {}
    for tid in tids:
        c = coord(tid)
        if c is None:
            continue
        d = hav(c[0], c[1], dlat, dlon); j = int(np.argmin(d))
        if float(d[j]) <= MATCH_KM:
            sub_of[tid] = dp[j]["s"]
    B = []
    for s in SUB_ORDER:
        idx = [i for i, t in enumerate(tids) if sub_of.get(t) == s]
        if not idx:
            B.append({"sub": s, "label": SUB_LAB[s], "raw": None, "w": None, "n": 0}); continue
        ai = ashare[idx]; wi = wv[idx]
        B.append({"sub": s, "label": SUB_LAB[s], "n": len(idx),
                  "raw": round(100 * float(ai.mean()), 1),
                  "w": round(100 * float((ai * wi).sum() / wi.sum()), 1)})

    # ---- C · theme x area lift, headline cells ----
    def lift(cont):
        row = cont.sum(1, keepdims=True); col = cont.sum(0, keepdims=True); N = cont.sum()
        exp = row @ col / N
        return np.divide(cont, exp, out=np.ones_like(cont), where=exp > 0)
    L_raw, L_w = lift(cont_raw), lift(cont_w)
    cells = [(10, "Europe", "Adventures × Europe"), (10, "Aboriginal Australia", "Adventures × Australia"),
             (1, "Aboriginal Australia", "Sun & Moon × Australia"), (11, "Sub-Saharan Africa", "Tricks × Sub-Saharan"),
             (3, "Mesoamerica & Andes", "Cosmogony × Mesoamerica")]
    C = [{"label": lab, "raw": round(float(L_raw[g - 1, aidx[a]]), 2), "w": round(float(L_w[g - 1, aidx[a]]), 2)}
         for g, a, lab in cells]

    # ---- D · co-occurrence blocks (CLR corr), within/between block means + key pair ----
    Lc = np.log(X + 0.005); Lc = Lc - Lc.mean(1, keepdims=True)
    tales = [10, 11, 12, 13, 9]; cosmo = [1, 3, 5, 6, 2]

    def blockstats(weight):
        def cij(i, j):
            return w_corr(Lc[:, i - 1], Lc[:, j - 1], weight)
        within = np.mean([cij(i, j) for blk in (tales, cosmo) for i in blk for j in blk if i < j])
        between = np.mean([cij(i, j) for i in tales for j in cosmo])
        return round(float(within), 2), round(float(between), 2), round(cij(3, 10), 2)
    d_raw = blockstats(np.ones(len(tids))); d_w = blockstats(wv)
    D = {"within_raw": d_raw[0], "between_raw": d_raw[1], "pair_raw": d_raw[2],
         "within_w": d_w[0], "between_w": d_w[1], "pair_w": d_w[2]}

    def verdict(raw, w, rel=0.15):
        if raw is None or w is None:
            return "n/a"
        if raw != 0 and ((raw > 0) != (w > 0)):
            return "flips"
        base = abs(raw) if abs(raw) > 1e-9 else 1.0
        return "survives" if abs(w - raw) / base <= rel else "weakens"

    findings = {
        "A": {"name": "theme_profile variance by macro-area (16)", "raw": round(100 * A_raw, 1),
              "w": round(100 * A_w, 1), "unit": "%", "verdict": verdict(A_raw, A_w)},
        "B": {"name": "subsistence × theme gradient (22)", "rows": B,
              "verdict": ("survives" if (B[0]["w"] and B[3]["w"] and B[0]["w"] > B[3]["w"]) else "weakens")},
        "C": {"name": "theme × area lift (23)", "cells": C,
              "verdict": ("survives" if all(verdict(x["raw"], x["w"], 0.25) != "flips" for x in C) else "flips")},
        "D": {"name": "co-occurrence A/B blocks (23)", **D,
              "verdict": ("survives" if (d_w[0] > 0 > d_w[1]) else "weakens")},
    }
    data = {"med": med, "cap": bias.CAP, "n_trad": len(tids), "min_motif": MIN_MOTIF,
            "sub_matched": len(sub_of), "findings": findings}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"median coverage {med:.0f} · {len(tids)} traditions (>= {MIN_MOTIF} motifs)")
    print(f"  A variance-by-area: raw {100*A_raw:.1f}% -> weighted {100*A_w:.1f}%  [{findings['A']['verdict']}]")
    print("  B subsistence A-share raw -> weighted:")
    for r in B:
        print(f"      {r['label']:18} {r['raw']} -> {r['w']} (n={r['n']})")
    print(f"    verdict {findings['B']['verdict']}")
    print("  C lift raw -> weighted:")
    for x in C:
        print(f"      {x['label']:28} {x['raw']} -> {x['w']}")
    print(f"    verdict {findings['C']['verdict']}")
    print(f"  D blocks within/between raw ({d_raw[0]}/{d_raw[1]}) -> weighted ({d_w[0]}/{d_w[1]})  [{findings['D']['verdict']}]")


if __name__ == "__main__":
    main()
