"""Landscape permeability / cost-distance geography (mockup 34, roadmap M34).

Replaces Method A's *isotropic* great-circle distance with **resistance (least-cost) distance**
over a friction surface — the physical, always-on connectivity substrate. Low-friction corridors
(coastlines, seaways, open land) carry motifs far; barriers (open ocean for land peoples, high
mountains, ice) block them. "Isolation by resistance," not "by distance."

Friction surface (coarse, procedural — a first cut):
  * land / ocean from the committed coastline (`land.js`, data-driven — the dominant structure);
  * a latitude penalty (ice / tundra above ~60°);
  * two clear mountain barriers (Himalaya–Tibet, Andes);
  * two variants — **terrestrial** (ocean ≈ barrier) and **maritime-enabled** (sea = cheap
    highway) — since the sea is a wall for land peoples but a road for maritime ones.
A full GIS friction raster (SRTM/GEBCO terrain, WWF ecoregions for deserts/rainforest,
HydroRIVERS) is the upgrade; here the land/sea/coast + ice + two ranges already capture the
corridors the test needs.

Headline test (falsifiable): does resistance-distance explain tradition–tradition motif-set
**Jaccard** *better than great-circle*, out of sample? If not, drop it.

Run:  python mockups/34-landscape-permeability/build_data.py
"""
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

ROOT = Path(__file__).resolve().parents[2]
MOCKS = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
OUT = HERE / "data.js"
RES = 1                 # cells per degree
W, H = 360 * RES, 180 * RES
MIN_MOTIF = 8


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, MOCKS / rel)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def land_mask():
    txt = (MOCKS / "31-phylogeography" / "land.js").read_text(encoding="utf-8")
    raw = txt[txt.index('"') + 1:txt.rindex('"')]
    img = Image.new("1", (W, H), 0); dr = ImageDraw.Draw(img)
    for seg in raw.split("Z"):
        seg = seg.strip().lstrip("M")
        if not seg:
            continue
        pts = []
        for tok in seg.split("L"):
            tok = tok.strip()
            if tok:
                x, y = tok.split(); pts.append((float(x) * RES, float(y) * RES))
        if len(pts) >= 3:
            dr.polygon(pts, fill=1)
    return np.array(img, dtype=bool)     # [row=y(lat), col=x(lon)]


