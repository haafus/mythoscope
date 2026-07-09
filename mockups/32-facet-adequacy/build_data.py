"""Facet adequacy & orthogonality (mockup 32, roadmap M32) — audits assumption #6.

The entity model of macro-area-facets.md rests on an untested design choice: that
`area · family · subsistence · theme_profile` are the *right* and *~orthogonal* tradition
facets. Orthogonality is already falsified (the categorical axes co-track one peopling
history), so this mockup audits the two claims that actually matter, on data we `have`:

  1. Association matrix — Cramér's V among {area, family, subsistence} + multivariate η² of
     theme_profile by each. The honest entanglement picture.
  2. Unique contribution (the headline) — drop-one variation partitioning: predict pairwise
     motif-set Jaccard from the facets, then from the facets minus X. Δ = R²(all) − R²(all−X)
     = the variance ONLY facet X explains. A facet with Δ≈0 is redundant.
  3. Residual structure — cluster traditions on raw motif vectors, measure how much of that
     structure the four facets jointly recover (adjusted Rand). Large residual → a missing axis.
  4. Granularity — held-out attestation log-likelihood over coarse↔fine facet variants
     (area 12 vs L0/L1, family 11 vs raw). Is 12 the right resolution?

Run:  python mockups/32-facet-adequacy/build_data.py
"""
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import adjusted_rand_score

ROOT = Path(__file__).resolve().parents[2]
MOCKS = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
OUT = HERE / "data.js"
MATCH_KM = 600.0      # subsistence join tolerance (looser than mockup 22's 250 to keep coverage)
MIN_MOTIF = 15        # traditions thinner than this are dropped (theme profile / Jaccard too noisy)
SUB_LABEL = {"forager": "Foragers", "pastoralist": "Pastoralists",
             "horticulturalist": "Horticulturalists", "agrarian_state": "Agrarian states"}


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, MOCKS / rel)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def haversine(lat1, lon1, lat2, lon2):
    r1, r2 = np.radians(lat1), np.radians(lat2)
    dlat, dlon = np.radians(lat2 - lat1), np.radians(lon2 - lon1)
    a = np.sin(dlat / 2) ** 2 + np.cos(r1) * np.cos(r2) * np.sin(dlon / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(a))


def cramers_v(x, y):
    cx = sorted(set(x)); cy = sorted(set(y))
    ix = {c: i for i, c in enumerate(cx)}; iy = {c: i for i, c in enumerate(cy)}
    tab = np.zeros((len(cx), len(cy)))
    for a, b in zip(x, y, strict=True):
        tab[ix[a], iy[b]] += 1
    n = tab.sum()
    if n == 0:
        return 0.0
    exp = tab.sum(1, keepdims=True) @ tab.sum(0, keepdims=True) / n
    chi2 = ((tab - exp) ** 2 / np.where(exp > 0, exp, 1)).sum()
    k = min(len(cx), len(cy))
    return float(np.sqrt(chi2 / (n * (k - 1)))) if k > 1 else 0.0


def eta2(labels, Y):
    """Multivariate correlation ratio: 1 − within-group SS / total SS on the 13-dim vectors."""
    labels = np.asarray(labels)
    sst = ((Y - Y.mean(0)) ** 2).sum()
    ssw = 0.0
    for c in set(labels):
        m = Y[labels == c]
        ssw += ((m - m.mean(0)) ** 2).sum()
    return float(1 - ssw / sst) if sst > 0 else 0.0


