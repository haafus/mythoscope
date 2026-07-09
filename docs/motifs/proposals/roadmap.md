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
