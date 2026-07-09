"""Stratum controls (mockup 20) — what the two mandatory §5 controls do to the estimate.

Re-runs the mockup-19 gated A × B estimator, then applies the two corrections the earlier
mockups skipped, and measures how much the modes move:

1. Attestation-intensity (sampling) control. Tradition coverage a(t) ranges 1..738
   (median 74): a densely-catalogued tradition records almost any motif, so a presence
   there is cheap evidence, while a presence in a thinly-covered tradition is costly and
   informative. We weight each present tradition by baseline-equivalent coverage
   w(t) = median / a(t) (capped), and count a macro-area as *real* breadth only where the
   motif carries at least one baseline-equivalent of evidence. Then re-gate on that
   effective breadth. (A degree-preserving configuration null was tried first and rejected
   — conditioning on the motif's own frequency is circular and nukes genuinely broad
   motifs like sun & moon; see README.)
2. Banality / homoplasy control. A proxy from generic (short) definitions + singleton
   scatter flags motifs whose "depth" is more likely independent reinvention than descent.

The payoff: raw breadth (n_macro) is largely explained by effort, so the areal-broad
class thins out under correction, while the deep-disjunct (both-hemisphere) class is
*not* predicted by the null and survives — an empirical restatement of axiom 4
(disjunction outranks mere breadth).

Run:  python mockups/20-stratum-controls/build_data.py
"""
import importlib.util
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MOCKS = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "data.js"
MIN_TRAD = 4
N_SHUFFLE = 8
NW = {"NORTH AMERICA: NORTH AND WEST", "PLAINS AND SOUTHEAST", "MEXICO – CENTRAL ANDES",
      "EASTERN SOUTH AMERICA", "SOUTHERN SOUTH AMERICA", "BERINGIA"}
IP = {"OCEANIA", "AUSTRALIA"}
SIG_DESCENT = 0.5
BROAD = 6            # raw macro-area gate (mockup 19)
BROAD_EFF = 6        # effective macro-area gate after the coverage-weighting correction
W_CAP = 2.0          # cap on a single tradition's baseline-equivalent evidence weight
TRACK = {"B4": "fished-out earth", "K25": "swan-maiden", "A3": "sun & moon",
         "K8aa": "Jonah (world-religion)", "M182": "tar-baby", "K57": "Cinderella"}
MODES = {
    "areal_deep": ("Deep areal substrate", "#7c3aed"),
    "descent": ("Descent (clade)", "#12a150"),
    "areal_broad": ("Broad areal", "#c2410c"),
    "areal_recent": ("Areal / borrowed", "#d97706"),
    "local": ("Local / insufficient", "#98a0a7"),
}


