# The analysis programme — a natural-history arc for folklore motifs

The umbrella over [`macro-area-facets.md`](macro-area-facets.md) (the entity model) and
[`stratum-derivation.md`](stratum-derivation.md) (the time-depth method). It states the
**line the whole investigation follows** — why the mockups and proposals are ordered the
way they are — by borrowing the arc every observational science walked before it had a
theory: **collect → describe → classify → explain**. Biology went from cabinets of
specimens, to comparative anatomy, to Linnaean systematics, to phylogeny and genetics;
linguistics from wordlists, to grammar, to language families, to comparative
reconstruction. We are doing the same to a catalogue of ~3500 motifs across ~1050
traditions.

The stages are **not bureaucratic phases** — they are a *dependency order*. Each stage's
decisions fix the vocabulary the next stage must use, and each stage can only ask questions
the previous one made answerable. You cannot classify what you have not described, or
explain a distribution you have not first mapped.

One rule runs through all of them: **separate the given from the inferred, and attach
confidence to the inferred.** Attestation is observed; area/family/theme are given or
deterministic; `stratum` is inferred and therefore always a hypothesis with a
confidence, never a fact.

## The arc at a glance

| # | Stage | Biological analogue | The question it answers | Given → inferred |
|---|---|---|---|---|
| 1 | **Collection & curation** | field collection, specimen prep | *What do we have, and how was it biased in the gathering?* | raw sources → a clean, provenanced matrix |
| 2 | **Morphology** | comparative anatomy | *What is one motif, and how do we measure it?* | a motif → its definition, identity, feature vector |
| 3 | **Systematics** | taxonomy / character analysis | *What kinds are there, on which axes, mapped exhaustively?* | features → a closed facet space (the entity model) |
| 4 | **Phylogeny & etiology** | phylogenetics, historical biogeography | *How did each distribution arise — descent, diffusion, reinvention — and how old is it?* | the mapped space → `stratum`, with confidence |
| 5 | **Synthesis** | evolutionary theory | *Which regularities survive across axes, and what still resists explanation?* | strata → laws + an honest residual |

## 1. Collection & curation — *from field to catalogue*

**Goal.** Turn three heterogeneous scraped indexes (Berezkin, TMI, ATU) into one clean,
provenanced, re-runnable attestation matrix, and — critically — **know how the collecting
itself is biased** before any count is trusted.

**Key decisions & conclusions.**
- One reproducible pipeline off committed sources, no credentials; local `file://` sources
  supported; the whole thing exportable as a bundle.
- A **crosswalk** links the same motif across indexes — the first act of saying "these are
  the same specimen", and a source of independent corroboration later.
- **Collection bias is real and must be carried forward, not forgotten.** Tradition
  coverage `a(t)` spans 1…738 motifs (median 74): a densely-catalogued tradition looks
  "central" for a reason that has nothing to do with age. This single fact becomes the
  mandatory attestation-intensity control in stage 4.

**Artifacts.** the `mytho motifs` pipeline (sources · crosswalk · store); coverage probes
(mockup 08); corpus dashboards (mockups 13–14); the committed coordinate snapshot.

## 2. Morphology — *what a motif is and how we measure one*

**Goal.** Fix the **unit** and the **characters** used to describe it — the motif's
definition, its cross-index identity, and the per-motif measurements everything downstream
consumes. This is comparative anatomy: before you can group organisms you must be able to
describe one and say when two are "the same part".

**Key decisions & conclusions.**
- The unit is the **motif**, described by its definition/name, its cross-index links, and
  above all its **attestation vector** — the set of traditions that carry it.
- From that vector come the measurable characters: prevalence, macro-area / language-family
  span, geographic spread and fragmentation, mega-set span, phylogenetic signal
  (`stratum-derivation.md` §3). These are the "morphological characters" the later stages
  score.
- How to *represent* a motif for matching is itself a morphological question — text
  embeddings vs lexical overlap were compared before settling.

**Artifacts.** cross-walk graph (01); semantic parallels (02, 04); embedding evaluation
(10); the TMI detail-hierarchy tree (11); the motifs-navigator (09); the feature list in
`stratum-derivation.md` §3.

## 3. Systematics — *the kinds, the dividing characters, mapped exhaustively*

**Goal.** Delimit the **space of kinds**: which axes genuinely divide the material, which
are orthogonal, how fine each must be, and a **closed, exhaustive value set** for each — the
taxonomy a user can slice by without gaps or overlaps.

**Key decisions & conclusions** (the entity model, `macro-area-facets.md`).
- **"Region" was three axes crammed into one.** The clean split is into **entities**: a
  *tradition* carries `area` (12), `family` (11), `subsistence` (4) and a derived
  `theme_profile`; a *motif* carries `theme` (given) and `stratum` (inferred). Expressiveness
  is multiplicative *across entities*, so no single axis needs to be fine — `area` drops
  from 18 to 12.
- **Character selection matters more than character count.** Choosing orthogonal axes
  (area ⟂ family ⟂ subsistence) is the systematic act; `theme_profile` clusters proved
  these carry real, partly cross-geographic structure (38% of profile variance is
  macro-area, 62% is not).
