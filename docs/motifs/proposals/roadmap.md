# Roadmap — prototypes ranked by significance

The actionable sequencing of [`synthesis-and-directions.md`](synthesis-and-directions.md).
Each item is the next mockup in the series (M24…). Ranked by **significance = (how decisively
it resolves a live doubt or unlocks a new capability) × feasibility**. Tier 1 leads because
it is cheap *and* removes the caveat that currently hangs on every result.

Legend: **effort** S/M/L · **data**: *have* (in `outputs/motifs/` + committed snapshots) or
*external* (needs a download + join).

## Tier 1 — do first: cheap, decisive, no new data

These two together retire the two alternative hypotheses that caveat almost everything.

- **M24 · Effort-correction sweep.** Re-run the count-based mockups (16 theme_profile, 22
  subsistence×theme, 23 lift + co-occurrence) with the §5 attestation-intensity weighting
  already prototyped in mockup 20, and report each finding **before vs after**. · *method:*
  coverage-weighted counts / occupancy weights · *data: have* · **proves:** resolves
  alternative-hypothesis #1 ("it's all sampling") across the board — the single highest
  value-per-effort experiment. · **S**
- **M25 · Galton-corrected association tests (PGLS / PGLMM).** Re-test subsistence×theme,
  theme×area and theme×stratum with the language tree as the covariance structure, so
  neighbours stop counting as independent samples. · *method:* phylogenetic mixed model ·
  *data: have* (tree from mockup 18) · **proves:** the gradients are real, not
  autocorrelation + area — the rigorous form of the "within-area partial correlation" we keep
  promising. · **S–M**

## Tier 2 — strong method upgrades on data we already have

Each replaces a descriptive heuristic with a generative model; medium effort, high payoff.

- **M26 · Degree-corrected bipartite SBM.** Replace k-means / spectral co-clustering (16, 23)
  and biclustering (06/07/15) with a stochastic block model that picks the block count by
  evidence and whose **degree-correction absorbs the `a(t)` confounder natively**. · *data:
  have* · **unlocks:** principled, sampling-robust co-clusters; one model subsumes several. ·
  **M**
- **M27 · Descent–areal–reinvention mixture per motif (EM).** Replace mockup 19's binary gate
  with a per-motif **inherited-share ∈ [0,1]** — a mixture of tree-inherited, areal-diffused
  and reinvented components. · *data: have* · **tests:** alternative-hypothesis #2 ("stratum
  isn't one axis"); may dissolve the A3-vs-K25 residual into "60% substrate / 40% diffusion".
  · **M**
- **M28 · Likelihood ASR (Mk / Dollo + rate heterogeneity).** Upgrade Method B (18) from Fitch
  parsimony to a continuous-time gain/loss model with a loss bias and across-motif rate
  variation. · *data: have* · **refines:** marginal ancestral *probabilities* and a principled
  homoplasy estimate instead of a hard gain count. · **M**
- **M29 · Motif content × stratum (BGE-M3).** Cross the semantic embeddings from the
  morphology stage with the computed `stratum`: do *content*-similar motifs share depth? ·
  *data: have* (embeddings already built) · **adds:** an independent (content) signal to the
  distributional one, plus a principled **banality** measure (minimally-counter-intuitive /
  generic definitions) to replace mockup 20's crude proxy. · **M**

## Tier 3 — new capability via external data (highest ceiling)

Heavier (download + join), but each opens a class of conclusion we cannot reach now.

- **M30 · Dated-phylogeny wiring (Glottolog CLDF + Bouckaert/EDGE).** Join traditions →
  Glottocodes, attach node dates. · *data: external* · **unlocks:** `stratum` becomes an
  **absolute age**, not an ordinal mode; external validation against published phylomemetic
  dates. Dependency for M31. · **L**
- **M31 · Bayesian phylogeography (relaxed random walk).** On the dated tree, jointly
  reconstruct each deep motif's **ancestral location and age**, and animate its spread over the
  peopling map. · *depends: M30* · **unlocks:** the etiology-stage visual capstone; dates space
  and tree together with real uncertainty. · **L**
- **M32 · Alternative-tree test (genetics).** Re-run descent detection on a
  genetic/admixture tree instead of the language tree. · *data: external* · **tests:**
  alternative-hypothesis #3 ("wrong tree, not rare descent") — is descent really ~1%, or just
  ~1% *along language*? · **M–L**

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
