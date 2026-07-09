"""Likelihood ancestral-state reconstruction (mockup 28, roadmap M28).

Upgrades Method B (mockup 18) from Fitch **parsimony** gain-counting to a 2-state
continuous-time Markov (Mk) gain/loss model with **marginal ancestral-state reconstruction**
by belief propagation (inside/outside sum-product). Per motif it gives:

  - `exp_gains` — the *expected* number of independent 0->1 transitions (a continuous,
    probabilistic homoplasy estimate);
  - `root_deep` — the posterior probability the motif was present at a deep ancestral node
    (its maximal top-level-family root), i.e. how strongly it reconstructs to a deep clade.

Gain/loss rates are fit globally with a **loss bias** (Dollo-flavoured).

**Dated re-run (the M30 payoff).** The model is run twice: once on the *undated* tree (every
branch = one unit edge — where likelihood largely reproduces parsimony), and once on a
**family-scaled dated tree**: each top-level family gets a calendar root age from mockup 30's
`FAMILY_DATES` (matched via the modal Glottolog family of its traditions), internal branch
durations are scaled by node height within the family, and `P(t) = expm(Q·t)` per branch.
The dated run yields rates in **absolute time**, a sharper Dollo loss on deep branches, and a
**node-level likelihood origin age** per descent motif — a cross-check on M30/M31's
family-ceiling estimate. Honest limit: the scaling is a topology-proportional proxy, not real
divergence times, and undated families take a default root age; a genuine BEAST RRW stays M31
future work.

Run:  python mockups/28-likelihood-asr/build_data.py
"""
import importlib.util
import json
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MOCKS = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "data.js"
MIN_TRAD = 8
TRACK = {"B4": "fished-out earth", "K25": "swan-maiden", "A3": "sun & moon",
         "K8aa": "Jonah", "M182": "tar-baby", "K57": "Cinderella", "M29B": "trickster"}


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, MOCKS / rel)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def pmat_t(q01, q10, t):
    """2-state gain/loss CTMC transition matrix over an edge of duration t (closed form)."""
    s = q01 + q10
    e = np.exp(-s * t)
    pi0, pi1 = q10 / s, q01 / s
    return np.array([[pi0 + pi1 * e, pi1 - pi1 * e],
                     [pi0 - pi0 * e, pi1 + pi0 * e]])


