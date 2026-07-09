"""Historical connectivity layer (mockup 35, roadmap M35) — dated polity co-membership.

The **human, dated** contact channel: two traditions are linked if they were **co-members of the
same historical polity** at some date. Tests a *distinct* mechanism from M34 (dated human contact
as a covariate, not a distance metric). M34's resistance-distance gate failed, so this is run at
lowered priority — and honestly: it leads with the roadmap's cheap **overlap audit** (what share
of ethnographic traditions are even inside any historical empire), because Berezkin's units are
often small-scale societies *outside* the great polities.

Data: `aourednik/historical-basemaps` (dated world political boundaries, GeoJSON, CC-BY-SA) —
a few dated snapshots, cached git-ignored. Point-in-polygon is ray-casting (no shapely).
(Trade routes — OWTRAD — would add short-path edges; not yet wired.)

Test: does **same-polity-ever** explain pairwise motif-Jaccard *beyond great-circle distance*
(and beyond same-area)? Reported as ΔR² and a within-area restricted comparison.

Run:  python mockups/35-historical-corridors/build_data.py
"""
import importlib.util
import json
import time
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MOCKS = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
OUT = HERE / "data.js"
MIN_MOTIF = 8
SNAPS = ["world_bc1", "world_1000", "world_1279", "world_1500"]  # classical→early-modern empires
# (Rome/Han, Byzantine/Caliphate/Song, Mongol, Ottoman/Ming). Colonial snapshots (1715/1880) are
# excluded — they blanket the globe administratively (British Empire links India↔Australia), not a
# folk-motif corridor; and pre-classical bc1000 has no empires, only culture-region labels.
BASE = "https://raw.githubusercontent.com/aourednik/historical-basemaps/master/geojson/"


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, MOCKS / rel)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def polygons(fn):
    """Return [(name, bbox, [rings])]; ring = Nx2 array of (lon,lat) exterior boundaries."""
    p = HERE / (fn + ".geojson")
    if not p.exists():
        req = urllib.request.Request(BASE + fn + ".geojson", headers={"User-Agent": "mythoscope"})
        for attempt in range(4):
            try:
                p.write_bytes(urllib.request.urlopen(req, timeout=40).read()); break
            except Exception:
                if attempt == 3:
                    raise
                time.sleep(2 * (attempt + 1))
    gj = json.loads(p.read_text(encoding="utf-8"))
    out = []
    for ft in gj["features"]:
        nm = (ft["properties"].get("NAME") or ft["properties"].get("name") or "").strip()
        g = ft.get("geometry") or {}
        if not nm or not g:
            continue
        rings = []
        if g["type"] == "Polygon":
            rings = [g["coordinates"][0]]
        elif g["type"] == "MultiPolygon":
            rings = [poly[0] for poly in g["coordinates"]]
        for r in rings:
            a = np.array(r, dtype=float)
            if a.ndim == 2 and len(a) >= 4:
                out.append((nm, (a[:, 0].min(), a[:, 0].max(), a[:, 1].min(), a[:, 1].max()), a))
    return out


def in_ring(lon, lat, ring):
    x, y = ring[:, 0], ring[:, 1]
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        if ((y[i] > lat) != (y[j] > lat)) and \
           (lon < (x[j] - x[i]) * (lat - y[i]) / ((y[j] - y[i]) or 1e-12) + x[i]):
            inside = not inside
        j = i
    return inside


