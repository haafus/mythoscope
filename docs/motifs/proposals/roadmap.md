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
> model, stratigraphy, cross-index). This new audit takes the next free number, **M36**
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
  spread lines. A family-resolution point estimate — node-consistent RRW with uncertainty (real
  BEAST on a dated tree) stays future work. The etiology-stage visual capstone. · **L** · *(orig:)* dates space
  and tree together with real uncertainty. · **L**
- **M32 · Alternative-tree / admixture-graph test (genetics).** Re-run descent detection on a
  genetic tree instead of the language tree, and — as a **reticulate admixture graph** —
  carry the published **back-migration** edges (Eurasian gene flow into Africa) as horizontal
  connections. · *data: external* · **tests:** alt-hypothesis #3 ("wrong tree, not rare
  descent") *and* alt-hypothesis #6 ("Africa is a sink"): is an Africa↔Eurasia motif deep
  out-of-Africa or recent back-into-Africa? Direction, not just span. · **M–L**

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
