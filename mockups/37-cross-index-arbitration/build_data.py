"""Cross-index arbitration (mockup 37, roadmap M37) — a per-motif confidence weight.

Uses the BZ↔TMI↔ATU crosswalk as **replication**: a Berezkin motif corroborated by an
*independent* cataloguer (Thompson's TMI, Uther's ATU) is trustworthy; a Berezkin-only motif is
coding-dependent. Emits a confidence level per motif — the weight the joint model (M38) can use —
and checks the honest question: **is confidence skewed by theme** (are our cosmology findings
Berezkin-specific, while the tale findings are cross-corroborated)?

Levels:  triple (TMI **and** ATU) · strong (TMI tier-A, or ATU) · moderate (TMI tier-B) ·
         berezkin-only (neither).

Run:  python mockups/37-cross-index-arbitration/build_data.py
"""
import csv
import importlib.util
import json
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MOCKS = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
OUT = HERE / "data.js"
XW = ROOT / "docs" / "motifs" / "crosswalk"
GROUP = {1: "Sun & Moon", 2: "Stars", 3: "Cosmogony", 4: "Origin of death", 5: "Origin of humans",
         6: "Origin of subsistence", 7: "Plants & animals", 8: "Monstrous beings",
         9: "Protagonist identity", 10: "Adventures", 11: "Tricks & contests", 12: "Proper names",
         13: "Formulae"}
LEVELW = {"triple": 1.0, "strong": 0.85, "moderate": 0.7, "berezkin_only": 0.5}


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, MOCKS / rel)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def rows(fn):
    with open(XW / fn, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    with open(ROOT / "outputs" / "motifs" / "berezkin.json", encoding="utf-8") as f:
        bz = json.load(f)
    M = bz["motifs"]

    # best TMI tier per BZ motif; ATU parallels; triangles (all three indexes)
    tmi = {}
    for r in rows("parallels_BZ_TMI.csv"):
        t = r["tier"]
        if r["BZ_id"] not in tmi or t < tmi[r["BZ_id"]]:   # "A" < "B"
            tmi[r["BZ_id"]] = t
    atu_xw = {r["BZ_id"] for r in rows("parallels_BZ_ATU.csv")}
    triangle = {r["BZ_id"] for r in rows("parallels_triangles.csv")}

    def level(r):
        has_tmi = r["id"] in tmi
        has_atu = bool(r.get("atu_refs")) or r["id"] in atu_xw
        if r["id"] in triangle or (has_tmi and has_atu):
            return "triple"
        if tmi.get(r["id"]) == "A" or has_atu:
            return "strong"
        if has_tmi:                                        # tier B
            return "moderate"
        return "berezkin_only"

    recs = []
    for r in M:
        g = int(r.get("motif_group_num") or 0)
        recs.append({"id": r["id"], "g": g, "cat": "A" if 1 <= g <= 9 else "B" if g else "?",
                     "np": len(r.get("traditions") or []), "lvl": level(r)})

    levels = Counter(x["lvl"] for x in recs)
    corr = lambda x: x["lvl"] != "berezkin_only"            # noqa: E731
    overall_corr = sum(corr(x) for x in recs) / len(recs)

    # confidence by theme group + by A/B category
    by_theme = []
    for g in range(1, 14):
        grp = [x for x in recs if x["g"] == g]
        if grp:
            by_theme.append({"g": g, "name": GROUP[g], "cat": "A" if g <= 9 else "B",
                             "n": len(grp), "corr": round(sum(corr(x) for x in grp) / len(grp), 2)})
    by_cat = {}
    for c in ("A", "B"):
        grp = [x for x in recs if x["cat"] == c]
        by_cat[c] = {"n": len(grp), "corr": round(sum(corr(x) for x in grp) / len(grp), 2)}

    # confidence by breadth (are the broad motifs — our findings — corroborated, or BZ-only?)
    def bin_(n):
        return "narrow (≤3)" if n <= 3 else "medium (4–15)" if n <= 15 else "broad (>15)"
    by_breadth = []
    for b in ["narrow (≤3)", "medium (4–15)", "broad (>15)"]:
        grp = [x for x in recs if bin_(x["np"]) == b]
        by_breadth.append({"bin": b, "n": len(grp),
                           "corr": round(sum(corr(x) for x in grp) / len(grp), 2) if grp else 0})

    id2 = {r["id"]: r for r in M}
    triples = [{"id": i, "n": id2[i].get("name", "")} for i in sorted(triangle) if i in id2][:12]
    # broad Berezkin-only motifs = findings that lean on Berezkin's coding alone
    broad_only = sorted((x for x in recs if x["lvl"] == "berezkin_only" and x["np"] > 15),
                        key=lambda x: -x["np"])[:12]
    broad_only = [{"id": x["id"], "n": id2[x["id"]].get("name", ""), "np": x["np"],
                   "grp": GROUP.get(x["g"], "?")} for x in broad_only]

    data = {
        "n": len(recs), "n_tmi": len(tmi), "n_atu": len(atu_xw | {r["id"] for r in M if r.get("atu_refs")}),
        "n_triangle": len(triangle), "overall_corr": round(overall_corr, 3),
        "levels": {k: levels[k] for k in ["triple", "strong", "moderate", "berezkin_only"]},
        "levelw": LEVELW, "by_theme": by_theme, "by_cat": by_cat, "by_breadth": by_breadth,
        "triples": triples, "broad_only": broad_only,
        "mean_w": round(float(np.mean([LEVELW[x["lvl"]] for x in recs])), 3),
    }
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"{len(recs)} motifs · TMI-corroborated {len(tmi)} · ATU {data['n_atu']} · triangles {len(triangle)}")
    print(f"  levels: {dict(levels)}  (overall corroborated {overall_corr:.0%}, mean weight {data['mean_w']})")
    print(f"  by category: A(cosmology) {by_cat['A']['corr']:.0%} vs B(tales) {by_cat['B']['corr']:.0%} corroborated")
    print("  by theme (corroboration rate):")
    for t in sorted(by_theme, key=lambda x: x["corr"]):
        print(f"    {t['name']:22} [{t['cat']}] n={t['n']:4} {t['corr']:.0%}")
    print(f"  by breadth: {[(b['bin'], b['corr']) for b in by_breadth]}")


if __name__ == "__main__":
    main()
