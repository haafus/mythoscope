# Dating & chronology methods for the motif corpus

How to put a **time axis** on the Berezkin motif material (3488 motifs × ~1000 traditions,
with coordinates, `language`, and `atu_refs`). Compiled 2026-07 from web validation of the
computational-mythology literature plus method transfer from population genetics, archaeology,
climate science and single-cell biology. Companion to
[`../proposals/stratigraphic-peeling.md`](../proposals/stratigraphic-peeling.md) (the M17 depth
proxy and mockups 45–48) — this doc is the *method landscape* for going from a depth *proxy* to a
defensible *chronology*.

## The two axes that structure everything

1. **Relative vs absolute.** A relative *ordering* (old→young sequence) is reachable from the data
   alone; *absolute* dates (years) require an **external anchor** — dated archaeology, dated
   language/genetic trees, or dated ancient texts. No internal method yields years.
2. **Vertical vs horizontal.** Only the **vertically transmitted** fraction (descent along a
   lineage) is datable in principle. **Horizontal diffusion** (borrowing) is a confound no internal
   method removes — a widely-borrowed young motif looks old on any breadth/frequency measure. Our
   own measurements say the geography is **clinal** (Mantel r = +0.42, F<sub>st</sub> ≈ 0.06;
   mockup 46), so the tree-like, datable fraction is probably *small* — which is the honest backdrop
   for every method below.

Consequence: the realistic programme is not "date everything." It is (a) *partition* what is even
datable, (b) put year-**floors** on the disjunct substrate via biogeographic barriers, (c) calibrate
the vertical fraction against dated language/genetic trees, and — most tractable of all — (d) build a
defensible **relative ordering** (§B), which delivers most of the value without years.

---

## A. Absolute-dating methods — ranked by effectiveness for *our* data

Effectiveness ≈ (defensibility of the date) × (fraction of corpus it can date) × (feasibility on
data we have) ÷ effort.

1. **Biogeographic lower bounds (recast M17 into years).** ⭐ best cheap win.
   A motif whose distribution spans a known barrier under signs of shared inheritance is *no younger*
   than the crossing: trans-Beringia ~15–17 ka, Sunda–Sahul, Wallace line, the Austronesian island
   sequence. This is Berezkin/d'Huy/Thuillard's own logic (Old- vs New-World set comparison anchored
   to the peopling of America). Turns M17 percentiles into real year-floors for the disjunct
   substrate (the mockup-48 teleconnector motifs). Needs only our data + hard-coded barrier dates.
   *Critique:* lower bounds only; barrier-spanning motifs only; one ancient long-range jump is
   indistinguishable from deep inheritance.
2. **Datability partition (phylogenetic-signal gate).**
   Not a date but the prerequisite: D-statistic (Fritz–Purvis), δ-score, TIGER, Q-residuals,
   retention/consistency index on a reference tree tell *which* motifs are tree-like enough to date.
   On clinal data, estimating that fraction is itself a first-order result.
   *Critique:* needs a reference tree (areal or language); on reticulate data the tree is shaky —
   but that is exactly why this gate must come first.
3. **Language-phylogeny calibration.**
   Map motif presence onto dated Bayesian language trees (Indo-European ~6–8.5 ka, Austronesian
   ~5.2 ka, Bantu, Uralic); a motif congruent with a clade inherits its MRCA age. The da Silva–Tehrani
   method that dated "tales of magic" to the Bronze Age. Uses our `language` field.
   *Critique:* covers only language-tracking motifs; most of ours are areal/clinal → low coverage;
   needs our language labels aligned to Glottolog + published trees.
4. **Genetic co-phylogeny calibration.**
   Correlate motif distances with **dated human population splits** (absolute dates from genomics:
   out-of-Africa ~60 ka, LGM, Beringia). Berezkin and the 2025 bioRxiv preprint do this — mythemes
   correlate with pre-LGM movements ≥38 ka.
   *Critique:* correlation ≠ per-motif date; Galton's problem and ecological confounds; yields broad
   epochs, not motif ages.
5. **Textual terminus ante quem (+ LLM harvesting).**
   A motif in a dated ancient text (Gilgamesh, Rigveda, Homer, Popol Vuh) is *no younger* than the
   source; `atu_refs` is a weak proxy. An LLM can scale the harvest of earliest attestations against a
   curated dated-source set, with verification.
   *Critique:* strong literacy/geographic bias (nothing for preliterate Americas/Oceania/Africa),
   lower bounds only, hallucination risk → verification mandatory.
