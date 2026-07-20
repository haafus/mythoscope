# Proposals — index, goals, and status

Design notes and analysis programmes. Each entry states **what it proposes**, **why it is needed** (the goal
it serves), and **where it stands**. "Proposal" = designed, not built; "partly done" = some layer landed;
"validated" = demonstrated in a mockup but not productionised. Spent, shipped, or prototyped-not-wired notes
live under [`archive/`](archive/) (see the **Archived** section below); they are kept for the reasoning trail,
not as live work.

## Active — the science

- [`regions.md`](regions.md) — **the canon**: the definitive **14-region** `region` classification (names,
  descriptions, subdivisions, strata, per-region traditions, intuitive/associative palette — one `color` per
  region). **Goal:** one
  authoritative region vocabulary; where any other doc diverges, this is authoritative. *Canon reference
  (drives `region-implementation.md`).*

## Active — data / architecture (the engineering)

- [`region-implementation.md`](region-implementation.md) — **the code plan** for wiring `region` into
  production after taxonomy/presentation closed: one curated `config/traditions.json` tree (14 region nodes in
  canon order, each with its canon fields + single `color`, holding only texted traditions), `major_tradition`
  renamed+re-partitioned to `region`, region-inherited colour (no random), backend-served grouping, fail-loud
  validation, one `UNASSIGNED`; the motif-index region system and embeddings untouched. Current state with
  file:line + settled decisions + config shape + phased migration. Supersedes
  `tradition-architecture-unified.md` §4/§6. **Goal:** an executable implementation plan. *Proposal; not started.*
- [`data-model-and-ids.md`](data-model-and-ids.md) — how corpus data is split across the three registries
  (tree / documents / embeddings), what is stored where vs resolved via load-once front indexes, and how ids
  are minted: one `slugify(name)→id` (three mint sites), `document_id = slugify(title)` as a single stored key,
  ids minted once and passed as data, the chunk id as a bare PK. Resolves `region-implementation.md` §3's
  document-identity question. **Goal:** a decided data-decomposition & id/join spec. *Proposal; not started.*
- [`pipeline-and-incrementality.md`](pipeline-and-incrementality.md) — the build pipeline as a
  content-addressed DAG: stage/artifact/cache map, fingerprints + per-stage transform versions (why not
  mtime/code-hash), downstream invalidation, deletions via set-reconciliation, GC tiers, the `(id, md5)`
  embeddings key, fetch-vs-build separation, and a unified web+local source model (immutable raw archive +
  override-diff layer). Companion to `data-model-and-ids.md`. **Goal:** automatic, minimal, coherent rebuilds.
  *Proposal; not started.*
- [`corpus-editorial-filtering.md`](corpus-editorial-filtering.md) — strip modern editorial prose from the
  embedding corpus. **Goal:** embed tradition text, not translators' 19th–20th-c. framing. *Layer 1
  (curated `content_start/end` + exclude) **done**; Layer 2 (cue-strip on interleaved notes) pending.*
- [`motifs-browser-ui.md`](motifs-browser-ui.md) — the Motifs section UX. **Goal:** browsable cross-indexed
  catalogue. *Shipped.*
- [`tmi-mellmann-migration.md`](tmi-mellmann-migration.md) — TMI edition/source migration. **Goal:** a
  cleaner Thompson provenance. *Partially implemented — additive-first phase shipped; full source swap not done.*

## Archived

Spent, shipped, or validated-but-not-productionised — kept for the reasoning trail under [`archive/`](archive/).

- [`macro-area-facets.md`](archive/macro-area-facets.md) — the **entity model**: a tradition carries `area` (12
  macro-areas) · `family` · `subsistence` · `theme_profile`; depth (`stratum`) is a **motif** property.
  *Validated (mockups 21/32/42); the multi-facet layer (`family`/`subsistence`) was not adopted — single-axis
  `region` won; the `area`→`region` geography survives via `region-implementation.md`.*
- [`tradition-architecture-unified.md`](archive/tradition-architecture-unified.md) — **one id-keyed, faceted
  `Tradition` entity**; `area` becomes the single region vocabulary; colour derived as a gradient within
  macro-area; `major_tradition` retired. *Parent synthesis (§1–3); §4/§6 superseded by `region-implementation.md`
  — which now carries the live plan.*
- [`tradition-taxonomy-final.md`](archive/tradition-taxonomy-final.md) — one-page reference for the converged
  classification. *Its multi-facet target superseded by the single-axis `region` decision.*
- [`analysis-program.md`](archive/analysis-program.md) — the natural-history arc **collect → describe →
  classify → explain** that orders every mockup and proposal. *Umbrella doc; framing, not live work.*
- [`synthesis-and-directions.md`](archive/synthesis-and-directions.md) / [`mockup-roadmap-24-59.md`](archive/mockup-roadmap-24-59.md) —
  the findings synthesis and the ranked mockup queue. *Living history of the mockup run (M24–M59); the queue is
  worked through.*
- [`stratum-derivation.md`](archive/stratum-derivation.md) — deriving a motif's **time-depth from its
  distribution** (Method A depth score + a phylogenetic model). *Method 17 prototyped; full method not built.*
- [`stratigraphic-peeling.md`](archive/stratigraphic-peeling.md) — **recursive data-driven stratigraphy**:
  let the statistics define layers, date and peel them, recurse. *Proposal + probes + mockup 45 (dated soft
  layers); production wiring remains.*
- [`theme-taxonomy-comparison.md`](archive/theme-taxonomy-comparison.md) — the two theme axes (etiological vs
  narrative). *Validated (mockups 41–43); productionisation is its own open step.*
- [`chunk-preprocessing-redesign.md`](archive/chunk-preprocessing-redesign.md) — the embedding-variant /
  preprocessing registry redesign. *Implemented (2026-07).*
- [`tradition-classification.md`](archive/tradition-classification.md) — the criteria and candidate history
  behind the `region` canon (what counts as a tradition, how the axis was chosen). *Superseded by the closed
  canon in `regions.md`; kept for the reasoning trail.*
- [`map-palette-and-projection.md`](archive/map-palette-and-projection.md) — ADR: region-map palette
  (CARTOColors Prism as canon; the associative palette explored, not adopted), map projection (equirectangular
  engine + Winkel Tripel atlas view), basemap tiles (CARTO Positron + the tiles↔projection constraint), and the
  presentation constants. *Accepted decision record (one open sub-decision, §2.3). **Palette choice later
  reversed (2026-07): the associative palette is now canon — see `region-palette-prism.md`.***
- [`region-palette-prism.md`](archive/region-palette-prism.md) — the former **CARTOColors-Prism** region
  palette (spectral out-of-Africa arc, hand-tuned swaps, `base` + `light`/`dark` ramp ends). *Superseded
  (2026-07): `regions.md` §8 now uses the **intuitive/associative** palette, `base`-only; kept for provenance.*
