# 17 · Motif depth-score

A first prototype of **Method A** from
[`stratum-derivation.md`](../../docs/motifs/proposals/stratum-derivation.md): estimate a
motif's time-depth from the **shape of its areal distribution alone**, with no Berezkin
stratum labels.

Per motif (≥3 attesting traditions) it computes distributional features — `n_trad`,
`n_macro` (macro-areas), `n_lang` (top-level language families), `spread` (mean
great-circle distance to the centroid), `fragments` (DBSCAN spatial components),
`set_span` (Continental / Indo-Pacific / New-World mega-sets touched), `xindex` (ATU
corroboration) — standardises them, and produces **two** scores: **PC1** (first
principal component) and a **disjunction-weighted** composite (down-weights raw
prevalence, up-weights cross-clade span + fragmentation), both oriented by
uncontroversial anchors.

## What it shows

- The PC1 top is the **most prevalent motifs** — the swan-maiden (K25) leads, then
  pan-global celestial cosmogony (stars-are-people, male-sun/female-moon, primeval waters,
  theft of fire — spanning all 16 macro-areas and 50–69 language families); narrow motifs
  sink. That the broadly-diffuse swan-maiden tops PC1 is itself the tell (next section).
- **Stress-test passed and amplified:** New-World-endemic adventure/trick motifs
  (absent from Europe) score deeper than Europe-only ones under both scores, and the
  **disjunction weighting nearly triples the gap** (40.6 vs 24.0, up from PC1's 17.5 vs
  11.8) — a naive "theme B = late" rule would miss this entirely.

## What it honestly shows about the method (the point of a prototype)

Neither linear score is "the answer". **PC1 is dominated by prevalence** (corr with
`n_macro` = 0.93), so it conflates *old* with *widespread* — which is why the broadly-
diffuse swan-maiden sits at #1. The disjunction weighting fixes that — but over-corrects:
it penalises prevalence so hard that genuinely broad-**and**-deep motifs collapse
(**K25 swan-maiden 100 → 10**, trickster-coyote 74 → 3) while sparse scattered motifs
float up. A single linear score cannot express
"old = broad **and** cross-clade **and** disjunct" at once — which is exactly the
argument for the model-based **Method B** (phylogenetic ancestral-state reconstruction,
weighing independent gains against node depth), plus the mandatory attestation-bias
control.

Note: an individual motif's breadth ≠ a cluster's deep-time story. The famous
trans-Pacific Sun-&-Moon layer is a property of **cluster 6** (many motifs together);
the single motif A11C is narrowly attested in Berezkin's data, so it correctly scores
low — it was never a good single-motif "deep anchor".

## Run

```bash
python mockups/17-motif-depth-score/build_data.py   # writes data.js
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/17-motif-depth-score/
```

`data.js` is git-ignored. Coordinates come from the committed `tradition-coords.json`
snapshot; missing ones fall back to the areal-subregion centroid.
