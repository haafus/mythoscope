# 48 · Teleconnections

The climate-science idea of a **teleconnection** — a correlation between distant locations that survives
after the local (seasonal / distance) trend is removed — applied to the motif matrix. The complement to
[migration-surface](../46-migration-surface/README.md): where 46 maps *local* barriers/corridors, 48 maps the
*long-range* reticulation that isolation-by-distance leaves unexplained.

## What it shows

- **Teleconnection network.** For every macro-area pair, the edge weight is the mean over their **long-range
  (> 3000 km) cross-pairs** of `(predicted − observed)` Jaccard dissimilarity — i.e. how much *more* similar
  than distance predicts. Nodes are areas (sized by tradition count) at their centroids; edges are the
  strongest teleconnections. The recognisable structure: a tight **western-Eurasian belt** (W-Europe ·
  N&E-Europe · SW/C-Asia–India · Siberia) and **trans-Pacific / trans-Atlantic** links (Oceania ↔ the
  Americas, Australia ↔ S Cone).
- **Communities.** Agglomerative clustering of the teleconnection matrix recovers four groups that ignore
  raw geography: a **Pacific-rim** community (New World + Oceania + Australia + Beringia), the
  **western-Eurasian belt**, an **East-Asian / African** cluster (East Asia · Tibet/SE-Asia · Sub-Saharan
  Africa), and **Meso/Andes** standing alone — the isolated high-civilisation pole.
- **Teleconnection matrix.** The full area × area excess-similarity heatmap behind the network.
- **Teleconnector motifs.** The motifs whose attestations span the most mutually-distant areas — ranked by
  geographic spread, annotated by **M17 depth**. They are overwhelmingly **deep** (M17 ≈ 74–100): the
  disjunct near-global celestial/cosmogonic substrate — Pleiades-as-people, "Sun & Moon are males", cloud /
  rainbow serpent, "Mankind ascends from the underworld", "People from the sky". This is the layer that
  *drives* the teleconnections, and it directly re-surfaces the deep substrate found by the peeling (mockup
  45) and the disjunction score (M17) — now as a network rather than a tree.

## Why it matters — and its limit

Teleconnections operationalise the project's deepest qualitative claim — a **pan-global disjunct substrate**
crossing continents — as an explicit, thresholded network with communities and a named motif set, rather than
a hand-wave. It cross-reads with mockup 46 (the bridges) and M17 (the same motifs are the deepest).

**Honest caveats.** Areas with < 6 traditions (Madagascar = 1, an unlabelled bucket = 3) are dropped — a
single tradition cannot anchor a teleconnection. "Excess similarity at distance" is a **descriptive**
residual, not a demographic migration estimate; and it conflates deep shared inheritance with long-range
diffusion exactly as the disjunction proxy does — a widespread motif can be old *or* borrowed far. The M17
annotation shows most teleconnectors are deep, but one shallow universal ("Figure on lunar disc", M17 ≈ 4)
is a reminder that breadth ≠ age on its own.

## Data

`build_data.py` builds the binary matrix, computes pairwise Jaccard + haversine, fits the isolation-by-distance
curve and its residual, aggregates long-range excess similarity into the area × area teleconnection matrix,
clusters it into communities, and ranks teleconnector motifs by area-spread with their M17 depth.
Deterministic; writes `data.js`.

## Run

```bash
python mockups/48-teleconnections/build_data.py    # writes data.js
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/48-teleconnections/
```
