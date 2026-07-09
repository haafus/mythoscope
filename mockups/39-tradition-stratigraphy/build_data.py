"""Tradition stratigraphy (mockup 39, roadmap M39) — turn `stratum` around.

Instead of classifying each *motif* by depth (mockups 17–20), profile each *tradition* as its
**stack of strata** — the share of its motifs that are deep/broad vs areal vs local/endemic — a
geological-column view of a corpus. Then the strong **falsification test**: deep-substrate-rich
traditions should cluster in **early-peopled regions / refugia** (Africa, Australia), not the
late-peopled ones (the Americas). If deep-share is flat across peopling age — or an artifact of
sampling — the depth story fails.

Motif depth proxy = **breadth** (# attesting traditions, mockup 17): deep/broad ≥ 85th pct, areal
50–85th, local < 50th. A tradition's depth = the share of its motifs in the deep tier. Because a
thinly-catalogued corpus records mostly the salient broad motifs (inflating deep-share), the test
is reported **both raw and controlled for coverage a(t)** — the honest partial correlation.

Run:  python mockups/39-tradition-stratigraphy/build_data.py
"""
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MOCKS = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
OUT = HERE / "data.js"
MIN_TRAD_MOTIF = 8
# coarse first-peopling age per macro-area (ky BP) — the falsification axis
PEOPLING = {
    "Sub-Saharan Africa": 65, "Aboriginal Australia": 50, "East & SE Asia": 50,
    "Iran, C. & S. Asia": 45, "Near East & N. Africa": 45, "Europe": 42,
    "Austronesia & Oceania": 33, "Siberia & Beringia": 32,
    "Northern & Western N. America": 15, "Eastern North America": 15,
    "Mesoamerica & Andes": 14, "South America": 14,
}


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, MOCKS / rel)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def partial_corr(x, y, z):
    """corr(x, y) controlling for z (all 1-D arrays)."""
    rxy = np.corrcoef(x, y)[0, 1]; rxz = np.corrcoef(x, z)[0, 1]; ryz = np.corrcoef(y, z)[0, 1]
    d = np.sqrt((1 - rxz ** 2) * (1 - ryz ** 2))
    return float((rxy - rxz * ryz) / d) if d > 0 else 0.0


def main():
    m21 = _load("21-facet-population/build_data.py", "m21")
    with open(ROOT / "outputs" / "motifs" / "berezkin.json", encoding="utf-8") as f:
        bz = json.load(f)
    T, motifs = bz["traditions"], bz["motifs"]

    breadth = {r["id"]: len(r.get("traditions") or []) for r in motifs}
    trad_motifs = defaultdict(list)
    for r in motifs:
        for t in (r.get("traditions") or []):
            trad_motifs[t].append(r["id"])

    bvals = np.array([breadth[m] for m in breadth])
    p50, p85 = np.percentile(bvals, 50), np.percentile(bvals, 85)

    def tier(b):
        return "deep" if b >= p85 else "areal" if b >= p50 else "local"

    rows = []
    for t, ms in trad_motifs.items():
        area = m21.area_of(T[t].get("areal_path") or [])
        if len(ms) < MIN_TRAD_MOTIF or area not in PEOPLING:
            continue
        c = Counter(tier(breadth[m]) for m in ms)
        n = len(ms)
        rows.append({"t": t, "name": T[t].get("name", t), "area": area, "a": n,
                     "deep": c["deep"] / n, "areal": c["areal"] / n, "local": c["local"] / n,
                     "peo": PEOPLING[area]})
    N = len(rows)
    deep = np.array([r["deep"] for r in rows]); peo = np.array([float(r["peo"]) for r in rows])
    loga = np.log(np.array([r["a"] for r in rows]))

    r_raw = float(np.corrcoef(deep, peo)[0, 1])
    r_cov = float(np.corrcoef(deep, loga)[0, 1])           # the confound: deep-share vs coverage
    r_partial = partial_corr(deep, peo, loga)

    # by-area geological columns (mean stack) ordered by peopling age
    by_area = []
    for a in sorted(PEOPLING, key=lambda x: -PEOPLING[x]):
        grp = [r for r in rows if r["area"] == a]
        if grp:
            by_area.append({"area": a, "peo": PEOPLING[a], "n": len(grp),
                            "deep": round(float(np.mean([g["deep"] for g in grp])), 3),
                            "areal": round(float(np.mean([g["areal"] for g in grp])), 3),
                            "local": round(float(np.mean([g["local"] for g in grp])), 3),
                            "a": round(float(np.mean([g["a"] for g in grp])), 1)})
    # deepest & shallowest individual traditions
    deep_rich = sorted(rows, key=lambda r: -r["deep"])[:10]
    shallow = sorted(rows, key=lambda r: r["deep"])[:10]

    def slim(r):
        return {"name": r["name"], "area": r["area"], "deep": round(r["deep"], 2), "a": r["a"]}

    data = {
        "n": N, "n_motif": len(breadth), "p50": int(p50), "p85": int(p85), "min_trad_motif": MIN_TRAD_MOTIF,
        "corr": {"raw": round(r_raw, 3), "coverage": round(r_cov, 3), "partial": round(r_partial, 3)},
        "by_area": by_area, "deep_rich": [slim(r) for r in deep_rich], "shallow": [slim(r) for r in shallow],
        "pts": [{"x": None} for _ in range(0)],
    }
    # scatter: peopling age (jittered by area) vs deep-share, subsample
    data["scatter"] = [{"peo": r["peo"], "deep": round(r["deep"], 3), "area": r["area"]}
                       for r in rows[::2]]
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"{N} traditions · deep tier breadth ≥ {int(p85)}, local < {int(p50)}")
    print(f"  corr(deep-share, peopling age): raw {r_raw:+.3f}")
    print(f"  confound corr(deep-share, log coverage): {r_cov:+.3f}")
    print(f"  PARTIAL corr(deep-share, peopling | coverage): {r_partial:+.3f}  "
          f"-> falsification test {'PASSES' if r_partial > 0.1 else 'FAILS' if r_partial < -0.1 else 'NULL'}")
    print("  by area (peopling ky · deep% · coverage):")
    for a in by_area:
        print(f"    {a['area']:26} {a['peo']:3}ky  deep {a['deep']:.2f}  a(t) {a['a']:.0f}")


if __name__ == "__main__":
    main()
