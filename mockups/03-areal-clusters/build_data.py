"""Find clusters of Berezkin motifs that co-occur geographically/culturally.

Each motif carries a set of ethnic *traditions*; every tradition sits in an areal
hierarchy (16 English macro-regions L1, 59 subregions L2). We cluster motifs by the
shape of their areal footprint (L2, rarity-weighted), and precompute per-motif
co-distribution neighbours (tradition-set Jaccard) — motifs that "travel together".

Run from repo root:  python mockups/03-areal-clusters/build_data.py
"""
import json
from collections import Counter
from pathlib import Path

import numpy as np
from scipy import sparse
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.preprocessing import normalize

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "data.js"
MIN_TRAD, K, TOPN = 4, 16, 8


def main():
    with open(ROOT / "outputs" / "motifs" / "berezkin.json", encoding="utf-8") as f:
        bz = json.load(f)
    trad = bz["traditions"]
    # tradition -> (L1 macro-region, L2 subregion)
    t_l1, t_l2 = {}, {}
    for code, v in trad.items():
        ap = v.get("areal_path") or []
        t_l1[code] = ap[0][1] if len(ap) >= 1 else "—"
        t_l2[code] = ap[1][1] if len(ap) >= 2 else (ap[0][1] if ap else "—")

    L1 = sorted({r for r in t_l1.values()})
    L2 = sorted({r for r in t_l2.values()})
    l2i = {r: i for i, r in enumerate(L2)}

    motifs, trad_sets, l1foot, rows2, cols2, vals2 = [], [], [], [], [], []
    r = 0
    for m in bz["motifs"]:
        ts = [t for t in (m.get("traditions") or []) if t in t_l1]
        if len(ts) < MIN_TRAD:
            continue
        motifs.append({"c": m["id"], "n": m.get("name") or m["id"], "nt": len(ts)})
        trad_sets.append(set(ts))
        f1 = Counter(t_l1[t] for t in ts)
        tot = sum(f1.values())
        l1foot.append([round(100 * f1.get(reg, 0) / tot) for reg in L1])
        c2 = Counter(t_l2[t] for t in ts)
        for reg, n in c2.items():
            rows2.append(r); cols2.append(l2i[reg]); vals2.append(n)
        r += 1

    n = len(motifs)
    M2 = sparse.csr_matrix((vals2, (rows2, cols2)), shape=(n, len(L2)))
    Xc = normalize(TfidfTransformer().fit_transform(M2))          # rarity-weighted, L2-normed
    labels = KMeans(n_clusters=K, random_state=0, n_init=10).fit_predict(Xc)

    # cluster profiles: dominant L1 regions (mean footprint)
    l1arr = np.array(l1foot, dtype=np.float32)
    clusters = []
    for k in range(K):
        idx = np.where(labels == k)[0]
        if not len(idx):
            continue
        mean = l1arr[idx].mean(0)
        top = sorted(((L1[i], float(mean[i])) for i in range(len(L1))), key=lambda t: -t[1])
        top = [{"r": r_, "share": round(s)} for r_, s in top if s >= 4][:5]
        clusters.append({"size": int(len(idx)), "top": top,
                         "members": sorted(int(i) for i in idx)})
    clusters.sort(key=lambda c: -c["size"])

    # co-distribution neighbours: tradition-set Jaccard, top-N per motif
    T = sorted({t for s in trad_sets for t in s})
    ti = {t: i for i, t in enumerate(T)}
    B = sparse.csr_matrix(
        ([1] * sum(len(s) for s in trad_sets),
         ([i for i, s in enumerate(trad_sets) for _ in s],
          [ti[t] for s in trad_sets for t in s])), shape=(n, len(T)), dtype=np.float32)
    inter = (B @ B.T).toarray()
    sizes = np.array([len(s) for s in trad_sets], dtype=np.float32)
    codist = []
    for i in range(n):
        jac = inter[i] / (sizes + sizes[i] - inter[i] + 1e-9)
        jac[i] = -1
        order = np.argsort(jac)[::-1][:TOPN]
        codist.append([[int(j), round(float(jac[j]) * 100)] for j in order if jac[j] > 0.05])

    data = {"regionsL1": L1, "motifs": motifs, "l1foot": l1foot,
            "clusters": clusters, "codist": codist}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"motifs={n}  clusters={len(clusters)} (sizes {[c['size'] for c in clusters]})")
    print(f"L1={len(L1)} L2={len(L2)}  data.js ~{OUT.stat().st_size // 1024}KB")


if __name__ == "__main__":
    main()
