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

> Numbering: the **M-number is the mockup directory number and follows build order** — the done
> mockups M24–M31 were built in sequence, and the planned queue **M32–M39** continues in the
> order they should be built. The next mockup to build is always the lowest un-built number.

**Build order of the planned queue (M32–M39).** Ordered so the joint capstone (**M38**) is built
**once**, after every structural input it consumes has landed — no v1/v2/v3 re-fits:

1. **M32 · Facet adequacy ✓ done** — non-orthogonal (V≤0.73); family & subsistence nearly
   redundant (Δ R²≈0.01), theme_profile + area carry the signal; set is incomplete (~36% of
   motif-similarity, big cross-continental residual); 12/11 granularity is right.
2. **M33 · Alternative-tree test ✓ done** — at continental resolution the genetic tree ≈ area
   (geographic join), so this is really a **language-vs-geography** contrast, not an independent
   genetic axis; leverage is only in the disagreement — the **language-only** bucket = the
   cross-continental families (IE, Altaic) proves linguistic transmission is real & area-independent.
   Wired the genetic join for M36. A true third axis needs fine SNP + the M34/M35 corridors.
3. **M34 · Landscape permeability ✓ done — gate NOT passed.** Coarse resistance-distance does
   **not** beat great-circle out of sample (held-out R² 0.158 vs 0.086; adds nothing to distance)
   → the connectivity-*geometry* upgrade is unwarranted, M38 keeps great-circle. A fine GIS raster
   is the only way to reopen it.
4. **M35 · Historical corridors ✓ done — weak but real.** Empire co-membership (historical-basemaps,
   ≥3-area empires) adds little globally (ΔR² +0.011 over distance+area), but the sharp cross-area
   test is positive: traditions in *different* areas sharing an empire share ×2.6 more motifs
   (distance-matched +0.029) — Rome / the Mongol world moved motifs across areas. Scoped to the
   ~32% empire belt (small-scale societies outside) → a narrow dated covariate, not a general axis.
5. **M36 · Admixture back-migration ✓ done — A8 critique confirmed.** Of 836 Africa↔W-Eurasia
   motifs, **43% sit only in the Eurasian-admixed corridor** (N.Africa/Horn/Sahel) → recent
   back-flow, not deep OoA (corridor-fraction 0.60 vs 0.17 for Africa-only, ×3.5). Weakens
   "African substratum = oldest." Confound: corridor = also the Near-East-proximal edge, so
   genetic back-migration ≡ cultural diffusion from distribution alone (both recent, the A8 point).
6. **M37 · Cross-index arbitration ✓ done — findings not a coding artifact.** 48% of motifs are
   corroborated by an independent index (TMI/ATU); crucially corroboration is **theme-blind**
   (cosmology 49% = tales 49%) and **higher for broad motifs** (54% vs 20% narrow) — the findings
   lean on the replicated core. Emits a per-motif confidence weight for M38 (triple 1.0 …
   berezkin-only 0.5). Caveat: the crosswalk is automated, so berezkin-only over-counts (K25
   swan-maiden = missed ATU 400) — an *upper* bound on coding-dependence.
7. **M38 · Joint HPF (capstone) ✓ done.** One Poisson factorization with the a(t) exposure offset
   (+ M37 weights) **de-confounds** (η²(a|component) 0.34 vs naive 0.67, mockup-26 ~0.80) **and
   recovers the 12 macro-areas** (ARI 0.37 vs 0.08) in a single fit — subsuming mockups 16–23.
   Great-circle geometry (M34 gate failed).
8. **M39 · Tradition stratigraphy** — reads M38's stratum back onto traditions (downstream).

Hard edges: **M34 → M35**, **M33 → M36**, everything → **M38 → M39**. Detailed specs follow, in
build order (the tier headings below are a *significance* overlay, orthogonal to the number).

### M32 · Facet adequacy & orthogonality (audits assumption #6) — ✓ done (mockup 32)

