# Mockups

Standalone feature prototypes, **separate from the main app**. Each is a single
self-contained `index.html` (inline CSS/JS, no build step, no framework). Most of the
numbered ones read a `data.js` snapshot extracted from the built indexes in
`outputs/motifs/` via a `build_data.py`; the design mocks
(`09-motifs-navigator`, `11-tmi-detail-tree`, `12-geographic-layer`) embed a small
real data slice directly and open with no build.

`data.js` files are git-ignored (they're regenerated artifacts, like `outputs/`).
Build one, then open the page.

> These are the lab bench for the analysis arc in
> [`docs/motifs/proposals/analysis-program.md`](../docs/motifs/proposals/analysis-program.md)
> (collect → describe → classify → explain). Roughly: 01–14 are stages 1–2
> (collection & morphology), 15–16, 21 & 23 are stage 3 (systematics), 17–20 & 22 are
> stage 4 (phylogeny & etiology).
>
> Each entry below carries a **Q** (the question or hypothesis it puts) and a **Finding**
> (what it actually showed).

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
**Q.** Can the confirmed cross-index links be explored as one navigable object?
**Finding.** Yes — a filterable graph over 7,274 edges makes the crosswalk's shape legible.

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
**Q.** Can we surface look-alike motifs the crosswalk misses, by meaning not words?
**Finding.** Yes — LSA nearest-neighbours across indexes (known/novel tagged), all in-browser; a viable stand-in for transformer vectors.

### 03 · Geographically co-occurring motif clusters
Uses Berezkin's areal data: every motif carries a set of ethnic **traditions**, each
placed in an areal hierarchy (17 English macro-regions). Motifs are clustered by the
shape of their areal footprint (subregion, rarity-weighted k-means). Browse clusters
(dominant regions shown as a colour bar) or pick a motif to see what **co-distributes**
with it (tradition-set Jaccard) — motifs that "travel together" culturally.
**Q.** Do motifs cluster by the shape of their areal footprint — which "travel together"?
**Finding.** Yes — rarity-weighted areal clustering yields regional motif clusters and per-motif co-distribution.

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
**Q.** How much better are real transformer embeddings than the LSA stand-in?
**Finding.** Quantified by recall@k on the confirmed crosswalk — BGE-M3 beats LSA; the quality gap is a number, and BGE was adopted downstream.

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
**Q.** Without a fixed grid, do the sources' own culture labels co-cluster traditions with their characteristic motifs?
**Finding.** Yes — SpectralCoclustering surfaces cross-index "for these peoples, these myths" blocks (Amazonian, NW-coast, Turkic, European tale-type…).

### 06 · Per-index tradition → motif biclusters
Same biclustering as #05, but run **separately for each catalogue** — Berezkin only,
Thompson only, ATU only — with a tab switcher, so you can compare the cultural
structure each index carries on its own. Berezkin gives crisp areal ethnic groups
(Siberian, NW-coast, Pueblo, Amazonian, Turkic…); ATU separates European sub-regions
and a Near-East/N-Africa/S-Asia block; TMI is coarser (its "cultures" are as much
source-collection as ethnos). Per-index thresholds are in `CFG` at the top of
`build_data.py`.
**Q.** What cultural structure does each catalogue carry on its own?
**Finding.** Berezkin → crisp areal ethnic groups; ATU → European sub-regions; TMI is coarser (source-collection as much as ethnos).

### 07 · Tradition → motif biclusters, combined
Merges #05 and #06 into one page: the cross-index co-clustering (#05) becomes the
first **All indexes** tab, alongside the per-index tabs (#06), with the cluster column
to the **left of the shared map**. For the *All* and *TMI* views, TMI's free-text
culture labels are normalized through the pipeline's curated dictionary
(`culture_dict.canonical` — merges `Icel.`→`Icelandic`, strips `(sub-area)`, keeps
genre labels distinct), and the clustering parameters are retuned for the cleaner
vocabulary. The before/after comparison and the parameter choices are in
[`07-tradition-motif-combined/NORMALIZATION.md`](07-tradition-motif-combined/NORMALIZATION.md).
**Q.** Does normalizing TMI's free-text culture labels improve the combined clustering?
**Finding.** Yes — the curated dictionary cleans the vocabulary and tightens the clusters (before/after in NORMALIZATION.md).

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
**Q.** Can a table of contents be auto-extracted from the raw corpus texts?
**Finding.** Feasible — a 5-strategy priority detector gets headings for all 28 books at real body offsets.

### 09 · motifs-navigator · unified motif navigator
A click-through mock of the [motifs-browser UI proposal](../docs/motifs/proposals/motifs-browser-ui.md)
— one navigator surface with composable lenses over a real ≈83-motif slice of TMI
chapter A, embedded in the file. No API, open `index.html` directly. See
[`09-motifs-navigator/README.md`](09-motifs-navigator/README.md).
**Q.** What would a unified motif-navigator (composable lenses) feel like in the hand?
**Finding.** A working click-through over a real TMI-chapter-A slice validates the browser-UI proposal.

### 10 · motif-text-embedding-eval · how to embed motifs for text matching
A grid experiment (a Python harness, not an HTML page) over Ashliman's ATU-tagged
tales: measures recall@k / MRR for motif embeddings composed as name / +summary /
+hierarchy against text as whole-tale / passage-chunks. Answers "what goes in a motif
embedding" on real data. See [`10-motif-text-embedding-eval/README.md`](10-motif-text-embedding-eval/README.md).
**Q.** What should go into a motif embedding (name / +summary / +hierarchy; whole-tale vs chunks)?
**Finding.** A recall@k / MRR grid on Ashliman's ATU-tagged tales settles it empirically rather than by guess.

### 11 · tmi-detail-tree · extracted TMI detail hierarchy tree
The **filter + category tree** that used to sit at the bottom of a Thompson motif's
detail page, removed from the app and preserved here (working). Reproduces
`renderTmiTree` + its tier filter over a real chapter-A slice; open `index.html`
directly. See [`11-tmi-detail-tree/README.md`](11-tmi-detail-tree/README.md).
**Q.** Preserve the TMI detail filter+tree removed from the app so it isn't lost?
**Finding.** Reproduced and working over a real chapter-A slice, ready to reinstate.

### 12 · geographic-layer · one shared region taxonomy over all three indexes
A design mock for reading the three indexes **geographically** through one shared
region taxonomy (ATU attestations · TMI cultures · Berezkin areal traditions): a
regional "fingerprint" for one entity via the cross-walk, an aggregate by region, and
linked region/list/detail pages for a Siberia slice. Multiple static HTML pages, no
build. See [`12-geographic-layer/README.md`](12-geographic-layer/README.md).
**Q.** Can the three indexes be read through one shared region taxonomy?
**Finding.** A design mock shows it works — regional fingerprint, aggregate-by-region, linked region/list/detail for a Siberia slice.

### 13 · Corpus overview (dashboard)
A design prototype for the corpus **overview page** — "what's in this corpus?".
Isolated: `build_data.py` reads `config/corpus.json` + `config/traditions.json`,
downloads the 28 raw Gutenberg texts, and computes headline stats, composition by
macro-area, per-text sizes, and a **text-similarity heatmap** (TF-IDF cosine, both
text×text and tradition×tradition, reordered by hierarchical clustering / seriation).
The heatmap is a model-free lexical stand-in for the pipeline's BGE-M3 semantic
distances, yet already recovers sensible groups (East-Asian, Oceanic, Germanic,
Christianity↔Islam, classical epics). The size bar makes the ~3-orders-of-magnitude
length skew (KJV vs a short folktale) obvious. Analytical-dashboard direction.
**Q.** "What's in this corpus?" — can it be shown at a glance?
**Finding.** Yes — stats + macro-area composition + a lexical similarity heatmap that already recovers sensible groups.

### 14 · Corpus overview, in the app's design
Mockup #13 **re-skinned in MythoScope's own design system** — the app navbar (with
*Sources* active), `.card` / `.stat-card` surfaces, tokens and accents — to show how
the overview would look as the real **Sources** page reached from the main nav. Same
data and blocks as #13; the change is purely presentational. See
[`14-corpus-overview-app/README.md`](14-corpus-overview-app/README.md).
**Q.** How would the overview look as a real Sources page in the app's design system?
**Finding.** Re-skinned #13 on the app's navbar/cards/tokens — same data, production look.

### 15 · Berezkin clusters — interactive report
An analytical report over the 14 Berezkin-index biclusters (numbered **1–14** in the
UI). Per cluster: a curated name / composition & boundaries / etiology / connections /
content write-up plus a longer **deep-content** exposition (narrative lines, recurring
motifs and folkloristic context, grounded in the motif definitions), macro-area and
theme bars, two collapsible tables — a **motif table** (code · English label · Russian
name from the index · score) and a **tradition table** (English name · Russian name ·
membership score) — and a world map highlighting that cluster's traditions; plus a
combined all-clusters map. A **cross-cluster synthesis** block precedes the clusters, and a
closing section contrasts the three indexes (Berezkin / Thompson / ATU) and their
fitness for different tasks, foregrounding the thin trans-continental Sun-&-Moon
deep-time layer (cluster 7). Interpretive prose is original; motif names are short
catalogue labels and the Russian column is the index's own `name_rus`. See
[`15-berezkin-clusters-report/README.md`](15-berezkin-clusters-report/README.md).
**Q.** What do the 14 Berezkin motif co-occurrence biclusters mean — region, theme, etiology?
**Finding.** A curated per-cluster report + maps; foregrounds the thin trans-continental Sun-&-Moon deep-time layer (cluster 7).

### 16 · Tradition thematic profiles
Tests the `theme_profile` idea from
[`macro-area-facets.md`](../docs/motifs/proposals/macro-area-facets.md): each Berezkin
tradition is a 13-dim vector of the proportion of its motifs in each thematic group, and
the 840 traditions with ≥30 motifs are clustered **by that profile alone** (k-means),
then mapped. 38% of the profile variance is explained by macro-area — a strong regional
signal — yet the clusters mix region and worldview (a cosmology-heavy cluster groups
Mesoamerica–Andes with Tibet/SE-Asia and Ancient Greece). See
[`16-tradition-theme-profiles/README.md`](16-tradition-theme-profiles/README.md).
**Q. (hypothesis)** A tradition's genre balance (`theme_profile`) is a real signal, partly independent of geography.
**Finding.** Upheld — 38% of profile variance is macro-area (→~26% once effort-corrected, M24), the rest orthogonal; clusters mix region and worldview (Mesoamerica–Andes with Tibet/SE-Asia).

### 17 · Motif depth-score
A first prototype of **Method A** from
[`stratum-derivation.md`](../docs/motifs/proposals/stratum-derivation.md): estimate a
motif's time-depth from the shape of its areal distribution alone (prevalence, spread,
fragmentation, language-family span, mega-set span). Shows two scores — PC1 and a
disjunction-weighted variant. The most prevalent motifs top PC1 (the swan-maiden leads,
then pan-global celestial cosmogony) and the adventure-endemism stress-test passes (the
disjunction weighting nearly triples the separation); but neither linear score suffices —
PC1 conflates old with *widespread*, the disjunction variant over-penalises prevalence
(swan-maiden K25 100→10) — which is the concrete argument for the phylogenetic Method B. See
[`17-motif-depth-score/README.md`](17-motif-depth-score/README.md).
**Q.** Can a motif's time-depth be read off the shape of its areal distribution alone?
**Finding.** A signal, not a dating — no single linear score works (PC1 conflates old with widespread; the disjunction variant over-penalises prevalence), which motivates Method B.