6. **Ancestral-state stochastic mapping (SIMMAP).**
   Given a *dated* backbone (from 1/3/4), stochastic character mapping yields a per-motif
   origin-age **posterior with uncertainty** — the principled replacement for the breadth proxy.
   *Critique:* a multiplier on backbone quality, not standalone; assumes tree-like descent we largely
   lack.
7. **Neutral cultural-drift / frequency spectrum (Neiman, cultural-F<sub>st</sub>).**
   Under neutral drift, old = frequent + widespread; the frequency spectrum gives relative age, +1
   anchor → absolute. Principled version of our breadth proxy.
   *Critique:* neutrality is false (myths are selected, not neutral); rate-constancy dubious.
8. **NeighborNet seriation / ordering (Thuillard–d'Huy–Berezkin).**
   A fast NeighborNet orders both peoples and motifs → relative chronology anchored to known
   migrations. Our peel/M17 already approximate it.
   *Critique:* relative only; network ordering unstable; still needs method 1 to anchor.
9. **Archaeological / iconographic fossils.**
   Dated depictions — rainbow serpent rock art, the Cosmic Hunt / Ursa Major (d'Huy: Palaeolithic),
   Pleiades, Mesoamerican codices — as **calibration points**.
   *Critique:* identification subjective and contested; few anchors; rock-art/Old-World bias. Useful
   only inside the Bayesian synthesis (10), not alone.
10. **Bayesian multi-anchor synthesis (FBD / tip-dating).**
    Put *all* anchors (barrier bounds, textual termini, iconographic fossils, language-clade ages) as
    calibration densities into one fossilised-birth-death model over the motif tree → a coherent
    **dated posterior with uncertainty**. Highest ceiling.
    *Critique:* costliest; on clinal data the tree prior is the weak link; premature until 1–3 exist.
11. **Diffusion-front / wave-of-advance fitting.**
    Fit reaction–diffusion to a motif's spatial spread, estimate rate, back-calculate origin.
    *Critique:* under-determined without dated points; idea-spread isn't Fickian (jumps, prestige);
    better realised via the migration surface (mockup 46). Low.
12. **Glottochronology / constant-rate clock.**
    Assume a constant motif-replacement rate; convert similarity to time.
    *Critique:* rate-constancy is the most discredited assumption in the space (failed for language).
    A sanity check at best. Lowest.

**Meta-conclusion (absolute).** Years only via external calibration, and the datable fraction is
limited on clinal data. Recommended order: **2** (how much is datable) → **1** (year-floors on the
substrate) → **3/4** (calibrate the vertical fraction) → optionally **10/6** (coherent dated
posterior). Mockups 46–48 already realise the population-genetics slice; a barrier-bound recast of
M17 (method 1) is the cheapest first artefact with real years.

---

## B. Relative ordering (pseudo-chronology) — the tractable goal

"Ordering is already good enough." A relative old→young sequence *is* reachable internally, and
carries most of the value. It splits into two separable problems: **ordination** (project the
material onto one axis) and **polarity** (argue which end is old — the only place a real assumption
enters).

### B1. Ordination machines (project to an axis), by fit to our data

- **Correspondence Analysis / reciprocal averaging (seriation).** ⭐ cheapest classic. CA's first
  axis simultaneously orders traditions *and* motifs so each motif's presence forms a unimodal
  "battleship curve" along the sequence — literally Petrie–Robinson–Brainerd archaeological
  seriation. Runs directly on the 0/1 matrix, deterministic, seconds. Gives a *raw* order, no
  polarity.
- **Single-cell-style pseudotime (DPT / Slingshot / Monocle).** ⭐ strongest fresh import. An entire
  subfield exists to order unlabelled snapshots into a **trajectory**: build a neighbour graph,
  diffuse over it, order objects along the trajectory — with branching, which CA can't do. Traditions
  / motifs are the direct analog of cells; needs one root object (= polarity).
- **NeighborNet ordering.** The field standard for exactly this data (Thuillard–d'Huy–Berezkin);
  orders both peoples and motifs.
- **Nestedness / NODF.** Under-used: if assemblages are **nested** (set A ⊂ set B), the nesting *is*
  an accumulation order. The NODF metric gives both the order and a test that nestedness exists.
- **Recursive peel + M17 (already built).** Also an ordering — with one baked-in polarity (breadth).

### B2. Polarity — where the arrow points (the crux)

An axis is arrow-less; "older" is an assumption. Sources of the arrow, strong→weak:

- **Outgroup rooting.** Root by the most divergent/isolated assemblage. By out-of-Africa logic,
  Africa as outgroup (Berezkin; 2025 preprint). Firmest.
- **Barrier anchors.** The few motifs we *can* bound (trans-Beringian / Sahul) *must* be old — they
  **fix the arrow's direction** for the whole axis even if individually they give only a bound. This
  is the bridge from §A method 1: a couple of dozen barrier motifs calibrate the polarity of the
  pseudotime.
- **Breadth / disjunction (M17).** Widespread + fragmented = old. Already in hand.
- **Dollo polarity.** A complex motif is gained once, lost many times; Dollo parsimony roots the tree
  and sets direction.
- **Drift frequency spectrum.** Old = frequent. Model assumption, weaker.

### B3. Making it honest — consensus + validation

No single ordering is trustworthy. The defensible procedure:

1. Build **3–4 independent orderings** (CA axis 1, DPT pseudotime, NeighborNet, M17 breadth) and
   **root them with one argument** (Africa outgroup + barrier anchors).
2. Measure their **agreement** (Spearman/Kendall rank correlation). Where methods converge the order
   is real; where they diverge, that flags diffusion or noise.
3. **Externally validate** with the little we have: barrier motifs should land at the old end;
   for the vertical fraction, correlate with language-clade depth (da Silva–Tehrani); for the ATU
   overlap, check against already-dated tales.

If independent ordinations + external anchors agree, that is **defensible relative time**, not just
the single M17 breadth axis.

**Honest limit.** The arrow is still an assumption (outgroup/barriers fix but don't prove it), and
diffusion still masquerades (a widely-borrowed young motif reads old on breadth). So a *consensus of
several polarities* beats any one, and the disagreement between them is a map of where the
pseudotime is unreliable.

### Proposed artefact — mockup 49 "Pseudo-chronology"

Compute CA axis 1, DPT pseudotime and a NeighborNet order; root them by outgroup (Africa) + barrier
anchors; show the **consensus motif rank with agreement bands** (narrow where methods concur, wide
where they argue); validate against the barrier bounds and ATU/language-clade depth. Output: an
ordered ribbon "ancient substrate → young märchen" with an honest reliability marking per segment —
the first artefact where the order comes from *several independent methods with an explicit rooting*,
not one breadth heuristic.

---

## Sources

- da Silva & Tehrani, *Comparative phylogenetic analyses uncover the ancient roots of Indo-European
  folktales*, R. Soc. Open Sci. 2016 — <https://royalsocietypublishing.org/doi/10.1098/rsos.150645>
- Tehrani, *The Phylogeny of Little Red Riding Hood*, PLoS ONE 2013 —
  <https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0078871>
- d'Huy, *A Cosmic Hunt in the Berber sky: a phylogenetic reconstruction of a Palaeolithic
  mythology*, 2013 — <https://shs.hal.science/halshs-00932197/document>
- Thuillard, d'Huy, Berezkin, *A Large-Scale Study of World Myths*, Trames 22(4) 2018 —
  <https://kirj.ee/public/trames_pdf/2018/issue_4/Trames-2018-4-407-424.pdf>
- Berezkin, *Peopling of the New World from Data on Distributions of Folklore Motifs*, 2016 —
  <https://link.springer.com/chapter/10.1007/978-3-319-39445-9_5>
- *Worldwide patterns in mythology echo the human expansion out of Africa*, bioRxiv 2025 —
  <https://www.biorxiv.org/content/10.1101/2025.01.24.634692v1.full>
- Greenhill et al., *Does horizontal transmission invalidate cultural phylogenies?*, Proc. R. Soc. B
  2009 — <https://pmc.ncbi.nlm.nih.gov/articles/PMC2677599/>
- *Detecting contact in language trees: a Bayesian phylogenetic model with horizontal transfer*,
  Humanit. Soc. Sci. Commun. 2022 — <https://www.nature.com/articles/s41599-022-01211-7>
- *A Practical Guide and Review of Fossil Tip-Dating in Phylogenetics*, Syst. Biol. 2026 —
  <https://academic.oup.com/sysbio/article/75/1/156/8262818>
- Havlíček et al. / Neiman, neutral cultural drift & seriation background; Robinson–Brainerd
  seriation; Haemig, NODF nestedness (method references, see the computational-folkloristics survey
  in this directory).
