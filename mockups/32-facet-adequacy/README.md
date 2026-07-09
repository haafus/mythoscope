# 32 · Facet adequacy & orthogonality (roadmap M32)

Audits **assumption #6** of the entity model (`macro-area-facets.md`): that
`area · family · subsistence · theme_profile` are the *right* and *~orthogonal* set of
tradition facets. Orthogonality is already falsified (the categorical axes co-track one
peopling history), so this mockup audits the two claims that actually matter —
**non-redundancy** (does each facet earn its place by a unique contribution?) and **adequacy**
(is the set complete, at the right granularity?) — on the **910 traditions** that carry all four
facets (subsistence joined from D-PLACE ≤ 600 km; ≥ 15 motifs each).

## Four sub-tests

1. **Association** — Cramér's V among {area, family, subsistence} + multivariate η² of
   `theme_profile` by each. **Result:** strong entanglement — V(area,family) = **0.73**,
   V(area,subsistence) = 0.59, V(family,subsistence) = 0.52; η²(theme) = 0.29 / 0.23 / 0.10. Not
   orthogonal; area↔family is the tightest pair.

2. **Unique contribution (the headline)** — drop-one variation partitioning: predict pairwise
   motif-set **Jaccard** from the facets, then from the facets minus X; Δ = R²(all) − R²(all−X).
   **Result:** Δ R² = **theme_profile 0.125**, **area 0.076**, subsistence 0.015, family 0.013
   (full R² = 0.36, Mantel p = 0.01). Every facet is non-zero (all earn a place), but
   **family and subsistence are nearly redundant** — their unique signal is ~0.01, mostly
   absorbed by area + theme. The work is done by `theme_profile` and `area`.

3. **Adequacy / residual** — cluster traditions on Jaccard distance (coverage-robust), measure
   how much of that structure the facets recover (adjusted Rand), cross-checked against the
   continuous MRM R². **Result:** the two agree — block-level ARI(family) = **0.36**, continuous
   R² = **0.36** → facets recover only ~36 % of motif-similarity, a **large ~64 % residual**. The
   least-explained core (n = 415, ~46 %) is **cross-continental** (Sub-Saharan Africa 24 %,
   Europe 22 %, East & SE Asia 16 %, Iran/C/S Asia 14 %) — a deep/areal convergence the facet set
   does not capture. **The set is incomplete → a missing axis**, exactly the one the connectivity
   layers (roadmap M34 / M35) target.

4. **Granularity** — held-out attestation log-likelihood (5-fold) over coarse↔fine facet
   variants. **Result:** `area·12` (ll −0.108) beats both coarser `area·L0·16` (−0.110) and finer
   `area·L1·59` (−0.146); `family·11` (−0.114) beats raw `language·92` (−0.155). Finer resolutions
   **overfit** held-out attestation → **12 areas / 11 families is the right granularity.**

## Reframes assumption #6

From "the four facets are orthogonal and right" to, with numbers: **(orthogonality)** false, V up
to 0.73; **(non-redundancy)** each carries a non-zero unique signal, but family & subsistence are
thin (Δ ≈ 0.01) — theme_profile and area do the work; **(granularity)** adequate at 12 areas / 11
families, finer overfits; **(completeness)** *incomplete* — the facets explain only ~36 % of
motif-similarity, leaving a large cross-continental convergence residual for the connectivity
layers. Feeds the joint model (**M38**): keep area + theme_profile as the load-bearing fixed
effects; family / subsistence are marginal.

## Run

```bash
python mockups/32-facet-adequacy/build_data.py   # writes data.js (~7 s)
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/32-facet-adequacy/
```

`data.js` is git-ignored. Reuses mockup 21's `area_of` / `family_of`, mockup 22's D-PLACE
subsistence snapshot, and the committed `tradition-coords.json`.
