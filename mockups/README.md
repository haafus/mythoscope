# Mockups

Standalone feature prototypes, **separate from the main app**. Each is a single
self-contained `index.html` (inline CSS/JS, no build step, no framework) that reads a
`data.js` snapshot extracted from the built indexes in `outputs/motifs/`.

`data.js` files are git-ignored (they're regenerated artifacts, like `outputs/`).
Build them once, then open the page.

## Run

```bash
# from the repo root, with the motif DB already built (`mytho motifs`)
. .venv/bin/activate
python mockups/01-crosswalk-graph/build_data.py
python mockups/02-semantic-parallels/build_data.py
python mockups/03-areal-clusters/build_data.py

# serve the folder (data.js loads via <script>, so file:// works too, but a server is cleaner)
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/01-crosswalk-graph/
```

## The three prototypes

### 01 · Interactive cross-walk graph
A force-directed explorer over the **confirmed** cross-index links (7,274 edges).
Nodes are TMI / ATU / Berezkin motifs; edge colour = linking method (constituent,
defining, TMI-note, ATU-summary, Berezkin citation, inferred triangle). Search or
click a node to recentre its neighbourhood; toggle 1-/2-hop and inferred links.
Built straight from `crosswalk.json`.

### 02 · Semantic parallels (cross-index)
Finds look-alike motifs the crosswalk may miss. Two modes:
- **Parallels for a motif** — nearest neighbours in the *other two* indexes, each
  tagged `✓ known link` (already in the crosswalk) or `✨ novel`.
- **Free-text search** — type a description; ranked motifs from all three indexes by
  meaning, not exact words.

Embeddings are **LSA (TF-IDF + truncated SVD)** computed offline over motif
name+definition/summary — a reproducible, dependency-light **stand-in for real
transformer embeddings**. The UX and cross-index behaviour are identical; swap the
vectoriser in `build_data.py` (sentence-transformers / an embeddings API) for
production quality. All 11k vectors + the projection matrix ship quantised (int8) so
the query is embedded and searched entirely in the browser.

### 03 · Geographically co-occurring motif clusters
Uses Berezkin's areal data: every motif carries a set of ethnic **traditions**, each
placed in an areal hierarchy (17 English macro-regions). Motifs are clustered by the
shape of their areal footprint (subregion, rarity-weighted k-means). Browse clusters
(dominant regions shown as a colour bar) or pick a motif to see what **co-distributes**
with it (tradition-set Jaccard) — motifs that "travel together" culturally.

## Notes
- Prototypes, not production: no error handling to speak of, one file each, hard-coded
  parameters (dim, k, top-N) near the top of each `build_data.py`.
- They read only from `outputs/motifs/` and never touch the app.
