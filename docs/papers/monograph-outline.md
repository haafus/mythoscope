# Monograph outline — *Computational Comparative Mythology*

How the four series papers compose into one book. The papers are written to be released either
**separately** (as a I→IV sequence) or **merged** into a single monograph; this note is the merge
plan — the front/back matter to add, the mapping of papers to parts, the shared apparatus, and the
edits that de-duplicate the seams.

## Title

**Computational Comparative Mythology: Field, Program, Machine, and Findings.**
(Working; alt. subtitle *A Natural-History of the Motif*.)

## Structure

```
Front matter
  Title, abstract, preface (why a natural-history framing), reader's guide
Part I  — The Field        (= Paper I, Survey)
Part II — The Program      (= Paper II, Position/Method/Roadmap)
Part III— The Machine      (= Paper III, Infrastructure & induction pipeline)
Part IV — The Findings     (= Paper IV, Results)
Part V  — Open Problems & Outlook   (= 5-outlook-draft.md — drafted; see below)
Back matter
  Unified bibliography, data & code availability, appendices, index
```

### The four parts, from the existing drafts

- **Part I · The Field** — the survey, lightly trimmed: it motivates the book by showing the field's
  two eras and its honest verdict (motif detection unsolved; embeddings as retrieval). Its "where
  Mythoscope sits" section becomes the bridge into Part II.
- **Part II · The Program** — the position/method paper, verbatim as the book's thesis: the
  natural-history arc, the given/inferred rule, the three-entity model, the explicit assumptions.
- **Part III · The Machine** — the infrastructure paper: the `corpus → embeddings → projections →
  graphs → motifs` induction pipeline and the cross-index crosswalk, with induction staged honestly
  (built machine, output-validation pending). Its §5 becomes a short "what the infrastructure
  validates" chapter that hands off to Part IV.
- **Part IV · The Findings** — the results paper, verbatim: systematics, stratum, dating, facet
  adequacy, connectivity gates, tradition stratigraphy, and the theme re-derivation.

### Part V · Open Problems & Outlook (drafted → [`5-outlook-draft.md`](5-outlook-draft.md))

Ends the book on the frontier rather than a restated conclusion, on four threads:
1. **Finishing motif induction from text** — the principal open milestone (Paper III §5.5): induced
   motifs at scale validated against the curated gold, baselines beaten, culture-bearers consulted.
2. **Closing the convergence residual** — the pending data enrichments (Paper II §6): fine SNP
   genetics for a true third axis, OWTRAD trade routes, node-level Bayesian dating (BEAST).
3. **Productionising the two-facet theme taxonomy** (etiological + narrative).
4. **Release** — corpus, indices, tools, and the `narrative_taxonomy.json` facet.

## Shared apparatus (merge tasks)

- **One bibliography.** Merge the four reference lists + [`bibliography.md`](bibliography.md) into a
  single deduplicated back-matter list; the annotated `bibliography.md` becomes the "Further reading"
  appendix. (~90 unique entries expected.)
- **One notation & glossary.** Define once, up front: `a(t)` (attestation intensity), `stratum`,
  facet, descent/areal/reinvention, mega-set span, the A1–A8 assumptions. Remove the per-paper
  re-definitions.
- **Cross-references become internal.** The papers already point at each other by filename; in the
  monograph these become "Part II §4"-style internal references.

## De-duplication at the seams (the only real editing)

The drafts were written to stand alone, so three overlaps must be trimmed when merged:
1. **Related work.** Part I (survey) is the full treatment; Part II §6 and Part IV §6 should shrink to
   a paragraph that points back to Part I.
2. **The theme re-derivation** appears in Part IV §4.7 (summary) and in
   `../proposals/archive/theme-taxonomy-comparison.md` (full). Keep the summary in IV; the full
   comparison becomes an appendix.
3. **Assumptions & method** are stated in Part II and *used* in Part IV; Part IV should cite, not
   restate, them.

Everything else is complementary, not redundant: Field/Program/Machine/Findings are four faces of one
programme, and the four-way split is the book's spine, not an accident of drafting.

## Is four the right number?

Yes. The split maps onto the natural structure of a research programme — *what exists* (field), *how
to reason* (program), *what we built* (machine), *what we found* (findings) — and mirrors the project's
own staged plan (survey → infrastructure → method → discovery). Motif induction from text is **not** a
missing fifth pillar; it is the through-line of Part III (the machine's purpose) and the head of Part V
(the open frontier), so it is load-bearing across the book without needing its own volume until it
produces validated results.
