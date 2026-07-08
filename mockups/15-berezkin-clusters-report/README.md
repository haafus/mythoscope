# 15 · Berezkin clusters — interactive report

An analytical HTML report over the **Berezkin-index biclusters** (mockup 06's
`bicluster("brz")`). For each of the 14 clusters it gives a curated write-up —
**name · composition & boundaries · etiology (what explains the shared corpus) ·
connections · content** — plus its macro-area composition, theme-group mix, a motif
table, and a **map** highlighting that cluster's traditions. A combined world map
shows all clusters at once. A closing section contrasts the three indexes (Berezkin /
Thompson / ATU) and their fitness for different tasks.

## Data

`build_data.py` runs the Berezkin biclustering, enriches each cluster with its
macro-area distribution (from the tradition `areal_path`), theme groups and top
motifs + map points (lon/lat per tradition), and merges in the hand-written
per-cluster analysis (a `PROSE` dict keyed by cluster id, with a `sig` tradition used
to assert alignment at build time). Motif *names* are short catalogue labels; all
interpretive prose is original.

Maps use the shared equirectangular world path (`land.js`, copied from mockup 07);
projection is `cx = lon+180, cy = 90-lat` over a `0 0 360 180` viewBox.

Each cluster also gets one filled **convex footprint**: isolated strays are dropped
first (DBSCAN noise at a generous eps, so a lone outlier can't stretch the hull), then
all remaining points are enclosed in a single convex hull, buffered outward and
Chaikin-smoothed, and drawn semi-transparent under the points. Trans-continental
clusters therefore span the intervening ocean — the price of one contour per cluster.

## Run

```bash
python mockups/15-berezkin-clusters-report/build_data.py   # writes data.js
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/15-berezkin-clusters-report/
```

## What the report surfaces

- The 14 clusters are **mostly areal** — they recover Berezkin's macro-areas and even
  split them into real sub-regions (North America → 3, South America → 2, Africa → 2,
  Western Eurasia → 2).
- Two deviations: a **civilisational/literate diffusion belt** (Inner-Asian, cluster 2)
  and a **thin trans-continental deep-time layer** — the Sun-&-Moon cosmogony (cluster
  6) scattered across Mesoamerica/Amazonia/New Guinea/SE Australia, the theoretically
  most interesting result.
- The closing prose explains why Thompson's index yields a non-areal "high-mythology"
  mega-cluster (a cataloguing artifact), why ATU is a clean European tale-dialectology,
  and why naively co-clustering all three indexes fails (incompatible culture
  vocabularies) — arguing for a shared areal taxonomy / the crosswalk.
