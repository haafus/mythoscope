# Element outline — *Computational Comparative Mythology*

Structure and table of contents for a **Cambridge Element** (short-form scholarly book, ~30,000
words). This is the *first book step*: a single-argument, self-contained volume assembled from the
existing drafts and the ~40 interactive prototypes, and itself the skeleton of a later full monograph
(70–120k words). Distinct from [`monograph-outline.md`](monograph-outline.md), which plans the larger
book; this file plans the Element.

Written to be read by someone who does not know the project.

---

## What a Cambridge Element is

A peer-reviewed short book, typically 20,000–30,000 words, one focused argument, published open access
online with a DOI and in print. Between a long article and a monograph. Series candidates: an Element
in a digital-humanities, cultural-evolution, or quantitative-social-science strand.

## The single thesis

> **The geography of a myth is written in *where* it is attested, not in *what* it says.** On a large
> cross-indexed global motif corpus, areal diffusion dominates; a small, datable descent minority
> tracks language; and a faint trans-hemispheric substrate — chiefly celestial cosmology — survives
> every de-confounding control and aligns with the peopling of the continents. A tradition is best
> described by the *narrative form* of its corpus (a data-derived axis) while the classical
> *etiological* themes remain the better instrument for reading geography. Depth is a property of a
> distribution, not of meaning, and is only partly recoverable — the honestly unexplained convergence
> residual is the map of what comes next.

Every chapter advances this one claim. That single throughline is what makes it a book, not five
stapled papers.

---

## Table of contents

| # | Chapter | Words | Built from |
|---|---|---|---|
| 1 | Introduction: the shape of a distribution | 3,000 | Findings §1; Program §1 |
| 2 | The field and its unsolved task | 3,000 | Survey (condensed) |
| 3 | A natural-history program | 3,000 | Program §§1–5 |
| 4 | The corpus and the bench | 3,500 | Machine/resource; mockups 01–14 |
| 5 | Systematics and the tradition | 3,500 | Findings §4.1–4.2, §4.5; mockups 21–27, 32, 38 |
| 6 | Depth, descent, and the deep substrate | 4,500 | Findings §4.3–4.4, §4.6; mockups 17–20, 28, 30–31, 39 |
| 7 | Connectivity: what the facets miss | 2,500 | Findings §4.5; mockups 34–37 |
| 8 | Two axes of theme | 3,000 | Findings §4.7; mockups 41–44 |
| 9 | Three motifs traced through the machine | 2,500 | new; mockups 40, 05 |
| 10 | Discussion and outlook | 2,500 | Findings §5; Outlook |
| — | Appendices | 1,500 | new + existing proposals |
| | **Total** | **~32,500** | |

(~32.5k leaves room to trim to a 30k target in execution.)

---

## Front matter

- **Title:** *Computational Comparative Mythology: A Natural History of the Motif.*
- **Abstract** (~200 words) — the thesis and the five headline results.
- **Keywords** — computational folkloristics; comparative mythology; cultural evolution; motif;
  areal diffusion; phylogenetics; digital humanities.
- **Reader's guide** — one paragraph on the chapter arc and who each chapter is for.

---

## The chapters

### 1. Introduction: the shape of a distribution

- **Purpose:** pose the question and state the thesis.
- **Covers:** why a motif recurs across cultures that never met — the three modes (shared descent,
  areal diffusion, independent reinvention) and Galton's problem; the three obstacles quantitative
  work has faced (non-interoperable catalogues, uneven cataloguing effort, an unexamined theme axis);
  the thesis in one paragraph; what the Element does and the chapter roadmap.

### 2. The field and its unsolved task

- **Purpose:** place the book in computational folkloristics; give the reader the field in one sitting.
- **Covers:** the classical era (index digitisation, topic-model induction, tale phylogenetics,
  narrative networks) and the modern era (transformer embeddings, large-language-model annotation);
  the hard lessons (motifs resist crisp boundaries, simple baselines match neural systems, models
  hallucinate); the verdict that embeddings serve best as a **retrieval / candidate-generation layer
  over a curated expert index**. Condensed from the standalone survey; the survey ships separately in
  full.

### 3. A natural-history program

- **Purpose:** the method and stance the results are produced under.
- **Covers:** the **collect → describe → classify → explain** arc as a dependency order; the
  three-entity data model (tradition, motif, attestation) in which a motif's time-depth is the single
  *inferred* field; the explicit substantive and methodological assumptions, each attackable on its
  own; the discipline of **de-confounding sampling at every step** and of **pre-registered falsifiable
  gates** that license reporting clean negatives.

### 4. The corpus and the bench

