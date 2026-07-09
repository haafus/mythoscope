"""Motif content vs theme / depth (mockup 29, roadmap M29).

Crosses the BGE-M3 semantic embeddings (built in the morphology stage, cached in
outputs/motifs/raw/bge_m3.npy) with the two motif axes: does a motif's *content* predict its
**theme** (what it is about) and its **depth/breadth** (how old its distribution is)?

Expectation from the program: content should predict theme strongly (theme is a content axis)
but be nearly uninformative about depth (stratum is distributional, not semantic) — a direct
check that `stratum` must come from distribution, not from what a motif is about. Also probes a
**content-based redundancy** measure (mean cosine to nearest neighbours) as a candidate
banality signal — and finds it captures near-duplicate motif families, not homoplasy, so it
does NOT replace mockup 20's proxy.

Embedding order is TMI, ATU, Berezkin (semantic_parallels.py); the Berezkin block is the last
len(motifs) rows, robust to TMI/ATU drift.

Run:  python mockups/29-content-stratum/build_data.py
"""
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "data.js"
K = 5
TN = {1: "Sun&Moon", 2: "Stars", 3: "Cosmogony", 4: "Death", 5: "Humans", 6: "Subsistence",
      7: "Plants&animals", 8: "Monsters", 9: "Identity", 10: "Adventures", 11: "Tricks",
      12: "Names", 13: "Formulae"}


def main():
    with open(ROOT / "outputs" / "motifs" / "berezkin.json", encoding="utf-8") as f:
        bz = json.load(f)
    M = bz["motifs"]; T = bz["traditions"]
    E = np.load(ROOT / "outputs" / "motifs" / "raw" / "bge_m3.npy")
    off = E.shape[0] - len(M)
    B = E[off:off + len(M)].astype(np.float32)
    B /= np.linalg.norm(B, axis=1, keepdims=True) + 1e-9

    grp = np.array([int(r.get("motif_group_num") or 0) for r in M])
    deflen = np.array([len(r.get("definition") or "") for r in M])

    def macro(t):
        ap = T[t].get("areal_path") or []
        return ap[0][1] if ap else None
    nmac = np.array([len({macro(t) for t in (r.get("traditions") or []) if t in T and macro(t)}) for r in M])
    ntrad = np.array([len([t for t in (r.get("traditions") or []) if t in T]) for r in M])

    # k nearest by cosine (block to bound memory)
    n = len(M)
    nn = np.zeros((n, K), int); nn_sim = np.zeros((n, K))
    for s in range(0, n, 512):
        e = min(s + 512, n)
        S = B[s:e] @ B.T
        for r in range(e - s):
            S[r, s + r] = -2
        top = np.argpartition(-S, K, 1)[:, :K]
        for r in range(e - s):
            o = top[r][np.argsort(-S[r, top[r]])]
            nn[s + r] = o; nn_sim[s + r] = S[r, o]

    keep = np.where(ntrad >= 4)[0]           # motifs with enough distribution to have a depth
    # theme concordance: fraction of NN sharing the theme group
    same_theme = np.array([np.mean(grp[nn[i]] == grp[i]) for i in keep if grp[i] > 0])
    pg = np.array([np.mean(grp == g) for g in range(1, 14)])
    base_theme = float((pg ** 2).sum() / pg.sum() ** 2) if pg.sum() else 0.0  # random same-group prob
    theme_obs = float(same_theme.mean())

    # depth concordance: does content predict breadth? corr(nmac_i, mean nmac of NN)
    kk = keep
    nn_nmac = np.array([nmac[nn[i]].mean() for i in kk])
    nn_ntrad = np.array([ntrad[nn[i]].mean() for i in kk])
    corr_breadth = float(np.corrcoef(nmac[kk], nn_nmac)[0, 1])
    corr_prev = float(np.corrcoef(ntrad[kk], nn_ntrad)[0, 1])
    # theme's own predictiveness of breadth, as a yardstick (eta^2 of nmac by theme group)
    y = nmac[kk].astype(float); mean = y.mean(); sst = ((y - mean) ** 2).sum()
    ssb = sum(len(ix) * (y[ix].mean() - mean) ** 2
              for ix in (np.where(grp[kk] == g)[0] for g in range(1, 14)) if len(ix))
    eta_theme_breadth = float(ssb / sst) if sst else 0.0

    # content banality: mean cosine to k neighbours (generic meaning = reinvention candidate)
    banal = nn_sim.mean(1)
    order = np.argsort(-banal)
    top_banal = [{"c": M[i]["id"], "n": M[i].get("name", ""), "sim": round(float(banal[i]), 2),
                  "g": TN.get(int(grp[i]), "?"), "nt": int(ntrad[i])}
                 for i in order[:12]]
    # does content-banality agree with the short-definition proxy? (corr, higher banal ~ shorter def)
    corr_banal_deflen = float(np.corrcoef(banal, deflen)[0, 1])

    # a couple of tracked examples of nearest-by-meaning
    ex = []
    idx = {r["id"]: i for i, r in enumerate(M)}
    for code in ("A3", "K25", "M182"):
        if code in idx:
            i = idx[code]
            ex.append({"c": code, "n": M[i].get("name", ""),
                       "nn": [{"c": M[j]["id"], "n": M[j].get("name", ""), "sim": round(float(nn_sim[i][r]), 2)}
                              for r, j in enumerate(nn[i][:4])]})

    data = {"n": len(M), "k": K,
            "theme_obs": round(theme_obs, 3), "theme_base": round(base_theme, 3),
            "corr_breadth": round(corr_breadth, 3), "corr_prev": round(corr_prev, 3),
            "eta_theme_breadth": round(eta_theme_breadth, 3),
            "corr_banal_deflen": round(corr_banal_deflen, 3),
            "top_banal": top_banal, "examples": ex}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"{len(M)} motifs · content K={K}-NN")
    print(f"  theme concordance: NN share theme {theme_obs:.1%}  vs chance {base_theme:.1%}")
    print(f"  content -> breadth corr {corr_breadth:.3f} · content -> prevalence corr {corr_prev:.3f}")
    print(f"  (theme -> breadth eta^2 {eta_theme_breadth:.3f}, as a yardstick)")
    print(f"  content-banality vs short-def corr {corr_banal_deflen:.3f}")
    print(f"  most generic-by-meaning: {[b['c'] for b in top_banal[:6]]}")


if __name__ == "__main__":
    main()
