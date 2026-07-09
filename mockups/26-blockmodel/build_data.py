"""Degree-corrected block model (mockup 26, roadmap M26).

Replaces the biclustering / spectral co-clustering of mockups 06/07/15/23 with a
degree-corrected co-clustering of the motif × tradition matrix, and shows the payoff: the
degree-correction **absorbs the a(t) sampling confounder natively**, so blocks reflect
structure, not catalogue density.

Method (alternating multinomial co-clustering = hard degree-corrected SBM):
  - traditions -> K_t blocks, motifs -> K_m blocks, alternately;
  - each tradition is clustered by its **degree-normalised profile** over motif-blocks
    (row shares that sum to 1) — normalising out the total degree is the degree correction;
  - K_t chosen by BIC on the reconstruction likelihood.
The naive baseline clusters the **raw** count rows (no normalisation) and, as expected,
separates traditions by how much Berezkin recorded — an artifact.

Run:  python mockups/26-blockmodel/build_data.py
"""
import importlib.util
import json
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.cluster import KMeans

ROOT = Path(__file__).resolve().parents[2]
MOCKS = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "data.js"
MIN_MOTIF = 10
KM = 10                    # motif blocks (fixed); tradition blocks K_t chosen by BIC
KT_GRID = [4, 5, 6, 7, 8, 9, 10]
TN = {1: "Sun&Moon", 2: "Stars", 3: "Cosmogony", 4: "Death", 5: "Humans", 6: "Subsistence",
      7: "Plants&animals", 8: "Monsters", 9: "Identity", 10: "Adventures", 11: "Tricks",
      12: "Names", 13: "Formulae"}


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, MOCKS / rel)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def eta2_num(x, labels):
    x = np.asarray(x, float); mean = x.mean(); sst = ((x - mean) ** 2).sum()
    ssb = sum(len(g) * (x[g].mean() - mean) ** 2
              for g in (np.where(labels == k)[0] for k in set(labels)) if len(g))
    return float(ssb / sst) if sst > 0 else 0.0


def cocluster(A, kt, km, iters=30, seed=0):
    """Alternating degree-corrected co-clustering. Returns (tb, mb)."""
    rng = np.random.default_rng(seed)
    mb = rng.integers(0, km, A.shape[1])
    tb = None
    for _ in range(iters):
        Rt = np.stack([A[:, mb == h].sum(1) for h in range(km)], 1)     # n_t x km edge counts
        Pt = Rt / np.clip(Rt.sum(1, keepdims=True), 1, None)            # degree-normalised profile
        tb = KMeans(kt, n_init=4, random_state=seed).fit_predict(Pt)
        Cm = np.stack([A[tb == g, :].sum(0) for g in range(kt)], 1)     # n_m x kt
        Pm = Cm / np.clip(Cm.sum(1, keepdims=True), 1, None)
        mb_new = KMeans(km, n_init=4, random_state=seed).fit_predict(Pm)
        if np.array_equal(mb_new, mb):
            break
        mb = mb_new
    return tb, mb


def loglik_bic(A, tb, mb, kt, km):
    """Poisson block-model log-likelihood and BIC for model selection."""
    B = np.stack([[A[tb == g][:, mb == h].sum() for h in range(km)] for g in range(kt)])
    dt = np.array([A[tb == g].sum() for g in range(kt)], float)
    dm = np.array([A[:, mb == h].sum() for h in range(km)], float)
    N = A.sum()
    ll = 0.0
    for g in range(kt):
        for h in range(km):
            if B[g, h] > 0 and dt[g] > 0 and dm[h] > 0:
                ll += B[g, h] * np.log(B[g, h] * N / (dt[g] * dm[h]))
    params = kt * km + A.shape[0] + A.shape[1]
    return ll, params * np.log(N) - 2 * ll