def main():
    geo = _load("_geo.py", "geo")
    m21 = _load("21-facet-population/build_data.py", "m21")
    coords = geo.berezkin_coords()
    with open(ROOT / "outputs" / "motifs" / "berezkin.json", encoding="utf-8") as f:
        bz = json.load(f)
    T = bz["traditions"]

    def coord(tid):
        c = coords.get(tid)
        if isinstance(c, (list, tuple)) and len(c) == 2:
            return float(c[0]), float(c[1])
        return None

    # membership: tid -> set of "snap|polity"
    membership = defaultdict(set)
    tids_coord = [t for t in T if coord(t)]
    for fn in SNAPS:
        polys = polygons(fn)
        for t in tids_coord:
            lat, lon = coord(t)
            for nm, (x0, x1, y0, y1), ring in polys:
                if x0 <= lon <= x1 and y0 <= lat <= y1 and in_ring(lon, lat, ring):
                    membership[t].add(f"{fn}|{nm}"); break
    print(f"snapshots {len(SNAPS)} · traditions with coords {len(tids_coord)}")
    area_of = {t: (m21.area_of(T[t].get("areal_path") or []) or "—") for t in tids_coord}

    # historical-basemaps TESSELLATES the world (every point is in some named region, incl.
    # culture-region catch-alls like "Manioc farmers" / "Aboriginal Australians"), so raw "in a
    # polity" ≈ always. A real diffusion corridor is a polity spanning **≥3 macro-areas** (Rome,
    # Mongol, Caliphate…) — big enough to link otherwise-separate regions, which single-area
    # tessellation cells and 1–2-area culture regions do not.
    poly_members = defaultdict(set)
    for t in tids_coord:
        for m in membership[t]:
            poly_members[m].add(t)
    empires = {m for m, ts in poly_members.items()
               if len(ts) >= 4 and len({area_of[t] for t in ts}) >= 3}
    emp_mem = {t: (membership[t] & empires) for t in tids_coord}

    # overlap audit: share of traditions inside a real (multi-area) empire, by macro-area
    area_tot, area_in = Counter(), Counter()
    for t in tids_coord:
        area_tot[area_of[t]] += 1
        if emp_mem[t]:
            area_in[area_of[t]] += 1
    overall = sum(1 for t in tids_coord if emp_mem[t]) / len(tids_coord)
    audit = sorted(({"area": a, "n": area_tot[a], "cov": round(area_in[a] / area_tot[a], 2)}
                    for a in area_tot), key=lambda r: -r["cov"])
    top_emp = sorted(((m.split("|", 1)[1], len(ts), len({area_of[t] for t in ts}), m.split("|")[0])
                      for m, ts in poly_members.items() if m in empires),
                     key=lambda x: -x[1])[:12]

    # ---- working set for the covariate test ----
    trad_motifs = defaultdict(set)
    for k, r in enumerate(bz["motifs"]):
        for t in (r.get("traditions") or []):
            trad_motifs[t].add(k)
    rows = [t for t in tids_coord if len(trad_motifs[t]) >= MIN_MOTIF]
    N = len(rows)
    area_arr = np.array([area_of[t] for t in rows])
    lat = np.array([coord(t)[0] for t in rows]); lon = np.array([coord(t)[1] for t in rows])
    cols = sorted(empires)
    ci = {c: k for k, c in enumerate(cols)}
    Mb = np.zeros((N, len(cols)), dtype=np.float32)
    for i, t in enumerate(rows):
        for m in emp_mem[t]:
            Mb[i, ci[m]] = 1.0
    P = np.zeros((N, len(bz["motifs"])), dtype=np.float32)
    for i, t in enumerate(rows):
        for m in trad_motifs[t]:
            P[i, m] = 1.0

    iu = np.triu_indices(N, 1)
    inter = P @ P.T; size = P.sum(1); union = size[:, None] + size[None, :] - inter
    jac = (inter / np.where(union > 0, union, 1))[iu]
    la1 = np.radians(lat)[:, None]; la2 = np.radians(lat)[None, :]
    dla = la2 - la1; dlo = np.radians(lon)[None, :] - np.radians(lon)[:, None]
    gcm = 6371.0 * 2 * np.arcsin(np.sqrt(np.sin(dla / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin(dlo / 2) ** 2))
    GC = gcm[iu]
    coemp = ((Mb @ Mb.T) > 0)[iu].astype(float)          # co-member of some multi-area empire
    samearea = (area_arr[:, None] == area_arr[None, :])[iu].astype(float)

    def r2(cols_):
        X = np.column_stack([np.ones(len(jac))] + cols_)
        b, *_ = np.linalg.lstsq(X, jac, rcond=None)
        return 1 - ((jac - X @ b) ** 2).sum() / ((jac - jac.mean()) ** 2).sum()

    def z(v):
        return (v - v.mean()) / v.std()
    r_gc = r2([z(GC)]); r_gc_area = r2([z(GC), samearea]); r_full = r2([z(GC), samearea, coemp])
    # the sharp test — CROSS-AREA pairs only: does sharing an empire lift Jaccard between
    # traditions in *different* macro-areas (a genuine corridor, not same-region tessellation)?
    xa = samearea == 0
    ce = coemp == 1
    mean_x_co = float(jac[xa & ce].mean()) if (xa & ce).any() else 0.0
    mean_x_nc = float(jac[xa & ~ce].mean()) if (xa & ~ce).any() else 0.0
    # matched on distance: restrict cross-area pairs to a comparable distance band
    band = xa & (np.quantile(GC[xa & ce], 0.9) > GC if (xa & ce).any() else GC.max())
    mean_b_co = float(jac[band & ce].mean()) if (band & ce).any() else 0.0
    mean_b_nc = float(jac[band & ~ce].mean()) if (band & ~ce).any() else 0.0

    data = {
        "n": N, "n_coord": len(tids_coord), "snaps": SNAPS, "min_motif": MIN_MOTIF,
        "n_empires": len(empires), "overall_cov": round(overall, 3), "audit": audit,
        "top_emp": [{"name": nm, "n": n, "areas": ar, "snap": sn.replace("world_", "")}
                    for nm, n, ar, sn in top_emp],
        "delta": {"gc": round(r_gc, 4), "gc_area": round(r_gc_area, 4), "full": round(r_full, 4),
                  "d_emp_over_gc_area": round(r_full - r_gc_area, 4)},
        "crossarea": {"co": round(mean_x_co, 4), "nc": round(mean_x_nc, 4),
                      "lift": round(mean_x_co - mean_x_nc, 4), "n_co": int((xa & ce).sum()),
                      "band_co": round(mean_b_co, 4), "band_nc": round(mean_b_nc, 4),
                      "band_lift": round(mean_b_co - mean_b_nc, 4)},
        "pts": [{"x": round(float(lon[i]), 1), "y": round(float(lat[i]), 1),
                 "in": bool(emp_mem[rows[i]])} for i in range(N)],
    }
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"real multi-area empires: {len(empires)} · traditions in one ever: {overall:.0%}")
    for a in audit[:8]:
        print(f"   {a['area']:26} n={a['n']:3} in-empire {a['cov']:.0%}")
    print(f"top empires: {[(e['name'], e['n'], e['areas']) for e in data['top_emp'][:6]]}")
    print(f"R²(Jaccard): gc {r_gc:.4f} · gc+area {r_gc_area:.4f} · +empire {r_full:.4f} "
          f"(Δ over gc+area {r_full-r_gc_area:+.4f})")
    print(f"CROSS-AREA pairs — mean Jaccard: co-empire {mean_x_co:.4f} vs {mean_x_nc:.4f} "
          f"(lift {mean_x_co-mean_x_nc:+.4f}, n_co={int((xa&ce).sum())})")
    print(f"   distance-matched: {mean_b_co:.4f} vs {mean_b_nc:.4f} (lift {mean_b_co-mean_b_nc:+.4f})")


if __name__ == "__main__":
    main()
