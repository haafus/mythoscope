# Papers — *Computational Comparative Mythology* (a four-paper series)

Working drafts for the MythoScope research programme, written as one coherent series under the
umbrella title **Computational Comparative Mythology**. Each paper stands alone but the four are
designed to read in order and to compose into a monograph (see
[`monograph-outline.md`](monograph-outline.md)). These are **evolving drafts**, not submissions;
numbers come from the prototype series (`mockups/`) and the design notes (`docs/motifs/proposals/`),
with the limits each carries.

| # | Face | Title | What it is |
|---|---|---|---|
| **I** | The Field | [Computational Folkloristics and the Induction of Motifs: A Survey](1-field-draft.md) | Review of the field — indices/ontologies, classification, topic models, embeddings & motif detection, sequence/network mining, phylogenetic mythology, Propp extraction; datasets & licences; open problems. |
| **II** | The Program | [A Natural-History Program for Computational Comparative Mythology](2-program-draft.md) | Position + method + roadmap — the stance (collect→describe→classify→explain), the three-entity model, the explicit assumptions, the gated method, the data-enrichment plan. |
| **III** | The Machine | [Inducing and Cross-Indexing Motifs: A Corpus Pipeline and Analysis Bench](3-machine-draft.md) | Infrastructure — the `corpus → embeddings → projections → graphs → motifs` induction pipeline, the three-index crosswalk, retrieval, and the analysis lab bench. |
| **IV** | The Findings | [Geography, Descent, and Genre in the Distribution of Folklore Motifs](4-findings-draft.md) | Results — descent vs areal diffusion, depth from distribution, facet adequacy & connectivity, and the data-driven theme re-derivation. |

Reading order I → II → III → IV: *what exists* → *how to reason* → *what we built* → *what we found*.

**Two tracks.** The programme pursues (1) **motif induction from raw text** — the purpose of the main
codebase (Paper III's pipeline), a real but not-yet-completed goal — and (2) **distributional analysis
over the curated indices** (Berezkin/TMI/ATU), the exploratory arc that has produced the results in
Paper IV. Paper III describes both and stages the first honestly.

Plus the monograph's closing chapter, not one of the four standalone papers:

- [`5-outlook-draft.md`](5-outlook-draft.md) — **Part V · Open Problems & Outlook**: finishing motif
  induction from text, closing the convergence residual (SNP / OWTRAD / BEAST), the two-facet taxonomy
  in production, and release. Ends the book on the frontier.

Shared apparatus:

- [`bibliography.md`](bibliography.md) — annotated **Further reading** (the canon with "why it
  matters"); *not* the works-cited — precise citations live in each paper's reference list and in
  `../research/`, to be merged into a generated `references.md` at monograph-assembly time.
- [`monograph-outline.md`](monograph-outline.md) — how the four papers + Part V compose into one book.
- [`release-plan.md`](release-plan.md) — preprints (how many / where), target venues, Quarto book +
  GitHub Pages tooling, DOIs, and the rights/licensing checklist.

Related, kept separate on purpose:

- Raw field-survey notes and the labs/venues landscape → [`../research/`](../research/).
- The full data-driven theme re-derivation vs Berezkin's themes →
  [`../motifs/proposals/theme-taxonomy-comparison.md`](../motifs/proposals/theme-taxonomy-comparison.md).
- Per-result method and figures → the individual `mockups/*/README.md`.