def _geo():
    spec = importlib.util.spec_from_file_location("_geo", MOCKS / "_geo.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def gate(nm, nme, signal, deep_set):
    """The mockup-19 gate, but the areal breadth trigger reads an effective count `nme`
    (raw `nm` when uncorrected). Returns (mode, depth)."""
    if nm < 4:
        return "local", 10 + nm * 3
    if signal >= SIG_DESCENT:
        return "descent", 62
    if deep_set and nme >= BROAD_EFF:
        return "areal_deep", 88
    if nme >= BROAD_EFF:
        return "areal_broad", 52
    return "areal_recent", 28 + nm


def main():
    with open(ROOT / "outputs" / "motifs" / "berezkin.json", encoding="utf-8") as f:
        bz = json.load(f)
    T = bz["traditions"]

    # attestation intensity c_t = #motifs recorded for tradition t
    c = Counter()
    for r in bz["motifs"]:
        for t in (r.get("traditions") or []):
            if t in T:
                c[t] += 1
    med_cov = float(np.median(list(c.values())))
    w_cov = {t: min(W_CAP, med_cov / c[t]) for t in c}   # baseline-equivalent evidence weight
    macro_of = {t: (T[t]["areal_path"][0][1] if T[t].get("areal_path") else None) for t in T}
    macro_trads = defaultdict(list)
    for t, mc in macro_of.items():
        if mc:
            macro_trads[mc].append(t)

    # language classification tree (as in mockup 18/19)
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
    is_leaf = [len(ch) == 0 for ch in children]
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
                for k in children[n]:
                    inter &= st[k]; uni |= st[k]
                if inter:
                    st[n] = inter
                else:
                    st[n] = uni; ch += 1
        return ch

    # def-length percentile for the banality proxy
    deflen = {r["id"]: len(r.get("definition") or "") for r in bz["motifs"]}
    dl_sorted = sorted(deflen.values())

    def pct_short(v):
        import bisect
        return 1 - bisect.bisect_left(dl_sorted, v) / len(dl_sorted)   # short def -> high

    rng = random.Random(0)
    recs = []
    for r in bz["motifs"]:
        tids = [t for t in (r.get("traditions") or []) if t in leaf_of]
        if len(tids) < MIN_TRAD:
            continue
        pres = {leaf_of[t] for t in tids}
        obs = fitch(pres)
        rand = np.mean([fitch(set(rng.sample(leaves, len(pres)))) for _ in range(N_SHUFFLE)])
        signal = 0.0 if rand <= 1 else max(0.0, min(1.0, (rand - obs) / (rand - 1)))

        present = set(tids)
        macros = {macro_of[t] for t in tids if macro_of[t]}
        n_macro = len(macros)
        sets = ({"NW"} if macros & NW else set()) | ({"IP"} if macros & IP else set())

        # --- sampling correction: a macro-area is "real" breadth only where the motif
        # carries >= 1 baseline-equivalent of evidence (coverage-weighted presence mass).
        macro_mass = defaultdict(float)
        singleton = 0
        for t in tids:
            macro_mass[macro_of[t]] += w_cov.get(t, 1.0)
        for mc in macros:
            if sum(1 for t in macro_trads[mc] if t in present) == 1:   # lone attester
                singleton += 1
        real_macros = {mc for mc in macros if macro_mass[mc] >= 1.0}
        n_macro_eff = len(real_macros)
        deep_set = bool(macros & NW) and bool(macros & IP)
        deep_set_eff = bool(real_macros & NW) and bool(real_macros & IP)

        mode_raw, _ = gate(n_macro, n_macro, signal, deep_set)
        mode_cor, _ = gate(n_macro, n_macro_eff, signal, deep_set_eff)

        # banality: generic (short) definition + scattered singletons
        singleton_frac = singleton / n_macro if n_macro else 0.0
        banality = round(0.5 * pct_short(deflen[r["id"]]) + 0.5 * singleton_frac, 2)

        recs.append({"c": r["id"], "n": r.get("name", ""), "g": int(r.get("motif_group_num") or 0),
                     "nm": n_macro, "nme": n_macro_eff, "sig": round(signal, 2),
                     "deep": deep_set, "raw": mode_raw, "cor": mode_cor,
                     "ban": banality, "sets": sorted(sets)})

    idx = {r["c"]: r for r in recs}
    counts_raw = Counter(r["raw"] for r in recs)
    counts_cor = Counter(r["cor"] for r in recs)
    changed = [r for r in recs if r["raw"] != r["cor"]]
    # net flow raw->cor
    flow = Counter((r["raw"], r["cor"]) for r in changed)
    flow_top = [{"from": a, "to": b, "n": n} for (a, b), n in flow.most_common(8)]

    # sampling-bias metric: corr of raw n_macro with mean coverage of its traditions
    # (high corr => breadth tracks catalogue density). Reported before/after via n_macro vs eff.
    nm = np.array([r["nm"] for r in recs], float)
    nme = np.array([r["nme"] for r in recs], float)
    shrink = round(float(1 - nme.sum() / nm.sum()), 3)

    # deep-set survival: of raw areal_deep, how many stay after correction
    deep_raw = [r for r in recs if r["raw"] == "areal_deep"]
    deep_keep = sum(1 for r in deep_raw if r["cor"] == "areal_deep")
    broad_raw = [r for r in recs if r["raw"] == "areal_broad"]
    broad_keep = sum(1 for r in broad_raw if r["cor"] == "areal_broad")

    # banality: motifs scored deep/broad but flagged banal (possible homoplasy, not age)
    banal_flag = sorted((r for r in recs if r["cor"] in ("areal_deep", "areal_broad") and r["ban"] >= 0.6),
                        key=lambda r: -r["ban"])[:12]

    tracked = [{**idx[c], "label": lab} for c, lab in TRACK.items() if c in idx]

    data = {"n": len(recs), "min_trad": MIN_TRAD, "modes": MODES,
            "counts_raw": dict(counts_raw), "counts_cor": dict(counts_cor),
            "n_changed": len(changed), "flow": flow_top, "shrink": shrink,
            "deep": {"raw": len(deep_raw), "keep": deep_keep},
            "broad": {"raw": len(broad_raw), "keep": broad_keep},
            "cov": {"min": min(c.values()), "med": int(np.median(list(c.values()))),
                    "p90": int(np.percentile(list(c.values()), 90)), "max": max(c.values())},
            "banal": [{"c": r["c"], "n": r["n"], "cor": r["cor"], "ban": r["ban"],
                       "nm": r["nm"], "nme": r["nme"]} for r in banal_flag],
            "tracked": tracked}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"{len(recs)} motifs · raw {dict(counts_raw)}")
    print(f"           · corrected {dict(counts_cor)}")
    print(f"  changed mode: {len(changed)}  · breadth shrink {shrink:.0%}")
    print(f"  areal_deep survives correction: {deep_keep}/{len(deep_raw)} · areal_broad: {broad_keep}/{len(broad_raw)}")
    for t in tracked:
        print(f"  {t['c']:5} {t['label']:22} raw={t['raw']:12} -> cor={t['cor']:12} nm={t['nm']} nme={t['nme']} ban={t['ban']}")


if __name__ == "__main__":
    main()
