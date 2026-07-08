# Mockups

Standalone feature prototypes, **separate from the main app**. Each is a single
self-contained `index.html` (inline CSS/JS, no build step, no framework). Most of the
numbered ones read a `data.js` snapshot extracted from the built indexes in
`outputs/motifs/` via a `build_data.py`; the design mocks
(`geographic-layer`, `motifs-navigator`, `tmi-detail-tree`) embed a small real data
slice directly and open with no build.

`data.js` files are git-ignored (they're regenerated artifacts, like `outputs/`).
Build one, then open the page.

## Run

```bash
# from the repo root, with the motif DB already built (`mytho motifs`)
. .venv/bin/activate
python mockups/07-tradition-motif-combined/build_data.py   # build any prototype's data.js

# serve the folder (data.js loads via <script>, so file:// works too, but a server is cleaner)
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/07-tradition-motif-combined/
```

The design mocks need no build — open their `index.html` directly.

## The prototypes

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

### 04 · Semantic parallels on BGE-M3 (vs LSA)
The same corpus as #02, embedded with **real transformer vectors** (`BAAI/bge-m3`,
1024-d) beside the LSA stand-in, for a direct A/B. Pick a motif → its nearest
neighbours in the other two indexes, computed by **BGE-M3 (left) and LSA (right)**
side by side, each tagged known/novel. The header shows **recall@k of the confirmed
cross-walk links** for both methods, so the quality gap is a number, not a hunch.

Neighbours are precomputed in `build_data.py` (a browser can't run BGE-M3, and there
is no live free-text mode here for the same reason). BGE embeddings are cached to
`bge_emb.npy`; first build downloads the ~2 GB model and encodes ~11k docs (slow on
CPU, minutes-to-an-hour; instant thereafter).

### 05 · Tradition → motif mapping (data-driven, no fixed grid)
Instead of a fixed macro-area grid, this takes the **culture/tradition labels the
sources actually list** on each motif across all three indexes — TMI `cultures`
(parsed from the notes + bibliographic citations), ATU attestation `people`, Berezkin
`traditions` — builds a motif × tradition incidence matrix, and **co-clusters** it
(`SpectralCoclustering`). Each bicluster pairs a *group of traditions* with the *group
of motifs* characteristic of them ("for these peoples, these myths"). Clusters emerge
across indexes: some are ATU tale-type blocks spanning European peoples, some Berezkin
areal ethnic groups (Amazonia, NW-coast North America, Turkic), some TMI literary
traditions — the source composition is shown as a colour bar on each.

Both #05 and #06 also plot the clustered traditions on a **world map**, coloured by
cluster (click a cluster to highlight its traditions; click a dot to open its
cluster). There are no coordinates in the source data, so `_geo.py` resolves each
tradition to an approximate centroid — Berezkin traditions via their areal subregion
(nearly all placed), TMI/ATU labels via a small country/people gazetteer (the common
labels; the long tail is dropped, and coverage is shown on the map).

### 06 · Per-index tradition → motif biclusters
Same biclustering as #05, but run **separately for each catalogue** — Berezkin only,
Thompson only, ATU only — with a tab switcher, so you can compare the cultural
structure each index carries on its own. Berezkin gives crisp areal ethnic groups
(Siberian, NW-coast, Pueblo, Amazonian, Turkic…); ATU separates European sub-regions
and a Near-East/N-Africa/S-Asia block; TMI is coarser (its "cultures" are as much
source-collection as ethnos). Per-index thresholds are in `CFG` at the top of
`build_data.py`.

### 07 · Tradition → motif biclusters, combined
Merges #05 and #06 into one page: the cross-index co-clustering (#05) becomes the
first **All indexes** tab, alongside the per-index tabs (#06), with the cluster column
to the **left of the shared map**. For the *All* and *TMI* views, TMI's free-text
culture labels are normalized through the pipeline's curated dictionary
(`culture_dict.canonical` — merges `Icel.`→`Icelandic`, strips `(sub-area)`, keeps
genre labels distinct), and the clustering parameters are retuned for the cleaner
vocabulary. The before/after comparison and the parameter choices are in
[`07-tradition-motif-combined/NORMALIZATION.md`](07-tradition-motif-combined/NORMALIZATION.md).

### 08 · Chapter / section detector (corpus coverage probe)
A **feasibility probe** for auto-extracting a table of contents from the downloaded
texts. Isolated from the pipeline: its `build_data.py` reads only the source list in
`config/corpus.json`, downloads the 28 raw Project Gutenberg `.txt` into a gitignored
`cache/`, and runs a layered heading detector on the **raw** text (blank-line cues
intact — the main cleaner flattens those away, so it works upstream). Five strategies,
tried in priority order: explicit `keyword` headings (Chapter/Book/Sura…), a parsed
`Contents` block located back in the body, standalone `roman` numerals, isolated
`allcaps` titles, and bare `numbered` lines. Each detected heading records its char
offset + a context preview. The viewer lists every book with its winning method and
chapter count, and shows per-strategy candidate counts so you can eyeball over/under-
detection. Current coverage: all 28 books get headings (12 keyword, 8 allcaps, 5
contents, 2 roman, 1 numbered), with offsets pointing at the real body positions —
the KJV book list and the Poetic Edda Contents are relocated to where each section
actually begins.

### motif-text-embedding-eval · how to embed motifs for text matching
A grid experiment (a Python harness, not an HTML page) over Ashliman's ATU-tagged
tales: measures recall@k / MRR for motif embeddings composed as name / +summary /
+hierarchy against text as whole-tale / passage-chunks. Answers "what goes in a motif
embedding" on real data. See [`motif-text-embedding-eval/README.md`](motif-text-embedding-eval/README.md).

### tmi-detail-tree · extracted TMI detail hierarchy tree
The **filter + category tree** that used to sit at the bottom of a Thompson motif's
detail page, removed from the app and preserved here (working). Reproduces
`renderTmiTree` + its tier filter over a real chapter-A slice; open `index.html`
directly. See [`tmi-detail-tree/README.md`](tmi-detail-tree/README.md).

### geographic-layer · one shared region taxonomy over all three indexes
A design mock for reading the three indexes **geographically** through one shared
region taxonomy (ATU attestations · TMI cultures · Berezkin areal traditions): a
regional "fingerprint" for one entity via the cross-walk, an aggregate by region, and
linked region/list/detail pages for a Siberia slice. Multiple static HTML pages, no
build. See [`geographic-layer/README.md`](geographic-layer/README.md).

### motifs-navigator · unified motif navigator
A click-through mock of the [motifs-browser UI proposal](../docs/motifs/proposals/motifs-browser-ui.md)
— one navigator surface with composable lenses over a real ≈83-motif slice of TMI
chapter A, embedded in the file. No API, open `index.html` directly. See
[`motifs-navigator/README.md`](motifs-navigator/README.md).

## Notes
- Prototypes, not production: no error handling to speak of, one file each, hard-coded
  parameters (dim, k, top-N) near the top of each `build_data.py`.
- They read only from `outputs/motifs/` and never touch the app.
