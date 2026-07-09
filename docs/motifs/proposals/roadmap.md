# Roadmap — prototypes ranked by significance

The actionable sequencing of [`synthesis-and-directions.md`](synthesis-and-directions.md).
Each item is the next mockup in the series (M24…). Ranked by **significance = (how decisively
it resolves a live doubt or unlocks a new capability) × feasibility**. Tier 1 leads because
it is cheap *and* removes the caveat that currently hangs on every result.

Legend: **effort** S/M/L · **data**: *have* (in `outputs/motifs/` + committed snapshots) or
*external* (needs a download + join).

## Tier 1 — do first: cheap, decisive, no new data

These two together retire the two alternative hypotheses that caveat almost everything.

- **M24 · Effort-correction sweep. ✓ done** (mockup 24). Re-ran the count-based findings raw
  vs coverage-weighted. **Result: 3 of 4 survive**; theme_profile variance-by-area weakens
  (34%→26%). Alternative-hypothesis #1 largely rejected for the theme findings. · **S**
- **M25 · Galton-corrected association test. ✓ done** (mockup 25). Restricted-permutation test
  of subsistence×theme within area and within language family. **Result: survives control for
  area (p=0.003) and for family/Galton (p=0.006)** individually; marginal (p=0.065) under both
  at once (low power). The gradient is real beyond area and ancestry. · **S–M** · *(a proper
  dated-tree PGLS still wanted once M30 lands.)*

## Next up — assumption audit

> Numbering: the **M-number is the mockup directory number** (M24 = `mockups/24-…`, and so
> on). The planned slots **M30–M35 stay put** (dated tree, phylogeography, alt-tree, joint
> model, stratigraphy, cross-index); **M37–M38** are the two connectivity layers (landscape
> permeability, historical corridors) and **M39** is the admixture-graph half split off from
> M32 — all added to Tier 3. This audit takes **M36**
> (`mockups/36-facet-adequacy/`) — the *number is its topic slot, not its build order*: it is
> flagged **build-next** by priority, ahead of the lower-numbered but heavier M30–M35.

### M36 · Facet adequacy & orthogonality (audits assumption #6) — *build next*

**Motivation.** The entity model of [`macro-area-facets.md`](macro-area-facets.md) rests on an
untested design choice: that `area · family · subsistence · theme_profile` are the *right* and
*~orthogonal* set of tradition facets (one of the program-level assumptions not yet folded into
`stratum-derivation.md` §0). A first probe already
shows they are **not orthogonal** — Cramér's V(area, family) = **0.74**, V(area, subsistence) =
0.57, V(family, subsistence) = 0.49; `theme_profile` variance explained is only 0.34 / 0.28 /
0.10 by area / family / subsistence. So the mockup does **not** try to prove orthogonality
(already falsified — the three tradition axes co-track one latent, the peopling history of §1);
it audits the two claims that actually matter, and reframes #6 accordingly.

The claim splits into **(A) non-redundancy** — does each facet earn its place by a *unique*
contribution? — and **(B) adequacy** — is the set *complete* (small residual) at the *right*
granularity? Four sub-tests, all on data we `have`:

1. **Association matrix (orthogonality, descriptive).** Cramér's V among the categorical facets
   {area, family, subsistence} + multivariate η² of `theme_profile` by each. *Deliverable:* a
   4×4 heatmap. *Verdict:* quantifies the entanglement (expected: strong area↔family, weakest
   for theme_profile) — the honest picture, not a pass/fail.
2. **Unique contribution (non-redundancy, the real test).** Variation partitioning / drop-one:
   predict tradition–tradition similarity (motif-set **Jaccard** on the attestation matrix, or a
   held-out attestation-prediction accuracy) from the facets, then from the facets *minus X*, for
   each facet X. *Metric:* Δ = R²(all) − R²(all − X) = the variance only X explains. *Verdict:* a
   facet with Δ ≈ 0 is redundant (drop candidate); Δ > 0 earns its place. Report Δ per facet.
3. **Residual structure (adequacy / completeness).** Cluster traditions on the **raw** motif
   vectors (or reuse the degree-corrected blocks of **mockup 26**), then measure the fraction of
   that structure the four facets jointly explain (R² / adjusted Rand between facet-predicted and
   observed grouping). *Verdict:* a large **unexplained residual → a missing axis** (the facet set
   is incomplete); a small residual → adequate. Name what the residual looks like if it is large.