### 18 · Motif phylo-strata (Method B)
A prototype of **Method B**: place each motif on a **language classification tree** (from
the `language` chains) and run Fitch parsimony ancestral-state reconstruction. The
**phylogenetic signal** (observed vs random gains) separates descent (clustered on the
tree) from areal diffusion (scattered). Finding: only ~1% of motifs are broad *and*
clade-clustered — and those are European fairy-tale types (Cinderella, "seven at a
blow"), independently recovering the published result that märchen track language
phylogeny within Eurasia; cosmology, trickster and the swan-maiden are broad but areally
diffused. So A and B are complementary — B flags the *mode* of spread and dates the
descent-minority, geography (A) handles the areal majority. See
[`18-motif-phylostrata/README.md`](18-motif-phylostrata/README.md).
**Q.** Do motifs follow the language tree (descent) or spread areally?
**Finding.** Only ~1% are broad *and* clade-clustered (Eurasian märchen — recovering the published result); the rest spread areally → **geography is primary**.

### 19 · Combined stratum (gated A × B)
Realises [`stratum-derivation.md`](../docs/motifs/proposals/stratum-derivation.md) §12 —
A and B in **one gated pipeline**, not two scores. **B** (phylo-signal) picks the *mode*
(descent vs areal); the mode picks the dating instrument (clade depth for descent,
geographic disjunction / deep mega-set span for areal); confidence comes from A–B
agreement. The payoff: the "broad" motifs neither method could resolve alone split three
ways — `areal-deep` / `descent` / `areal-broad`. **Theme is deliberately not an input**
(that would be circular); it stays an independent cross-check and corroborates anyway —
the Category-A cosmology share falls from 64% in the deep-areal mode to 24% in descent.
See [`19-combined-stratum/README.md`](19-combined-stratum/README.md).
**Q.** Can A and B be combined so each dates what it can, without theme leaking in?
**Finding.** Yes — B gates the mode, the mode picks the instrument; the "broad" motifs split three ways; theme (kept out) corroborates independently (64%→24%).

### 20 · Stratum controls (sampling + banality)
Applies the two mandatory §5 controls mockups 17–19 skipped, on top of the mockup-19
gate, and measures the effect. **Attestation-intensity:** tradition coverage a(t) spans
1…738, so raw breadth partly measures catalogue density; weight each present tradition by
baseline-equivalent coverage and count a macro toward breadth only with real evidence.
**Banality:** a generic-definition + singleton-scatter proxy flags likely homoplasy.
Finding: breadth shrinks 31%, 504 motifs (15%) change mode (mostly areal-broad →
areal-recent), but the deep both-hemisphere class survives 320/480 — an empirical
restatement of axiom 4. See [`20-stratum-controls/README.md`](20-stratum-controls/README.md).
**Q.** Do the stratum findings survive the mandatory sampling + banality controls?
**Finding.** The "broad areal" class thins (breadth −31%, 504 motifs change mode), but the deep both-hemisphere spine survives 320/480 — an empirical restatement of axiom 4.

### 21 · Deterministic facet population
Checks whether the deterministic recipe in `macro-area-facets.md` covers the whole corpus
before it becomes `region_facets.py`. `area(areal_path)` → 12 macro-areas covers 1042/1046
(4 empty paths); `theme(motif_group_num)` covers 3347/3488; `family(language[0])` resolves
99% (seed + area-fallback), leaving 10 linguistic isolates for curation. Marks each family
assignment seed vs area-fallback and is explicit that the religion-overlay families need a
small curated overlay. See [`21-facet-population/README.md`](21-facet-population/README.md).
**Q.** Does the deterministic facet recipe cover the whole corpus?
**Finding.** area 1042/1046, theme 3347/3488, family 99% — the residual is *known* data gaps (empty paths, isolates); only the religion overlay needs curation.

### 22 · Subsistence from D-PLACE + theme test
Wires the one external dataset the model needs — **D-PLACE** (Ethnographic Atlas, CC-BY) —
to populate `tradition.subsistence` (the 4th facet, with no in-corpus source), joining each
tradition to its nearest society. Then tests the correlation the proposal asserted but never
checked: Category-A (cosmology) share splits **extractive economies high** (foragers 54.7%,
horticulturalists 57.6%) from **intensive/mobile ones low** (agrarian-states 39.5%,
pastoralists 36.2%) — cosmology yields to tale as production intensifies, as predicted, with
an honest area confound. See [`22-subsistence-external/README.md`](22-subsistence-external/README.md).
**Q. (hypothesis)** Foragers are cosmology-heavy, farmers tale-heavy (the proposal's asserted `subsistence × theme`).
**Finding.** Confirmed — extractive high (forager 54.7, hort 57.6) vs intensive/mobile low (agrarian 39.5, pastoralist 36.2); the area confound is real but does not explain it away (tested in M25).

### 23 · Theme × geography
Visualises the `theme × area` signal `macro-area-facets.md` only states in prose. Four
views: a **lift heatmap** (13 theme groups × 12 macro-areas — Adventures ×1.2 in the
Eurasian belt, ×0.3 in Australia; Sun & Moon ×3.4 in Australia); a **theme × theme
co-occurrence matrix** (CLR correlation across traditions, seriated) that recovers Berezkin's
Category A vs B split from co-occurrence alone; a **co-cluster map** that biclusters
traditions × themes (SpectralCoclustering) and draws each cluster as footprint blobs in the
style of mockup 15 — the traditions-×-themes analogue of its traditions-×-motifs clusters;
and a **theme picker** that shades the map by any single group's share. See
[`23-theme-geography/README.md`](23-theme-geography/README.md).
**Q.** Where do the thematic blocks concentrate geographically, and do they co-occur into Berezkin's A/B?
**Finding.** Strong `theme × area` lift; and the **A/B split re-emerges from theme co-occurrence** (seriated CLR) without using his labels — the taxonomy is data-confirmed.

### 24 · Effort-correction sweep (roadmap M24)
Tests whether the theme findings are catalogue-density artifacts (synthesis alt-hypothesis
#1): re-runs four headline results **raw vs coverage-weighted** (shared weight
`w(t)=min(2, median/a(t))`, [`_bias.py`](_bias.py)) with a per-finding verdict. **3 of 4
survive** — subsistence×theme, theme×area lift and the A/B co-occurrence blocks hold; the one
that **weakens** is theme_profile variance-by-area (34%→26%), so geography's grip on genre
balance was partly over-stated by sampling. See [`24-bias-sweep/README.md`](24-bias-sweep/README.md).
**Q.** Are the theme findings artifacts of catalogue density (alt-hypothesis #1)?
**Finding.** **3 of 4 survive** effort-correction; only theme_profile variance-by-area weakens (34%→26%). Alt-hypothesis #1 largely rejected for the theme findings.

### 25 · Galton-corrected test (roadmap M25)
Tests whether the `subsistence × theme` gradient (mockup 22) is neighbour autocorrelation
(Galton's problem) or just `area × theme`, by **restricted permutation** — shuffling the
subsistence label within strata. It **survives** control for area (p=0.003) and for language
family / Galton (p=0.006) individually, attenuating to marginal (p=0.065) only when both are
controlled at once (low power). Subsistence carries its own contribution, partly entangled
with geography. See [`25-galton-test/README.md`](25-galton-test/README.md).
**Q.** Is `subsistence × theme` just neighbour autocorrelation (Galton) or `area × theme`?
**Finding.** Survives control for area (p=0.003) and for family/Galton (p=0.006) individually; marginal only when both are controlled at once (low power) — subsistence has its own contribution.

### 26 · Degree-corrected block model (roadmap M26)
Replaces the biclustering of 06/07/15/23 with a generative **degree-corrected** co-clustering
of the motif × tradition matrix (self-contained numpy; K chosen by BIC). The payoff: naive
clustering of raw counts separates traditions by coverage (`eta²(a(t)|block)=0.80` — a
sampling artifact); the degree-correction halves it to **0.48** while keeping interpretable,
region-coherent tradition blocks and Category-A-stratified motif blocks. See
[`26-blockmodel/README.md`](26-blockmodel/README.md).
**Q.** Can co-clustering be de-confounded from sampling and pick its own resolution?
**Finding.** Yes — degree-correction halves the coverage artifact (`eta²(a(t)|block)` 0.80→0.48) and BIC selects K=9; blocks stay region-coherent.

### 27 · Descent / areal / reinvention mixture (roadmap M27)
Replaces mockup 19's binary gate with a per-motif continuous decomposition into three shares
(descent = chance-corrected phylo-signal, areal, reinvention). **Most motifs areal-dominant**
(2311/2775), B slightly more inheritable than A; B4→descent, Cinderella→50/50. But **A3 and K25
get near-identical mixtures** (descent≈0.16) — the deep-substrate-vs-wide-diffusion residual is
confirmed irreducible from distribution, needing external calibration. See
[`27-mixture/README.md`](27-mixture/README.md).
**Q.** Is `stratum` one axis, or a mixture — and does the A3-vs-K25 residual dissolve?
**Finding.** The continuum beats the gate (most motifs areal-dominant), but A3≈K25 mixtures stay near-identical — the deep-vs-diffuse residual is irreducible from distribution.

### 28 · Likelihood ASR (roadmap M28)
Upgrades Method B (18) from Fitch parsimony to a 2-state Mk gain/loss model with marginal ASR
(inside/outside) and a loss bias (Dollo-fit, loss≈8×gain). On the **undated** tree it largely
reproduces parsimony (`corr=0.90` — the motivation for M30), but adds probabilistic output and
a loss-vs-gain decomposition: swan-maiden K25 needs 120 parsimony gains but only ~20 *expected*
gains, the model preferring loss-from-ancestor. See [`28-likelihood-asr/README.md`](28-likelihood-asr/README.md).
**Q.** Does likelihood ASR beat Fitch parsimony for Method B?
**Finding.** On the undated tree it ≈parsimony (corr 0.90 — motivating M30's dated tree); the genuine gain is probabilistic output + a loss-vs-gain split (K25: 120 → ~20 expected gains).

### 29 · Content vs theme / depth (roadmap M29)
Crosses the BGE-M3 motif embeddings with the theme and depth axes. **Content is theme, not
depth:** nearest-by-meaning motifs share the theme group 58% of the time (vs 20% chance) but
content barely predicts breadth (corr 0.28) or prevalence (0.18) — meaning says *what* a motif
is, not *how old*, confirming `stratum` must come from distribution. A content-redundancy
"banality" attempt is an honest negative (it flags near-duplicate M29* trickster variants, not
homoplasy; corr with the short-def proxy ≈0). See [`29-content-stratum/README.md`](29-content-stratum/README.md).
**Q.** Does a motif's content (embedding) predict its theme and its depth?
**Finding.** Content ≈ theme (58% vs 20% chance) but not depth (breadth corr 0.28) → `stratum` is distributional, not semantic; the content-banality idea is a clean negative.

### 30 · Dated phylogeny (roadmap M30)
Wires **Glottolog** (CC-BY) — each tradition joined to its language **name-first** (`build_join.py`;
fixes wrong-neighbour matches, name-agreement 14%→29%) → standard family + glottocode — plus a
curated table of published **family expansion dates** (45 families), to turn a descent motif's
ordinal clade depth into a **calendar age**.
**Q.** Can ordinal clade-depth become an absolute (calendar) age?
**Finding.** Yes for the descent minority: **451 motifs dated**, concentrated at Indo-European
~5500 BP (the märchen belt) with B4 → ~5200 BP (Austronesian); the areal majority (A3, K25) is
correctly left undated (geography's job). Family-resolution only — node-level Bayesian ages are
M31. See [`30-dated-phylogeny/README.md`](30-dated-phylogeny/README.md).

### 31 · Phylogeography (roadmap M31)
The etiology capstone: reconstructs each dated descent motif's **origin location + age** and
maps its spread. Location = spherical centroid of the motif's traditions within its family;
age = the mockup-30 family-date ceiling.
**Q.** Where and when did each descent motif originate, and how did it spread?
**Finding.** 451 origins on one map, coloured by age — dense at the Indo-European märchen belt
(~5500 BP), with **B4 (fished-earth) centred in Western Oceania ≤ 5200 BP** and spread lines
fanning across the Pacific. A family-resolution point estimate, not a node-consistent RRW with
uncertainty (that needs a real dated tree — BEAST — future work). See
[`31-phylogeography/README.md`](31-phylogeography/README.md).

### 32 · Facet adequacy (roadmap M32)
Audits assumption #6 — are `area · family · subsistence · theme_profile` the right,
non-redundant, complete set of tradition facets? Four sub-tests on the 910 traditions carrying
all four facets: Cramér's V association, drop-one unique contribution, residual structure, and a
granularity curve.
**Q.** Does each facet earn its place, and is the set complete at the right resolution?
**Finding.** Not orthogonal (V(area,family)=0.73). Each facet is non-zero but **family &
subsistence are nearly redundant** (unique Δ R² ≈ 0.01) — **theme_profile (0.13) and area (0.08)**
do the work. The set is **incomplete**: facets recover only ~36% of motif-similarity (block ARI
and continuous R² agree), leaving a large **cross-continental convergence residual** for the
connectivity layers (M34/M35). Granularity is right — 12 areas / 11 families beat both coarser
and finer (which overfit). See [`32-facet-adequacy/README.md`](32-facet-adequacy/README.md).

### 33 · Alternative-tree test (roadmap M33)
Tests alt-hypothesis #3 (descent is an artifact of the language tree) by re-running the
chance-corrected Fitch phylo-signal on a **curated consensus genetic tree** (continental
resolution, geography-joined) and comparing per-motif signal.
**Q.** Does the descent signal survive a swap from the language tree to a genetic one?
**Finding.** Caveat first — at continental resolution the genetic tree is built from `area`, so
genetic ≈ geography and both correlate with family (V=0.73): this is really a **language-vs-
geography** test, not an independent genetic axis, and the modes separate *only where the
classifications disagree* (the correlated `both` core is confounded, so the 89% "robust" is
largely tautological). The real result is the off-diagonal: the **language-only** bucket is
non-empty and is exactly the cross-continental families (**Indo-European, Altaic**) → *linguistic
transmission is real and area-independent*; **genetic-only** (e.g. Jonah in Africa) = areal
diffusion. A true third axis needs fine SNP + the M34/M35 corridors; the join is wired for M36.
See [`33-alt-tree/README.md`](33-alt-tree/README.md).

### 34 · Landscape permeability (roadmap M34)
Tests whether **resistance (least-cost) distance** over a coarse friction surface (land/sea from
the coastline + ice + two mountain ranges; three a-priori sea regimes; Dijkstra on a 1° grid)
beats Method A's isotropic **great-circle** distance at predicting pairwise motif-Jaccard.
**Q.** Does anisotropic connectivity explain motif-sharing better than raw distance?
**Finding — the falsifiable gate is NOT passed (honest negative).** Across all three sea regimes
**great-circle wins** out of sample (held-out R² 0.158 vs 0.086/0.110/0.058), and
great-circle+resistance = great-circle alone — resistance adds nothing. Either isolation-by-distance
dominates at this scale or the coarse friction is inadequate (indistinguishable without a fine GIS
raster). So the connectivity-**geometry** upgrade for M38 is unwarranted (keep great-circle); this
is what the gate is for — a clean negative saves the line. See
[`34-landscape-permeability/README.md`](34-landscape-permeability/README.md).

### 35 · Historical corridors (roadmap M35)
Do historical **empires** move motifs across macro-area boundaries? Links traditions co-resident
in the same multi-area empire (historical-basemaps, 4 pre-colonial snapshots; ≥3-area empires to
skip the world-tessellation), and tests the lift beyond distance + area.
**Q.** Does dated empire co-membership explain motif-sharing beyond geography?
**Finding — weak but real (vs M34's clean negative).** Only ~32% of traditions were ever in a real
empire (Old-World/Mongol-belt biased — South America, Australia, Oceania ~0%). Globally empire adds
little (ΔR² +0.011 over distance+area), **but** the sharp cross-area test is positive: traditions in
*different* areas sharing an empire share **×2.6** more motifs (distance-matched +0.029) — Rome and
the Mongol world genuinely carried motifs across boundaries. A narrow dated covariate for the empire
belt, not a general axis; trade routes (OWTRAD) not yet wired. See
[`35-historical-corridors/README.md`](35-historical-corridors/README.md).

### 36 · Admixture back-migration (roadmap M36)
Tests alt-hypothesis #6 / the A8 back-migration critique: is an Africa↔West-Eurasia motif deep
out-of-Africa or recent back-into-Africa? Reads **direction** off the within-Africa footprint —
deep un-admixed reservoir (West/Central/Southern, San) vs the Eurasian-admixed corridor
(N.Africa/Horn/Sahel), the documented back-migration edge.
**Q.** For a shared Africa–Eurasia motif, which way did it flow?
**Finding — the A8 critique is confirmed.** Of 836 Africa↔W-Eurasia motifs, **43% sit
corridor-only** = back-migration candidates (corridor-fraction 0.60 vs 0.17 for Africa-only, ×3.5)
→ a large slice of the "African substratum" is recent back-flow, **weakening "African substratum =
oldest"**. Honest confound: the corridor is also the Near-East-proximal edge, so genetic
back-migration ≡ cultural diffusion from distribution alone (both recent — the point for A8); a
fine SNP graph is the mechanistic upgrade. See
[`36-admixture-backmigration/README.md`](36-admixture-backmigration/README.md).

### 37 · Cross-index arbitration (roadmap M37)
Uses the BZ↔TMI↔ATU crosswalk as replication → a per-motif confidence weight (triple / strong /
moderate / berezkin-only), and checks whether our findings are Berezkin coding artifacts.
**Q.** Are the findings corroborated by independent motif indexes, and is confidence theme-skewed?
**Finding — not a coding artifact.** 48% of motifs are cross-index corroborated; corroboration is
**theme-blind** (cosmology 49% = tales 49%) and **higher for broad motifs** (54% vs 20% narrow) —
the analysis leans on the replicated core. Emits the observation weight for M38. Caveat: the
crosswalk is automated, so berezkin-only over-counts (K25 swan-maiden's ATU 400 was missed) — an
upper bound on coding-dependence. See
[`37-cross-index-arbitration/README.md`](37-cross-index-arbitration/README.md).

### 38 · Joint HPF — the capstone (roadmap M38)
One model replacing the 16–23 pipeline: a Poisson factorization of the tradition×motif presence
matrix with the attestation intensity **a(t) as an exposure offset** (+ M37 confidence as motif
weights), so the latent factors are the emergent area/theme components de-confounded from sampling.
**Q.** Can one de-confounded fit recover the structure the piecemeal mockups found?
**Finding — yes.** In a single fit it **de-confounds** (η²(log a | component) 0.34 vs naive KMeans
0.67, mockup-26 naive ~0.80) **and recovers geography** (ARI 0.37 vs 0.08): the 12 emergent
components are the 12 macro-areas, each with a theme profile — subsuming mockups 16–23. Built on the
settled inputs (facets M32, tree/direction M33/M36, empire covariate M35, weights M37, great-circle
geometry since M34's gate failed). Honest limit: the MAP/NMF core, not full Bayesian HPF with
uncertainty. See [`38-joint-hpf/README.md`](38-joint-hpf/README.md).

## Notes
- Prototypes, not production: no error handling to speak of, one file each, hard-coded
  parameters (dim, k, top-N) near the top of each `build_data.py`.
- They read only from `outputs/motifs/` and never touch the app (mockup 22 also reads a
  committed CC-BY D-PLACE derivative, `22-subsistence-external/dplace_subsistence.json`).