def main():
    m30 = _load("30-dated-phylogeny/build_data.py", "m30")
    FAMILY_DATES = m30.FAMILY_DATES
    with open(ROOT / "outputs" / "motifs" / "berezkin.json", encoding="utf-8") as f:
        bz = json.load(f)
    T = bz["traditions"]
    join = json.loads((MOCKS / "30-dated-phylogeny" / "glottolog_join.json").read_text(encoding="utf-8"))
    gfam = {t: j["gfam"] for t, j in join.items()}

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
    tid_of_leaf = {v: k for k, v in leaf_of.items()}

    # ---- family-scaled branch durations (kyr) from mockup 30's FAMILY_DATES ----
    default_kyr = float(np.median([v[0] for v in FAMILY_DATES.values()])) / 1000.0
    topanc = [-1] * nN
    for r in top_roots:
        st = [r]
        while st:
            x = st.pop(); topanc[x] = r; st.extend(children[x])
    # node height (longest downward path in edges); leaves = 0
    height = [0] * nN
    for n in post:
        if not is_leaf[n]:
            height[n] = 1 + max(height[c] for c in children[n])
    # per top-family root age (kyr): modal *dated* Glottolog family of its traditions
    dated_leaves = 0
    root_age = {}
    for r in top_roots:
        fams = Counter(gfam.get(tid_of_leaf[n]) for n in range(nN)
                       if is_leaf[n] and topanc[n] == r and gfam.get(tid_of_leaf.get(n)) in FAMILY_DATES)
        if fams:
            fam = fams.most_common(1)[0][0]
            root_age[r] = FAMILY_DATES[fam][0] / 1000.0
            dated_leaves += sum(1 for n in range(nN) if is_leaf[n] and topanc[n] == r)
        else:
            root_age[r] = default_kyr
    n_leaves = sum(is_leaf)
    # node ages (kyr before present) then branch durations
    age = [0.0] * nN
    for r in top_roots:
        A, H = root_age[r], height[r]
        for n in range(nN):
            if topanc[n] == r:
                age[n] = (A * height[n] / H) if H > 0 else 0.0
    blen_dated = np.ones(nN)
    for c in range(1, nN):
        p = parent_of[c]
        blen_dated[c] = 0.0 if p == 0 else max(age[p] - age[c], 1e-6)
    blen_unit = np.ones(nN)

    # ---- parsimony gains (Fitch) for the comparison ----
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

    sample = [r for r in bz["motifs"] if len([t for t in (r.get("traditions") or []) if t in leaf_of]) >= MIN_TRAD]
    pres_sets = [{leaf_of[t] for t in (r.get("traditions") or []) if t in leaf_of} for r in sample[:400]]

    def edge_mats(q01, q10, blen):
        return [pmat_t(q01, q10, blen[c]) for c in range(nN)]

    def inside(Pe, pres):
        """Scaled inside pass (rescale each internal node to sum 1 — the classification tree
        is deep enough that the unscaled product underflows to 0 on the dated branches)."""
        In = np.ones((nN, 2)); logsc = 0.0
        for n in post:
            if is_leaf[n]:
                In[n] = [0.0, 1.0] if n in pres else [1.0, 0.0]
            else:
                m = np.ones(2)
                for c in children[n]:
                    m *= Pe[c] @ In[c]
                s = m.sum(); In[n] = m / s if s > 0 else m; logsc += np.log(s) if s > 0 else -700
        return In, logsc

    def loglik(Pe, prior, pres):
        In, logsc = inside(Pe, pres)
        return logsc + np.log(max(prior @ In[0], 1e-300))

    def infer(Pe, prior, pres):
        In, _ = inside(Pe, pres)
        Out = np.ones((nN, 2)); Out[0] = prior
        for n in pre:
            if is_leaf[n]:
                continue
            for c in children[n]:
                sib = np.ones(2)
                for c2 in children[n]:
                    if c2 != c:
                        sib *= Pe[c2] @ In[c2]
                o = (Out[n] * sib) @ Pe[c]
                so = o.sum(); Out[c] = o / so if so > 0 else o
        exp_gains = 0.0
        for c in range(1, nN):
            p = parent_of[c]
            joint = np.outer(Out[p], np.ones(2)) * Pe[c] * np.outer(np.ones(2), In[c])
            joint = joint / max(joint.sum(), 1e-300)
            exp_gains += joint[0, 1]              # P(parent=0, child=1) = a gain on this edge
        p1 = np.zeros(nN)
        for n in range(nN):
            m = Out[n] * In[n]; p1[n] = m[1] / max(m.sum(), 1e-300)
        # Deep/origin are restricted to the *dominant* family (the top-level clade holding the
        # most present tips) — a "max over all family roots" metric rewards breadth and lights up
        # for any widespread motif, so it mis-flags areal motifs as deep. root_deep = posterior at
        # the dominant family root; origin = oldest node inside that family reconstructed present.
        domr = Counter(topanc[n] for n in pres).most_common(1)[0][0]
        conc = sum(topanc[n] == domr for n in pres) / len(pres)
        root_deep = float(p1[domr])
        origin = None
        for n in range(1, nN):
            if topanc[n] == domr and p1[n] >= 0.5 and age[n] > (origin or -1):
                origin = age[n]
        return exp_gains, root_deep, origin, round(conc, 2), int(round(root_age[domr] * 1000))

    def fit(blen, grid):
        best = None
        for q01 in grid:
            for mult in (2, 4, 8):
                Pe = edge_mats(q01, q01 * mult, blen)
                prior = np.array([mult / (1 + mult), 1 / (1 + mult)])
                ll = sum(loglik(Pe, prior, ps) for ps in pres_sets)
                if best is None or ll > best[0]:
                    best = (ll, q01, q01 * mult, Pe, prior)
        return best

    def run(blen, grid):
        _, q01, q10, Pe, prior = fit(blen, grid)
        recs = {}
        for r in bz["motifs"]:
            P_ = [t for t in (r.get("traditions") or []) if t in leaf_of]
            if len(P_) < MIN_TRAD:
                continue
            pres = {leaf_of[t] for t in P_}
            eg, rd, origin, conc, ceil = infer(Pe, prior, pres)
            recs[r["id"]] = {"c": r["id"], "n": r.get("name", ""), "np": len(P_),
                             "pars": fitch(pres), "eg": round(eg, 1), "rd": round(rd, 2), "conc": conc,
                             "ceil": ceil, "age": None if origin is None else int(round(origin * 1000))}
        return q01, q10, recs

    q01_u, q10_u, rec_u = run(blen_unit, (0.05, 0.1, 0.2))
    q01_d, q10_d, rec_d = run(blen_dated, (0.01, 0.02, 0.05, 0.1, 0.2))

    def corr(recs):
        a = np.array([r["pars"] for r in recs.values()], float)
        b = np.array([r["eg"] for r in recs.values()], float)
        return round(float(np.corrcoef(a, b)[0, 1]), 3)

    n_deep_u = sum(r["rd"] >= 0.5 for r in rec_u.values())
    n_deep_d = sum(r["rd"] >= 0.5 for r in rec_d.values())
    # honest aggregate: a node origin age is a *meaningful* origin only for a motif concentrated
    # in its dominant family. Low-conc areal motifs get a "proto-family" age for their inherited
    # sliver only, not a real origin. So report over the concentrated (conc>=0.5) set.
    CONC = 0.5
    conc_aged = [r for r in rec_d.values() if r["conc"] >= CONC and r["age"]]
    younger = [r for r in conc_aged if r["age"] < r["ceil"]]
    median_conc_origin = int(np.median([r["age"] for r in conc_aged])) if conc_aged else None

    tracked = []
    for c, lab in TRACK.items():
        if c in rec_u and c in rec_d:
            u, d = rec_u[c], rec_d[c]
            tracked.append({"c": c, "label": lab, "n": u["n"], "np": u["np"], "pars": u["pars"],
                            "conc": d["conc"], "ceil": d["ceil"], "eg_u": u["eg"], "rd_u": u["rd"],
                            "eg_d": d["eg"], "rd_d": d["rd"], "age": d["age"]})

    data = {"n": len(rec_u), "min_trad": MIN_TRAD, "conc_thr": CONC,
            "undated": {"q01": round(q01_u, 3), "q10": round(q10_u, 3),
                        "loss_mult": round(q10_u / q01_u, 1), "corr": corr(rec_u), "n_deep": n_deep_u},
            "dated": {"q01": round(q01_d, 3), "q10": round(q10_d, 3),
                      "loss_mult": round(q10_d / q01_d, 1), "corr": corr(rec_d), "n_deep": n_deep_d,
                      "default_kyr": round(default_kyr, 1), "cov": round(dated_leaves / n_leaves, 2),
                      "median_conc_origin": median_conc_origin, "n_conc_aged": len(conc_aged),
                      "n_younger": len(younger)},
            "tracked": tracked}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"{len(rec_u)} motifs (>={MIN_TRAD} traditions)")
    print(f"  undated: gain={q01_u} loss={q10_u} ({q10_u/q01_u:.0f}x) corr(pars,eg)={corr(rec_u)} deep={n_deep_u}")
    print(f"  dated:   gain={q01_d}/kyr loss={q10_d}/kyr ({q10_d/q01_d:.0f}x) corr={corr(rec_d)} deep={n_deep_d} "
          f"[coverage {dated_leaves/n_leaves:.0%}, default {default_kyr:.1f} kyr]")
    print(f"  concentrated (conc>={CONC}) motifs with a node origin age: {len(conc_aged)} "
          f"(median {median_conc_origin} BP); {len(younger)} sit BELOW their family ceiling")
    for t in tracked:
        a = f"{t['age']} BP" if t["age"] else "—"
        print(f"  {t['c']:5} {t['label']:18} pars={t['pars']:3} conc={t['conc']:.2f} ceil={t['ceil']:5} "
              f"eg_u={t['eg_u']:5} eg_d={t['eg_d']:5} deep {t['rd_u']:.2f}->{t['rd_d']:.2f} origin={a}")


if __name__ == "__main__":
    main()
