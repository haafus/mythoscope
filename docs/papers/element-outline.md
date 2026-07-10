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

---

## Detailed budgets: subsections, mockups, and figures

Each chapter broken into subsections with word budgets, the exact source prototypes, and a numbered
figure list. "new" = a diagram to be drawn, not from a prototype. Every other figure is a static
render of an existing interactive prototype. Target ~28 figures; trim to ~25 in production.

### Chapter 1 — Introduction: the shape of a distribution · 3,000 words · 1 figure
- 1.1 Why a motif recurs; the three modes and Galton's problem — 900 — *Findings §1*
- 1.2 The three obstacles (catalogues, coverage, the theme axis) — 700 — *Findings §1*
- 1.3 The thesis, in one paragraph — 400 — *new*
- 1.4 What the Element does; chapter roadmap — 1,000 — *new*
- **Figures:** Fig 1.1 — the three transmission modes (descent / areal / reinvention) as a schematic over a world map (*new*).

### Chapter 2 — The field and its unsolved task · 3,000 words · 1 figure + 1 table
- 2.1 The classical era — 900 — *Survey*
- 2.2 The modern era — 900 — *Survey*
- 2.3 The hard lessons — 700 — *Survey*
- 2.4 The verdict: embeddings as a retrieval layer — 500 — *Survey*
- **Figures:** Fig 2.1 — two-era timeline of the field by method family (*new*). Table 2.1 — open datasets and their licences (*Survey*).

### Chapter 3 — A natural-history program · 3,000 words · 2 figures
- 3.1 The collect → describe → classify → explain arc — 800 — *Program §1*
- 3.2 The three-entity model; the single inferred field — 800 — *Program §2*
- 3.3 Explicit assumptions — 700 — *Program §3*
- 3.4 De-confounding and falsifiable gates — 700 — *Program §4–5*
- **Figures:** Fig 3.1 — the dependency arc (*new*). Fig 3.2 — the tradition / motif / attestation data model (*new*).

### Chapter 4 — The corpus and the bench · 3,500 words · 4 figures + 1 table
- 4.1 The three catalogues into one attestation matrix — 900 — *Machine; mockups 13, 14*
- 4.2 The cross-catalogue link set — 800 — *Machine; mockup 01*
- 4.3 The retrieval layer and its evaluation — 800 — *Machine; mockups 02, 04, 10*
- 4.4 The spatial and coverage layers; the bench; induction staged — 1,000 — *Machine; mockups 12, 09, 11*
- **Figures:** Fig 4.1 — the three-catalogue crosswalk graph (*mockup 01*). Fig 4.2 — recall@k, embeddings vs lexical baseline (*mockup 10*). Fig 4.3 — corpus-overview dashboard (*mockups 13/14*). Fig 4.4 — attestation-intensity distribution a(t) (*mockup 13*). Table 4.1 — corpus composition by catalogue (*Machine*).

### Chapter 5 — Systematics and the tradition · 3,500 words · 5 figures
- 5.1 De-confoundable structure (co-clustering + block model) — 900 — *Findings §4.1; mockups 06, 07, 15, 26*
- 5.2 The four facets and their audit — 900 — *Findings §4.5; mockups 21, 32*
- 5.3 The theme axis, data-confirmed — 700 — *Findings §4.2; mockups 16, 23*
- 5.4 The subsistence gradient and its controls — 1,000 — *Findings §4.2; mockups 22, 24, 25*
- **Figures:** Fig 5.1 — co-clustered motif × tradition blocks (*mockup 26*). Fig 5.2 — degree-correction halving the coverage confound (*mockup 26*). Fig 5.3 — facet drop-one ΔR² and redundancy (*mockup 32*). Fig 5.4 — subsistence × Category-A gradient with restricted-permutation controls (*mockups 22, 25*). Fig 5.5 — theme × area lift heatmap (*mockup 23*).

