"""Subsistence from external data (mockup 22) — the 4th tradition facet, and a test.

macro-area-facets.md leaves `tradition.subsistence` as the one facet with no in-corpus
source: it must come from D-PLACE's Ethnographic Atlas. This wires it in and tests the
correlation the proposal asserted but never checked: *foragers are etiology-heavy, farmers
adventure/tale-heavy* (Category A vs B).

Pipeline:
1. Each D-PLACE society already carries a subsistence bucket (derived from EA042 dominant
   activity, EA028 agriculture intensity) + coordinates — see dplace_subsistence.json.
2. Join each Berezkin tradition to its nearest D-PLACE society by great-circle distance.
3. Assign subsistence; report match quality (distance), coverage, and distribution.
4. Test subsistence × theme: mean Category-A (cosmology) share of each tradition's motifs,
   grouped by subsistence — with the area confound stated honestly.

Data: D-PLACE (Kirby et al. 2016), Ethnographic Atlas (Murdock), CC-BY-4.0.

Run:  python mockups/22-subsistence-external/build_data.py
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
MATCH_KM = 250.0     # a join farther than this is reported but flagged low-confidence
MIN_MOTIF = 20       # traditions with fewer motifs are too thin for a theme share
SUBS = {"forager": ("Foragers", "#5f7d99"), "pastoralist": ("Pastoralists", "#b28a3e"),
        "horticulturalist": ("Horticulturalists", "#3c8a5e"), "agrarian_state": ("Agrarian states", "#6a5aa6")}
SUB_ORDER = ["forager", "pastoralist", "horticulturalist", "agrarian_state"]

# area(), reused from mockup 21 so the cross-tab is on the same 12 macro-areas
_spec = importlib.util.spec_from_file_location("m21", MOCKS / "21-facet-population" / "build_data.py")
m21 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(m21)


def _geo():
    spec = importlib.util.spec_from_file_location("_geo", MOCKS / "_geo.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def haversine(lat1, lon1, lat2, lon2):
    r1, r2 = np.radians(lat1), np.radians(lat2)
    dlat, dlon = np.radians(lat2 - lat1), np.radians(lon2 - lon1)
    a = np.sin(dlat / 2) ** 2 + np.cos(r1) * np.cos(r2) * np.sin(dlon / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(a))


def _need(p, hint=""):
    """Fail with a clear message (not a raw traceback) when a required input is absent."""
    if not p.exists():
        raise SystemExit(f"\n✗ missing input: {p}" + (f"\n  → {hint}\n" if hint else "\n"))
    return p


def main():
    geo = _geo()
    coords = geo.berezkin_coords()   # {areal_id: [lat, lon]}
    with open(_need(ROOT / "outputs" / "motifs" / "berezkin.json",
                    "build the motif DB first: `mytho build motifs`"), encoding="utf-8") as f:
        bz = json.load(f)
    T = bz["traditions"]
    dp = json.loads(_need(HERE / "dplace_subsistence.json",
                          "committed D-PLACE snapshot missing from mockups/22-subsistence-external/"
                          ).read_text(encoding="utf-8"))
    dlat = np.array([d["lat"] for d in dp]); dlon = np.array([d["lon"] for d in dp])

    def coord(tid):
        """(lat, lon): the committed tradition-coords.json snapshot if present, else the
        areal-subregion centroid fallback for any tradition the snapshot misses."""
        c = coords.get(tid)
        if isinstance(c, (list, tuple)) and len(c) == 2:
            return float(c[0]), float(c[1])
        ap = T[tid].get("areal_path") or []
        if len(ap) >= 2:
            cen = geo.SUBREGION.get(ap[1][1].upper())   # _geo.SUBREGION is (lon, lat)
            if cen:
                return float(cen[1]), float(cen[0])
        return None

    # per-tradition Category-A share + motif count
    a_cnt, ab_cnt = Counter(), Counter()
    for r in bz["motifs"]:
        g = int(r.get("motif_group_num") or 0)
        if 1 <= g <= 13:
            for t in (r.get("traditions") or []):
                ab_cnt[t] += 1
                if g <= 9:
                    a_cnt[t] += 1

    matched, dists = [], []
    sub_c = Counter()
    area_sub = defaultdict(Counter)          # area -> subsistence counts
    sub_ashare = defaultdict(list)           # subsistence -> [cat-A shares]
    samples = []
    for tid, v in T.items():
        c = coord(tid)
        if c is None:
            continue
        lat, lon = c
        d = haversine(lat, lon, dlat, dlon)
        j = int(np.argmin(d)); dist = float(d[j])
        sub = dp[j]["s"]
        dists.append(dist)
        if dist > MATCH_KM:
            continue
        matched.append(tid); sub_c[sub] += 1
        area = m21.area_of(v.get("areal_path") or [])
        if area:
            area_sub[area][sub] += 1
        if ab_cnt[tid] >= MIN_MOTIF:
            sub_ashare[sub].append(a_cnt[tid] / ab_cnt[tid])
        if len(samples) < 14:
            samples.append({"n": v.get("name", tid), "sub": sub, "km": round(dist),
                            "match": dp[j]["n"], "area": area or "—",
                            "aA": round(100 * a_cnt[tid] / ab_cnt[tid]) if ab_cnt[tid] else None})

    n_coord = sum(1 for tid in T if coord(tid) is not None)
    theme_test = [{"sub": s, "label": SUBS[s][0], "n": len(sub_ashare[s]),
                   "aShare": round(100 * float(np.mean(sub_ashare[s])), 1) if sub_ashare[s] else None}
                  for s in SUB_ORDER]
    area_order = [a for a in m21.AREAS12 if area_sub.get(a)]

    data = {
        "n_trad": len(T), "n_coord": n_coord, "n_matched": len(matched),
        "n_dplace": len(dp), "match_km": MATCH_KM, "min_motif": MIN_MOTIF,
        "dist": {"med": round(float(np.median(dists))) if dists else 0,
                 "within": int(np.sum(np.array(dists) <= MATCH_KM)) if dists else 0,
                 "p90": round(float(np.percentile(dists, 90))) if dists else 0},
        "subs": SUBS, "order": SUB_ORDER, "counts": dict(sub_c),
        "area_sub": {a: dict(area_sub[a]) for a in area_order}, "area_order": area_order,
        "theme_test": theme_test,
        "dplace_dist": dict(Counter(d["s"] for d in dp)),
        "samples": samples,
    }
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"traditions with coords {n_coord} · matched <= {MATCH_KM:.0f}km: {len(matched)}"
          f" (median {data['dist']['med']}km)")
    print(f"  subsistence: {dict(sub_c)}")
    print("  theme test — mean Category-A share by subsistence:")
    for r in theme_test:
        print(f"    {r['label']:18} A-share {r['aShare']}%  (n={r['n']})")


if __name__ == "__main__":
    main()