def main():
    geo = _load("_geo.py", "geo")
    coords = geo.berezkin_coords()
    with open(ROOT / "outputs" / "motifs" / "berezkin.json", encoding="utf-8") as f:
        bz = json.load(f)
    T = bz["traditions"]

    land = land_mask()
    # cell-centre lat/lon
    latc = 90 - (np.arange(H) + 0.5) / RES
    lonc = (np.arange(W) + 0.5) / RES - 180
    LON, LAT = np.meshgrid(lonc, latc)
    coast = land & ~(  # land adjacent to ocean
        np.pad(land, 1)[2:, 1:-1] & np.pad(land, 1)[:-2, 1:-1] &
        np.pad(land, 1)[1:-1, 2:] & np.pad(land, 1)[1:-1, :-2])
    sea_coast = (~land) & (np.pad(land, 1)[2:, 1:-1] | np.pad(land, 1)[:-2, 1:-1] |
                           np.pad(land, 1)[1:-1, 2:] | np.pad(land, 1)[1:-1, :-2])

    open_sea = (~land) & ~sea_coast

    def friction(mode):
        # three physically-motivated regimes (chosen a priori, NOT tuned to the outcome):
        #   realistic  — land easy, coasts easy, open ocean a costly-but-crossable barrier;
        #   maritime   — the whole sea is a cheap highway (upper bound on sea permeability);
        #   terrestrial— the sea is a near-wall (lower bound).
        f = np.ones((H, W)); f[land] = 1.0
        if mode == "terrestrial":
            f[~land] = 30.0
        elif mode == "maritime":
            f[~land] = 0.7; f[sea_coast] = 0.5
        else:  # realistic (primary)
            f[sea_coast] = 1.2; f[open_sea] = 8.0
        f[coast & land] = 0.9
        ice = np.abs(LAT) > 60; f[ice & land] *= 2.0; f[(np.abs(LAT) > 72)] *= 2.0
        mtn = (((LON > 70) & (LON < 105) & (LAT > 27) & (LAT < 40)) |   # Himalaya–Tibet
               ((LON > -80) & (LON < -65) & (LAT > -55) & (LAT < 10)))  # Andes
        f[mtn & land] *= 4.0
        return f

    def graph(f):
        rows, cols, data = [], [], []
        idx = np.arange(H * W).reshape(H, W)
        stepv = (111.0 / RES)                       # km per lat step
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            si = slice(max(0, -di), H - max(0, di)); sj = slice(max(0, -dj), W - max(0, dj))
            ti = slice(max(0, di), H - max(0, -di)); tj = slice(max(0, dj), W - max(0, -dj))
            src = idx[si, sj].ravel(); dst = idx[ti, tj].ravel()
            dx = abs(dj) * stepv * np.cos(np.radians(LAT[si, sj].ravel()))
            dy = abs(di) * stepv
            dist = np.sqrt(dx * dx + dy * dy)
            w = 0.5 * (f[si, sj].ravel() + f[ti, tj].ravel()) * dist
            rows.append(src); cols.append(dst); data.append(w)
        return csr_matrix((np.concatenate(data), (np.concatenate(rows), np.concatenate(cols))),
                          shape=(H * W, H * W))

    # working set: traditions with coords + enough motifs
    trad_motifs = {}
    mi_of = {r["id"]: k for k, r in enumerate(bz["motifs"])}
    for r in bz["motifs"]:
        for t in (r.get("traditions") or []):
            trad_motifs.setdefault(t, set()).add(mi_of[r["id"]])

    def cell(tid):
        c = coords.get(tid)
        if not (isinstance(c, (list, tuple)) and len(c) == 2):
            return None
        lat, lon = float(c[0]), float(c[1])
        i = int(min(H - 1, max(0, (90 - lat) * RES))); j = int(min(W - 1, max(0, (lon + 180) * RES)))
        if not land[i, j]:                          # snap to nearest land cell within a few steps
            for r in range(1, 7):
                i0, i1 = max(0, i - r), min(H, i + r + 1)
                j0, j1 = max(0, j - r), min(W, j + r + 1)
                sub = land[i0:i1, j0:j1]
                if sub.any():
                    ii, jj = np.nonzero(sub)
                    di = (i0 + ii) - i; dj = (j0 + jj) - j
                    k = int(np.argmin(di * di + dj * dj))
                    i, j = int(i0 + ii[k]), int(j0 + jj[k]); break
        return i, j

    rows = []
    for tid in T:
        n = len(trad_motifs.get(tid, ()))
        c = cell(tid)
        if n >= MIN_MOTIF and c is not None:
            rows.append((tid, c, trad_motifs[tid]))
    N = len(rows)
    cells = [i * W + j for _, (i, j), _ in rows]
    uniq = sorted(set(cells)); u_of = {c: k for k, c in enumerate(uniq)}
    lat_t = np.array([90 - (c // W + 0.5) / RES for c in cells])
    lon_t = np.array([(c % W + 0.5) / RES - 180 for c in cells])

    def gc(a, b):
        la1, la2 = np.radians(lat_t[a]), np.radians(lat_t[b])
        dla = np.radians(lat_t[b] - lat_t[a]); dlo = np.radians(lon_t[b] - lon_t[a])
        h = np.sin(dla / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin(dlo / 2) ** 2
        return 6371.0 * 2 * np.arcsin(np.sqrt(h))

    def resist(maritime):
        D = dijkstra(graph(friction(maritime)), directed=False, indices=uniq)  # (len uniq, H*W)
        R = np.empty((N, N))
        for a in range(N):
            R[a] = D[u_of[cells[a]], cells]
        return R

    # pairwise vectors
    iu = np.triu_indices(N, 1)
    P = np.zeros((N, len(bz["motifs"])), dtype=np.float32)
    for k, (_, _, ms) in enumerate(rows):
        for m in ms:
            P[k, m] = 1.0
    inter = P @ P.T; size = P.sum(1); union = size[:, None] + size[None, :] - inter
    jac = (inter / np.where(union > 0, union, 1))[iu]
    GC = gc(iu[0], iu[1])
    RC = resist("realistic")[iu]; RM = resist("maritime")[iu]; RT = resist("terrestrial")[iu]

    def r2(preds, tr, te):
        X = np.column_stack([np.ones(len(preds[0]))] + preds)
        b, *_ = np.linalg.lstsq(X[tr], jac[tr], rcond=None)
        pr = X[te] @ b
        return 1 - ((jac[te] - pr) ** 2).sum() / ((jac[te] - jac[te].mean()) ** 2).sum()

    rng = np.random.default_rng(0)
    m = np.arange(len(jac)); rng.shuffle(m)
    cut = int(0.8 * len(m)); tr, te = m[:cut], m[cut:]

    def z(v):
        return (v - v.mean()) / v.std()
    zGC, zRC, zRM, zRT = z(GC), z(RC), z(RM), z(RT)
    res = {
        "gc": {"in": round(r2([zGC], m, m), 4), "out": round(r2([zGC], tr, te), 4)},
        "resist": {"in": round(r2([zRC], m, m), 4), "out": round(r2([zRC], tr, te), 4)},
        "resist_mar": {"in": round(r2([zRM], m, m), 4), "out": round(r2([zRM], tr, te), 4)},
        "resist_terr": {"in": round(r2([zRT], m, m), 4), "out": round(r2([zRT], tr, te), 4)},
        "both": {"in": round(r2([zGC, zRC], m, m), 4), "out": round(r2([zGC, zRC], tr, te), 4)},
    }
    corr = {"gc": round(float(np.corrcoef(jac, GC)[0, 1]), 3),
            "resist": round(float(np.corrcoef(jac, RC)[0, 1]), 3),
            "resist_mar": round(float(np.corrcoef(jac, RM)[0, 1]), 3),
            "resist_terr": round(float(np.corrcoef(jac, RT)[0, 1]), 3)}

    # downsampled friction map (realistic) for the figure
    fm = friction("realistic")
    ds = 2 * RES
    fmap = fm[::ds, ::ds]
    grid = {"h": fmap.shape[0], "w": fmap.shape[1],
            "v": [round(float(x), 2) for x in np.log(fmap).ravel()]}
    pts = [{"x": round(float(lon_t[a]), 1), "y": round(float(lat_t[a]), 1)} for a in range(N)]

    data = {"n": N, "n_motif": len(bz["motifs"]), "res": RES, "min_motif": MIN_MOTIF,
            "r2": res, "corr": corr, "gain": round(res["resist"]["out"] - res["gc"]["out"], 4),
            "grid": grid, "pts": pts}
    OUT.write_text("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"{N} traditions · {len(jac)} pairs · friction grid {H}x{W}")
    print(f"  corr(Jaccard, ·): great-circle {corr['gc']}  resist {corr['resist']}  "
          f"(maritime {corr['resist_mar']}, terr {corr['resist_terr']})")
    print(f"  held-out R²: great-circle {res['gc']['out']}  resist {res['resist']['out']}  both {res['both']['out']}")
    print(f"  HEADLINE gain (resist − gc, out-of-sample R²): {data['gain']:+.4f}  "
          f"-> resistance {'BEATS' if data['gain'] > 0 else 'does NOT beat'} great-circle")


if __name__ == "__main__":
    main()
