"""Combined stratum estimator (mockup 19) — the gated A × B pipeline.

Realises stratum-derivation.md §12. For every motif it computes BOTH the geographic
signals of Method A (breadth, mega-set span, fragmentation) and the phylogenetic signal
of Method B (Fitch parsimony on the language tree), then GATES: B decides the mode
(descent vs areal), and the mode picks the dating instrument — clade depth for descent,
geographic disjunction / deep-set span for areal. Output is a combined stratum label +
a depth score + a confidence from A/B agreement. The payoff: the "broad" motifs that
neither method could resolve alone split into areal-deep / descent / areal-recent.

Run:  python mockups/19-combined-stratum/build_data.py
"""
import json
import random
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.cluster import DBSCAN

ROOT = Path(__file__).resolve().parents[2]
MOCKS = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "data.js"
MIN_TRAD = 4
N_SHUFFLE = 8
NW = {"NORTH AMERICA: NORTH AND WEST", "PLAINS AND SOUTHEAST", "MEXICO – CENTRAL ANDES",
      "EASTERN SOUTH AMERICA", "SOUTHERN SOUTH AMERICA", "BERINGIA"}
IP = {"OCEANIA", "AUSTRALIA"}
SIG_DESCENT = 0.5     # phylo-signal gate: descent vs areal
BROAD = 6             # macro-areas
TRACK = {"B4": "fished-out earth", "K25": "swan-maiden", "A3": "sun & moon",
         "K8aa": "Jonah (world-religion)", "M182": "tar-baby", "K57": "Cinderella"}
MODES = {
    "areal_deep": ("Deep areal substrate", "areal, spans both hemispheres (Indo-Pacific + New World) — Pleistocene-era", "#6a5aa6"),
    "descent": ("Descent (clade)", "clustered on the language tree — dated by clade (Neolithic-era expansions)", "#3c8a5e"),
    "areal_broad": ("Broad areal", "widespread by contact, one hemisphere — age ambiguous", "#c05540"),
    "areal_recent": ("Areal / borrowed", "compact, single set — recent diffusion", "#b28a3e"),
    "local": ("Local / insufficient", "too narrow to place", "#98a0a5"),
}


