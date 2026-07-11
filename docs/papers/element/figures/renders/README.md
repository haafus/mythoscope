# Rendered figures — first pass

Static renders of the analysis prototypes, screenshotted from the committed `mockups/*/index.html`
(with their committed `data.js`) via headless Chromium. Every figure shows real data matching the
numbers in the chapters.

**Status.** The interactive prototypes are authored in Russian; these renders translate them to English.
- **Fully English (UI + data): 19 figures** — fig-4-3, 5-3, 5-4a, 5-5, 6-1, 6-2, 6-3-6-4, 6-5, 6-6, 6-7,
  6-8, 7-1, 7-2, 7-3, 7-4, 9-3, plus the manual 5-1-5-2 — and the 5 conceptual diagrams. These carry
  English motif names (from `berezkin.json`) and are book-ready (modulo cropping).
- **English UI, residual Russian in the DATA LAYER: 8 figures** — fig-4-1 (01), fig-4-2 (04),
  fig-9-1 (40): individual Berezkin motif *names*; fig-8-1 (41), fig-8-3 (43), fig-8-4 (44): theme /
  narrative-cluster names; fig-5-4b (25), fig-8-2 (42): a few legend labels. These come from each
  mockup's `data.js` (not the UI), so the final fix is to remap the Berezkin names to their English
  `berezkin.json` equivalents (by motif id) and translate the fixed theme/cluster label set, then
  re-render. Tracked as a remaining production step.
- All are full-window captures and several need **cropping** to the relevant panel for final layout.

| File | Prototype | Figure(s) | Chapter |
|---|---|---|---|
| fig-4-1 | 01-crosswalk-graph | 4.1 crosswalk graph | 4 |
| fig-4-2 | 04-semantic-parallels-bge | 4.2 retrieval | 4 |
| fig-4-3 | 13-corpus-overview | 4.3 corpus overview | 4 |
| fig-5-1-5-2 | 26-blockmodel | 5.1–5.2 co-clustering, block model | 5 |
| fig-5-3 | 32-facet-adequacy | 5.3 facet audit | 5 |
| fig-5-4a | 22-subsistence-external | 5.4 subsistence gradient | 5 |
| fig-5-4b | 25-galton-test | 5.4 restricted-permutation controls | 5 |
| fig-5-5 | 23-theme-geography | 5.5 theme × area | 5 |
| fig-6-1 | 17-motif-depth-score | 6.1 depth score | 6 |
| fig-6-2 | 18-motif-phylostrata | 6.2 phylogenetic signal | 6 |
| fig-6-3-6-4 | 27-mixture | 6.3–6.4 mixture, A3 vs K25 | 6 |
| fig-6-5 | 20-stratum-controls | 6.5 substrate under controls | 6 |
| fig-6-6 | 29-content-stratum | 6.6 content vs age | 6 |
| fig-6-7 | 30-dated-phylogeny | 6.7 dating | 6 |
| fig-6-8 | 39-tradition-stratigraphy | 6.8 stratigraphy | 6 |
| fig-7-1 | 38-joint-hpf | 7.1 joint factorization | 7 |
| fig-7-2 | 34-landscape-permeability | 7.2 landscape gate | 7 |
| fig-7-3 | 35-historical-corridors | 7.3 empires | 7 |
| fig-7-4 | 36-admixture-backmigration | 7.4 back-migration | 7 |
| fig-8-1 | 41-theme-rederivation | 8.1 UMAP re-derivation | 8 |
| fig-8-2 | 42-facet-showdown | 8.2 facet showdown | 8 |
| fig-8-3 | 43-narrative-tradition-profiles | 8.3 worldview clusters | 8 |
| fig-8-4 | 44-narrative-stratum | 8.4 catch-all depth | 8 |
| fig-9-1 | 40-motif-map-explorer | 9.1–9.2 case-study maps | 9 |
| fig-9-3 | 31-phylogeography | 9.3 fished-up earth | 9 |

New conceptual diagrams (Figs 1.1, 2.1, 3.1, 3.2, 10.1) and Table 2.1 are in the parent `figures/`.
