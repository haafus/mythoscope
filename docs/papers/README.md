# Papers — *Computational Comparative Mythology* (a four-paper series)

Working drafts for the MythoScope research programme, written as one coherent series under the
umbrella title **Computational Comparative Mythology**. Each paper stands alone but the four are
designed to read in order and to compose into a monograph (see
[`monograph-outline.md`](monograph-outline.md)). These are **evolving drafts**, not submissions;
numbers come from the prototype series (`mockups/`) and the design notes (`docs/motifs/proposals/`),
with the limits each carries.

| # | Face | Title | What it is |
|---|---|---|---|
| **I** | The Field | [Computational Folkloristics and the Induction of Motifs: A Survey](survey-draft.md) | Review of the field — indices/ontologies, classification, topic models, embeddings & motif detection, sequence/network mining, phylogenetic mythology, Propp extraction; datasets & licences; open problems. |
| **II** | The Program | [A Natural-History Program for Computational Comparative Mythology](program-draft.md) | Position + method + roadmap — the stance (collect→describe→classify→explain), the three-entity model, the explicit assumptions, the gated method, the data-enrichment plan. |
| **III** | The Machine | [Inducing and Cross-Indexing Motifs: A Corpus Pipeline and Analysis Bench](draft.md) | Infrastructure — the `corpus → embeddings → projections → graphs → motifs` induction pipeline, the three-index crosswalk, retrieval, and the analysis lab bench. |
| **IV** | The Findings | [Geography, Descent, and Genre in the Distribution of Folklore Motifs](motif-distribution-draft.md) | Results — descent vs areal diffusion, depth from distribution, facet adequacy & connectivity, and the data-driven theme re-derivation. |

Reading order I → II → III → IV: *what exists* → *how to reason* → *what we built* → *what we found*.

**Two tracks.** The programme pursues (1) **motif induction from raw text** — the purpose of the main
codebase (Paper III's pipeline), a real but not-yet-completed goal — and (2) **distributional analysis
over the curated indices** (Berezkin/TMI/ATU), the exploratory arc that has produced the results in
Paper IV. Paper III describes both and stages the first honestly.

- [`bibliography.md`](bibliography.md) — the annotated, thematically-grouped reading list (shared).
- [`monograph-outline.md`](monograph-outline.md) — how the four papers compose into one book.

Related, kept separate on purpose:

- Raw field-survey notes and the labs/venues landscape → [`../research/`](../research/).
- The full data-driven theme re-derivation vs Berezkin's themes →
  [`../motifs/proposals/theme-taxonomy-comparison.md`](../motifs/proposals/theme-taxonomy-comparison.md).
- Per-result method and figures → the individual `mockups/*/README.md`.