4. **Granularity (right resolution).** A BIC / held-out curve over coarse↔fine variants — area
   12 vs the 18-way finer forks, merged vs split families — echoing mockup 26's BIC-for-K.
   *Verdict:* if 18 areas explain materially more held-out structure, 12 is too coarse; if not,
   12 is right.

**Deliverable.** One page: the association heatmap, a per-facet unique-contribution bar chart
(the headline), the residual-structure number with a note on what (if anything) is missing, and
the granularity curve. **Reframes assumption #6** from "~orthogonal" (false) to "each facet
carries a non-zero unique signal; the set is adequate at granularity G; residual = R", with the
numbers to back each clause. **Data:** *have*. **Effort:** **M**.

**Why build it next (ahead of M30–M35).** It is the cheapest way to audit the entity model
itself — everything in stages 3–4 slices by these facets, so knowing which are redundant,
whether one is missing, and at what granularity, hardens the foundation before the heavier
Tier-3 dating work (M30–M35, which keep their slots). It also feeds directly into the joint
model (M33): the unique-contribution result tells that model which facets to keep as fixed
effects.

## Tier 2 — strong method upgrades on data we already have

Each replaces a descriptive heuristic with a generative model; medium effort, high payoff.

- **M26 · Degree-corrected bipartite SBM. ✓ done** (mockup 26). Alternating degree-corrected
  co-clustering (self-contained numpy), K_t chosen by BIC (=9). **Result:** naive raw-count
  clustering is 80% coverage-driven (`eta²(a(t)|block)=0.80`); the degree-correction halves it
  to **0.48**, with interpretable region-coherent blocks. Sampling-robust replacement for the
  biclustering. · **M** · *(a full nested DC-SBM would need graph-tool; deferred.)*
- **M27 · Descent–areal–reinvention mixture per motif. ✓ done** (mockup 27). Per-motif
  decomposition into inherited/areal/reinvention shares (a per-tradition EM was tried and
  rejected as unidentifiable under Galton; the motif-level version uses the chance-corrected
  phylo-signal). **Result:** most motifs areal-dominant (2311/2775), B slightly more
  inheritable than A; the continuum beats the gate, but A3 and K25 get near-identical mixtures
  so the deep-vs-diffuse residual **does not dissolve** — external calibration needed. · **M**
- **M28 · Likelihood ASR (Mk / Dollo). ✓ done** (mockup 28). 2-state gain/loss CTMC with
  marginal ASR (inside/outside) and a Dollo-flavoured loss bias (loss≈8×gain). **Result:** on
  the *undated* tree it largely reproduces parsimony (`corr=0.90`) — motivating M30 — but adds
  probabilistic output and a loss-vs-gain split (K25: 120 parsimony gains → ~20 expected). Best
  re-run once M30 supplies branch dates. · **M**
- **M29 · Motif content × stratum (BGE-M3). ✓ done** (mockup 29). **Result:** content predicts
  theme strongly (nearest-by-meaning share theme group 58% vs 20% chance) but depth only weakly
  (breadth corr 0.28) — confirms stratum is distributional, not semantic. The content-banality
  idea is an honest negative (flags near-duplicates, not homoplasy). · **M**

## Tier 3 — new capability via external data (highest ceiling)

Heavier (download + join), but each opens a class of conclusion we cannot reach now.

- **M30 · Dated-phylogeny wiring. ✓ done** (mockup 30). Wired Glottolog (coordinate join,
  median 53 km → family + glottocode) + a curated family-expansion-date table. **Result:**
  **439 descent motifs get a calendar age** (Indo-European ~5500 BP märchen belt; B4 →
  ~5200 BP Austronesian); the areal majority is correctly left undated. Family resolution —
  node-level Bayesian ages are M31, which needs the glottocodes this mockup attaches. · **L**
- **M31 · Bayesian phylogeography. ✓ done** (mockup 31). Reconstructs each dated descent
  motif's **origin location + age** (spherical family-foothold centroid + mockup-30 family-date
  ceiling) and maps its spread. **Result:** 439 origins coloured by age, dense at the
  Indo-European märchen belt ~5500 BP; B4 centred in Western Oceania ≤5200 BP with Pacific
  spread lines. The map **re-centres on the selected motif's region** (central meridian =
  circular-mean longitude) so a Pacific-diffusion motif like B4 reads as **circum-Pacific**
  rather than split by the Atlantic seam. A family-resolution point estimate — node-consistent
  RRW with uncertainty (real BEAST on a dated tree) stays future work. The etiology-stage
  visual capstone. · **L**
