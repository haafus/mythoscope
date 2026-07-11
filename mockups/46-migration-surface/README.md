# 46 · Migration surface

The tradition × motif presence matrix read as a **landscape-genetics** dataset — the population-genetics
angle from the [stratigraphic-peeling](../../docs/proposals/stratigraphic-peeling.md) discussion made
concrete. Our soft-factor model (mockup 45 · M38 Poisson) is already an *admixture* model; this prototype
adds the three complementary tools genetics uses on the *same* kind of presence matrix.

## What it shows

- **Isolation by distance (Mantel).** Motif Jaccard-dissimilarity vs geographic (haversine) distance over
  all 448 878 tradition pairs: **r = +0.42** (p = 0.003, 299 permutations). The distance-decay curve rises
  smoothly from ~0.89 (neighbours) to a ~0.97 plateau by ~8000 km with **no step** — the textbook signature
  of a **clinal** continuum. This is the quantitative version of the "geography is clinal" result.
- **Areal differentiation (AMOVA / F<sub>st</sub>).** Fraction of motif variance *between* Berezkin's 17
  macro-areas: **F<sub>st</sub> ≈ 0.059** (p = 0.003). Moderate structure — most variance sits *within*
  areas. For scale: human continental F<sub>st</sub> ≈ 0.10–0.15, sub-continental ≈ 0.01–0.03, so
  mythological macro-areas differ about as much as human sub-continental populations. The **pairwise area
  F<sub>st</sub> heatmap** shows *which* areas: the pale low-F<sub>st</sub> Eurasian block (SW/C-Asia–India ·
  W-Europe · Tibet/SE-Asia · East Asia) is the märchen corridor; N&E-Europe and the New-World areas are the
  most isolated.
- **EEMS-lite effective-migration surface.** The isolation-by-distance fit's **residual mapped in space**:
  where similarity decays *faster* than distance predicts = a <span>**barrier**</span> (red, low effective
  migration); *slower* = a <span>**corridor**</span> (blue, high effective migration). Corridors light up
  across the **Eurasian belt** and the northern latitudes; barriers ring the **American** interior/periphery,
  **Sub-Saharan Africa** and **Australia** — exactly the endemic/isolated zones the peeling flagged.
- **Bridges.** The strongest long-range corridors (surprising similarity at > 4000 km) drawn as edges — the
  recognisable diffusion corridors: the **Indo-European / Eurasian tale belt** (SW/C-Asia–India ↔ W-Europe,
  5427 km, the single strongest), the **trans-Saharan** link (Sub-Saharan Africa ↔ W-Europe/N-Africa), and
  the **Austronesian reach** within Oceania (7239 km).

## Why this frame fits — and its honest limit

Our M38 Poisson factorisation *is* an admixture model (Q·P factorisation of a presence matrix), so importing
STRUCTURE/ADMIXTURE, f-statistics, AMOVA and EEMS is a principled upgrade, not a metaphor — and the numbers
here confirm the corpus behaves like an isolation-by-distance landscape (r = 0.42, F<sub>st</sub> = 0.06).

**Descriptive, not demographic.** Cultural transmission is horizontal and biased (borrowing, prestige, no
recombination), so the drift null underlying F<sub>st</sub> / EEMS is only *analogical*. In particular there
is **no admixture-LD clock** here — genetics dates admixture from recombination × generations, which has no
cultural analog; dating stays with the M17 disjunction proxy (mockup 45). What this view adds is **rigour**
(permutation p-values instead of eyeballed silhouettes), the **right generative framing**, and **two strong
visualisations that test existing findings** (the barrier/corridor surface, the bridge network) rather than a
new discovery. The folklore-phylogenetics programme (d'Huy, Tehrani, Berezkin) already uses the *tree* half
of the bio-toolkit; because our geography is **reticulate/clinal**, the *reticulation-aware* half borrowed
here (EEMS, f-stats, admixture graphs) is the more appropriate import.

## Data

`build_data.py` builds the binary matrix from `outputs/motifs/berezkin.json` (traditions with ≥ 15 motifs and
a resolvable coordinate), computes pairwise Jaccard + haversine, the Mantel test and F<sub>st</sub> with
permutation p-values, a binned isolation-by-distance fit and its per-pair residual, the EEMS-lite grid
surface (Gaussian-smoothed residual of local < 3500 km pairs), the pairwise-area F<sub>st</sub> matrix, and
the strongest long-range bridges. Deterministic (seeded permutations); writes `data.js`.

## Run

```bash
python mockups/46-migration-surface/build_data.py      # writes data.js (~20 s)
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/46-migration-surface/
```
