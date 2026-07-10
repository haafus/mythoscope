# 40 · Motif map explorer

Pick a motif → its attesting **traditions** are plotted on the map and each geographic
**cluster** is outlined with a smoothed contour. The intersection of mockup **17**
(depth-ranked motif list) and mockup **31** (per-motif geography), but over the *whole*
corpus — 3265 motifs with ≥ 4 locatable traditions — not only the datable descent minority.

## Two panels

- **Left — depth-ranked list.** Every mappable motif, sorted by **breadth** (# attesting
  traditions, the depth proxy of mockup 17): deep ≥ 85th pct (≥ 60), areal 50–85th, local
  < 50th (< 18) — the same tiers as mockup 39. Each row carries a 12-cell **footprint**
  sparkline (where it is attested, intensity = count). Filter by search, theme group, tier.
- **Right — the map.** Selecting a motif draws its traditions as points and outlines each
  **DBSCAN cluster** (radius ≈ 22°) with a buffered-Chaikin contour (mockup 15's hull);
  isolated strays stay bare so a lone outlier can't balloon a shape. Points are coloured by
  cluster to match their contour. The map **re-centres** on the motif's own region (central
  meridian = circular mean of its traditions, mockup 31) so a Pacific-spread motif is not
  torn by the Atlantic seam.

## What it shows

- **K25 swan-maiden** (breadth 513): two mega-contours — the whole Old World and the whole
  New World — the honest picture of a pan-continental motif whose only real break is the ocean.
- **I108 "the Pleiades are a person"** (breadth 76): **eleven** tight regional contours —
  South America, N. America, Europe, Siberia, East Asia, Australia, Sub-Saharan Africa… — a
  motif that recurs as discrete regional pockets rather than one continuous belt.
- Narrow/areal motifs draw a single small blob; that a motif fragments into many far-apart
  contours is itself the signal of independent innovation or deep-time diffusion.

## Honest limit

Tradition coordinates are **coarse subregion centroids** (mockup `_geo`), not exact points,
so contours are approximate. "Depth" is a **breadth proxy** that conflates ancient descent
with wide diffusion — the contour shows **where** a motif is attested, not where it originated
(for reconstructed origins of the datable minority see mockup 31).

## Run

```bash
python mockups/40-motif-map-explorer/build_data.py   # writes data.js (~3.5 MB)
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/40-motif-map-explorer/
```

`data.js` is git-ignored. Reads `outputs/motifs/berezkin.json`, mockup 21's `area_of`,
`mockups/_geo.py` coordinates, and the committed `land.js` basemap.