**Result.** On 910 traditions carrying all four facets: **not orthogonal** (V(area,family)=0.73,
V(area,sub)=0.59, V(family,sub)=0.52); **unique Δ R²** = theme_profile 0.125, area 0.076,
subsistence 0.015, family 0.013 (full R²=0.36, Mantel p=0.01) → all non-zero but **family &
subsistence nearly redundant**, theme_profile + area load-bearing; **adequacy** — facets recover
only ~36% of motif-similarity (block ARI = continuous R² = 0.36), a large ~64% **cross-continental
convergence residual** = the set is *incomplete* (the missing axis M34/M35 target); **granularity**
— 12 areas / 11 families beat coarser and finer (which overfit held-out attestation). Spec below.

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

**Why build it first (M32).** It is the cheapest way to audit the entity model itself —
everything downstream slices by these facets, so knowing which are redundant, whether one is
missing, and at what granularity hardens the foundation before the heavier connectivity and
dating work. It also feeds directly into the joint model (**M38**): the unique-contribution
result tells that model which facets to keep as fixed effects.

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
- **M28 · Likelihood ASR (Mk / Dollo). ✓ done + dated re-run** (mockup 28). 2-state gain/loss
  CTMC with marginal ASR (inside/outside), Dollo loss bias (loss≈8×gain). **Result:** on the
  *undated* tree it reproduces parsimony (`corr=0.91`); the **M30-dated re-run** (family-scaled
  branches, `P(t)=expm(Q·t)`) turns family ceilings into **node origin ages** for the 778
  concentrated motifs (conc≥0.5, median ≈1833 BP, all *below* their family root — e.g. B4 1733 vs
  5200 BP). Honest limit: a tree-only ASR dates the inherited *core* but is blind to the areal
  tail (low-conc K25/A3 get only their proto-IE sliver age) — the conflation M34 / M19 resolve. · **M**
- **M29 · Motif content × stratum (BGE-M3). ✓ done** (mockup 29). **Result:** content predicts
  theme strongly (nearest-by-meaning share theme group 58% vs 20% chance) but depth only weakly
  (breadth corr 0.28) — confirms stratum is distributional, not semantic. The content-banality
  idea is an honest negative (flags near-duplicates, not homoplasy). · **M**

## Tier 3 — new capability via external data (highest ceiling)

Heavier (download + join), but each opens a class of conclusion we cannot reach now.

- **M30 · Dated-phylogeny wiring. ✓ done** (mockup 30). Wired Glottolog (coordinate join,
  median 53 km → family + glottocode) + a curated family-expansion-date table. **Result:**
  **451 descent motifs get a calendar age** (Indo-European ~5500 BP märchen belt; B4 →
  ~5200 BP Austronesian); the areal majority is correctly left undated. Family resolution —
  node-level Bayesian ages are M31, which needs the glottocodes this mockup attaches. The join is
  built name-first (`build_join.py`, fixing wrong-neighbour matches; name-agreement 14%→29%) and
  the family-date table expanded to 45 families (dated-family coverage 68%→85% of traditions,
  +12 dated motifs — a data-hygiene upgrade that left every existing age unchanged). · **L**
- **M31 · Bayesian phylogeography. ✓ done** (mockup 31). Reconstructs each dated descent
  motif's **origin location + age** (spherical family-foothold centroid + mockup-30 family-date
  ceiling) and maps its spread. **Result:** 451 origins coloured by age, dense at the
  Indo-European märchen belt ~5500 BP; B4 centred in Western Oceania ≤5200 BP with Pacific
  spread lines. The map **re-centres on the selected motif's region** (central meridian =
  circular-mean longitude) so a Pacific-diffusion motif like B4 reads as **circum-Pacific**
  rather than split by the Atlantic seam. A family-resolution point estimate — node-consistent
  RRW with uncertainty (real BEAST on a dated tree) stays future work. The etiology-stage
  visual capstone. · **L**
- **M33 · Alternative-tree test (genetics). ✓ done** (mockup 33). Re-ran descent detection
  (chance-corrected Fitch, as mockups 18 / 28) on a **curated consensus genetic tree**
  (continental resolution, geography-joined) vs the language tree. **Honest caveat:** at
  continental resolution the genetic tree is built from `area`, so genetic ≈ geography and both
  correlate with family (V=0.73) — this is really the **language-vs-geography** contrast (Method
  B vs A), not an independent genetic axis. The modes separate **only where the classifications
  disagree**; the correlated core (`both`, 905) is *confounded*, not validated, so the 89% "robust"
  is largely tautological. **Real result (the off-diagonal):** the **language-only** bucket is
  non-empty and is exactly the cross-continental families (**Indo-European 68, Altaic 23**) →
  *linguistic transmission is real and not reducible to area*; **genetic-only** = areal diffusion.
  A true third axis needs fine SNP genetics + the M34/M35 corridors. Wires the join for **M36**. · **M**