### Chapter 6 — Depth, descent, and the deep substrate · 4,500 words · 8 figures
- 6.1 Depth from a distribution's shape (Method A) — 700 — *Findings §4.3; mockup 17*
- 6.2 Depth from the language tree (Method B) — 700 — *Findings §4.3; mockups 18, 19*
- 6.3 Areal diffusion dominates; the ~1% descent minority — 800 — *Findings §4.3; mockup 27*
- 6.4 The deep substrate: real but small; the controls — 700 — *Findings §4.3; mockups 20, 37*
- 6.5 Irreducibility (A3 vs K25); content does not predict age — 700 — *Findings §4.3; mockups 27, 29*
- 6.6 Dating the descent minority — 500 — *Findings §4.4; mockups 30, 31*
- 6.7 Tradition stratigraphy — 400 — *Findings §4.6; mockup 39*
- **Figures:** Fig 6.1 — depth score + histogram (*mockup 17*). Fig 6.2 — phylogenetic signal, descent vs diffusion (*mockup 18*). Fig 6.3 — three-way descent/areal/reinvention mixture (*mockup 27*). Fig 6.4 — A3 vs K25 near-identical mixtures (*mockup 27*). Fig 6.5 — deep substrate surviving controls, 320/480 (*mockup 20*). Fig 6.6 — content barely predicts breadth (*mockup 29*). Fig 6.7 — dated descent minority, calendar ages (*mockup 30*). Fig 6.8 — tradition stratigraphy, deep-share vs peopling age +0.48 (*mockup 39*). (Robustness — alt-tree, mockup 33 — folded into text.)

### Chapter 7 — Connectivity: what the facets miss · 2,500 words · 3 figures
- 7.1 The convergence residual — 600 — *Findings §4.5; mockup 38*
- 7.2 Landscape permeability fails its gate — 700 — *Findings §4.5; mockup 34*
- 7.3 Historical empires weakly pass — 700 — *Findings §4.5; mockup 35*
- 7.4 The back-migration critique — 500 — *Findings §4.5; mockup 36*
- **Figures:** Fig 7.1 — held-out R², resistance vs great-circle distance (*mockup 34*). Fig 7.2 — cross-area motif sharing by shared empire (*mockup 35*). Fig 7.3 — the Africa↔Eurasia corridor fraction (*mockup 36*).

### Chapter 8 — Two axes of theme · 3,000 words · 4 figures
- 8.1 Re-deriving theme from meaning — 700 — *Findings §4.7; mockup 41*
- 8.2 Orthogonality: etiology vs narrative form — 700 — *Findings §4.7; mockup 41*
- 8.3 Head-to-head as a tradition descriptor — 800 — *Findings §4.7; mockups 42, 43*
- 8.4 Catch-all dissolution and the hidden depth gradient — 800 — *Findings §4.7; mockup 44*
- **Figures:** Fig 8.1 — UMAP re-derivation, 16 clusters × 61 sub-themes (*mockup 41*). Fig 8.2 — facet showdown, ΔR² narrative vs etiological (*mockup 42*). Fig 8.3 — narrative worldview clusters across traditions (*mockup 43*). Fig 8.4 — catch-alls dissolving; the deep swallowing-monster complex (*mockup 44*).

### Chapter 9 — Three motifs traced through the machine · 2,500 words · 3 figures
- 9.1 The swan-maiden — the irreducibility case — 850 — *new synthesis; mockups 40, 27*
- 9.2 Sun and moon as kin — the deep celestial substrate — 850 — *new synthesis; mockups 40, 17*
- 9.3 The fished-up earth — dated descent in Oceania — 800 — *new synthesis; mockups 31, 40*
- **Figures:** Fig 9.1 — swan-maiden map + mixture (*mockup 40*). Fig 9.2 — sun-and-moon distribution (*mockup 40*). Fig 9.3 — fished-up-earth origin and Pacific spread (*mockup 31*).

### Chapter 10 — Discussion and outlook · 2,500 words · 1 figure
- 10.1 The three cross-cutting conclusions — 900 — *Findings §5*
- 10.2 The residual as the map of future work — 700 — *Findings §5; Outlook*
- 10.3 Open milestones and release — 900 — *Outlook*
- **Figures:** Fig 10.1 — the convergence residual as a research map (*new*).

### Appendices · 1,500 words · 0–2 figures
- A. Data model — 300 — *proposals (entity model)*
- B. Cross-catalogue link methodology — 400 — *Machine; mockup 01*
- C. Methods reference (depth score, de-confounding, ancestral-state reconstruction) — 500 — *mockups 17, 24, 25, 28*
- D. Reproducibility: figure → prototype map; data & code DOIs — 300 — *all mockups*

### Totals
- **Prose:** ~30,000 words across ten chapters + ~1,500 appendix.
- **Figures:** ~28 (of which 6 new diagrams: Figs 1.1, 2.1, 3.1, 3.2, 10.1 + Table 2.1); the rest are static renders of existing prototypes.
- **Prototypes used:** 01, 02, 04, 06, 07, 09, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44 — nearly the whole bench. (Not drawn on: 03, 05, 08, 28 feed the text/appendix but not a numbered figure.)
