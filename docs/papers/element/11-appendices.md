# Appendices

*Computational Comparative Mythology: A Natural History of the Motif — Back matter. Draft.*

---

## Appendix A · The three-entity data model

The whole analysis rests on a deliberately small schema of three entities, with one — and only one —
inferred field.

- **Tradition** — a people with a mythological corpus. *Given or deterministic* facets: macro-area (one
  of twelve), language or religious family, subsistence economy (one of four), thematic profile,
  coordinates, and attestation richness a(t) — the number of motifs recorded for it.
- **Motif** — a portable narrative unit. Fields: definition, cross-catalogue links, theme, and
  `stratum` — its inferred time-depth and mode of spread. `stratum` is the **only** inferred field in
  the model; it is always a hypothesis carrying a confidence, never a recorded fact.
- **Attestation** — the presence of a motif in a tradition. This is the observed raw material from which
  `stratum` is computed; it is never itself inferred.

The one discipline the schema enforces is the separation of the *given* from the *inferred* (Chapter 3):
attestation is observed, tradition facets are given, and stratum alone is estimated — so that
uncertainty is never quietly lost by letting a computed quantity pass downstream as if it were data.

## Appendix B · The cross-catalogue link methodology

The crosswalk connects a motif in one catalogue to its counterpart in another on **graded evidence**,
not a single criterion. An edge is drawn when two motifs share a defining constituent, when their
definitions align, when a note or summary in one points to the other, or when they cite a common source;
each edge records which kind of evidence justifies it. Accumulating these yields **7,274 confirmed
edges** across Thompson's *Motif-Index*, the Aarne–Thompson–Uther type index, and Berezkin's catalogue,
with an inferred-triangle layer extending the confirmed core.

Two properties matter for the analyses. First, the link set is **reused as independent corroboration**:
a motif whose finding is echoed by a linked motif in another catalogue is weighted up as replicated;
one that stands alone is flagged as resting on a single coder's judgement. Second, the link set is
**incomplete and it undercounts** — it is partly automated, and real correspondences are missed (the
swan-maiden's ATU 400 among them). The direction of the error is therefore known and must be stated:
cross-catalogue corroboration is a *lower* bound on true agreement, and any single-catalogue result is
an *upper* bound on how much depends on one catalogue's coding.

## Appendix C · Methods reference

- **The depth score (Method A).** A motif's time-depth is scored from the shape of its areal footprint —
  prevalence, geographic spread, spatial fragmentation, language-family span, and, weighted most
  heavily, the number of separate continental "mega-sets" it touches. Every feature is oriented toward
  antiquity by the rule that cross-continental *disjunction* outranks mere breadth. The score is a
  hypothesis with a confidence, and it conflates ancient descent with wide diffusion by construction —
  a limit inseparable from the proxy.
- **The phylogenetic estimator (Method B).** Each motif is placed on the language-classification tree
  and its history of gains and losses reconstructed by parsimony, upgraded to a two-state gain/loss
  model with marginal reconstruction. The **phylogenetic signal** — observed clustering against a
  label-permuted null — separates descent (clustered) from diffusion (scattered). Theme is excluded
  from the estimation so it can serve as an independent cross-check.
- **De-confounding.** Attestation intensity a(t) is carried throughout — as coverage weights, as a
  degree-correction in the block model, and as an exposure offset in the joint Poisson factorization; a
  banality proxy flags likely reinvention; restricted permutation (shuffling labels only within strata)
  controls Galton's problem; cross-catalogue replication guards against single-catalogue artefacts.
- **Falsifiable gates.** A candidate upgrade must beat the incumbent *out of sample* before adoption,
  and a clean negative is reported rather than buried (Chapter 7's landscape model is the worked case).

## Appendix D · Reproducibility

Every figure in the book is a static render of a self-contained prototype that reads only the assembled
corpus and the committed external joins, with fixed random seeds. The map from figure to prototype:

| Figure(s) | Source prototype |
|---|---|
| 4.1 crosswalk graph | 01 · crosswalk-graph |
| 4.2 retrieval recall@k | 02/04 · semantic-parallels; 10 · embedding-eval |
| 4.3 corpus overview; 4.4 a(t) | 13/14 · corpus-overview |
| 5.1–5.2 co-clustering, block model | 26 · blockmodel (with 06/07, 15) |
| 5.3 facet adequacy | 32 · facet-adequacy (with 21) |
| 5.4 subsistence gradient | 22 · subsistence; 25 · galton-test |
| 5.5 theme × area | 23 · theme-geography |
| 6.1 depth score | 17 · motif-depth-score |
| 6.2 phylogenetic signal | 18 · phylostrata (with 19) |
| 6.3–6.4 mixture, A3 vs K25 | 27 · mixture |
| 6.5 substrate under controls | 20 · stratum-controls (with 37) |
| 6.6 content vs age | 29 · content-stratum |
| 6.7 dating; 9.3 spread | 30 · dated-phylogeny; 31 · phylogeography |
| 6.8 tradition stratigraphy | 39 · tradition-stratigraphy |
| 7.1 joint factorization | 38 · joint-hpf |
| 7.2 landscape gate | 34 · landscape-permeability |
| 7.3 empires | 35 · historical-corridors |
| 7.4 back-migration | 36 · admixture-backmigration |
| 8.1 UMAP re-derivation | 41 · theme-rederivation |
| 8.2 facet showdown | 42 · facet-showdown |
| 8.3 worldview clusters | 43 · narrative-tradition-profiles |
| 8.4 catch-all depth | 44 · narrative-stratum |
| 9.1–9.2 case-study maps | 40 · motif-map-explorer |

New diagrams (not from a prototype): Figs 1.1 (transmission modes), 2.1 (field timeline), 3.1
(dependency arc), 3.2 (entity model), 10.1 (residual map), and Table 2.1 (datasets).

The derived data (the narrative taxonomy, the crosswalk edges, the external joins, the depth metrics)
and the code are released under open licences with citable DOIs; original authors of all source data
are cited. Full per-figure method is documented in each prototype's own notes.
