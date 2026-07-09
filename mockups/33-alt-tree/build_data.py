"""Alternative-tree test (mockup 33, roadmap M33) — does descent survive a genetic tree?

Re-runs the descent detector (chance-corrected Fitch phylo-signal, mockups 18 / 28) on a
**human genetic tree** instead of the language tree, and compares per-motif signal. Tests
alt-hypothesis #3 ("the descent signal is an artifact of the wrong — language — tree").

The genetic tree is a **curated consensus topology at continental resolution** — the
uncontroversial population-genetics backbone (Africa outgroup → out-of-Africa → West vs East
Eurasian; Native Americans nested inside East Eurasia via Beringia; Australo-Papuans deep in the
East branch) — joined tradition → population by **geography** (Berezkin macro-area), NOT by
language (which would be circular). Honest limit: this is continental resolution; a fine
SNP-based population tree (HGDP / 1000G) is the full version and needs the actual genetic data.

Why it is a real test: the language tree unites families that cross genetic/continental lines
(Altaic runs Anatolia→Yakutia; Indo-European spans West-Eurasian + South Asian), while the
genetic tree splits them by continent — so comparing signals asks whether a motif's inheritance
follows *language* or *genes/geography*.

Run:  python mockups/33-alt-tree/build_data.py
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
DESCENT = 0.4
TRACK = {"B4": "fished-out earth", "K57": "Cinderella", "K25": "swan-maiden",
         "A3": "sun & moon", "M29B": "trickster", "K8aa": "Jonah"}

# curated consensus genetic topology, keyed by Berezkin macro-area (m21.AREAS12) → path root→population
GEN = {
    "Sub-Saharan Africa": ["African"],
    "Europe": ["OoA", "WestEurasian", "European"],
    "Near East & N. Africa": ["OoA", "WestEurasian", "NearEastern"],
    "Iran, C. & S. Asia": ["OoA", "WestEurasian", "SouthAsian"],
    "East & SE Asia": ["OoA", "EastEurasian", "EastAsianClade", "EastAsian"],
    "Siberia & Beringia": ["OoA", "EastEurasian", "EastAsianClade", "Siberian"],
    "Austronesia & Oceania": ["OoA", "EastEurasian", "EastAsianClade", "Austronesian"],
    "Aboriginal Australia": ["OoA", "EastEurasian", "AustraloPapuan"],
    "Northern & Western N. America": ["OoA", "EastEurasian", "NativeAmerican", "NAmNorth"],
    "Eastern North America": ["OoA", "EastEurasian", "NativeAmerican", "NAmNorth"],
    "Mesoamerica & the Andes": ["OoA", "EastEurasian", "NativeAmerican", "NAmSouth"],
    "South America": ["OoA", "EastEurasian", "NativeAmerican", "NAmSouth"],
}


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, MOCKS / rel)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def build_tree(path_of):
    """path_of: {tid: tuple(levels)}. Returns tree arrays + leaf_of + postorder + leaves."""
    children, node_of, depth, leaf_of = [[]], {(): 0}, [0], {}
    for tid, levels in path_of.items():
        path, parent = (), 0
        for lvl in levels:
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
    return children, is_leaf, order, leaf_of, leaves


def signaler(children, is_leaf, order, leaves, rng):
    """Returns a function pres_leaves -> chance-corrected phylo-signal in [0,1]."""
    nN = len(children); st = [0] * nN

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

    def signal(pres):
        obs = fitch(pres)
        rand = np.mean([fitch(set(rng.sample(leaves, len(pres)))) for _ in range(N_SHUFFLE)])
        return 0.0 if rand <= 1 else float(max(0.0, min(1.0, (rand - obs) / (rand - 1))))

    return signal


def main():
    m21 = _load("21-facet-population/build_data.py", "m21")
    with open(ROOT / "outputs" / "motifs" / "berezkin.json", encoding="utf-8") as f:
        bz = json.load(f)
    T = bz["traditions"]

    # per-tradition language path and genetic path (both required)
    lang_path, gen_path, gen_pop, lang_fam = {}, {}, {}, {}
    for tid, v in T.items():
        area = m21.area_of(v.get("areal_path") or [])
        if area not in GEN:
            continue
        lang = tuple(v.get("language") or ["(unknown)"])
        lang_path[tid] = lang
        gen_path[tid] = tuple(GEN[area])
        gen_pop[tid] = GEN[area][-1]
        lang_fam[tid] = lang[0]
    tids = list(lang_path)

    cL = build_tree(lang_path)
    cG = build_tree(gen_path)
    leaf_L, leaf_G = cL[3], cG[3]
    rng = random.Random(0)
    sigL = signaler(cL[0], cL[1], cL[2], cL[4], rng)
    sigG = signaler(cG[0], cG[1], cG[2], cG[4], random.Random(0))

    recs, tracked = [], {}
    for r in bz["motifs"]:
        P = [t for t in (r.get("traditions") or []) if t in leaf_L]
        if len(P) < MIN_TRAD:
            continue
        sl = sigL({leaf_L[t] for t in P})
        sg = sigG({leaf_G[t] for t in P})
        fam = Counter(lang_fam[t] for t in P).most_common(1)[0]
        pop = Counter(gen_pop[t] for t in P).most_common(1)[0]
        rec = {"c": r["id"], "n": r.get("name", ""), "np": len(P),
               "sl": round(sl, 3), "sg": round(sg, 3),
               "fam": fam[0], "famc": round(fam[1] / len(P), 2),
               "pop": pop[0], "popc": round(pop[1] / len(P), 2)}
        recs.append(rec)
        if r["id"] in TRACK:
            tracked[r["id"]] = {**rec, "label": TRACK[r["id"]]}

    sl = np.array([r["sl"] for r in recs]); sg = np.array([r["sg"] for r in recs])
    corr = float(np.corrcoef(sl, sg)[0, 1])
    lang_d = sl >= DESCENT; gen_d = sg >= DESCENT
    n_lang = int(lang_d.sum()); n_gen = int(gen_d.sum())
    n_both = int((lang_d & gen_d).sum())
    n_lang_only = int((lang_d & ~gen_d).sum()); n_gen_only = int((~lang_d & gen_d).sum())
    robust = round(n_both / n_lang, 3) if n_lang else 0.0
    # among language-descent motifs, why do some lose genetic signal? cross-continental families
    lang_only_fams = Counter(r["fam"] for r in recs if r["sl"] >= DESCENT and r["sg"] < DESCENT)
    both_fams = Counter(r["fam"] for r in recs if r["sl"] >= DESCENT and r["sg"] >= DESCENT)
    # scatter subsample (deterministic, thinned per quadrant to keep the SVG light)
    def quad(r):
        ld, gd = r["sl"] >= DESCENT, r["sg"] >= DESCENT
        return "both" if ld and gd else "lang" if ld else "gen" if gd else "none"
    step = {"both": 3, "gen": 4, "lang": 1, "none": 10}
    buckets = {"both": [], "gen": [], "lang": [], "none": []}
    for r in recs:
        buckets[quad(r)].append(r)
    scatter = [{"x": r["sl"], "y": r["sg"], "q": q}
               for q, rs in buckets.items() for r in rs[::step[q]]]

    data = {
        "n": len(recs), "n_trad": len(tids), "min_trad": MIN_TRAD, "descent": DESCENT,
        "corr": round(corr, 3),
        "counts": {"lang": n_lang, "gen": n_gen, "both": n_both,
                   "lang_only": n_lang_only, "gen_only": n_gen_only, "robust": robust},
        "lang_only_fams": lang_only_fams.most_common(6),
        "both_fams": both_fams.most_common(6),
        "scatter": scatter,
        "tracked": [tracked[c] for c in TRACK if c in tracked],
        "gen_pops": sorted(set(gen_pop.values())),
    }
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"{len(recs)} motifs · {len(tids)} traditions on both trees · corr(lang,gen)={corr:.3f}")
    print(f"  descent (>= {DESCENT}): language {n_lang}, genetic {n_gen}; both {n_both} "
          f"(robust {robust:.0%}), language-only {n_lang_only}, genetic-only {n_gen_only}")
    print(f"  language-only families (cross-continental): {lang_only_fams.most_common(5)}")
    print(f"  both-tree families (genes+language agree):  {both_fams.most_common(5)}")
    for t in data["tracked"]:
        print(f"  {t['c']:5} {t['label']:16} sigL={t['sl']:.2f} sigG={t['sg']:.2f} "
              f"[{t['fam']} {t['famc']:.0%} / {t['pop']} {t['popc']:.0%}]")


if __name__ == "__main__":
    main()
