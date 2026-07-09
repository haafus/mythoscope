"""Joint effort-corrected factorization — the capstone (mockup 38, roadmap M38).

The one model of synthesis §3: factorize the tradition×motif presence matrix `P` with the
attestation intensity **a(t) as an exposure offset**, so the latent factors are the emergent
area/theme components *de-confounded from sampling* — subsuming mockups 16–23 (area recovery,
coverage control, theme structure) in a single fit. Motifs are down-weighted by their M37
cross-index confidence, so coding-dependent motifs pull the factors less.

Model (Poisson / Hierarchical-Poisson core, MAP by weighted KL multiplicative updates):

    P[t,m] ~ Poisson( a(t) · (W H)[t,m] ),   W ≥ 0 (T×K),  H ≥ 0 (K×M)

The offset a(t) removes the coverage that made naive clustering ~80% sampling-driven
(mockup 26). Each tradition's row of W, renormalised, is its **de-confounded mixture** over K
emergent components; H[k,·] is component k's motif profile.

Run:  python mockups/38-joint-hpf/build_data.py
"""
import csv
import importlib.util
import json
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score

ROOT = Path(__file__).resolve().parents[2]
MOCKS = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
OUT = HERE / "data.js"
K = 12
ITERS = 80
MIN_TRAD_MOTIF = 8       # traditions thinner than this are dropped
MIN_MOTIF_ATT = 4        # motifs in fewer traditions are dropped (noise)
GROUP = {1: "Sun & Moon", 2: "Stars", 3: "Cosmogony", 4: "Origin of death", 5: "Origin of humans",
         6: "Origin of subsistence", 7: "Plants & animals", 8: "Monstrous beings",
         9: "Protagonist identity", 10: "Adventures", 11: "Tricks & contests", 12: "Proper names",
         13: "Formulae"}
LEVELW = {"triple": 1.0, "strong": 0.85, "moderate": 0.7, "berezkin_only": 0.5}


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, MOCKS / rel)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def confidence_weights(M):
    """M37's per-motif cross-index confidence (upper bound; automated crosswalk)."""
    xw = ROOT / "docs" / "motifs" / "crosswalk"

    def rows(fn):
        with open(xw / fn, encoding="utf-8") as f:
            return list(csv.DictReader(f))
    tmi = {}
    for r in rows("parallels_BZ_TMI.csv"):
        if r["BZ_id"] not in tmi or r["tier"] < tmi[r["BZ_id"]]:
            tmi[r["BZ_id"]] = r["tier"]
    atu = {r["BZ_id"] for r in rows("parallels_BZ_ATU.csv")}
    tri = {r["BZ_id"] for r in rows("parallels_triangles.csv")}
    w = {}
    for r in M:
        i = r["id"]; has_atu = bool(r.get("atu_refs")) or i in atu
        if i in tri or (i in tmi and has_atu):
            lv = "triple"
        elif tmi.get(i) == "A" or has_atu:
            lv = "strong"
        elif i in tmi:
            lv = "moderate"
        else:
            lv = "berezkin_only"
        w[i] = LEVELW[lv]
    return w


def eta2_log(a, labels):
    la = np.log(a); gm = la.mean(); sst = ((la - gm) ** 2).sum(); ssb = 0.0
    for c in set(labels):
        m = la[np.asarray(labels) == c]
        ssb += len(m) * (m.mean() - gm) ** 2
    return float(ssb / sst) if sst > 0 else 0.0


