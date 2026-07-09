"""Tradition -> motif biclustering run *separately for each index* — Berezkin only,
Thompson (TMI) only, ATU only. Same method as mockup 05, but each catalogue's own
motif x tradition table is co-clustered on its own, so you can compare the areal /
cultural structure each index carries independently.

Run from repo root:  python mockups/06-per-index-biclusters/build_data.py
"""
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy import sparse
from sklearn.cluster import SpectralCoclustering
from sklearn.feature_extraction.text import TfidfTransformer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _geo import SUBREGION, berezkin_coords, gaz_coord  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "data.js"


def _sunflower_offset(i, n):
    """Unit-disk position of point ``i`` of ``n`` on a Fermat (sunflower) spiral.

    Deterministic and gives even areal density with no overlaps, so a group of
    traditions sharing one base coordinate spreads into an even cloud instead of
    piling up. Returns (dx, dy) with radius in [0, 1]; scale by the desired span.
    """
    if n <= 1:
        return 0.0, 0.0
    golden = math.pi * (3.0 - math.sqrt(5.0))   # golden angle, ~2.39996 rad
    r = math.sqrt((i + 0.5) / n)                 # sqrt -> uniform density
    theta = i * golden
    return r * math.cos(theta), r * math.sin(theta)


def coord_resolver(index):
    """label -> (lon, lat, precise) or None, per index.

    ``precise`` is True for a real per-tradition location, False for a
    subregion-centroid fallback (many traditions share one centroid; they are
    spread out afterwards so they don't pile up).

    For the Berezkin index the real location is the tradition's own map
    coordinate, read from the built motif pipeline
    (``outputs/motifs/mapsofmyths_traditions.json``, areal_id -> [lat, lon]).
    Only where that is missing do we fall back to the areal-subregion centroid —
    optionally nudged by a per-people gazetteer hit, but only when it agrees with
    the tradition's subregion so an accidental name collision can't fling a point
    across the world.
    """
    if index == "brz":
        bz = load("berezkin.json")
        coords = berezkin_coords()   # areal_id -> [lat, lon]
        name2coord, name2sub = {}, {}
        for aid, v in bz["traditions"].items():
            key = canon(v.get("name") or "")
            c = coords.get(aid) or v.get("coordinates")   # pipeline coords, index row as fallback
            if isinstance(c, (list, tuple)) and len(c) == 2:
                name2coord[key] = (float(c[1]), float(c[0]))   # [lat, lon] -> (lon, lat)
            ap = v.get("areal_path") or []
            if len(ap) >= 2:
                name2sub[key] = ap[1][1].upper()
        def r(label):
            real = name2coord.get(label)
            if real:
                return (real[0], real[1], True)
            cen = SUBREGION.get(name2sub.get(label))
            g = gaz_coord(label)
            if g and cen:
                if abs(g[0] - cen[0]) <= 35 and abs(g[1] - cen[1]) <= 25:
                    return (float(g[0]), float(g[1]), True)
                return (float(cen[0]), float(cen[1]), False)
            if g:
                return (float(g[0]), float(g[1]), True)
            if cen:
                return (float(cen[0]), float(cen[1]), False)
            return None
        return r
    def r(label):
        c = gaz_coord(label)
        if c:
            return (float(c[0]), float(c[1]), True)
        return None
    return r


def place_points(resolve, labels_by_cluster, trad_mem):
    """Resolve every tradition to a map point, then spread points that share a
    base coordinate into an even cloud (sunflower spiral) so nothing piles up.

    ``labels_by_cluster``: list of (cluster_index, [labels]). Returns
    (points, placed). Placement is fully deterministic (ordered by label).
    """
    raw = []   # (label, k, lon, lat, precise)
    for k, labels in labels_by_cluster:
        for label in labels:
            xy = resolve(label)
            if xy:
                raw.append((label, k, xy[0], xy[1], xy[2]))

    # group points sharing one base coordinate; a subregion centroid gets a
    # wider spread than a real per-people coordinate that a few labels collide on.
    groups = defaultdict(list)
    for idx, (_label, _k, lon, lat, precise) in enumerate(raw):
        groups[(round(lon, 3), round(lat, 3), precise)].append(idx)

    coords = [None] * len(raw)
    for (lon, lat, precise), members in groups.items():
        members.sort(key=lambda i: raw[i][0])    # deterministic order by label
        n = len(members)
        span = (0.8 if precise else 1.3) * math.sqrt(n)   # degrees
        for j, idx in enumerate(members):
            ox, oy = _sunflower_offset(j, n)
            coords[idx] = (round(lon + ox * span * 1.35, 2),
                           round(lat + oy * span, 2))

    points = []
    for idx, (label, k, _lon, _lat, _precise) in enumerate(raw):
        x, y = coords[idx]
        points.append({"t": label, "x": x, "y": y, "k": k, "s": trad_mem.get(label, 0)})
    return points, len(points)

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
        cvocab = [c for c, k in zip(cvocab, nz, strict=True) if k]
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

    # map points: each cluster's traditions placed by coordinate, coloured by
    # cluster, then spread within their locale so nothing piles into a blob.
    resolve = coord_resolver(index)
    labels_by_cluster = [(k, c.pop("_all")) for k, c in enumerate(clusters)]
    points, placed = place_points(resolve, labels_by_cluster, trad_mem)
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
