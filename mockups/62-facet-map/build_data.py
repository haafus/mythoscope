"""62 · Facet map — one world map, switch the tradition facet.

Colours the same set of Berezkin traditions on the world map by a chosen facet:
`area` (12, from areal_path), `family` (11, from language), or the dominant
`theme` group (13, argmax of the theme profile). `subsistence` is listed but has
no data source yet (needs a D-PLACE join) — it shows as a disabled facet so the
gap is visible rather than hidden. Reuses mockup 21's area/family functions and
mockup 16's coordinate resolution + jitter.

Run:  python mockups/62-facet-map/build_data.py
"""
import importlib.util
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MOCKS = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "data.js"

MIN_MOTIFS = 30  # below this a theme profile is too noisy to call a dominant group

THEMES = ["Sun & Moon", "Stars & constellations", "Cosmogony & elements",
          "Origin of death", "Origin of humans", "Origin of subsistence",
          "Plants & animals", "Monstrous beings", "Protagonist identity",
          "Adventures", "Tricks & competitions", "Proper names", "Formulae"]

# Subsistence comes from D-PLACE (nearest society), reusing mockup 22's snapshot.
SUB_ORDER = ["forager", "pastoralist", "horticulturalist", "agrarian_state"]
SUB_LABEL = {"forager": "Foragers", "pastoralist": "Pastoralists",
             "horticulturalist": "Horticulturalists", "agrarian_state": "Agrarian states"}
MATCH_KM = 250.0  # a nearest-society join farther than this is dropped (too weak)

# One 16-colour qualitative ramp, sliced per facet (fixed order, never cycled).
RAMP = ["#2f6fed", "#12a150", "#d97706", "#9151d8", "#0e9aa7", "#c2410c",
        "#e11d48", "#7d8b3a", "#0891b2", "#a3457e", "#4338ca", "#65a30d",
        "#be123c", "#0f766e", "#7c3aed", "#b45309"]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _sunflower(j, n):
    r = math.sqrt((j + 0.5) / n)
    a = j * math.pi * (3 - math.sqrt(5))
    return r * math.cos(a), r * math.sin(a)


def _haversine(lat, lon, lats, lons):
    lat, lon = math.radians(lat), math.radians(lon)
    lats, lons = np.radians(lats), np.radians(lons)
    dlat, dlon = lats - lat, lons - lon
    h = np.sin(dlat / 2) ** 2 + math.cos(lat) * np.cos(lats) * np.sin(dlon / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(h))


def main():
    geo = _load("_geo", MOCKS / "_geo.py")
    f21 = _load("_f21", MOCKS / "21-facet-population" / "build_data.py")
    coords = geo.berezkin_coords()

    with open(ROOT / "outputs" / "motifs" / "berezkin.json", encoding="utf-8") as f:
        bz = json.load(f)
    T = bz["traditions"]

    # per-tradition 13-dim theme counts → dominant group
    prof = defaultdict(lambda: np.zeros(13))
    for r in bz["motifs"]:
        g = r.get("motif_group_num")
        if not g:
            continue
        gi = int(g) - 1
        if 0 <= gi < 13:
            for tid in (r.get("traditions") or []):
                prof[tid][gi] += 1

    def coord(t):
        c = coords.get(t)
        if isinstance(c, (list, tuple)) and len(c) == 2:
            return float(c[1]), float(c[0])   # [lat,lon] -> (lon,lat)
        ap = T[t].get("areal_path") or []
        if len(ap) >= 2:
            cen = geo.SUBREGION.get(ap[1][1].upper())
            if cen:
                return float(cen[0]), float(cen[1])
        return None

    # D-PLACE societies (id, name, lat, lon, subsistence bucket) — mockup 22's snapshot.
    with open(MOCKS / "22-subsistence-external" / "dplace_subsistence.json", encoding="utf-8") as f:
        dp = json.load(f)
    dp_lat = np.array([s["lat"] for s in dp])
    dp_lon = np.array([s["lon"] for s in dp])
    dp_sub = [s["s"] for s in dp]

    area_ix = {a: i for i, a in enumerate(f21.AREAS12)}
    fam_ix = {a: i for i, a in enumerate(f21.FAMILIES11)}
    sub_ix = {s: i for i, s in enumerate(SUB_ORDER)}

    recs = []  # (tid, lon, lat, area_idx, fam_idx, theme_idx, sub_idx)  (-1 = no value)
    for t, v in T.items():
        xy = coord(t)
        if not xy:
            continue
        lon, lat = xy
        ap = v.get("areal_path") or []
        area = f21.area_of(ap)
        lang0 = (v.get("language") or [None])[0]
        family, _ = f21.family_of(lang0, area)
        p = prof.get(t)
        theme = int(np.argmax(p)) if (p is not None and p.sum() >= MIN_MOTIFS) else -1
        d = _haversine(lat, lon, dp_lat, dp_lon)
        j = int(np.argmin(d))
        sub = sub_ix[dp_sub[j]] if d[j] <= MATCH_KM else -1
        recs.append((t, lon, lat, area_ix.get(area, -1), fam_ix.get(family, -1), theme, sub))

    # spread points sharing a base coordinate so nothing piles up (mockup 16 recipe)
    groups = defaultdict(list)
    for i, r in enumerate(recs):
        groups[(round(r[1], 2), round(r[2], 2))].append(i)
    xy_by_i = {}
    for (lon, lat), members in groups.items():
        members.sort(key=lambda i: recs[i][0])
        n = len(members)
        span = 1.1 * math.sqrt(n)
        for j, i in enumerate(members):
            ox, oy = _sunflower(j, n)
            xy_by_i[i] = (round(lon + ox * span * 1.35, 2), round(lat + oy * span, 2))

    points = [{"x": xy_by_i[i][0], "y": xy_by_i[i][1],
               "a": r[3], "f": r[4], "t": r[5], "s": r[6]}
              for i, r in enumerate(recs)]

    def facet(label, cats, key, colors=None):
        counts = Counter(p[key] for p in points if p[key] >= 0)
        return {
            "label": label,
            "cats": [{"name": c, "color": (colors or RAMP)[i % len(colors or RAMP)],
                      "n": counts.get(i, 0)}
                     for i, c in enumerate(cats)],
        }

    # forager · pastoralist · horticulturalist · agrarian_state — blue/amber/green/red
    # for maximum separation between the four buckets.
    sub_colors = ["#2f6fed", "#e08215", "#16a34a", "#dc2626"]
    facets = {
        "area": facet(f"Area · {len(f21.AREAS12)}", f21.AREAS12, "a"),
        "family": facet(f"Family · {len(f21.FAMILIES11)}", f21.FAMILIES11, "f"),
        "theme": facet(f"Dominant theme · {len(THEMES)}", THEMES, "t"),
        "subsistence": facet("Subsistence · 4",
                             [SUB_LABEL[s] for s in SUB_ORDER], "s", sub_colors),
    }
    facets["subsistence"]["note"] = f"nearest D-PLACE society ≤ {MATCH_KM:.0f} km (mockup 22)"

    data = {"facets": facets, "order": ["area", "family", "theme", "subsistence"],
            "points": points, "n": len(points), "min_motifs": MIN_MOTIFS}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";",
                   encoding="utf-8")
    n_theme = sum(1 for p in points if p["t"] >= 0)
    n_sub = sum(1 for p in points if p["s"] >= 0)
    print(f"{len(points)} traditions placed · {n_theme} with a dominant theme "
          f"(>={MIN_MOTIFS} motifs) · {n_sub} with subsistence (<= {MATCH_KM:.0f}km)")


if __name__ == "__main__":
    main()
