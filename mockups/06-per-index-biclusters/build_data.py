"""Tradition -> motif biclustering run *separately for each index* — Berezkin only,
Thompson (TMI) only, ATU only. Same method as mockup 05, but each catalogue's own
motif x tradition table is co-clustered on its own, so you can compare the areal /
cultural structure each index carries independently.

Run from repo root:  python mockups/06-per-index-biclusters/build_data.py
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from scipy import sparse
from sklearn.cluster import SpectralCoclustering
from sklearn.feature_extraction.text import TfidfTransformer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _geo import SUBREGION, gaz_coord  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "data.js"


def jitter(label):
    h = abs(hash(label))
    return ((h % 1000) / 1000 - 0.5) * 6, ((h // 1000 % 1000) / 1000 - 0.5) * 4


def coord_resolver(index):
    """label -> (lon, lat) or None, per index."""
    if index == "brz":
        bz = load("berezkin.json")
        name2sub = {}
        for v in bz["traditions"].values():
            ap = v.get("areal_path") or []
            if len(ap) >= 2:
                name2sub[canon(v.get("name") or "")] = ap[1][1].upper()
        def r(label):
            sub = name2sub.get(label)
            c = SUBREGION.get(sub) if sub else None
            if c:
                dx, dy = jitter(label)
                return [round(c[0] + dx, 1), round(c[1] + dy, 1)]
            return None
        return r
    def r(label):
        c = gaz_coord(label)
        if c:
            dx, dy = jitter(label)
            return [round(c[0] + dx, 1), round(c[1] + dy, 1)]
        return None
    return r

# per-index tuning: (K clusters, MIN_DF, MAX_DF_FRAC, MIN_CULT-per-motif)
CFG = {
    "brz": (14, 6, 0.40, 2),
    "tmi": (16, 20, 0.33, 2),
    "atu": (12, 8, 0.60, 3),
}


def load(n):
    with open(ROOT / "outputs" / "motifs" / n, encoding="utf-8") as f:
        return json.load(f)


def canon(s):
    return re.sub(r"\s+", " ", (s or "").strip()).rstrip(".,;:")


def collect(index, tmi_norm=None):
    """namespaced motif id -> (code, name, set(tradition labels)) for one index.

    ``tmi_norm``: optional callable applied to each raw TMI culture label
    (e.g. ``culture_dict.canonical``); only used for the ``tmi`` index.
    """
    out = {}
    if index == "tmi":
        for r in load("tmi.json")["motifs"]:
            cs = {tmi_norm(c) for c in (r.get("cultures") or {})} if tmi_norm \
                else {canon(c) for c in (r.get("cultures") or {})}
            cs = {c for c in cs if c}
            if cs:
                out[r["id"]] = (r["id"], r.get("name") or r["id"], cs)
    elif index == "brz":
        bz = load("berezkin.json")
        tname = {c: canon(v.get("name") or c) for c, v in bz["traditions"].items()}
        for r in bz["motifs"]:
            cs = {tname[c] for c in (r.get("traditions") or []) if c in tname}
            if cs:
                out[r["id"]] = (r["id"], r.get("name") or r["id"], cs)
    else:  # atu
        for r in load("atu.json")["types"]:
            ppl = set()
            for reg in (r.get("attestations_grouped") or {}).get("regions", []):
                for e in reg.get("entries", []):
                    if e.get("people"):
                        ppl.add(canon(e["people"]))
            if ppl:
                out[r["id"]] = (r["id"], r.get("name") or r["id"], ppl)
    return out


def bicluster(index, tmi_norm=None, cfg=None):
    # cfg overrides CFG[index] as (K, MIN_DF, MAX_DF_FRAC, MIN_CULT); mockup 07
    # uses it to retune the normalized TMI view.
    K, MIN_DF, MAX_DF_FRAC, MIN_CULT = cfg or CFG[index]
    motifs = collect(index, tmi_norm)
    ids = list(motifs)
    df = Counter(c for _, _, cs in motifs.values() for c in cs)
    keep = {c for c, n in df.items() if n >= MIN_DF and n <= MAX_DF_FRAC * len(ids)}
    cvocab = sorted(keep)
    ci = {c: i for i, c in enumerate(cvocab)}

    rows, cols, kept = [], [], []
    for mid in ids:
        cc = [ci[c] for c in motifs[mid][2] if c in ci]
        if len(cc) < MIN_CULT:
            continue
        r = len(kept); kept.append(mid)
        for c in cc:
            rows.append(r); cols.append(c)
    M = sparse.csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(len(kept), len(cvocab)))
    # Drop traditions whose every motif was filtered out (all-zero columns): they
    # pass MIN_DF on the raw df but carry no kept motif, and the spectral
    # normalisation would divide by their zero column sum. Matters at low MIN_DF.
    nz = np.asarray(M.sum(axis=0)).ravel() > 0
    if not nz.all():
        M = M[:, nz]
        cvocab = [c for c, k in zip(cvocab, nz) if k]
        ci = {c: i for i, c in enumerate(cvocab)}
    W = TfidfTransformer().fit_transform(M)
    K = min(K, len(cvocab), len(kept))
    model = SpectralCoclustering(n_clusters=K, random_state=0, svd_method="arpack").fit(W)
    rlab, clab = model.row_labels_, model.column_labels_

    # Membership (0..1): a tradition's share of motifs that sit in its own cluster
    # (the symmetric motif measure is `score()` below).
    Mcsc = M.tocsc()
    trad_mem = {name: round(float(np.mean(rlab[Mcsc.getcol(j).indices] == clab[j]))
                            if Mcsc.getcol(j).indices.size else 0.0, 3)
                for j, name in enumerate(cvocab)}

    clusters = []
    for k in range(K):
        cnames = {cvocab[j] for j in np.where(clab == k)[0]}
        mrows = np.where(rlab == k)[0]
        if not cnames or not len(mrows):
            continue
        mem = [kept[i] for i in mrows]

        def score(mid, cnames=cnames):
            cs = [c for c in motifs[mid][2] if c in ci]
            return sum(c in cnames for c in cs) / (len(cs) or 1)

        mem = sorted(mem, key=score, reverse=True)
        clusters.append({
            "traditions": sorted(cnames, key=lambda c: -df[c])[:50],
            "n_trad": len(cnames), "n_motif": len(mrows),
            "_all": sorted(cnames, key=lambda c: -df[c]),
            "motifs": [{"c": motifs[m][0], "n": motifs[m][1], "s": round(score(m), 3),
                        "t": sorted([c for c in motifs[m][2] if c in cnames],
                                    key=lambda c: -df.get(c, 0))[:5]} for m in mem[:80]],
        })
    clusters.sort(key=lambda c: -c["n_motif"])

    # map points: each cluster's traditions placed by coordinate, coloured by cluster
    resolve = coord_resolver(index)
    points, placed = [], 0
    for k, c in enumerate(clusters):
        for label in c.pop("_all"):
            xy = resolve(label)
            if xy:
                points.append({"t": label, "x": xy[0], "y": xy[1], "k": k,
                               "s": trad_mem.get(label, 0)})
                placed += 1
    return {"n_motifs": len(kept), "n_traditions": len(cvocab),
            "clusters": clusters, "points": points, "placed": placed, "trad_mem": trad_mem}


def main():
    data = {ix: bicluster(ix) for ix in ("brz", "tmi", "atu")}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    for ix in ("brz", "tmi", "atu"):
        d = data[ix]
        print(f"[{ix}] motifs={d['n_motifs']} traditions={d['n_traditions']} clusters={len(d['clusters'])}")
        for c in d["clusters"][:6]:
            print(f"    {c['n_motif']:4d} motifs · {', '.join(c['traditions'][:7])}")
    print(f"data.js ~{OUT.stat().st_size // 1024}KB")


if __name__ == "__main__":
    main()
