"""Mockup 63 — where settlement AGE and network CONNECTIVITY diverge.

Two axes are usually conflated in the "old regions have deep mythology" story:
  · age         — when anatomically modern humans first settled the macro-area (ky BP);
  · connectivity — how embedded the area is in the Old-World diffusion network.
They correlate weakly, so most regions sit off the diagonal. The gap between them
is where the natural experiments live: old-but-isolated regions (Australia) test
whether depth needs age, connected-but-young regions (the Old-World hub) test the reverse.

Connectivity here is a reproducible, myth-free geographic proxy: BETWEEN-region
centrality. Each area's spherical centroid is computed from its traditions' coordinates,
then centrality = Σ over the OTHER area centroids of exp(-great_circle / SCALE).
This deliberately ignores within-area sampling density (a raw neighbour count would
just measure how finely a continent was catalogued, not how connected it is).

gap = z(centrality) − z(age):
  gap < 0  →  OLD but ISOLATED  (age exceeds connectivity)
  gap > 0  →  CONNECTED but YOUNG (connectivity exceeds age)
  gap ≈ 0  →  the two axes agree — not an informative region.
"""
import importlib.util
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MOCKS = ROOT / "mockups"
HERE = Path(__file__).resolve().parent

AGE = {"Sub-Saharan Africa": 65, "Aboriginal Australia": 50, "East & SE Asia": 50,
       "Iran, C. & S. Asia": 45, "Near East & N. Africa": 45, "Europe": 42,
       "Austronesia & Oceania": 33, "Siberia & Beringia": 32,
       "Northern & Western N. America": 15, "Eastern North America": 15,
       "Mesoamerica & Andes": 14, "South America": 14}

SCALE = 4000.0   # km — between-centroid distance decay
R = 6371.0


def load(rel, name):
    spec = importlib.util.spec_from_file_location(name, MOCKS / rel)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def main():
    f21 = load("21-facet-population/build_data.py", "f21")
    T = json.loads((ROOT / "outputs/motifs/berezkin.json").read_text())["traditions"]
    COORD = json.loads((MOCKS / "tradition-coords.json").read_text())["coordinates"]

    # per-tradition (area, lat, lon); per-area unit-vector list for a spherical centroid
    rows = []
    vecs = defaultdict(list)
    for t in T:
        a = f21.area_of(T[t].get("areal_path") or [])
        c = COORD.get(t)
        if a in AGE and c:
            la, lo = np.radians(c[0]), np.radians(c[1])
            rows.append((a, c[1], c[0]))   # (area, lon, lat)
            vecs[a].append([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)])

    areas = [a for a in AGE if a in vecs]
    cent_vec = {}
    for a in areas:
        v = np.mean(vecs[a], axis=0); cent_vec[a] = v / np.linalg.norm(v)

    def gc(u, w):
        return R * np.arccos(np.clip(np.dot(u, w), -1, 1))

    conn = {a: sum(np.exp(-gc(cent_vec[a], cent_vec[b]) / SCALE) for b in areas if b != a)
            for a in areas}
    age = np.array([AGE[a] for a in areas], float)
    con = np.array([conn[a] for a in areas], float)
    az = (age - age.mean()) / age.std()
    cz = (con - con.mean()) / con.std()
    gap = {a: float(cz[i] - az[i]) for i, a in enumerate(areas)}

    # centroid lon/lat for area labels (invert the unit vector)
    def vec_lonlat(v):
        lat = np.degrees(np.arcsin(v[2]))
        lon = np.degrees(np.arctan2(v[1], v[0]))
        return round(float(lon), 2), round(float(lat), 2)

    bound = max(abs(g) for g in gap.values())
    aidx = {a: i for i, a in enumerate(areas)}

    points = [{"x": round(lon, 2), "y": round(lat, 2), "a": aidx[a]} for a, lon, lat in rows]

    area_meta = []
    for a in areas:
        clon, clat = vec_lonlat(cent_vec[a])
        area_meta.append({
            "name": a, "age": AGE[a], "conn": round(conn[a], 3),
            "gap": round(gap[a], 3), "cx": clon, "cy": clat,
            "n": sum(1 for r in rows if r[0] == a),
        })
    area_meta.sort(key=lambda m: m["gap"])   # most old-isolated first

    data = {
        "scale_km": SCALE, "bound": round(bound, 3),
        "areas": area_meta, "aorder": areas,
        "points": points,
        # ColorBrewer RdBu diverging (CVD-safe): blue = old&isolated, red = connected&young,
        # near-white midpoint recedes into the ocean so only divergent regions stand out.
        "ramp": ["#2166ac", "#67a9cf", "#d1e5f0", "#f7f7f7",
                 "#fddbc7", "#ef8a62", "#b2182b"],
    }
    (HERE / "data.js").write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";\n")
    print(f"areas={len(areas)}  points={len(points)}  bound={bound:.2f}")
    for m in area_meta:
        print(f"  {m['name']:30} age={m['age']:3d}  conn={m['conn']:5.2f}  gap={m['gap']:+.2f}")


if __name__ == "__main__":
    main()
