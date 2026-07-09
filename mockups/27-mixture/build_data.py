"""Descent / areal / reinvention decomposition per motif (mockup 27, roadmap M27).

Alternative-hypothesis #2 (synthesis §4): `stratum` may not be one ordinal axis — a motif can
be a *mixture* of inheritance, areal diffusion and independent reinvention. This replaces
mockup 19's binary descent-vs-areal gate with a per-motif continuous decomposition into three
shares that sum to 1.

A per-tradition EM was tried first and **rejected**: for broad motifs "has a same-family
relative present" is trivially satisfied (Galton) and cannot be told from areal contiguity, so
the mixture is unidentifiable and over-attributes to descent. Instead we use a **motif-level**
decomposition anchored in the *chance-corrected* phylogenetic signal (mockup 18), which does
NOT saturate with breadth:

  - reinvention = fraction of present traditions that are isolated (no same-family relative and
    no neighbour within R km) — genuine scatter / homoplasy;
  - descent     = (1 - reinvention) · phylo_signal   (structure that follows the language tree);
  - areal       = (1 - reinvention) · (1 - phylo_signal)  (structure that does not).

Run:  python mockups/27-mixture/build_data.py
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
MIN_TRAD = 8
N_SHUFFLE = 8
R_KM = 1500.0
CAP_GEO = 400
TRACK = {"B4": "fished-out earth", "K25": "swan-maiden", "A3": "sun & moon",
         "K8aa": "Jonah", "M182": "tar-baby", "K57": "Cinderella", "M29B": "trickster"}


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, MOCKS / rel)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def main():
    geo = _load("_geo.py", "_geo")
    coords = geo.berezkin_coords()
    with open(ROOT / "outputs" / "motifs" / "berezkin.json", encoding="utf-8") as f:
        bz = json.load(f)
    T = bz["traditions"]
    fam = {t: (v.get("language") or ["?"])[0] for t, v in T.items()}

    # language classification tree (as mockup 18/19)
    children, node_of, depth, leaf_of = [[]], {(): 0}, [0], {}
    for tid, v in T.items():
        path, parent = (), 0
        for lvl in (v.get("language") or ["(unknown)"]):
            path = path + (lvl,); nid = node_of.get(path)
            if nid is None:
                nid = len(children); children.append([]); depth.append(depth[parent] + 1)
                node_of[path] = nid; children[parent].append(nid)
            parent = nid
        leaf = len(children); children.append([]); depth.append(depth[parent] + 1)
        children[parent].append(leaf); leaf_of[tid] = leaf
    nN = len(children); is_leaf = [len(c) == 0 for c in children]
    order, stack, seen = [], [0], [False] * nN
    while stack:
        x = stack[-1]
        if not seen[x]:
            seen[x] = True; stack.extend(children[x])
        else:
            order.append(stack.pop())
    leaves = [i for i in range(nN) if is_leaf[i]]
    st = [0] * nN

    def fitch(pres):
        ch = 0
        for n in order:
            if is_leaf[n]:
                st[n] = 2 if n in pres else 1
            else:
                inter, uni = 3, 0
                for c in children[n]:
                    inter &= st[c]; uni |= st[c]
                st[n] = inter if inter else uni
                ch += 0 if inter else 1
        return ch

    def coord(t):
        c = coords.get(t)
        if isinstance(c, (list, tuple)) and len(c) == 2:
            return float(c[0]), float(c[1])
        ap = T[t].get("areal_path") or []
        if len(ap) >= 2:
            cen = geo.SUBREGION.get(ap[1][1].upper())
            if cen:
                return float(cen[1]), float(cen[0])
        return None

    rng = random.Random(0); nrng = np.random.default_rng(0)

    def reinv_frac(P):
        """Fraction of present traditions isolated: no same-family relative present AND no
        present neighbour within R km."""
        fc = Counter(fam[t] for t in P)
        pts = [coord(t) for t in P]
        idx = [i for i, p in enumerate(pts) if p]
        if len(idx) < 2:
            return 1.0
        sub = idx if len(idx) <= CAP_GEO else list(nrng.choice(idx, CAP_GEO, replace=False))
        la = np.radians([pts[i][0] for i in sub]); lo = np.radians([pts[i][1] for i in sub])
        iso = 0
        for i in idx:
            if fc[fam[P[i]]] > 1:
                continue
            a, o = np.radians(pts[i][0]), np.radians(pts[i][1])
            d = 6371.0 * 2 * np.arcsin(np.sqrt(
                np.sin((la - a) / 2) ** 2 + np.cos(a) * np.cos(la) * np.sin((lo - o) / 2) ** 2))
            if np.sum(d < R_KM) <= 1:
                iso += 1
        return iso / len(idx)

    recs, idx_track = [], {}
    for r in bz["motifs"]:
        P = [t for t in (r.get("traditions") or []) if t in leaf_of]
        if len(P) < MIN_TRAD:
            continue
        pres = {leaf_of[t] for t in P}
        obs = fitch(pres)
        rand = np.mean([fitch(set(rng.sample(leaves, len(pres)))) for _ in range(N_SHUFFLE)])
        signal = 0.0 if rand <= 1 else max(0.0, min(1.0, (rand - obs) / (rand - 1)))
        rv = reinv_frac(P)
        desc = (1 - rv) * signal; areal = (1 - rv) * (1 - signal)
        rec = {"c": r["id"], "n": r.get("name", ""), "g": int(r.get("motif_group_num") or 0),
               "np": len(P), "sig": round(float(signal), 2),
               "desc": round(float(desc), 3), "areal": round(float(areal), 3), "reinv": round(float(rv), 3)}
        recs.append(rec)
        if r["id"] in TRACK:
            idx_track[r["id"]] = rec

    desc = np.array([r["desc"] for r in recs])
    hist = [int(x) for x in np.histogram(desc, bins=np.linspace(0, 1, 11))[0]]
    dom = Counter(max(("inherited", "areal", "reinvention"),
                      key=lambda k: r[{"inherited": "desc", "areal": "areal", "reinvention": "reinv"}[k]])
                  for r in recs)

    def mean_shares(pred):
        sub = [r for r in recs if pred(r)]
        return {k: round(float(np.mean([r[k] for r in sub])), 3) for k in ("desc", "areal", "reinv")} if sub else {}
    byA, byB = mean_shares(lambda r: 1 <= r["g"] <= 9), mean_shares(lambda r: 10 <= r["g"] <= 13)
    tracked = [{**idx_track[c], "label": lab} for c, lab in TRACK.items() if c in idx_track]
    top_desc = sorted(recs, key=lambda r: -r["desc"])[:12]

    data = {"n": len(recs), "min_trad": MIN_TRAD, "r_km": R_KM, "hist": hist,
            "dom": dict(dom), "byA": byA, "byB": byB, "tracked": tracked, "top_desc": top_desc}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"{len(recs)} motifs (>= {MIN_TRAD} traditions) · dominant {dict(dom)}")
    print(f"  mean shares  Category A: {byA}\n               Category B: {byB}")
    for t in tracked:
        print(f"  {t['c']:5} {t['label']:18} desc={t['desc']:.2f} areal={t['areal']:.2f} reinv={t['reinv']:.2f} sig={t['sig']} (n={t['np']})")


if __name__ == "__main__":
    main()
