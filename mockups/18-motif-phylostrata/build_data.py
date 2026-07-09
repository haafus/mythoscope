"""Motif phylo-strata prototype (mockup 18) — Method B of the stratum proposal.

Method A (mockup 17) dated motifs from GEOGRAPHY and could not tell deep inheritance
from areal diffusion or reinvention. Method B maps each motif onto a language
classification tree (built from the `language` chains in berezkin.json) and runs Fitch
parsimony ancestral-state reconstruction. The key output it adds is COHERENCE — few
independent gains (one deep origin, clustered on the tree) vs many (scattered =
diffused/convergent). Crossed with geographic breadth this separates
inheritance-by-descent from areal diffusion, which no purely geographic score can.

Interim: a coarse family→subfamily tree from our own `language` field. Swapping in the
dated Glottolog + Bouckaert/EDGE phylogeny (open data) upgrades this to true node ages.

Run:  python mockups/18-motif-phylostrata/build_data.py
"""
import json
import random
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "data.js"
MIN_TRAD = 4
N_SHUFFLE = 12   # random tip placements per motif, for the phylogenetic-signal test
TRACK = {"K25": "swan-maiden", "M29B": "trickster (coyote/fox)", "C6i1": "earth-diver",
         "B4": "fished-out earth", "K8aa": "Jonah (world-religion)", "A3": "sun & moon (male/female)"}


def main():
    with open(ROOT / "outputs" / "motifs" / "berezkin.json", encoding="utf-8") as f:
        bz = json.load(f)
    T = bz["traditions"]

    # ---- build the language classification trie: ROOT -> family -> ... -> tradition leaf
    children = [[]]          # node 0 = ROOT
    node_of = {(): 0}
    depth = [0]
    leaf_of = {}
    for tid, v in T.items():
        path, parent = (), 0
        for lvl in (v.get("language") or ["(unknown)"]):
            path = path + (lvl,)
            nid = node_of.get(path)
            if nid is None:
                nid = len(children); children.append([]); depth.append(depth[parent] + 1)
                node_of[path] = nid; children[parent].append(nid)
            parent = nid
        leaf = len(children); children.append([]); depth.append(depth[parent] + 1)
        children[parent].append(leaf); leaf_of[tid] = leaf
    n_nodes = len(children)
    is_leaf = np.array([len(c) == 0 for c in children])

    # post-order (children before parents)
    order, stack = [], [0]
    seen = [False] * n_nodes
    while stack:
        n = stack[-1]
        if not seen[n]:
            seen[n] = True
            for c in children[n]:
                stack.append(c)
        else:
            order.append(stack.pop())

    def macro(t):
        ap = T[t].get("areal_path") or []
        return ap[0][1] if ap else None

    def lang(t):
        lg = T[t].get("language") or []
        return lg[0] if lg else None

    # ---- Fitch parsimony: minimum independent gains for a presence set ----
    st = [0] * n_nodes
    leaves = [n for n in range(n_nodes) if is_leaf[n]]

    def fitch_changes(pres):
        ch = 0
        for n in order:
            if is_leaf[n]:
                st[n] = 2 if n in pres else 1
            else:
                inter, uni = 3, 0
                for c in children[n]:
                    inter &= st[c]; uni |= st[c]
                if inter:
                    st[n] = inter
                else:
                    st[n] = uni; ch += 1
        return ch

    # phylogenetic signal = how much fewer gains than random tip placement (a D-like
    # statistic): 1 = perfectly clustered on the tree (inheritance), ~0 = indistinguishable
    # from random w.r.t. the tree (areal diffusion / homoplasy).
    rng = random.Random(0)
    rows, mids = [], []
    for r in bz["motifs"]:
        tids = [t for t in (r.get("traditions") or []) if t in leaf_of]
        if len(tids) < MIN_TRAD:
            continue
        pres = set(leaf_of[t] for t in tids)
        n_pres = len(pres)
        obs = fitch_changes(pres)
        rand = np.mean([fitch_changes(set(rng.sample(leaves, n_pres))) for _ in range(N_SHUFFLE)])
        signal = 0.0 if rand <= 1 else max(0.0, min(1.0, (rand - obs) / (rand - 1)))
        n_macro = len({macro(t) for t in tids if macro(t)})
        n_lang = len({lang(t) for t in tids if lang(t)})
        rows.append([n_pres, obs, round(signal, 3), n_macro, n_lang])
        mids.append(r)

    A = np.array(rows, dtype=float)   # cols: n_pres, gains, signal, n_macro, n_lang
    coh, brd = A[:, 2], A[:, 3]

    def rec(i):
        r = mids[i]
        return {"c": r["id"], "n": r.get("name", ""), "g": int(r.get("motif_group_num") or 0),
                "np": int(A[i, 0]), "ch": int(A[i, 1]), "coh": round(float(A[i, 2]), 2),
                "nm": int(A[i, 3]), "nl": int(A[i, 4])}

    idx = {r["id"]: i for i, r in enumerate(mids)}

    # quadrant thresholds: broad = n_macro>=6, coherent = coherence>=0.5
    BR, CO = 6, 0.5
    quad = {"deep": [], "diffuse": [], "clade": [], "noise": []}
    for i in range(len(mids)):
        b, c = brd[i] >= BR, coh[i] >= CO
        key = "deep" if (b and c) else "diffuse" if (b and not c) else "clade" if (not b and c) else "noise"
        quad[key].append(i)
    counts = {k: len(v) for k, v in quad.items()}
    examples = {k: [rec(int(i)) for i in sorted(v, key=lambda i: -A[i, 0])[:8]] for k, v in quad.items()}

    tracked = [{**rec(idx[c]), "label": lab} for c, lab in TRACK.items() if c in idx]

    # scatter cloud (lightweight): breadth (n_macro) vs phylo signal
    cloud = [{"x": int(A[i, 3]), "y": round(float(A[i, 2]), 3)} for i in range(len(mids))]

    data = {"n_motifs": len(mids), "min_trad": MIN_TRAD, "n_nodes": n_nodes,
            "br": BR, "co": CO, "counts": counts, "examples": examples,
            "tracked": tracked, "cloud": cloud}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"{len(mids)} motifs · tree {n_nodes} nodes · quadrants {counts} · data.js ~{OUT.stat().st_size // 1024}KB")
    for t in tracked:
        print(f"  {t['c']:5} {t['label']:24} phylo-signal={t['coh']:.2f} gains={t['ch']:3} macro={t['nm']:2} lang={t['nl']:2}")


if __name__ == "__main__":
    main()