- **M34 · Landscape permeability / cost-distance geography. ✓ done — gate NOT passed** (mockup 34).
  Built a coarse procedural friction surface (land/sea from the committed coastline + ice + two
  ranges; three a-priori sea regimes) and Dijkstra least-cost distance. **Result:** across all
  three regimes **great-circle beats resistance-distance out of sample** (held-out R² 0.158 vs
  realistic 0.086 / maritime 0.110 / terrestrial 0.058; great-circle+resistance = 0.158, i.e.
  resistance adds nothing). Either isolation-by-distance dominates at this scale or the coarse
  friction is inadequate — indistinguishable without a fine GIS raster. **The gate does not
  license replacing great-circle**, so the connectivity-geometry upgrade for M38 is unwarranted
  (a clean negative, exactly the gate's job). Spec below. · *data: external* · **Effort: L.**
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
  - **Caveats.** Milder anachronism than M35 (physical geography is Holocene-stable, so this is
    valid *deep*) — but sea level (Beringia, Sunda / Sahul shelves) and vegetation (green Sahara
    ~6000 BP) shifted, so the deepest questions want a **time-sliced** surface (paleo-coastlines,
    ICE-6G); a single Holocene surface is the first cut. Friction weights are free parameters —
    **calibrate on known cases** (steppe transmissions, Austronesian sea routes) or fit them to
    the language-family structure, never tune to the target result.
  - **Why it sits first among the two.** It upgrades the *baseline* Method A that everything
    downstream uses, its data is cleaner and more complete than the historical layer, and it is
    the physical substrate on which M35's human corridors ride. **Build M34 before M35.**

- **M35 · Historical connectivity layer (empires + trade routes). ✓ done — weak but real** (mockup
  35). The **human, dated** channel: co-membership of a multi-area empire (historical-basemaps,
  4 pre-colonial snapshots). **Result:** only ~32% of traditions were ever in a real empire
  (Old-World/Mongol-belt biased — small-scale societies outside); empire co-membership adds little
  globally (ΔR² +0.011 over distance+area), **but** the cross-area test is positive — traditions in
  *different* macro-areas sharing an empire share **×2.6** more motifs (distance-matched +0.029),
  so Rome/the Mongol world really carried motifs across area boundaries. A narrow dated covariate
  for the empire belt, not a general axis. Trade routes (OWTRAD) not yet wired. · *data: external*
  · **Effort: M–L.**
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
    **Directionality** — the historical-corridor counterpart to M36's genetic back-migration test
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

- **M36 · Admixture-graph back-migration (genetics). ✓ done — A8 critique confirmed** (mockup 36).
  Took the documented Eurasian→Africa back-migration edges (coarse settled geno-geography) and
  read **direction** off each motif's within-Africa footprint (deep un-admixed reservoir vs the
  Eurasian-admixed N.Africa/Horn/Sahel corridor). **Result:** of 836 Africa↔W-Eurasia motifs,
  **43% are corridor-only back-migration candidates** (corridor-fraction 0.60 vs 0.17 for
  Africa-only motifs, ×3.5) → a large slice of the "African substratum" is recent back-flow, not
  deep OoA, **weakening axiom A8**. Honest confound: the admixed corridor is also the
  Near-East-proximal edge, so genetic back-migration is indistinguishable from cultural diffusion
  from distribution alone (both recent). A fine SNP graph (HGDP/SGDP) is the mechanistic upgrade. ·
  *data: external* · **depends on M33** · **Effort: M–L.**
  - **Substrate — the fine SNP tree lives here, not as its own mockup.** M33 used a *continental*
    consensus tree (built from `area`, so genetic ≈ geography). The genuinely de-confounding step
    is a **fine SNP-based population tree** — a published NJ-on-Fst / TreeMix topology or an Fst
    matrix over ~50–130 populations (**HGDP**, **SGDP**, or the **AADR**; population-level summary
    data, not raw genomes, so a small download), joined to traditions by coordinates + name. A bare
    finer tree still joins geographically, so it does **not** by itself remove the area confound —
    its payoff is precisely the **admixture edges** below, which is why the SNP tree is folded in
    here rather than getting a separate number.
  - **Why its own mockup.** M33 is a *swap-and-rerun* on our existing tree machinery (Fitch / Mk
    on a swapped tree); this needs genuine **reticulate-network inference** — ASR on a graph with
    gene-flow edges, a different and heavier method — so bundling the two violated the
    one-question-per-mockup discipline that kept M24 / M25 clean.
  - **Tests alt-hypothesis #6 ("Africa is a sink").** Is an Africa↔Eurasia motif **deep
    out-of-Africa** or **recent back-into-Africa**? It recovers **direction, not just span** — the
    concrete challenge to axiom A8. The same directional claim is tested independently by **M35**
    through *dated human corridors*; M36 is its **genetic** counterpart, so a motif flagged
    back-migratory by both channels is strongly corroborated.

