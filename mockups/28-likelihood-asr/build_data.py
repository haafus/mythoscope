"""Likelihood ancestral-state reconstruction (mockup 28, roadmap M28).

Upgrades Method B (mockup 18) from Fitch **parsimony** gain-counting to a 2-state
continuous-time Markov (Mk) gain/loss model with **marginal ancestral-state reconstruction**
by belief propagation (inside/outside sum-product). Instead of a hard minimum gain count it
gives, per motif:

  - `exp_gains` — the *expected* number of independent 0->1 transitions (a continuous,
    probabilistic homoplasy estimate);
  - `root_deep` — the posterior probability the motif was present at a deep ancestral node
    (its maximal top-level-family root), i.e. how strongly it reconstructs to a deep clade.

Gain/loss rates are fit globally with a **loss bias** (Dollo-flavoured: motifs are lost more
readily than independently re-invented). Honest limit: the classification tree has no branch
lengths, so results largely track parsimony; the real payoff (calendar ages, sharp ASR) needs
the dated tree of M30. What is genuinely new here is the *probabilistic* output.

Run:  python mockups/28-likelihood-asr/build_data.py
"""
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MOCKS = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "data.js"
MIN_TRAD = 8
TRACK = {"B4": "fished-out earth", "K25": "swan-maiden", "A3": "sun & moon",
         "K8aa": "Jonah", "M182": "tar-baby", "K57": "Cinderella", "M29B": "trickster"}


def pmat(q01, q10):
    """Transition matrix over one unit edge for the 2-state gain/loss CTMC (closed form)."""
    s = q01 + q10
    e = np.exp(-s)
    pi0, pi1 = q10 / s, q01 / s
    return np.array([[pi0 + pi1 * e, pi1 - pi1 * e],
                     [pi0 - pi0 * e, pi1 + pi0 * e]]), np.array([pi0, pi1])


def main():
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
    nN = len(children); is_leaf = [len(c) == 0 for c in children]
    parent_of = [-1] * nN
    for p in range(nN):
        for c in children[p]:
            parent_of[c] = p
    post, stack, seen = [], [0], [False] * nN
    while stack:
        x = stack[-1]
        if not seen[x]:
            seen[x] = True; stack.extend(children[x])
        else:
            post.append(stack.pop())
    pre = post[::-1]
    top_roots = children[0]                      # top-level language families

    # parsimony gains (Fitch) for the comparison
    stf = [0] * nN

    def fitch(pres):
        ch = 0
        for n in post:
            if is_leaf[n]:
                stf[n] = 2 if n in pres else 1
            else:
                inter, uni = 3, 0
                for c in children[n]:
                    inter &= stf[c]; uni |= stf[c]
                stf[n] = inter if inter else uni
                ch += 0 if inter else 1
        return ch

    # ---- global loss-biased rate fit over a small grid ----
    sample = [r for r in bz["motifs"] if len([t for t in (r.get("traditions") or []) if t in leaf_of]) >= MIN_TRAD]
    pres_sets = [{leaf_of[t] for t in (r.get("traditions") or []) if t in leaf_of} for r in sample[:400]]

    def loglik(P, prior, pres):
        In = np.ones((nN, 2))
        for n in post:
            if is_leaf[n]:
                In[n] = [0.0, 1.0] if n in pres else [1.0, 0.0]
            else:
                m = np.ones(2)
                for c in children[n]:
                    m *= P @ In[c]
                In[n] = m
        return np.log(max(prior @ In[0], 1e-300))

    best = None
    for q01 in (0.05, 0.1, 0.2):
        for mult in (2, 4, 8):                   # loss = mult * gain (Dollo-flavoured)
            P, prior = pmat(q01, q01 * mult)
            ll = sum(loglik(P, prior, ps) for ps in pres_sets)
            if best is None or ll > best[0]:
                best = (ll, q01, q01 * mult)
    _, q01, q10 = best
    P, prior = pmat(q01, q10)

    def infer(pres):
        In = np.ones((nN, 2))
        for n in post:
            if is_leaf[n]:
                In[n] = [0.0, 1.0] if n in pres else [1.0, 0.0]
            else:
                m = np.ones(2)
                for c in children[n]:
                    m *= P @ In[c]
                In[n] = m
        Out = np.ones((nN, 2)); Out[0] = prior
        for n in pre:
            if is_leaf[n]:
                continue
            for c in children[n]:
                sib = np.ones(2)
                for c2 in children[n]:
                    if c2 != c:
                        sib *= P @ In[c2]
                Out[c] = (Out[n] * sib) @ P
        exp_gains = 0.0
        for c in range(1, nN):
            p = parent_of[c]
            joint = np.outer(Out[p], np.ones(2)) * P * np.outer(np.ones(2), In[c])
            joint = joint / max(joint.sum(), 1e-300)
            exp_gains += joint[0, 1]              # P(parent=0, child=1) = a gain on this edge
        # deep presence: max posterior of state 1 at a top-level family root
        marg = {n: (Out[n] * In[n]) for n in top_roots}
        root_deep = max((m[1] / max(m.sum(), 1e-300)) for m in marg.values()) if top_roots else 0.0
        return exp_gains, float(root_deep)

    recs, idx_track = [], {}
    for r in bz["motifs"]:
        P_ = [t for t in (r.get("traditions") or []) if t in leaf_of]
        if len(P_) < MIN_TRAD:
            continue
        pres = {leaf_of[t] for t in P_}
        pars = fitch(pres)
        eg, rd = infer(pres)
        rec = {"c": r["id"], "n": r.get("name", ""), "g": int(r.get("motif_group_num") or 0),
               "np": len(P_), "pars": pars, "eg": round(eg, 1), "rd": round(rd, 2)}
        recs.append(rec)
        if r["id"] in TRACK:
            idx_track[r["id"]] = rec

    pars = np.array([r["pars"] for r in recs], float)
    eg = np.array([r["eg"] for r in recs], float)
    corr = float(np.corrcoef(pars, eg)[0, 1])
    # descent-ish: few expected gains AND deep reconstruction
    deep = [r for r in recs if r["rd"] >= 0.5]
    tracked = [{**idx_track[c], "label": lab} for c, lab in TRACK.items() if c in idx_track]
    top_deep = sorted(recs, key=lambda r: (-r["rd"], r["eg"]))[:12]

    data = {"n": len(recs), "min_trad": MIN_TRAD, "q01": round(q01, 3), "q10": round(q10, 3),
            "loss_mult": round(q10 / q01, 1), "corr_pars_eg": round(corr, 3),
            "n_deep": len(deep), "tracked": tracked, "top_deep": top_deep}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"{len(recs)} motifs · fitted gain={q01} loss={q10} (loss={q10/q01:.0f}x gain)")
    print(f"  corr(parsimony gains, expected gains) = {corr:.3f}")
    print(f"  motifs reconstructed present at a deep family root (>=0.5): {len(deep)}")
    for t in tracked:
        print(f"  {t['c']:5} {t['label']:18} parsimony={t['pars']:3} exp_gains={t['eg']:5} deep={t['rd']:.2f} (n={t['np']})")


if __name__ == "__main__":
    main()