- **M32 · Alternative-tree test (genetics).** Re-run descent detection (Fitch / likelihood ASR,
  mockups 18 / 28) on a **human genetic tree** instead of the language tree — a *swap-and-rerun*
  on our existing tree machinery. · *data: external* · **tests:** alt-hypothesis #3 ("wrong
  tree, not rare descent"): do the inherited motifs survive a change of classification (language
  → genes)? · **M** · *(splits from the old combined M32; the reticulate back-migration half is
  now **M39**, which builds on this mockup's genetic-tree wiring.)*

- **M37 · Landscape permeability / cost-distance geography.** Replace Method A's *isotropic*
  great-circle distance with **resistance / least-cost distance** over a friction surface — the
  physical, always-on connectivity substrate. · *data: external* · **Effort: L.**
  - **Motivation.** Method A treats 500 km of Eurasian steppe, ocean, Sahara and Himalaya as
    equal. Diffusion friction is strongly anisotropic: low-friction corridors (the Great
    Eurasian Steppe, navigable rivers, coastlines/seaways) carry motifs far, while mountains,
    rainforest and open ocean block them. "Isolation by resistance," not "by distance."
  - **Build.** A pre-modern *walking* friction raster from open terrain (SRTM · GEBCO · ETOPO →
    slope / ruggedness), biomes (WWF ecoregions), rivers (HydroRIVERS) and coasts (GSHHG); then
    least-cost / circuit resistance distance (`Circuitscape.jl`, GRASS `r.walk`, Tobler's hiking
    function) between the Berezkin tradition centroids. **Two variants** — terrestrial-only vs
    maritime-enabled — keyed to the `subsistence` facet, since the sea is a barrier for land
    peoples but a *highway* for maritime ones (Austronesian, circum-Pacific, Mediterranean).
  - **Tests.** (1) **Headline, falsifiable:** does resistance-distance explain tradition–tradition
    motif-Jaccard *better* than great-circle, out of sample? (MRM / Mantel, ΔAIC / held-out ΔR²).
    If it does not beat isotropic distance, drop it. (2) Re-run the stratum gate with resistance
    geography: how many of the deep-vs-diffuse residual motifs (mockup 27's A3 / K25 look-alikes)
    move to *areal* once a corridor explains their spread? (3) Sanity: the circum-Pacific /
    Beringian (Siberia ↔ NW America) and Austronesian-maritime links — the very "wrong-hemisphere"
    cases mockups 15 & 31 had to re-project — should be *predicted* by coastal / maritime
    permeability, not treated as anomalous long jumps.
  - **Caveats.** Milder anachronism than M38 (physical geography is Holocene-stable, so this is
    valid *deep*) — but sea level (Beringia, Sunda / Sahul shelves) and vegetation (green Sahara
    ~6000 BP) shifted, so the deepest questions want a **time-sliced** surface (paleo-coastlines,
    ICE-6G); a single Holocene surface is the first cut. Friction weights are free parameters —
    **calibrate on known cases** (steppe transmissions, Austronesian sea routes) or fit them to
    the language-family structure, never tune to the target result.
  - **Why it sits first among the two.** It upgrades the *baseline* Method A that everything
    downstream uses, its data is cleaner and more complete than the historical layer, and it is
    the physical substrate on which M38's human corridors ride. **Build M37 before M38.**

- **M38 · Historical connectivity layer (empires + trade routes).** The **human, dated** channel
  layered on M37's physical substrate: contact diffusion that jumps across both tree and space
  along documented corridors. · *data: external* · **Effort: M–L.**
  - **Motivation.** Our model has only descent (tree) and proximity (space); it has no channel
    for a motif *carried by an empire or trade network* between unrelated, non-adjacent peoples —
    exactly the mechanism behind the unresolved deep-vs-diffuse residual (cluster 7's
    trans-continental Sun & Moon; the jātaka / Buddhist literary transmission K27z2; the
    Inner-Asian civilisational belt of mockup 15's cluster 3). `FAMILY_DATES` already captures
    the *genealogical* migrations (Bantu, Austronesian, IE, Turkic); this adds the
    *non-genealogical* contact layer.
  - **Build.** A **dated contact graph**: a pair of traditions is linked if they were
    co-members of the same polity at date *t* (dated polity footprints) or short-path-connected
    on the trade network at date *t*; edges carry timestamps and direction.
  - **Uses.** (1) **Reclassify** low-phylo-signal, corridor-coherent, geographically-scattered
    motifs into a **historical-diffusion stratum** with a *recent* age ceiling (the corridor's
    date) — **guarded**: never touches a family-dated-deep or high-signal motif. (2) A **third
    Galton axis** (empire / corridor co-membership) beyond area and family (extends M25). (3)
    **Directionality** — the historical-corridor counterpart to M39's genetic back-migration test
    (axiom A8): deep out-of-Africa vs recent back-into-Africa (Arab / Islamic, trans-Saharan).
  - **Data.** `aourednik/historical-basemaps` (dated world political boundaries, GeoJSON,
    CC-BY-SA) · OWTRAD / ORION historical trade routes · DARMC · Seshat Global History Databank ·
    Pleiades / World Historical Gazetteer (place join) · Hellenthal et al. 2014 admixture events
    (direction).
  - **Caveats.** **Anachronism:** empires are shallow (mostly < 2500 yr) — informative only for
    the *top* of the stratigraphic column; forbid it from touching deep strata. **Coverage
    bias:** Berezkin's ethnographic units often lie *outside* the great empires, so measure
    overlap first. **Circularity:** pre-register which corridor predicts which motif class, then
    test — not a fishing expedition.
  - **First probe (cheap, before the full build).** An **overlap audit**: for each tradition, does
    its coordinate fall inside any historical polity at any snapshot, and how near an OWTRAD
    route? Report the % "reachable" by macro-area. Good coverage → build the corridor facet;
    mostly the Old-World literate belt → scope the claim to that belt.

- **M39 · Admixture-graph back-migration (genetics).** The reticulate half split off from the old
  combined M32: take M32's genetic-tree wiring and add the published **back-migration** edges
  (Eurasian gene flow into Africa) as horizontal connections — an **admixture graph (a DAG), not
  a tree**. · *data: external* · **depends on M32** (its genetic-tradition join) · **Effort:
  M–L.**
  - **Why its own mockup.** M32 is a *swap-and-rerun* on our existing tree machinery (Fitch / Mk
    on a swapped tree); this needs genuine **reticulate-network inference** — ASR on a graph with
    gene-flow edges, a different and heavier method — so bundling the two violated the
    one-question-per-mockup discipline that kept M24 / M25 clean.
  - **Tests alt-hypothesis #6 ("Africa is a sink").** Is an Africa↔Eurasia motif **deep
    out-of-Africa** or **recent back-into-Africa**? It recovers **direction, not just span** — the
    concrete challenge to axiom A8. The same directional claim is tested independently by **M38**
    through *dated human corridors*; M39 is its **genetic** counterpart, so a motif flagged
    back-migratory by both channels is strongly corroborated.

## Tier 4 — synthesis & product

- **M33 · Joint effort-corrected factorization (Hierarchical Poisson).** The one model of
  synthesis §3: factorize `M` with `a(t)` as an exposure offset; latent factors are the
  emergent themes/strata, de-confounded globally. · *data: have* · **subsumes:** mockups
  16–23 as one fit; the true capstone. · **L**
- **M34 · Tradition stratigraphy.** Turn `stratum` around — profile each *tradition* as its
  stack of strata (share of African-substratum … colonial motifs), a geological-column view. ·
  *depends: a trusted stratum (M24/M27)* · **checks:** deep-substrate-rich traditions should
  cluster in refugia / early-peopled regions — a strong falsification surface. · **S–M**
- **M35 · Cross-index arbitration (TMI / ATU vote).** Use the crosswalk as replication:
  promote motifs consistent across indexes, flag Berezkin-only ones as coding-dependent. ·
  *data: partly have* · **adds:** a confidence multiplier on every motif. · **M**

## The critical path

If only three get built: **M24** (kill the sampling doubt) → **M25** (kill the Galton doubt)
→ **M30 + M31** (absolute dating + reconstruction). The first two make the existing findings
trustworthy; the last two make them *datable*. Everything in Tier 2 is a quality upgrade that
can slot in whenever, and M33 is the long-horizon consolidation once M24/M25 have proven the
signals are worth one joint model.

The **connectivity pair (M37 → M38)** is the highest-ceiling addition after dating: M37
replaces isotropic geography with a resistance surface (attacking the deep-vs-diffuse residual
from the *baseline* side, valid at all depths), then M38 layers dated human corridors on top
(attacking it from the *recent-literate* side) and composes with M32's admixture graph. Build
**M37 before M38**; gate both behind M37's single falsifiable test (does resistance-distance
beat great-circle out of sample?) — a clean negative there saves the whole line.