- **Purpose:** the infrastructure the results stand on — described so a reader could reuse it.
- **Covers:** the three catalogues (Thompson's Motif-Index, the Aarne–Thompson–Uther tale-type index,
  Berezkin's areal catalogue) assembled into one provenanced attestation matrix; the ~7,300-edge
  cross-catalogue link set and how the links were drawn; the multilingual motif embeddings with a
  word-frequency baseline and a recall evaluation; the spatial and coverage layers; the analysis bench
  of self-contained prototypes; and the raw-text **induction pipeline described as built
  infrastructure**, its validated output staged to future work.

### 5. Systematics and the tradition

- **Purpose:** show the catalogue carries real structure, and define what a tradition *is*.
- **Covers:** region-coherent structure recovered by co-clustering and shown not to be a sampling
  artifact (a sampling-corrected block model); the four descriptors of a tradition (area, language
  family, subsistence, theme profile) and their audit — non-orthogonal, with language family and
  subsistence nearly redundant, area and theme doing the work, and the set **incomplete** (recovering
  only about a third of motif similarity); the theme axis data-confirmed from co-occurrence alone; the
  subsistence gradient (cosmology-heavy foragers, tale-heavy states) and its restricted-permutation
  controls.

### 6. Depth, descent, and the deep substrate

- **Purpose:** the core result — the balance of descent, diffusion, and a deep substrate.
- **Covers:** two ways to read depth — from the *shape* of a distribution, and from the language tree
  by ancestral-state reconstruction; the finding that **areal diffusion dominates**, with a ~1%
  descent minority (the Eurasian fairy-tale core) that tracks language and can be **calendar-dated**
  (~5,500 years for the Indo-European märchen belt); the deep trans-hemispheric substrate — chiefly
  celestial cosmology — **real but small**, surviving coverage and banality controls; the central
  negative result that a *deep shared substrate* and a *widely diffused* motif are **irreducible from
  distribution alone** (sun-and-moon versus swan-maiden receive near-identical mixtures) and that
  content does not supply the missing signal; and **tradition stratigraphy** — deep-substrate-rich
  traditions sit in early-peopled regions (partial correlation +0.48 with first-peopling age).

### 7. Connectivity: what the facets miss

- **Purpose:** confront the large residual honestly; test two ways to close it.
- **Covers:** the cross-continental convergence residual left after the descriptors; the pre-set test
  that **landscape permeability fails** (plain distance beats resistance distance out of sample); the
  weak but real signal from **historical empires** (traditions in different macro-areas sharing an
  empire share far more motifs); and the **back-migration critique** — much apparent African–Eurasian
  sharing sits only in the admixed corridor, weakening "African substratum = oldest."

### 8. Two axes of theme

- **Purpose:** show there are two good theme axes, not one, and what each is for.
- **Covers:** re-deriving the theme axis bottom-up from motif meaning and finding it **orthogonal** to
  the classical etiological one — *what the myth explains* versus *how the tale is built*; the
  data-driven axis winning as a **descriptor of a tradition** while the etiological axis remains the
  better **reader of geography**; the two giant genre catch-alls dissolving into narrative complexes;
  and a depth gradient hidden inside them (a deep swallowing-monster complex the flat category buried).
  The argument for a **two-facet representation**, not a replacement.

### 9. Three motifs traced through the machine

- **Purpose:** the book affordance a paper cannot give — narrative case studies.
- **Covers:** three motifs walked through the whole apparatus. **The swan-maiden** — broad, areal, an
  almost-even descent/diffusion mixture: the irreducibility case in the flesh. **Sun and moon as kin**
  — the deep celestial substrate, pan-global yet diffused. **The fished-up earth** — a dated descent
  motif placed in Western Oceania with spread lines across the Pacific. Each shows the corpus, the
  depth read, the phylogeny, the theme placement, and the map.

### 10. Discussion and outlook

- **Purpose:** consolidate the thesis and end on the frontier.
- **Covers:** the three cross-cutting conclusions (geography primary; depth a property of distribution;
  two good theme axes); the residual as the map of future work; the open milestones — finishing motif
  induction from text, a true genetic third axis and node-level Bayesian dating, the two-facet taxonomy
  in production, and the open release of corpus, tools, and derived data.

---

## Back matter

- **Appendix A — the three-entity data model:** tradition, motif, attestation; the schema and the one
  inferred field.
- **Appendix B — the cross-catalogue link methodology:** evidence types, the extension layer, coverage
  and known gaps.
- **Appendix C — methods reference:** the distribution-shape depth score; the de-confounding (coverage
  weighting, restricted permutation, cross-catalogue replication); ancestral-state reconstruction.
- **Appendix D — reproducibility:** the map from each figure to the prototype that produces it, and how
  to regenerate them; data and code DOIs.
- **Further reading** — the annotated canon (from `bibliography.md`).
- **Unified bibliography** — one deduplicated list (~90 entries).

---

## What already exists vs what must be written

- **Exists (reuse, condense, unify):** chapters 2, 3, 4, 5, 6, 7, 8, 10 map onto existing drafts and
  the mockups; most of the intellectual content and every figure is done.
- **Must be written new:** the single-thesis **introduction (1)**; the **case-studies chapter (9)**;
  the appendices; and — the real editing work — the **connective tissue** that makes ten chapters
  advance one argument instead of reading as five papers.
- **Must be trimmed:** related-work duplication (the survey chapter is the full treatment; chapters 6
  and 8 point back to it rather than restating); assumptions stated once in chapter 3 and *used*, not
  restated, later.

## Word-count reality

The existing drafts total ~15k words; the Element targets ~30k. So this is roughly a **2× expansion**,
concentrated in chapters 6 and 8 (the result chapters), the new introduction, and the case studies —
achievable from current material, unlike the 5–8× a full monograph would need.
