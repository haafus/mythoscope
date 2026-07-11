# 47 · Admixture

The proper population-genetics **admixture / STRUCTURE** model fit to the tradition × motif matrix — the
principled version of the soft factors in mockups 45 (NMF, M38 Poisson). Follows directly from the
[migration-surface](../46-migration-surface/README.md) result that the corpus behaves like an
isolation-by-distance landscape.

## The model

Each presence is generated as **X[t,m] ~ Bernoulli( Σₖ Q[t,k]·P[k,m] )**, where **Q** (row-stochastic) is a
tradition's *ancestry proportions* over **K latent motif-pools** and **P[k,m] ∈ [0,1]** is pool k's frequency
for motif m. Fit by **exact EM** (monotone in the Bernoulli likelihood). This is the same generative model
ADMIXTURE/STRUCTURE use on genotypes, applied to motif "alleles".

## What it shows

- **Choosing K by cross-validation.** A random 12% of matrix entries are held out; the model is fit on the
  rest for K = 2…11 (3 folds averaged) and scored by held-out Bernoulli deviance — exactly ADMIXTURE's CV.
  The curve **drops steeply to K ≈ 5 then plateaus** (K6 = K7, K8 rises, later gains within ±0.002 CV noise):
  there is **no sharp optimum**. That flatness *is* the result — admixture finds **no discrete K**, the
  signature of a **clinal** continuum of mixtures rather than K real populations. The knee (**K = 5**) is used
  for display.
- **Admixture structure plot.** The classic STRUCTURE barplot: ~950 vertical bars (traditions, grouped by
  macro-area), each a stack of its K pool proportions. **Very few bars are one colour** — most traditions are
  genuinely admixed, again the clinal hallmark.
- **Dominant-pool map.** Each tradition coloured by its argmax pool, opacity = assignment confidence — a
  smooth geographic gradient (New-World hero/thunderbird pool over N America, celestial-cosmogony pool
  scattered, European-märchen pool over Europe, trickster pool over Africa), not crisp territories.
- **The K dated pools.** Each pool ordered deep→shallow by the **M17 disjunction depth** of its motifs, with
  its top motifs (by pool frequency × over-representation), continents, and per-motif M17 depth. The dated
  pools recover the familiar layering: deep New-World/celestial cosmogony (M17 ≈ 75–77) → mid Eurasian/African
  cosmogony (≈ 70) → African/Eurasian trickster (≈ 51) → shallow European ATU märchen (≈ 32).

## Why it matters — and its honest limit

This replaces mockup 45's ad-hoc `k = 6` with a **principled, uncertainty-aware, CV-selected** soft-factor
model on the correct (Bernoulli) likelihood, and the pools cross-read cleanly against the M38 factors and the
worldview strata. The headline finding is *negative and honest*: the CV curve's **plateau confirms there is
no natural K** — consistent with everything else (clinal geography, weak silhouettes, moderate F<sub>st</sub>).

**Descriptive, not demographic.** The drift null is analogical (horizontal, biased transmission; no
recombination). Crucially there is **no admixture-LD clock** — genetics dates admixture from recombination ×
generations, which has no cultural analog — so the pool ordering here is the **M17 disjunction proxy**, not a
calibrated age.

## Data

`build_data.py` builds the binary matrix (traditions ≥ 15 motifs with a coordinate), runs 3-fold CV over
K = 2…11, picks the knee, fits the final EM at K\*, orders pools by M17 depth, and emits the CV curve, the
per-tradition Q, the macro-area-grouped structure order, the dominant-pool points and the dated pool
signatures. Deterministic (seeded); writes `data.js` (~2 min).

## Run

```bash
python mockups/47-admixture/build_data.py      # writes data.js (~2 min: CV is the cost)
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/47-admixture/
```