- **Exhaustive mapping is a deliverable, not an afterthought.** Every facet has a canonical
  closed value list, and the deterministic population is coverage-checked against the whole
  corpus (area 1042/1046, theme 3347/3488, family 99%) so the residual is a *known* set of
  data gaps, not a silent one.
- **Berezkin's rule adopted:** don't pool the catalogue — the primary slicer is `theme`; the
  tradition axes are cross-cuts within a theme slice.
- **The chosen characters are natural, not imposed.** The taxonomy's own axes re-emerge from
  the data: `theme_profile` clusters recover regional worldviews, and the theme **Category
  A vs B** split falls out of theme co-occurrence across traditions alone (seriated CLR
  correlation) — a systematic division confirmed, not just declared.

**Artifacts.** the entity model + canonical values (`macro-area-facets.md`); the shared
geographic layer (12); co-occurrence biclusters (03, 05–07); the Berezkin cluster report
(15); theme-profile clustering (16); theme × geography — lift heatmap, seriated theme
co-occurrence, traditions × themes co-clusters (23); deterministic facet population +
coverage (21).

## 4. Phylogeny & etiology — *how the distributions arose, dated and explained*

**Goal.** Explain the maps stage 3 drew: for each motif, decide **descent vs diffusion vs
reinvention**, and **date** it — producing `stratum`, the one inferred field, always with a
confidence. This is phylogenetics + historical biogeography, and it is done by **forming
axioms and testing hypotheses**, not by reading depth off a label.

**Key decisions & conclusions** (`stratum-derivation.md`).
- **The foundation is made explicit** as a set of substantive hypotheses and methodological
  axioms (§0), so every estimate can be read against its assumptions.
- **Two instruments, gated, not averaged.** Method A dates by geography (breadth,
  cross-barrier disjunction, deep mega-set span); Method B dates by the language tree
  (Fitch parsimony, phylogenetic signal). **B routes the mode, then the mode picks the
  instrument** — descent → clade depth, areal → geographic disjunction.
- **Geography is primary.** Only ~1% of motifs actually follow language descent (Eurasian
  fairy-tales, recovering the published phylomemetics result); the rest spread areally — so
  `area` carries most structure and `stratum` is a gated **A×B** estimate.
- **Controls are non-negotiable** (the collection bias of stage 1 comes due here): the
  attestation-intensity weighting thins the "broad areal" class by more than half, while
  the deep, both-hemisphere class survives — an empirical restatement of the
  disjunction-outranks-breadth axiom. A banality proxy flags likely reinvention (homoplasy).
- **Everything is a hypothesis with confidence.** A–B agreement raises it; disagreement is
  itself diagnostic; the deep-substrate-vs-wide-diffusion residual is admitted as
  irreducible from distribution alone.

**Artifacts.** `stratum-derivation.md`; Method A (17); Method B (18); the gated A×B
estimator (19); the mandatory controls (20); external calibration — subsistence via D-PLACE
and the theme test (22).

## 5. Synthesis — *the regularities that survive, and what resists*

**Goal.** State the **laws** that emerge across the axes once strata exist, and — as
honestly — the questions still open.

**What we can say.**
- **The theme axis is a real division, not an editorial one**: Berezkin's Category A vs B
  re-emerges from theme co-occurrence across traditions alone (seriated CLR correlation,
  mockup 23) — two contiguous blocks (cosmology vs tales) with a strong negative rectangle
  between them.
- **Theme is orthogonal to stratum per motif, but a statistical prior in aggregate**:
  Category A (cosmology) is broader + more areal-deep, Category B (tales) narrower + more
  descent-tracking. It must stay an *independent cross-check*, never an estimator input
  (that would be circular).
- **Theme maps onto geography**: adventures over-represented in the Eurasian belt,
  cosmology in the Americas–Pacific and the boreal north (lift heatmap, mockup 23) — the
  systematics view that stage 3 mapped, one block at a time.
- **Subsistence tracks theme**: extractive economies (foragers, horticulturalists) are
  cosmology-heavy, intensive/mobile ones (agrarian states, pastoralists) tale-heavy — the
  predicted gradient, with an honest area confound.
- **The three axes each remove the others' confound**: analysis fixes a theme (Berezkin's
  method), groups by the tradition axes, and dates within by gated A×B.

**What resists** (see [`stratum-derivation.md` §14](stratum-derivation.md)): absolute
dating (needs a dated phylogeny), the deep-substrate/wide-diffusion residual, whether the
historical strata belong on the same axis at all, and the un-run controls. These are open
questions, held open on purpose.

## Cross-cutting principles

- **Given vs inferred, always labelled; confidence on everything inferred.**
- **Each stage's output is the next stage's vocabulary** — description feeds classification
  feeds explanation; skipping a stage produces a facet with no support or a stratum with no
  map behind it.
- **No silent truncation.** Coverage gaps, dropped controls, and capped classes are
  reported, so "we mapped everything" never overstates what was mapped.
- **Prototypes before production.** The mockups are the lab bench; only the given/
  deterministic facets are production-ready, and `stratum` stays an explicitly-experimental,
  offline, reproducible score until its controls and calibration are wired.
