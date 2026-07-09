"""Phylogeographic reconstruction (mockup 31, roadmap M31) — where + when a motif arose.

The etiology-stage capstone: for the descent motifs that mockup 30 could date, reconstruct
each one's **ancestral origin** — a location *and* an age — and show its spread over the map.

- Age: the family-expansion date from mockup 30 (`FAMILY_DATES`).
- Location: the **ancestral-location point estimate** = the centroid of the motif's attesting
  traditions (the mean of what a full Bayesian relaxed-random-walk over the dated tree would
  reconstruct at the origin node). Honest: this is the *point estimate*, not the stochastic
  RRW with an uncertainty cloud — that needs a real dated tree + MCMC (BEAST), beyond a
  self-contained mockup.

Only the inherited, family-concentrated minority is placed; the areal majority has no single
origin to reconstruct (its history is diffusion, mockup 19).

Run:  python mockups/31-phylogeography/build_data.py
"""
import importlib.util
import json
import random
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MOCKS = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
OUT = HERE / "data.js"
MIN_TRAD = 6
N_SHUFFLE = 8
SIG_DESCENT = 0.4
CONC = 0.55
TRACK = {"B4": "fished-out earth", "K57": "Cinderella", "K27z2": "jātaka incest"}


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, MOCKS / rel)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def main():
    geo = _load("_geo.py", "geo")
    m30 = _load("30-dated-phylogeny/build_data.py", "m30")
    FAMILY_DATES = m30.FAMILY_DATES
    coords = geo.berezkin_coords()
    with open(ROOT / "outputs" / "motifs" / "berezkin.json", encoding="utf-8") as f:
        bz = json.load(f)
    T = bz["traditions"]
    join = json.loads((MOCKS / "30-dated-phylogeny" / "glottolog_join.json").read_text(encoding="utf-8"))
    gfam = {t: j["gfam"] for t, j in join.items()}

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

    # tree + Fitch for phylo-signal (as mockup 30)
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

    def centroid(pts):
        """Spherical mean (handles the antimeridian; arithmetic lat/lon means don't)."""
        la = np.radians([p[0] for p in pts]); lo = np.radians([p[1] for p in pts])
        x = np.mean(np.cos(la) * np.cos(lo)); y = np.mean(np.cos(la) * np.sin(lo)); z = np.mean(np.sin(la))
        lat0 = np.degrees(np.arctan2(z, np.sqrt(x * x + y * y))); lon0 = np.degrees(np.arctan2(y, x))
        return round(float(lat0), 2), round(float(lon0), 2)

    rng = random.Random(0)
    origins, tracked = [], []
    age_lo, age_hi = 1e9, 0
    for r in bz["motifs"]:
        P = [t for t in (r.get("traditions") or []) if t in leaf_of]
        if len(P) < MIN_TRAD:
            continue
        pres = {leaf_of[t] for t in P}
        obs = fitch(pres)
        rand = np.mean([fitch(set(rng.sample(leaves, len(pres)))) for _ in range(N_SHUFFLE)])
        signal = 0.0 if rand <= 1 else max(0.0, min(1.0, (rand - obs) / (rand - 1)))
        fams = Counter(gfam.get(t) for t in P if gfam.get(t))
        if not fams:
            continue
        dom, dn = fams.most_common(1)[0]
        conc = dn / len(P)
        if not (signal >= SIG_DESCENT and conc >= CONC and dom in FAMILY_DATES):
            continue
        # origin = homeland centroid: only the dominant-family traditions (not stray occurrences)
        dom_pts = [coord(t) for t in P if gfam.get(t) == dom]; dom_pts = [p for p in dom_pts if p]
        pts = [coord(t) for t in P]; pts = [p for p in pts if p]
        if len(dom_pts) < 2:
            continue
        lat, lon = centroid(dom_pts)
        age = FAMILY_DATES[dom][0]
        age_lo, age_hi = min(age_lo, age), max(age_hi, age)
        origins.append({"c": r["id"], "lat": lat, "lon": lon, "age": age, "fam": dom, "n": len(pts)})
        if r["id"] in TRACK:
            tracked.append({"c": r["id"], "label": TRACK[r["id"]], "n": r.get("name", ""),
                            "lat": lat, "lon": lon, "age": age, "fam": dom,
                            "tips": [{"lat": round(p[0], 2), "lon": round(p[1], 2)} for p in pts]})

    by_fam = Counter(o["fam"] for o in origins)
    data = {"n": len(origins), "min_trad": MIN_TRAD, "age_lo": int(age_lo), "age_hi": int(age_hi),
            "origins": origins, "tracked": tracked,
            "fams": [{"fam": f, "n": n, "age": FAMILY_DATES[f][0]} for f, n in by_fam.most_common()]}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"{len(origins)} descent motifs placed (origin location + age) · ages {int(age_lo)}–{int(age_hi)} BP")
    for t in tracked:
        print(f"  {t['c']:6} {t['label']:16} origin ({t['lat']},{t['lon']}) {t['age']} BP [{t['fam']}] tips={len(t['tips'])}")


if __name__ == "__main__":
    main()
