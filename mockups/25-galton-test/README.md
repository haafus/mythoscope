# 25 · Galton-corrected test (roadmap M25)

Puts a number on the caveat we kept writing by hand: the `subsistence × theme` gradient
(mockup 22 — foragers cosmology-heavy, agrarian-states tale-heavy) could be **neighbour
autocorrelation** (Galton's problem) or just **`area × theme`**, not a subsistence effect.

## Method — restricted permutation

The statistic is `eta²` of a tradition's Category-A (cosmology) share explained by its 4-way
subsistence (observed **0.187**, a **+17.4 pp** extractive-minus-intensive gap). It is
compared to nulls that shuffle the subsistence label only *within strata*, holding that
stratum's structure fixed:

| null | shuffles within | controls | p |
|---|---|---|---|
| free | everything | nothing (the naive test) | **0.000** |
| within-area | each macro-area | the area confound | **0.003** |
| within-family | each language family | shared ancestry (Galton) | **0.006** |
| within-both | each area × family cell | both (low power) | 0.065 |

## Result — the signal is real beyond area *and* beyond ancestry, individually

Survives control for **area** (p=0.003) and for **language family / Galton** (p=0.006), so it
is neither purely `area × theme` nor purely neighbour autocorrelation. Controlling **both** at
once it attenuates to marginal (p=0.065) — but that test has sharply lower power (33 strata
over 659 traditions, many thin cells), so this is *weakened*, not *killed*. Verdict:
**subsistence carries its own contribution to thematic balance, partly entangled with
geography** — which retires the hand-waved "area confound" on mockup 22 with an actual test.

Family here is a coarse (family-level) phylogenetic control; a proper dated-tree PGLS (M30/M31)
would tighten it, but the restricted-permutation result already answers the first-order doubt.

## Run

```bash
python mockups/25-galton-test/build_data.py   # writes data.js (~10 s, 3000 permutations)
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/25-galton-test/
```

`data.js` is git-ignored. Reads only `outputs/motifs/` + the committed D-PLACE derivative.
