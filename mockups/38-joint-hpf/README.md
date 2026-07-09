# 38 · Joint effort-corrected factorization — the capstone (roadmap M38)

The **one model** of `synthesis-and-directions.md` §3, replacing the mockup 16–23 pipeline with a
single fit: a **Poisson factorization** of the tradition×motif presence matrix `P` with the
attestation intensity **a(t) as an exposure offset**, so the latent factors are the emergent
area/theme components **de-confounded from sampling**. Motifs are down-weighted by their **M37**
cross-index confidence, so coding-dependent motifs pull the factors less.

```
P[t,m] ~ Poisson( a(t) · (W H)[t,m] ),   W ≥ 0 (T×K),  H ≥ 0 (K×M)
```

Fit by weighted-KL multiplicative updates (the MAP / NMF core of Hierarchical Poisson
Factorization). Each tradition's renormalised row of `W` is its de-confounded mixture over K
emergent components; `H[k,·]` is component k's motif profile.

## What it shows (one fit subsumes 16–23)

- **De-confounding works.** η²(log a(t) | component) = **0.34** for the offset factorization vs
  **0.67** for naive KMeans on the same matrix (and the ~0.80 naive clustering carried in mockup
  26). The exposure offset removes most of the coverage that dominated raw clustering.
- **And it recovers geography — simultaneously.** ARI(component, macro-area) = **0.37** vs **0.08**
  for naive KMeans. Naive clustering lumps well-catalogued traditions; the de-confounded
  factorization recovers the real 12 macro-areas (mockups 16–19).
- **The 12 emergent components = the 12 macro-areas**, each with a **theme profile** (mockup 23):
  a New-World component (South America + N-America + Mesoamerica; Adventures + Cosmogony + theft-of-
  fire), an Austronesian/Oceanian one (K25 swan-maiden, man-in-the-moon), a Sub-Saharan one
  (M29G trickster-hare), an Iran/S-Asian **cosmogony**-heavy one (A12 eclipses, primeval waters),
  Near-Eastern, Siberian (cosmic hunt B42), several European (märchen) — recovered from the data
  with **no** area or theme label given.

## Verdict

The capstone **de-confounds and recovers structure in one model** — area (mockups 16–19), coverage
control (20/24/26) and the theme profile (23) fall out of a single fit, with the M37 confidence
weights, the M33/M36 tree/direction and the M35 empire covariate as settled inputs, and
**great-circle geometry** (M34's resistance-distance gate having failed).

**Honest limits.** This is the **MAP / NMF core** (confidence as observation weights), not the full
Bayesian HPF with Gamma priors and posterior uncertainty. The areal signal is stronger than the
thematic one — most components are Adventures-dominant (the modal group) with a secondary theme —
exactly because theme cross-cuts area (mockup 23). K=12 is chosen to match the macro-areas; a
held-out-likelihood sweep over K is the natural next refinement.

## Run

```bash
python mockups/38-joint-hpf/build_data.py   # writes data.js (~8 s)
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/38-joint-hpf/
```

`data.js` is git-ignored. Reads `outputs/motifs/` (reusing mockup 21's `area_of` and the M37
crosswalk CSVs).
