# 17 · Motif depth-score

A first prototype of **Method A** from
[`stratum-derivation.md`](../../docs/motifs/proposals/stratum-derivation.md): estimate a
motif's time-depth from the **shape of its areal distribution alone**, with no Berezkin
stratum labels.

Per motif (≥3 attesting traditions) it computes distributional features — `n_trad`,
`n_macro` (macro-areas), `n_lang` (top-level language families), `spread` (mean
great-circle distance to the centroid), `fragments` (DBSCAN spatial components),
`set_span` (Continental / Indo-Pacific / New-World mega-sets touched), `xindex` (ATU
corroboration) — standardises them, and takes the **first principal component** as a
depth score, oriented so uncontroversial deep anchors (celestial cosmogony, earth-diver,
flood) score higher than shallow ones (Job, Jonah, tar-baby, a jātaka).

## What it shows

- The ranking is sensible: **pan-global celestial cosmogony tops it** (male-sun/female-
  moon, stars-are-people, theft of fire, primeval waters — spanning all 16 macro-areas
  and 50–69 language families); narrow motifs sink.
- **Stress-test passed:** New-World-endemic adventure/trick motifs (absent from Europe)
  score deeper (mean 15.5) than Europe-only ones (12.1) — a naive "theme B = late" rule
  would miss this; the distributional score catches it.

## What it honestly gets wrong (the point of a prototype)

PC1 is dominated by prevalence (corr with `n_macro` = 0.95), so the heuristic conflates
**old** with **widespread**. Two anchors expose it: **A11C** (the thin trans-Pacific
Sun-&-Moon) sinks because it is rare; **the tar-baby** (a broadly diffused *late* tale)
floats up. These are exactly the confounds that motivate the mandatory controls
(attestation-bias correction, disjunction weighting) and the phylogenetic **Method B**.
This mockup is a signal check, not a dating.

## Run

```bash
python mockups/17-motif-depth-score/build_data.py   # writes data.js
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/17-motif-depth-score/
```

`data.js` is git-ignored. Coordinates come from the pipeline; missing ones fall back to
the areal-subregion centroid.
