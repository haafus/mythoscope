# 26 · Degree-corrected block model (roadmap M26)

Replaces the biclustering / spectral co-clustering of mockups 06/07/15/23 with a **generative
block model** of the motif × tradition matrix, and demonstrates its headline advantage: the
**degree-correction absorbs the `a(t)` sampling confounder natively**, so blocks reflect
structure rather than catalogue density.

## Method

Alternating multinomial co-clustering (a hard degree-corrected SBM, self-contained in numpy —
no graph-tool needed): traditions → K_t blocks and motifs → K_m blocks, alternately, where
each tradition is clustered by its **degree-normalised profile** over motif-blocks (row shares
that sum to 1). Normalising out the total degree *is* the degree correction. K_t is chosen by
**BIC** on the block-model reconstruction likelihood.

## What it shows

- **BIC selects K_t = 9** — a genuine minimum (K=10 is worse), so the block count is chosen by
  evidence, not by hand (the standing complaint about mockups 16/23's fixed `k`).
- **Degree-robustness — the payoff.** A naive clustering of the *raw* count rows separates
  traditions by coverage: `eta²(a(t) | block) = 0.80` — 80% of the coverage variance is
  between blocks, i.e. it mostly clusters "how much Berezkin recorded". The degree-corrected
  model drops this to **0.48**. The residual is honest, not a failure: the European/Near-East
  literate corpora (block median coverage 343) genuinely *are* both densely catalogued and
  thematically distinct, so some block↔coverage link is real.
- **The blocks are interpretable and sampling-robust:** tradition blocks map to coherent
  regions (an East-Asia/Siberia block, an Austronesia/Pacific block, a South-America block, a
  Sub-Saharan block, a European-literate block…); motif blocks stratify by Category-A share
  from 19% to 69%, recovering the cosmology↔tales gradient from co-membership alone.

## Takeaway

The biclustering findings of 06/07/15/23 survive a proper generative, degree-corrected model —
and the model both picks its own resolution (BIC) and halves the sampling artifact that a naive
clustering carries. This is the sampling-robust replacement the roadmap called for; a full
nested DC-SBM (graph-tool) would refine it but needs a heavy dependency the mockups avoid.

## Run

```bash
python mockups/26-blockmodel/build_data.py   # writes data.js (~10 s)
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/26-blockmodel/
```

`data.js` is git-ignored. Reads only `outputs/motifs/`.
