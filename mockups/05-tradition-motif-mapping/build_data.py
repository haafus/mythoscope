"""Map *traditions the sources actually name* to the motifs characteristic of them —
no fixed macro-area grid. We take the culture/tradition labels listed on each motif
across all three indexes (TMI `cultures`, parsed from notes+bibliography; ATU
attestation `people`; Berezkin `traditions`), build a motif x tradition incidence
matrix, and co-cluster it: each bicluster is a *group of traditions* paired with the
*group of motifs* that co-occur with them ("for these peoples, these myths").

Run from repo root:  python mockups/05-tradition-motif-mapping/build_data.py
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
K, MIN_DF, MIN_CULT, MAX_DF_FRAC = 16, 25, 2, 0.33


def jitter(label):
    h = abs(hash(label))
    return ((h % 1000) / 1000 - 0.5) * 6, ((h // 1000 % 1000) / 1000 - 0.5) * 4


def load(n):
    with open(ROOT / "outputs" / "motifs" / n, encoding="utf-8") as f:
        return json.load(f)


def canon(s):
    s = re.sub(r"\s+", " ", (s or "").strip()).rstrip(".,;:")
    return s


def collect():
    """namespaced motif id -> (index, code, name, set(culture labels))."""
    out = {}
    for r in load("tmi.json")["motifs"]:
        cults = {canon(c) for c in (r.get("cultures") or {})}
        if cults:
            out[f"tmi:{r['id']}"] = ("tmi", r["id"], r.get("name") or r["id"], cults)
    bz = load("berezkin.json")
    tname = {code: canon(v.get("name") or code) for code, v in bz["traditions"].items()}
    for r in bz["motifs"]:
        cults = {tname[c] for c in (r.get("traditions") or []) if c in tname}
        if cults:
            out[f"brz:{r['id']}"] = ("brz", r["id"], r.get("name") or r["id"], cults)
    for r in load("atu.json")["types"]:
        people = set()
        grouped = r.get("attestations_grouped") or {}
        for reg in grouped.get("regions", []):
            for e in reg.get("entries", []):
                if e.get("people"):
                    people.add(canon(e["people"]))
        if people:
            out[f"atu:{r['id']}"] = ("atu", r["id"], r.get("name") or r["id"], people)
    return out


def main():
    motifs = collect()
    ids = list(motifs)
    df = Counter(c for _, _, _, cs in motifs.values() for c in cs)
    nmot = len(ids)
    # keep informative traditions: seen enough, but not near-ubiquitous
    keep = {c for c, n in df.items() if n >= MIN_DF and n <= MAX_DF_FRAC * nmot}
    cvocab = sorted(keep)
    ci = {c: i for i, c in enumerate(cvocab)}

    rows, cols = [], []
    kept_ids = []
    for mid in ids:
        _, _, _, cs = motifs[mid]
        cc = [ci[c] for c in cs if c in ci]
        if len(cc) < MIN_CULT:
            continue
        r = len(kept_ids)
        kept_ids.append(mid)
        for c in cc:
            rows.append(r); cols.append(c)
    M = sparse.csr_matrix((np.ones(len(rows)), (rows, cols)),
                          shape=(len(kept_ids), len(cvocab)))
    W = TfidfTransformer().fit_transform(M)          # damp ubiquitous traditions

    model = SpectralCoclustering(n_clusters=K, random_state=0, svd_method="arpack")
    model.fit(W)
    rlab, clab = model.row_labels_, model.column_labels_

    clusters = []
    for k in range(K):
        cul = [cvocab[j] for j in np.where(clab == k)[0]]
        mrows = np.where(rlab == k)[0]
        if not len(cul) or not len(mrows):
            continue
        cul_sorted = sorted(cul, key=lambda c: -df[c])
        mem = [kept_ids[i] for i in mrows]
        cnames = set(cul)                      # this cluster's traditions (by name)
        # rank a cluster's motifs by how concentrated they are in its own traditions
        def score(mid, cnames=cnames):
            cs = [c for c in motifs[mid][3] if c in ci]
            return sum(c in cnames for c in cs) / (len(cs) or 1)
        mem_sorted = sorted(mem, key=score, reverse=True)
        by = Counter(motifs[m][0] for m in mem)
        clusters.append({
            "traditions": cul_sorted[:60], "_all": cul_sorted,
            "n_trad": len(cul), "n_motif": len(mem),
            "by_index": dict(by),
            "motifs": [{"x": motifs[m][0], "c": motifs[m][1], "n": motifs[m][2],
                        "t": sorted([c for c in motifs[m][3] if c in cnames],
                                    key=lambda c: -df.get(c, 0))[:5]}
                       for m in mem_sorted[:80]],
        })
    clusters.sort(key=lambda c: -c["n_motif"])

    # map points: place each cluster's traditions (Berezkin subregion, else gazetteer)
    bz = load("berezkin.json")
    name2sub = {canon(v.get("name") or ""): (v["areal_path"][1][1].upper())
                for v in bz["traditions"].values() if len(v.get("areal_path") or []) >= 2}

    def coord(label):
        c = SUBREGION.get(name2sub.get(label)) or gaz_coord(label)
        if c:
            dx, dy = jitter(label)
            return [round(c[0] + dx, 1), round(c[1] + dy, 1)]
        return None

    points = []
    for k, c in enumerate(clusters):
        for lab in c.pop("_all"):
            xy = coord(lab)
            if xy:
                points.append({"t": lab, "x": xy[0], "y": xy[1], "k": k})

    data = {
        "n_motifs_total": len(kept_ids), "n_traditions": len(cvocab),
        "by_index_total": dict(Counter(motifs[m][0] for m in kept_ids)),
        "clusters": clusters, "points": points, "placed": len(points),
    }
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"motifs(kept)={len(kept_ids)} traditions(kept)={len(cvocab)} clusters={len(clusters)}")
    for c in clusters:
        print(f"  [{c['n_motif']:4d} motifs {c['by_index']}] traditions: "
              + ", ".join(c["traditions"][:8]))


if __name__ == "__main__":
    main()