def main():
    m21 = _load("21-facet-population/build_data.py", "m21")
    with open(ROOT / "outputs" / "motifs" / "berezkin.json", encoding="utf-8") as f:
        bz = json.load(f)
    T = bz["traditions"]; motifs = bz["motifs"]

    at = Counter()
    for r in motifs:
        for t in (r.get("traditions") or []):
            if t in T:
                at[t] += 1
    tids = [t for t in T if at[t] >= MIN_MOTIF]
    tidx = {t: i for i, t in enumerate(tids)}
    mids = [r["id"] for r in motifs]
    midx = {m: j for j, m in enumerate(mids)}
    A = np.zeros((len(tids), len(mids)), np.int16)
    grp = {}
    for r in motifs:
        j = midx[r["id"]]; grp[j] = int(r.get("motif_group_num") or 0)
        for t in (r.get("traditions") or []):
            if t in tidx:
                A[tidx[t], j] = 1
    a_t = np.array([at[t] for t in tids], float)
    area_of = [m21.area_of(T[t].get("areal_path") or []) for t in tids]

    # ---- model selection: BIC over K_t ----
    bic_curve = []
    best = None
    for kt in KT_GRID:
        tb, mb = cocluster(A, kt, KM)
        ll, bic = loglik_bic(A, tb, mb, kt, KM)
        bic_curve.append({"kt": kt, "bic": round(float(bic))})
        if best is None or bic < best["bic_val"]:
            best = {"kt": kt, "tb": tb, "mb": mb, "bic_val": bic}
    tb, mb, kt = best["tb"], best["mb"], best["kt"]

    # ---- degree-robustness: DC blocks vs a naive raw-count clustering ----
    naive = KMeans(kt, n_init=4, random_state=0).fit_predict(A.astype(float))
    eta_dc = eta2_num(a_t, tb)
    eta_naive = eta2_num(a_t, naive)

    # ---- interpret blocks ----
    tblocks = []
    for g in range(kt):
        idx = np.where(tb == g)[0]
        if not len(idx):
            continue
        areas = Counter(area_of[i] for i in idx if area_of[i]).most_common(3)
        tblocks.append({"g": int(g), "n": int(len(idx)),
                        "cov_med": int(np.median(a_t[idx])),
                        "areas": [{"name": a, "n": n} for a, n in areas]})
    tblocks.sort(key=lambda b: -b["n"])
    mblocks = []
    for h in range(KM):
        idx = np.where(mb == h)[0]
        if not len(idx):
            continue
        themes = Counter(TN.get(grp.get(j, 0), "?") for j in idx).most_common(3)
        cata = sum(1 for j in idx if 1 <= grp.get(j, 0) <= 9)
        mblocks.append({"h": int(h), "n": int(len(idx)), "catA": round(100 * cata / len(idx)),
                        "themes": [{"name": t, "n": n} for t, n in themes]})
    mblocks.sort(key=lambda b: -b["n"])

    data = {"n_trad": len(tids), "n_motif": len(mids), "min_motif": MIN_MOTIF,
            "kt": int(kt), "km": KM, "bic": bic_curve,
            "eta_dc": round(eta_dc, 3), "eta_naive": round(eta_naive, 3),
            "cov": {"min": int(a_t.min()), "med": int(np.median(a_t)), "max": int(a_t.max())},
            "tblocks": tblocks, "mblocks": mblocks}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"{len(tids)} traditions x {len(mids)} motifs · chosen K_t={kt} (BIC), K_m={KM}")
    print(f"  degree-robustness  eta^2(a(t) | block):  DC={eta_dc:.3f}   naive-raw={eta_naive:.3f}")
    print("  tradition blocks (n, median coverage, top areas):")
    for b in tblocks:
        print(f"    blk {b['g']:2} n={b['n']:4} cov~{b['cov_med']:3}  {[a['name'] for a in b['areas']]}")
    print("  motif blocks (n, Cat-A%, top themes):")
    for b in mblocks:
        print(f"    blk {b['h']:2} n={b['n']:4} A={b['catA']:3}%  {[t['name'] for t in b['themes']]}")


if __name__ == "__main__":
    main()
