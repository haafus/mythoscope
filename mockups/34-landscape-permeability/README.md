# 34 · Landscape permeability / cost-distance geography (roadmap M34)

Tests whether **resistance (least-cost) distance** over a friction surface explains
tradition–tradition motif-sharing better than Method A's **isotropic great-circle** distance —
the physical, always-on connectivity substrate. The falsifiable gate (roadmap): *does
resistance-distance beat great-circle for predicting pairwise motif-**Jaccard**, out of sample?
If not, drop it.*

## The friction surface (coarse, procedural)

- **land / ocean** rasterised from the committed coastline (`land.js`) — the dominant structure,
  data-driven;
- a **latitude penalty** (ice / tundra above ~60°);
- two clear **mountain barriers** (Himalaya–Tibet, Andes);
- **three physically-motivated sea regimes**, chosen *a priori* (not tuned to the outcome):
  **realistic** (coasts easy, open ocean a costly-but-crossable barrier), **maritime** (the whole
  sea a cheap highway), **terrestrial** (the sea a near-wall).

Least-cost distance between traditions is Dijkstra over a 1° grid (`scipy.csgraph`). A full GIS
friction raster (SRTM/GEBCO terrain, WWF ecoregions for deserts/rainforest, HydroRIVERS) is the
upgrade — this is a first cut.

## Result — the gate is NOT passed (an honest negative)

Across **all three** sea regimes, **great-circle beats resistance-distance** out of sample:

| predictor | held-out R² (Jaccard) |
|---|---|
| **great-circle** | **0.158** |
| resistance · realistic | 0.086 |
| resistance · maritime | 0.110 |
| resistance · terrestrial | 0.058 |
| great-circle + resistance | 0.158 |

`corr(Jaccard, great-circle) = −0.40`, stronger than any resistance variant (−0.24…−0.33); and
**great-circle + resistance = great-circle alone** (0.158) — resistance adds *nothing* beyond raw
distance. The detours a friction surface adds (around coasts, over mountains) do **not** track
reduced motif-sharing at this resolution.

## What it means

Either (a) **isolation-by-distance dominates** at this scale — over millennia diffusion runs in
all directions and coarse anisotropy averages out — or (b) the **coarse procedural friction is
inadequate**, and only a real GIS raster with calibrated (cross-validated) weights could
distinguish these. We cannot tell which from here. **As it stands the test does not license
replacing great-circle.**

**Consequence.** The connectivity-*geometry* upgrade for the joint capstone (**M38**) is **not
warranted** by this evidence — keep great-circle. This is exactly what the falsifiable gate is
for: a clean negative saves the downstream line (the roadmap's "gate both behind M34"). It does
*not* by itself kill **M35** (historical corridors), which tests a **distinct** mechanism — dated
human contact as a *covariate*, not a physical distance metric — but M35's priority drops, and a
fine friction raster is the only way to reopen the geometry question.

## Run

```bash
python mockups/34-landscape-permeability/build_data.py   # writes data.js (~1 min: 3 Dijkstra sweeps)
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/34-landscape-permeability/
```

`data.js` is git-ignored. Reads `outputs/motifs/`, the committed `tradition-coords.json`, and
`land.js`. Needs `Pillow` + `scipy`.