def main():
    m21 = _load("21-facet-population/build_data.py", "m21")
    with open(ROOT / "outputs" / "motifs" / "berezkin.json", encoding="utf-8") as f:
        bz = json.load(f)
    T, motifs = bz["traditions"], bz["motifs"]
    wm_all = confidence_weights(motifs)

    # attestation matrix + facets
    att = Counter()
    for r in motifs:
        for t in (r.get("traditions") or []):
            att[t] += 1
    keep_m = [r for r in motifs if len(r.get("traditions") or []) >= MIN_MOTIF_ATT]
    rows_t = [t for t in T if att[t] >= MIN_TRAD_MOTIF and m21.area_of(T[t].get("areal_path") or [])]
    ti = {t: i for i, t in enumerate(rows_t)}
    Tn, Mn = len(rows_t), len(keep_m)
    P = np.zeros((Tn, Mn), dtype=np.float64)
    for k, r in enumerate(keep_m):
        for t in (r.get("traditions") or []):
            if t in ti:
                P[ti[t], k] = 1.0
    a = P.sum(1)                                   # exposure offset a(t)
    wm = np.array([wm_all[r["id"]] for r in keep_m])
    area = np.array([m21.area_of(T[t].get("areal_path") or []) for t in rows_t])
    grp = np.array([int(r.get("motif_group_num") or 0) for r in keep_m])

    # ---- weighted Poisson NMF with the a(t) offset (multiplicative updates) ----
    rng = np.random.default_rng(0)
    W = rng.random((Tn, K)) + 0.1
    H = rng.random((K, Mn)) + 0.1
    aW_col = None
    for _ in range(ITERS):
        R = (a[:, None] * (W @ H)) + 1e-9
        PR = P / R
        aW = a[:, None] * W
        H *= (aW.T @ PR) / (aW.sum(0)[:, None] + 1e-9)
        R = (a[:, None] * (W @ H)) + 1e-9
        PR = P / R
        W *= ((wm * PR) @ H.T) / ((H @ wm)[None, :] + 1e-9)
        aW_col = aW
    mix = W / (W.sum(1, keepdims=True) + 1e-12)     # de-confounded mixture per tradition
    dom = mix.argmax(1)

    # ---- validation ----
    eta_hpf = eta2_log(a, dom)
    km = KMeans(n_clusters=K, n_init=4, random_state=0).fit(P).labels_   # naive baseline
    eta_naive = eta2_log(a, km)
    ari_area = round(adjusted_rand_score(dom, area), 3)
    ari_area_naive = round(adjusted_rand_score(km, area), 3)

    # ---- interpret components ----
    comps = []
    Hn = H / (H.sum(1, keepdims=True) + 1e-12)
    for k in range(K):
        members = np.where(dom == k)[0]
        ar = Counter(area[members]).most_common(3)
        # theme mix of the component (motif-loading weighted)
        th = np.zeros(14)
        for m in range(Mn):
            if 1 <= grp[m] <= 13:
                th[grp[m]] += Hn[k, m]
        th = th[1:] / (th[1:].sum() + 1e-12)
        topth = sorted(((GROUP[g + 1], float(th[g])) for g in range(13)), key=lambda x: -x[1])[:3]
        topm = [keep_m[m]["id"] for m in np.argsort(-H[k])[:4]]
        topm_names = [keep_m[m].get("name", "") for m in np.argsort(-H[k])[:4]]
        comps.append({"k": k, "n": int(len(members)), "size": round(float(aW_col[:, k].sum()), 1),
                      "areas": [{"a": x, "n": n} for x, n in ar],
                      "themes": [{"t": t, "p": round(p, 2)} for t, p in topth],
                      "motifs": [{"id": i, "n": n} for i, n in zip(topm, topm_names, strict=True)]})
    comps.sort(key=lambda c: -c["n"])

    data = {
        "n_trad": Tn, "n_motif": Mn, "K": K, "iters": ITERS,
        "eta": {"hpf": round(eta_hpf, 3), "naive": round(eta_naive, 3)},
        "ari_area": {"hpf": ari_area, "naive": ari_area_naive},
        "mean_conf": round(float(wm.mean()), 3), "comps": comps,
        "areas12": list(dict.fromkeys(area.tolist())),
    }
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"HPF: {Tn} traditions × {Mn} motifs, K={K}")
    print(f"  DE-CONFOUNDING eta2(log a | component): HPF {eta_hpf:.3f}  vs naive KMeans {eta_naive:.3f}  (mockup-26 naive ~0.80)")
    print(f"  area recovery ARI: HPF {ari_area}  vs naive {ari_area_naive}")
    print("  components (dominant area · dominant theme · size):")
    for c in comps:
        print(f"    k{c['k']:2} n={c['n']:3} {c['areas'][0]['a'][:22]:22} · {c['themes'][0]['t']:16} · top {c['motifs'][0]['id']}")


if __name__ == "__main__":
    main()
