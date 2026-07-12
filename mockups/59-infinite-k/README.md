# 59 · Infinite-K (a Bayesian-nonparametric latent model)

The fourth Tier-A text-free experiment from
[`synthesis-and-directions.md`](../../docs/proposals/synthesis-and-directions.md). Mockup 47's admixture
cross-validation curve just **plateaus** — there is no clean number of populations K. The principled response
is a model that never fixes K in the first place.

## Method

Fit a **Hierarchical Dirichlet Process** (`gensim.HdpModel`) with traditions as documents and their motif
ids as words. The HDP infers an *unbounded* number of latent components and lets the data decide how much
weight each carries. We read off:

- **effective K** — components covering 90% of the mass, and components with ≥ 1% each;
- the **shape of the component-weight decay** (the real object of interest);
- each surviving component's top motifs and dominant macro-areas.

Deterministic (fixed `random_state`, truncation T = 150).

## What it shows

- **Effective K ≈ 3 (+ a tail).** Three components hold ~90% of the mass (weights ≈ 0.38 / 0.30 / 0.25),
  then a smooth low tail with **no elbow**. The model is free to use 150 components and declines to — but it
  also declines to snap to a clean count. That flat tail *is* the formalisation of mockup 47's "no natural K."
- **The components are the familiar blocks, not a hidden partition.** Component 1 (~38%) is Old-World
  tale-type material (SW/Central Asia, W Europe, Sub-Saharan Africa); component 2 (~30%) is
  cosmology/sun-and-moon weighted to the Americas and SE Asia; component 3 (~25%) is New-World cosmogony
  plus the shared long tail. Nothing carves the corpus more finely than geography and theme already do.

The bar chart shows the sorted stick-weights (blue = the three mass-bearing components, amber = the tail);
the cards show each component's top motifs and where its traditions sit.

## Honest limits

HDP on **binary bag-of-motifs** inherits every confound the rest of the project has: the components track
sampling density and areal blocks (results 1–2), not latent "mythologies." The effective-K count is
sensitive to the concentration hyperparameters (α, γ fixed at 1) and the truncation T; the robust reading is
the *shape* (few big + long tail), not the exact "3." This is a description of the weight geometry, not a
discovery of populations.

`build_data.py` builds the gensim corpus, fits the HDP, ranks components by corpus-level mass, and writes
`data.js`.
