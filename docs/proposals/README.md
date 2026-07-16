# Proposals — index, goals, and status

Design notes and analysis programmes. Each entry states **what it proposes**, **why it is needed** (the goal
it serves), and **where it stands**. "Proposal" = designed, not built; "partly done" = some layer landed;
"validated" = demonstrated in a mockup but not productionised.

## Analysis programme (the science)

- [`analysis-program.md`](analysis-program.md) — the natural-history arc **collect → describe → classify →
  explain** that orders every mockup and proposal. **Goal:** give the whole investigation one legible line
  so each step's purpose is clear. *Umbrella doc.*
- [`synthesis-and-directions.md`](synthesis-and-directions.md) / [`roadmap.md`](roadmap.md) — the findings
  synthesis and the ranked mockup queue (M24–M40). **Goal:** sequence the work by significance × feasibility.
  *M32–M39 done; M40 (peeling) proposed.*
- [`macro-area-facets.md`](macro-area-facets.md) — the **entity model**: a tradition carries `area` (12
  macro-areas) · `family` · `subsistence` · `theme_profile`; depth (`stratum`) is a **motif** property.
  **Goal:** replace the eclectic single `major_tradition` tree with a principled, audited multi-facet model.
  *Validated (mockups 21/32/42); `region_facets.py` not yet written.*
- [`stratum-derivation.md`](stratum-derivation.md) — deriving a motif's **time-depth from its distribution**
  (Method A depth score + a phylogenetic model). **Goal:** date motifs without gold labels. *Method 17
  prototyped; full method not built.*
- [`stratigraphic-peeling.md`](stratigraphic-peeling.md) — **recursive data-driven stratigraphy**: let the
  statistics define layers, date and peel them, recurse. **Goal:** a bottom-up dated stratigraphy of world
  mythology. *Proposal + probes + mockup 45 (incl. dated soft layers); production wiring remains.*
- [`theme-taxonomy-comparison.md`](theme-taxonomy-comparison.md) — the two theme axes (etiological vs
  narrative). **Goal:** decide the tradition `theme_profile` facet. *Validated (mockups 41–43).*

## Data / architecture (the engineering)

- [`tradition-taxonomy-final.md`](tradition-taxonomy-final.md) — one-page reference for the converged
  classification. **Goal:** a single orientation point instead of three scattered ones. *Reference.*
- [`tradition-architecture-unified.md`](tradition-architecture-unified.md) — **one id-keyed, faceted
  `Tradition` entity**; `area` becomes the single region vocabulary; colour derived as a gradient within
  macro-area; `major_tradition` retired. **Goal:** kill the fragile string-join, the six overlapping region
  schemes, and non-deterministic colour in one coherent model. *Proposal; 6-phase migration not started.*
- [`region-implementation.md`](region-implementation.md) — **the code plan** for wiring `region` into
  production after taxonomy/presentation closed: authored `region` in a `config/regions.json` + id-keyed
  `config/traditions.json` registry, fail-loud validation, delete `major_tradition`, region-derived colour,
  normalised served/chunk model, one `UNASSIGNED`. Current state with file:line + settled decisions + config
  shapes + phased migration. Supersedes `tradition-architecture-unified.md` §4/§6. **Goal:** an executable
  implementation plan. *Proposal; not started.*
- [`map-palette-and-projection.md`](map-palette-and-projection.md) — ADR: region-map palette (CARTOColors
  Prism as canon; the associative palette explored, not adopted), map projection (equirectangular engine +
  Winkel Tripel atlas view), basemap tiles (CARTO Positron + the tiles↔projection constraint), and the
  presentation constants. **Goal:** record the reasoning so it survives past the conversation. *Decision record.*
- [`corpus-editorial-filtering.md`](corpus-editorial-filtering.md) — strip modern editorial prose from the
  embedding corpus. **Goal:** embed tradition text, not translators' 19th–20th-c. framing. *Layer 1
  (curated `content_start/end` + exclude) **done**; Layer 2 (cue-strip on interleaved notes) pending.*
- [`motifs-browser-ui.md`](motifs-browser-ui.md) — the Motifs section UX. **Goal:** browsable cross-indexed
  catalogue. *Shipped.*
- [`tmi-mellmann-migration.md`](tmi-mellmann-migration.md) — TMI edition/source migration. **Goal:** a
  cleaner Thompson provenance. *Proposal.*

## Open next steps (proposed, not built) — with their goal

| Next step | Goal — why it's needed | Home |
|---|---|---|
| **`region_facets.py`** — productionise the 12 macro-areas + `area/family/subsistence` recipe | Turn the validated facet model into the pipeline's real classification; collapses the six region schemes onto one `area` | macro-area-facets |
| **Tradition architecture migration** (id identity + build validation → facet registry → area-gradient colour → retire `major_tradition` → collapse region schemes → one `UNASSIGNED` default) | Remove silent join breakage, denormalisation, non-deterministic colour; make region unambiguous | tradition-architecture-unified |
| **Editorial Layer 2** — cue-strip of interleaved `[N]` notes on annotated editions | Clean the ~5 critical editions (Edda, Beowulf, Babylonian…) that start/stop can't reach | corpus-editorial-filtering |
| **Two-axis theme taxonomy** in the pipeline (etiological + narrative) | Make both theme facets standing infrastructure, not a prototype result | theme-taxonomy-comparison |
| **Peeling production wiring** — real M38 factors + calibrated M17/clade ages + full M24 weights + bootstrap/clade validation | Turn the proof-of-concept dated soft layers into a defensible **dated stratigraphy** (the one path here that could add a *new result*, not just rigour) | stratigraphic-peeling |
| **GPU embedding run** — enable qwen-4b + story-emb, compute embeddings | Benchmark narrative-similarity embedders for the induction task (SemEval-2026 Task 4) | ../embeddings-gpu-howto.md |
| **Connectivity axis** — fine genetics + trade-route networks + node-level dating | Close the ~64% convergence residual the facets leave (the expensive, result-bearing joins) | macro-area-facets / roadmap |

**Reading the table:** most of these are **rigour / engineering** — they make results defensible, the code
clean, and the corpus honest, but they do **not** move the scientific conclusions. The one row that could
yield a *new* finding is **peeling production wiring** (dated soft layers); everything else strengthens what
already stands.