def main():
    geo = _load("_geo.py", "geo")
    m21 = _load("21-facet-population/build_data.py", "m21")
    coords = geo.berezkin_coords()
    with open(ROOT / "outputs" / "motifs" / "berezkin.json", encoding="utf-8") as f:
        bz = json.load(f)
    T, motifs = bz["traditions"], bz["motifs"]
    dp = json.loads((MOCKS / "22-subsistence-external" / "dplace_subsistence.json").read_text(encoding="utf-8"))
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

    # subsistence per tradition (nearest D-PLACE society within MATCH_KM)
    sub_of = {}
    for tid in T:
        c = coord(tid)
        if c is None:
            continue
        d = haversine(c[0], c[1], dlat, dlon)
        j = int(np.argmin(d))
        if float(d[j]) <= MATCH_KM:
            sub_of[tid] = dp[j]["s"]

    # attestation: per-tradition motif set + 13-group theme counts
    trad_motifs = defaultdict(set)
    theme_cnt = defaultdict(lambda: np.zeros(13))
    for mi, r in enumerate(motifs):
        g = int(r.get("motif_group_num") or 0)
        for t in (r.get("traditions") or []):
            if t in T:
                trad_motifs[t].add(mi)
                if 1 <= g <= 13:
                    theme_cnt[t][g - 1] += 1

    # working set: every facet present + enough motifs
    rows, meta = [], []
    for tid, v in T.items():
        ap = v.get("areal_path") or []
        area = m21.area_of(ap)
        lang0 = (v.get("language") or [None])[0]
        fam, _ = m21.family_of(lang0, area)
        sub = sub_of.get(tid)
        n = len(trad_motifs.get(tid, ()))
        if area and fam and sub and n >= MIN_MOTIF:
            rows.append(tid)
            meta.append({"area": area, "fam": fam, "sub": sub,
                         "ap0": ap[0][1] if ap else "?",
                         "ap1": ap[1][1] if len(ap) > 1 else (ap[0][1] if ap else "?"),
                         "lang0": lang0 or "?"})
    N = len(rows)
    M = len(motifs)
    area_arr = np.array([m["area"] for m in meta])
    fam_arr = np.array([m["fam"] for m in meta])
    sub_arr = np.array([m["sub"] for m in meta])
    P = np.zeros((N, M), dtype=np.float32)
    theme = np.zeros((N, 13))
    for i, tid in enumerate(rows):
        for mi in trad_motifs[tid]:
            P[i, mi] = 1.0
        tc = theme_cnt[tid]; theme[i] = tc / tc.sum() if tc.sum() > 0 else tc

    # ---- 1. association matrix ----
    cat = {"area": area_arr, "family": fam_arr, "subsistence": sub_arr}
    assoc = {}
    for a in ["area", "family", "subsistence"]:
        for b in ["area", "family", "subsistence"]:
            assoc[f"{a}|{b}"] = 1.0 if a == b else round(cramers_v(cat[a], cat[b]), 3)
    eta = {a: round(eta2(cat[a], theme), 3) for a in ["area", "family", "subsistence"]}

    # ---- 2. unique contribution (drop-one MRM on pairwise motif-Jaccard) ----
    inter = P @ P.T
    size = P.sum(1)
    union = size[:, None] + size[None, :] - inter
    jac = inter / np.where(union > 0, union, 1)
    tn = theme / (np.linalg.norm(theme, axis=1, keepdims=True) + 1e-9)
    cos = tn @ tn.T
    same = {"area": (area_arr[:, None] == area_arr[None, :]).astype(float),
            "family": (fam_arr[:, None] == fam_arr[None, :]).astype(float),
            "subsistence": (sub_arr[:, None] == sub_arr[None, :]).astype(float),
            "theme_profile": cos}
    iu = np.triu_indices(N, 1)
    y = jac[iu]
    ymean = y.mean(); sstot = ((y - ymean) ** 2).sum()
    cols = {k: same[k][iu] for k in same}

    def r2(keys):
        X = np.column_stack([np.ones_like(y)] + [cols[k] for k in keys])
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        return 1 - ((y - X @ beta) ** 2).sum() / sstot

    allk = ["area", "family", "subsistence", "theme_profile"]
    full = r2(allk)
    delta = {k: round(full - r2([q for q in allk if q != k]), 4) for k in allk}
    # Mantel permutation p for the full model (permute tradition order of the response)
    rng = np.random.default_rng(0)
    perm_r2 = []
    for _ in range(99):
        pp = rng.permutation(N)
        yp = jac[np.ix_(pp, pp)][iu]
        Xf = np.column_stack([np.ones_like(yp)] + [cols[k] for k in allk])
        beta, *_ = np.linalg.lstsq(Xf, yp, rcond=None)
        perm_r2.append(1 - ((yp - Xf @ beta) ** 2).sum() / ((yp - yp.mean()) ** 2).sum())
    mantel_p = round((1 + sum(r >= full for r in perm_r2)) / (1 + len(perm_r2)), 3)

    # ---- 3. residual structure (motif clustering vs facet grouping) ----
    # Cluster on Jaccard distance (coverage-robust) rather than Euclidean on raw binary vectors,
    # which is dominated by a(t) and collapses into one giant coverage blob.
    K = 12
    dist = 1.0 - jac; np.fill_diagonal(dist, 0.0)
    lab = AgglomerativeClustering(n_clusters=K, metric="precomputed", linkage="average").fit(dist).labels_
    joint = np.array([f"{a}|{f}" for a, f in zip(area_arr, fam_arr, strict=True)])
    ari = {"area": round(adjusted_rand_score(lab, area_arr), 3),
           "family": round(adjusted_rand_score(lab, fam_arr), 3),
           "subsistence": round(adjusted_rand_score(lab, sub_arr), 3),
           "area×family": round(adjusted_rand_score(lab, joint), 3)}
    # block-level residual uses the best single facet (area×family over-partitions vs K=12,
    # so its ARI is granularity-depressed, not genuinely lower).
    best_ari = max(ari["area"], ari["family"], ari["subsistence"])
    residual = round(1 - best_ari, 3)
    # the least-explained motif cluster = highest area entropy (a cross-area convergence zone)
    worst, worst_h, worst_desc = None, -1, ""
    for c in range(K):
        idx = lab == c
        if idx.sum() < 5:
            continue
        ac = Counter(area_arr[idx]); tot = idx.sum()
        h = -sum((v / tot) * np.log(v / tot) for v in ac.values())
        if h > worst_h:
            worst_h, worst = h, c
            worst_desc = ", ".join(f"{a} {round(100*v/tot)}%" for a, v in ac.most_common(4))

    # ---- 4. granularity (held-out attestation log-likelihood, 5-fold) ----
    ap0 = np.array([m["ap0"] for m in meta]); ap1 = np.array([m["ap1"] for m in meta])
    lang = np.array([m["lang0"] for m in meta])
    grans = [("area · 12", area_arr), ("area · L0", ap0), ("area · L1", ap1),
             ("family · 11", fam_arr), ("family · raw", lang)]
    fold = rng.permutation(N) % 5

    def heldout_ll(groups):
        lls = []
        for f in range(5):
            tr = fold != f; te = fold == f
            glob = (P[tr].sum(0) + 1) / (tr.sum() + 2)
            rate = {}
            for g in set(groups[tr]):
                idx = tr & (groups == g)
                rate[g] = (P[idx].sum(0) + 1) / (idx.sum() + 2)
            s, cnt = 0.0, 0
            for i in np.where(te)[0]:
                p = np.clip(rate.get(groups[i], glob), 1e-6, 1 - 1e-6)
                s += float((P[i] * np.log(p) + (1 - P[i]) * np.log(1 - p)).sum()); cnt += M
            lls.append(s / cnt)
        return round(float(np.mean(lls)), 4)

    gran = [{"name": nm, "k": int(len(set(g))), "ll": heldout_ll(g)} for nm, g in grans]

    data = {
        "n": N, "n_motif": M, "match_km": MATCH_KM, "min_motif": MIN_MOTIF,
        "facets": ["area", "family", "subsistence", "theme_profile"],
        "assoc": assoc, "eta": eta,
        "unique": {"full_r2": round(float(full), 4), "delta": delta, "mantel_p": mantel_p},
        "residual": {"K": K, "ari": ari, "residual": residual,
                     "cont_residual": round(1 - float(full), 3),
                     "worst_cluster_size": int((lab == worst).sum()), "worst_desc": worst_desc},
        "gran": gran,
        "counts": {"area": len(set(area_arr)), "family": len(set(fam_arr)), "subsistence": len(set(sub_arr))},
    }
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"working set: {N} traditions ({data['counts']}) · {M} motifs")
    print(f"1. Cramér's V: area|family={assoc['area|family']} area|sub={assoc['area|subsistence']} "
          f"family|sub={assoc['family|subsistence']}; η²(theme)= {eta}")
    print(f"2. unique Δ R²: {delta} (full R²={full:.4f}, Mantel p={mantel_p})")
    print(f"3. residual: ARI {ari}; residual={residual}; worst cluster (n={data['residual']['worst_cluster_size']}): {worst_desc}")
    print("4. granularity held-out ll:")
    for gg in gran:
        print(f"   {gg['name']:14} k={gg['k']:3} ll={gg['ll']}")


if __name__ == "__main__":
    main()