## Tier 4 — synthesis & product

- **M37 · Cross-index arbitration (TMI / ATU vote). ✓ done** (mockup 37). Used the BZ↔TMI↔ATU
  crosswalk as replication → a per-motif confidence weight (triple / strong / moderate /
  berezkin-only). **Result:** 48% corroborated by an independent index; **corroboration is
  theme-blind** (cosmology 49% = tales 49%) and **higher for broad motifs** (54% vs 20% narrow) →
  the findings are **not artifacts of Berezkin's coding**, they lean on the replicated core.
  Emits the observation multiplier M38 can use. Caveat: the crosswalk is automated (title/doc
  similarity), so berezkin-only over-counts (K25 swan-maiden's ATU 400 was missed) — an upper
  bound on coding-dependence. · *data: partly have* · **M**
- **M38 · Joint effort-corrected factorization (Hierarchical Poisson) — the capstone. ✓ done**
  (mockup 38). Poisson factorization of the tradition×motif presence matrix with `a(t)` as an
  **exposure offset** (+ M37 confidence as motif weights). **Result:** in one fit it
  **de-confounds** — η²(log a | component) **0.34** vs naive KMeans 0.67 (mockup-26 naive ~0.80) —
  **and recovers geography** — ARI(component, area) **0.37** vs naive 0.08: the 12 emergent
  components are the 12 macro-areas, each with a theme profile, **subsuming mockups 16–23**. Built
  on the settled inputs — facets (M32), tree/direction (M33/M36), empire covariate (M35), weights
  (M37); **geometry stays great-circle** (M34's gate failed). Honest limit: MAP/NMF core, not full
  Bayesian HPF with uncertainty; areal signal > thematic (theme cross-cuts area). · *data: have* · **L**
- **M39 · Tradition stratigraphy.** Turn `stratum` around — profile each *tradition* as its
  stack of strata (share of African-substratum … colonial motifs), a geological-column view. ·
  *depends: a trusted stratum from M38 (and M24/M27)* · **checks:** deep-substrate-rich traditions
  should cluster in refugia / early-peopled regions — a strong falsification surface. · **S–M**

## The critical path

If only three get built: **M24** (kill the sampling doubt) → **M25** (kill the Galton doubt)
→ **M30 + M31** (absolute dating + reconstruction). The first two make the existing findings
trustworthy; the last two make them *datable*. Everything in Tier 2 is a quality upgrade that
can slot in whenever, and **M38** is the long-horizon consolidation once M24/M25 have proven the
signals are worth one joint model.

The **connectivity line** was gated behind M34's single falsifiable test (does resistance-distance
beat great-circle out of sample?). **M34 returned a clean negative** — coarse resistance does not
beat distance and adds nothing to it — so the physical-geometry upgrade is **off** (M38 keeps
great-circle), exactly the outcome the gate was meant to catch cheaply. **M35** (dated human
corridors) survives as a *distinct* mechanism — corridor co-membership as a covariate, not a
distance metric — but at lowered priority; the resistance-geometry question reopens only with a
fine GIS friction raster.
