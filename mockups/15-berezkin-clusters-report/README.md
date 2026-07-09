# 15 · Berezkin clusters — interactive report

An analytical HTML report over the **Berezkin-index biclusters** (mockup 06's
`bicluster("brz")`). For each of the 14 clusters it gives a curated write-up —
**name · composition & boundaries · etiology (what explains the shared corpus) ·
connections · content** and a longer **deep content** exposition (its narrative lines,
recurring motifs and folkloristic context, grounded in the motif definitions) — plus
its macro-area composition, theme-group mix, two collapsible tables — a **motif table**
(code · English label · Russian name from the index · score) and a **tradition table**
(English name · Russian name · in-cluster membership score) — and a **map** highlighting
that cluster's traditions. Clusters are numbered **1–14** in the UI. A combined world map shows all
clusters at once. A
**cross-cluster synthesis** block (etiology as universal glue, the locally-dressed
trickster, where cosmogony concentrates, cluster 7 as the one trans-continental core)
precedes the clusters, and a closing section contrasts the three indexes (Berezkin /
Thompson / ATU) and their fitness for different tasks.

## Data

`build_data.py` runs the Berezkin biclustering, enriches each cluster with its
macro-area distribution (from the tradition `areal_path`), theme groups and top
motifs + map points (lon/lat per tradition), and merges in the hand-written
per-cluster analysis (a `PROSE` dict keyed by cluster id, with a `sig` tradition used
to assert alignment at build time). Each `PROSE` entry carries the four short fields
plus a `deep` list of paragraphs (the extended exposition). Motif *names* are short
English catalogue labels; the **Russian translation** shown in the table is the index's
own `name_rus`, not a machine translation. All interpretive prose is original — the deep
content paraphrases the Berezkin motif definitions rather than reproducing them.

Maps use the shared equirectangular world path (`land.js`, copied from mockup 07);
projection is `cx = lon+180, cy = 90-lat` over a `0 0 360 180` viewBox, with a
**configurable central meridian**. The combined all-clusters map stays Atlantic-centred
(`lon0 = 0`); a **single cluster card re-centres on that cluster's own region** (`lon0` =
circular-mean longitude of its points), so a Pacific / Beringian / Oceanic cluster is
one contiguous footprint instead of being torn by the Atlantic seam.

Each cluster also gets one filled **convex footprint**: isolated strays are dropped
first (DBSCAN noise at a generous eps, so a lone outlier can't stretch the hull), then
all remaining points are enclosed in a single convex hull, buffered outward and
Chaikin-smoothed, and drawn semi-transparent under the points. The hull is built in a
**longitude-unwrapped frame** (each cluster's longitudes are wrapped around their
circular mean before DBSCAN/hull), so a cluster straddling the antimeridian no longer
smears straight across the map through the Atlantic — its contour follows the *short*
way across the Pacific. On the combined map such a blob is drawn as three ±360-shifted
copies and appears as two lobes hugging the left and right edges; on its own re-centred
card it is a single centred lobe. Trans-continental clusters still span the intervening
ocean (the price of one contour per cluster) — but now the *correct* ocean.

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
- Two deviations: a **civilisational/literate diffusion belt** (Inner-Asian, cluster 3)
  and a **thin trans-continental deep-time layer** — the Sun-&-Moon cosmogony (cluster
  7) scattered across Mesoamerica/Amazonia/New Guinea/SE Australia, the theoretically
  most interesting result.
- The closing prose explains why Thompson's index yields a non-areal "high-mythology"
  mega-cluster (a cataloguing artifact), why ATU is a clean European tale-dialectology,
  and why naively co-clustering all three indexes fails (incompatible culture
  vocabularies) — arguing for a shared areal taxonomy / the crosswalk.
