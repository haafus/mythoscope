"""Galton-corrected association test (mockup 25, roadmap M25).

Alternative-hypothesis #5 (synthesis §4) + the area confound we keep flagging: the
subsistence x theme gradient could be neighbour autocorrelation (Galton's problem) or just
area x theme, not a subsistence effect. This tests it by **restricted permutation**: the
association statistic is recomputed against nulls that shuffle the subsistence label only
*within* strata, so a stratum's structure is held fixed —

  - free            : shuffle across all traditions        (assumes independence — the naive test)
  - within-area     : shuffle within each macro-area       (controls the area confound)
  - within-family   : shuffle within each language family  (controls shared ancestry — Galton)
  - within-both     : shuffle within each area x family cell (controls both; lower power)

If the association survives a restricted null, it is *not* explained by that stratum. Statistic:
eta^2 of a tradition's Category-A (cosmology) share explained by its 4-way subsistence, plus
the extractive-minus-intensive gap.

Run:  python mockups/25-galton-test/build_data.py
"""
import importlib.util
import json
import random
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MOCKS = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "data.js"
MIN_MOTIF = 30
MATCH_KM = 250.0
N_PERM = 3000
EXTRACT = {"forager", "horticulturalist"}
INTENS = {"pastoralist", "agrarian_state"}


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, MOCKS / rel)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def _need(p, hint=""):
    """Fail with a clear message (not a raw traceback) when a required input is absent."""
    if not p.exists():
        raise SystemExit(f"\n✗ missing input: {p}" + (f"\n  → {hint}\n" if hint else "\n"))
    return p


def eta2(y, labels):
    """Fraction of variance in y explained by categorical labels."""
    y = np.asarray(y, float); mean = y.mean()
    sst = ((y - mean) ** 2).sum()
    ssb = 0.0
    for g in set(labels):
        idx = [i for i, gg in enumerate(labels) if gg == g]
        ssb += len(idx) * (y[idx].mean() - mean) ** 2
    return float(ssb / sst) if sst > 0 else 0.0


def gap(y, subs):
    y = np.asarray(y, float)
    ex = [i for i, s in enumerate(subs) if s in EXTRACT]
    it = [i for i, s in enumerate(subs) if s in INTENS]
    return float(y[ex].mean() - y[it].mean()) if ex and it else 0.0


def main():
    m21 = _load("21-facet-population/build_data.py", "m21")
    geo = _load("_geo.py", "_geo")
    coords = geo.berezkin_coords()
    with open(_need(ROOT / "outputs" / "motifs" / "berezkin.json",
                    "build the motif DB first: `mytho build motifs`"), encoding="utf-8") as f:
        bz = json.load(f)
    T = bz["traditions"]; motifs = bz["motifs"]

    # per-tradition Category-A share
    aA, ab = Counter(), Counter()
    for r in motifs:
        g = int(r.get("motif_group_num") or 0)
        if 1 <= g <= 13:
            for t in (r.get("traditions") or []):
                if t in T:
                    ab[t] += 1
                    if g <= 9:
                        aA[t] += 1

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

    ashare, subs, areas, fams = [], [], [], []
    for tid, v in T.items():
        if ab[tid] < MIN_MOTIF:
            continue
        c = coord(tid)
        if c is None:
            continue
        d = hav(c[0], c[1], dlat, dlon); j = int(np.argmin(d))
        if float(d[j]) > MATCH_KM:
            continue
        area = m21.area_of(v.get("areal_path") or [])
        fam = m21.family_of((v.get("language") or [None])[0], area)[0]
        ashare.append(100 * aA[tid] / ab[tid]); subs.append(dp[j]["s"])
        areas.append(area or "?"); fams.append(fam or "?")
    y = np.array(ashare); n = len(y)
    obs_eta = eta2(y, subs); obs_gap = gap(y, subs)

    def strata(kind):
        if kind == "free":
            return [list(range(n))]
        key = {"area": areas, "family": fams}.get(kind)
        if kind == "both":
            key = [f"{areas[i]}|{fams[i]}" for i in range(n)]
        groups = {}
        for i, k in enumerate(key):
            groups.setdefault(k, []).append(i)
        return list(groups.values())

    rng = random.Random(0)
    tests = {}
    for kind in ("free", "area", "family", "both"):
        blocks = strata(kind)
        permutable = sum(len(b) for b in blocks if len(b) > 1)
        ge = 0
        for _ in range(N_PERM):
            perm = list(subs)
            for b in blocks:
                if len(b) > 1:
                    vals = [subs[i] for i in b]; rng.shuffle(vals)
                    for pos, i in zip(b, vals, strict=True):
                        perm[pos] = i
            if eta2(y, perm) >= obs_eta:
                ge += 1
        p = (ge + 1) / (N_PERM + 1)
        tests[kind] = {"p": round(p, 4), "permutable": permutable,
                       "sig": p < 0.05, "blocks": len(blocks)}

    means = {s: round(float(y[[i for i in range(n) if subs[i] == s]].mean()), 1)
             for s in set(subs)}
    data = {"n": n, "min_motif": MIN_MOTIF, "n_perm": N_PERM,
            "obs_eta": round(obs_eta, 4), "obs_gap": round(obs_gap, 1),
            "means": means, "tests": tests,
            "labels": {"free": "наивно (независимость)", "area": "внутри ареала (контроль ареала)",
                       "family": "внутри семьи (контроль происхождения / Гальтон)",
                       "both": "внутри ареал×семья (оба)"}}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"n={n} · observed eta^2={obs_eta:.4f} gap={obs_gap:.1f}pp")
    for k, t in tests.items():
        print(f"  {k:8} p={t['p']:.4f} {'SIG' if t['sig'] else 'ns '} (blocks {t['blocks']}, permutable {t['permutable']})")


if __name__ == "__main__":
    main()
