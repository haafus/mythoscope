"""Precompute the region-area polygons for mockup 62's `borders` facet.

Regions are draped over REAL vector borders (Natural Earth 50m admin-0 countries,
plus admin-1 provinces for the eight big countries that straddle regions), so the
areas tile cleanly with no tearing. Each country/province is assigned to a canon
region by proximity to that region's traditions (REGIONS in build_data.py), with a
few overrides, then simplified. Output: regions_geo.json = {region name: SVG path d}.

The Natural Earth files (~5 MB) are downloaded to a cache and NOT committed; the
small JSON output is. Re-run when the region traditions or the assignment change:

    python mockups/62-facet-map/build_region_geo.py
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_data import REGIONS  # noqa: E402

CACHE = Path("/tmp/ne_cache")
NE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
FILES = {"admin0": "ne_50m_admin_0_countries.geojson",
         "admin1": "ne_50m_admin_1_states_provinces.geojson"}

# countries with admin-1 provinces here — split these, they straddle regions
SPLIT = {"Russia", "China", "United States of America", "Canada",
         "Indonesia", "India", "Brazil", "Australia"}
# canon overrides where a unit's centroid snaps to the wrong region (e.g. the Arab
# SE-Arabian shore is closer to an Iranian anchor across the narrow Gulf than to ours)
OVERRIDE = {"Libya": "Near East & North Africa", "Turkey": "Caucasus & Iran",
            "Oman": "Near East & North Africa", "United Arab Emirates": "Near East & North Africa",
            "Ecuador": "Mesoamerica & the Andes"}  # Andean highland heartland, not its Amazon Oriente


def fetch(name):
    CACHE.mkdir(exist_ok=True)
    dest = CACHE / FILES[name]
    if not dest.exists():
        subprocess.run(["curl", "-sSL", "-o", str(dest), NE + FILES[name]], check=True)
    return json.loads(dest.read_text())


def parts_of(geom):  # split into individual polygons (each = [exterior, *holes])
    return geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]


def centroid(poly):  # exterior ring of one polygon; circular-mean lon + mean lat
    ext = poly[0]
    lons = np.radians([c[0] for c in ext])
    lon = math.degrees(math.atan2(np.sin(lons).mean(), np.cos(lons).mean()))
    return lon, float(np.mean([c[1] for c in ext]))


def _dp_open(poly, eps):
    keep = np.zeros(len(poly), bool)
    keep[0] = keep[-1] = True
    stack = [(0, len(poly) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        a, ab = poly[i], poly[j] - poly[i]
        length = math.hypot(*ab) or 1.0
        seg = poly[i + 1:j] - a
        d = np.abs(ab[0] * seg[:, 1] - ab[1] * seg[:, 0]) / length
        k = int(d.argmax())
        if d[k] > eps:
            keep[i + 1 + k] = True
            stack += [(i, i + 1 + k), (i + 1 + k, j)]
    return poly[keep]


def dp(ring, eps=0.2):  # closed ring — split at the point farthest from ring[0]
    ring = np.asarray(ring, float)
    if len(ring) > 1 and np.allclose(ring[0], ring[-1]):
        ring = ring[:-1]
    if len(ring) < 4:
        return ring
    m = int(np.hypot(*(ring - ring[0]).T).argmax())
    a = _dp_open(ring[:m + 1], eps)
    b = _dp_open(np.vstack([ring[m:], ring[0]]), eps)
    return np.vstack([a[:-1], b[:-1]])


def path_d(poly):  # SVG path for one polygon (exterior + holes); x = lon+180, y = 90-lat
    d = []
    for ring in poly:
        r = dp(ring)
        if len(r) < 4:
            continue
        d.append("M" + "L".join(f"{c[0] + 180:.1f} {90 - c[1]:.1f}" for c in r) + "Z")
    return "".join(d)


def main():
    names = [r[0] for r in REGIONS]
    rname_i = {n: i for i, n in enumerate(names)}
    pts, reg = [], []
    for ri, (_, _, trads) in enumerate(REGIONS):
        for _, lat, lon in trads:
            pts.append((lon, lat)); reg.append(ri)
    pts = np.array(pts, float)
    tree = cKDTree(np.vstack([pts, pts + [360, 0], pts - [360, 0]]))  # dateline wrap
    rr = np.concatenate([reg, reg, reg]).astype(int)

    paths = {n: [] for n in names}
    a0, a1 = fetch("admin0"), fetch("admin1")
    for src, feats in (("a0", a0["features"]), ("a1", a1["features"])):
        for f in feats:
            pr = f["properties"]
            admin = pr.get("admin") or pr.get("ADMIN") or pr.get("name")
            if src == "a0" and (admin in SPLIT or admin == "Antarctica"):
                continue
            if src == "a1" and admin not in SPLIT:
                continue
            for poly in parts_of(f["geometry"]):  # assign each part (e.g. overseas islands) on its own
                lon, lat = centroid(poly)
                if lat < -60:  # Antarctica — nobody lives there, leave it blank
                    continue
                if admin in OVERRIDE:
                    ri = rname_i[OVERRIDE[admin]]
                else:
                    ri = int(rr[tree.query([lon, lat], k=1)[1]])
                if names[ri] == "Inner Asia" and lat >= 62:  # keep the Circumpolar ring intact
                    ri = rname_i["Circumpolar North"]
                paths[names[ri]].append(path_d(poly))

    out = {n: "".join(paths[n]) for n in names}
    dest = HERE / "regions_geo.json"
    dest.write_text(json.dumps(out, ensure_ascii=False))
    print(f"{sum(len(v) for v in paths.values())} units → regions_geo.json "
          f"({dest.stat().st_size / 1024:.0f}KB)")


if __name__ == "__main__":
    main()