def _geo():
    import importlib.util
    spec = importlib.util.spec_from_file_location("_geo", MOCKS / "_geo.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def main():
    geo = _geo()
    coords = geo.berezkin_coords()
    with open(ROOT / "outputs" / "motifs" / "berezkin.json", encoding="utf-8") as f:
        bz = json.load(f)
    T = bz["traditions"]

    # language classification tree
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
    nN = len(children)
    is_leaf = [len(c) == 0 for c in children]
    order, stack, seen = [], [0], [False] * nN
    while stack:
        x = stack[-1]
        if not seen[x]:
            seen[x] = True; stack.extend(children[x])
        else:
            order.append(stack.pop())
    maxd = max(depth)
    leaves = [i for i in range(nN) if is_leaf[i]]
    st = [0] * nN

    def fitch(pres, want_depth=False):
        ch, origin = 0, maxd
        for n in order:
            if is_leaf[n]:
                st[n] = 2 if n in pres else 1
            else:
                inter, uni = 3, 0
                for c in children[n]:
                    inter &= st[c]; uni |= st[c]
                if inter:
                    st[n] = inter
                    if want_depth and inter == 2:
                        origin = min(origin, depth[n])
                else:
                    st[n] = uni; ch += 1
        return (ch, origin) if want_depth else ch

    def macro(t):
        ap = T[t].get("areal_path") or []
        return ap[0][1] if ap else None

    def coord(t):
        c = coords.get(t)
        if isinstance(c, (list, tuple)) and len(c) == 2:
            return float(c[1]), float(c[0])
        ap = T[t].get("areal_path") or []
        if len(ap) >= 2:
            cen = geo.SUBREGION.get(ap[1][1].upper())
            if cen:
                return float(cen[0]), float(cen[1])
        return None

    rng = random.Random(0)
    recs = []
    for r in bz["motifs"]:
        tids = [t for t in (r.get("traditions") or []) if t in leaf_of]
        if len(tids) < MIN_TRAD:
            continue
        pres = set(leaf_of[t] for t in tids); npres = len(pres)
        obs, origin = fitch(pres, want_depth=True)
        rand = np.mean([fitch(set(rng.sample(leaves, npres))) for _ in range(N_SHUFFLE)])
        signal = 0.0 if rand <= 1 else max(0.0, min(1.0, (rand - obs) / (rand - 1)))
        macros = {macro(t) for t in tids if macro(t)}
        sets = ({"NW"} if macros & NW else set()) | ({"IP"} if macros & IP else set()) \
            | ({"CONT"} if macros - NW - IP else set())
        deep_set = "IP" in sets and "NW" in sets
        pts = [coord(t) for t in tids]; pts = [p for p in pts if p]
        frags = len(set(DBSCAN(eps=0.35, min_samples=1, metric="haversine")
                        .fit(np.radians([[p[1], p[0]] for p in pts])).labels_)) if len(pts) >= 2 else 1
        n_macro = len(macros)
        clade = 1 - origin / maxd    # deeper clade origin -> larger

        # ---- gate: purely distributional (A × B). Theme is deliberately NOT used here —
        # feeding it in would be circular and would forfeit theme × stratum as an
        # independent cross-check. It stays a separate axis. ----
        if n_macro < 4:
            mode = "local"; dep = 10 + n_macro * 3
        elif signal >= SIG_DESCENT:
            mode = "descent"; dep = 50 + 20 * clade          # clade age (Neolithic band)
        elif deep_set and n_macro >= BROAD:
            mode = "areal_deep"; dep = 80 + min(15, frags)   # spans both hemispheres
        elif n_macro >= BROAD:
            mode = "areal_broad"; dep = 48 + min(10, frags)
        else:
            mode = "areal_recent"; dep = 28 + n_macro
        # confidence: gate decisiveness + how hard the depth signal is. areal_deep is the
        # irreducibly uncertain call (deep substrate vs wide diffusion) so it is capped —
        # NOT rescued by theme.
        gate = min(1.0, abs(signal - SIG_DESCENT) / 0.35)
        depth_ok = {"local": 1.0, "areal_recent": 0.8, "descent": 0.8, "areal_broad": 0.6,
                    "areal_deep": 0.5}[mode]
        conf = round(0.5 * gate + 0.5 * depth_ok, 2)
        recs.append({"c": r["id"], "n": r.get("name", ""), "g": int(r.get("motif_group_num") or 0),
                     "mode": mode, "dep": round(min(100.0, dep), 1), "conf": round(conf, 2),
                     "sig": round(signal, 2), "nm": n_macro, "nl": len({T[t]["language"][0] for t in tids if T[t].get("language")}),
                     "fr": frags, "sets": sorted(sets)})

    idx = {r["c"]: r for r in recs}
    counts = Counter(r["mode"] for r in recs)
    examples = {}
    for m in MODES:
        pool = sorted((r for r in recs if r["mode"] == m), key=lambda r: -r["dep"])
        examples[m] = pool[:8]
    ranked = sorted(recs, key=lambda r: -r["dep"])[:24]
    tracked = [{**idx[c], "label": lab} for c, lab in TRACK.items() if c in idx]
    # A-alone would call anything broad "deep": show how the broad set splits by mode
    broad_split = Counter(r["mode"] for r in recs if r["nm"] >= BROAD)

    # theme × mode cross-check — INDEPENDENT: theme was not used to assign the mode, so a
    # gradient of cosmology (Category A) across modes is genuine corroboration, not circular.
    TN = {1: "Sun&Moon", 2: "Stars", 3: "Cosmogony", 4: "Death-orig", 5: "Human-orig",
          6: "Subsist-orig", 7: "Plants&animals", 8: "Monsters", 9: "Identity",
          10: "Adventures", 11: "Tricks", 12: "Names", 13: "Formulae"}
    xtab = {}
    for m in MODES:
        sub = [r for r in recs if r["mode"] == m]
        catA = sum(1 for r in sub if 1 <= r["g"] <= 9)
        top = Counter(TN.get(r["g"], "?") for r in sub).most_common(3)
        xtab[m] = {"catA_pct": round(100 * catA / len(sub)) if sub else 0,
                   "top": [{"n": cnt, "k": name} for name, cnt in top]}

    data = {"n": len(recs), "min_trad": MIN_TRAD, "modes": MODES,
            "counts": dict(counts), "broad_split": dict(broad_split), "xtab": xtab,
            "examples": examples, "ranked": ranked, "tracked": tracked}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"{len(recs)} motifs · modes {dict(counts)} · data.js ~{OUT.stat().st_size // 1024}KB")
    print(f"  broad (>= {BROAD} macro) split by combined mode: {dict(broad_split)}")
    for t in tracked:
        print(f"  {t['c']:5} {t['label']:22} -> {t['mode']:12} depth={t['dep']:5} conf={t['conf']}")


if __name__ == "__main__":
    main()
