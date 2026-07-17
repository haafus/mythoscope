# Dating & chronology methods for the motif corpus

How to put a **time axis** on the Berezkin motif material (3488 motifs × ~1000 traditions,
with coordinates, `language`, and `atu_refs`). Compiled 2026-07 from web validation of the
computational-mythology literature plus method transfer from population genetics, archaeology,
climate science and single-cell biology. Companion to
[`../proposals/archive/stratigraphic-peeling.md`](../proposals/archive/stratigraphic-peeling.md) (the M17 depth
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

> **Much of this is already built** — the roadmap M-series (mockups 17–39) is a prior dating/stratigraphy
> programme; the mockup 45–50 arc re-treads a lot of it. The genuinely *realised* calendar dating lives in
> **M30 · dated-phylogeny** (language-family expansion dates, 451 motifs), **M28 · likelihood-ASR** (dated
> gain/loss reconstruction) and **M31 · Bayesian phylogeography**; admixture in **M36/M38**, dated contact in
> **M35**, cost-distance geography in **M34**. The ✅ tags below point at the existing mockup, not at future
> work. **Two calendar methods now exist and were cross-validated** (M30 family-ages × mockup-50 textual
> floors): only **40 motifs overlap**, they don't rank-correlate (Spearman −0.03, different clocks) but are
> **fully consistent** (textual floor ≤ family age in 100% of cases) and **complementary** — union **1118**
> motifs get some calendar estimate, vs 451 from M30 alone.

1. **Biogeographic lower bounds (recast M17 into years).** ⭐ best cheap win. ✅ realised — mockup 49 (②).
   A motif whose distribution spans a known barrier under signs of shared inheritance is *no younger*
   than the crossing: trans-Beringia ~15–17 ka, Sunda–Sahul, Wallace line, the Austronesian island
   sequence. This is Berezkin/d'Huy/Thuillard's own logic (Old- vs New-World set comparison anchored
   to the peopling of America). Turns M17 percentiles into real year-floors for the disjunct
   substrate (the mockup-48 teleconnector motifs). Needs only our data + hard-coded barrier dates.
   *Critique:* lower bounds only; barrier-spanning motifs only; one ancient long-range jump is
   indistinguishable from deep inheritance.
2. **Datability partition (phylogenetic-signal gate).** ✅ realised — mockups 18/28 (phylo-signal) + 49 (①).
   Not a date but the prerequisite: D-statistic (Fritz–Purvis), δ-score, TIGER, Q-residuals,
   retention/consistency index on a reference tree tell *which* motifs are tree-like enough to date.
   On clinal data, estimating that fraction is itself a first-order result. M18/M28 compute the Fitch/Mk
   phylo-signal that M30 already uses as its descent gate; mockup 49 (①) adds the areal-tree NRI route split.
   *Critique:* needs a reference tree (areal or language); on reticulate data the tree is shaky —
   but that is exactly why this gate must come first.
3. **Language-phylogeny calibration.** ✅ realised — mockup 30.
   Map motif presence onto dated language trees; a motif congruent with a clade inherits its expansion age.
   The da Silva–Tehrani method that dated "tales of magic" to the Bronze Age. **Built** in
   [`mockups/30-dated-phylogeny`](../../mockups/30-dated-phylogeny/README.md): Berezkin traditions joined to
   Glottolog (median 53 km) + a curated 45-family expansion-date table (Bouckaert, Gray, Grollemund, Heggarty,
   Bowern…). A motif that is phylo-clustered (signal ≥ 0.4) *and* ≥ 55% in one family is dated to that family's
   spread → **451 motifs dated**, ~9000 BP (Afro-Asiatic) → ~1500 BP (Quechuan), peak at Indo-European ~5500 BP.
   *Critique confirmed:* covers only the language-tracking minority; the areal majority (sun & moon, swan-maiden)
   is correctly left undated — its age is a geographic question, not a phylogenetic one.
4. **Genetic co-phylogeny calibration.** ◑ partially realised — mockups 31/36.
   Correlate motif distances with **dated human population splits** (absolute dates from genomics:
   out-of-Africa ~60 ka, LGM, Beringia). Berezkin and the 2025 bioRxiv preprint do this — mythemes
   correlate with pre-LGM movements ≥38 ka. M31 (Bayesian phylogeography) reconstructs dated descent origins;
   M36 (admixture-graph back-migration) uses settled human back-migration geography to direction Africa↔Eurasia
   sharing. A direct motif-distance × dated-genetic-split regression is still open.
   *Critique:* correlation ≠ per-motif date; Galton's problem and ecological confounds; yields broad
   epochs, not motif ages.
5. **Textual terminus ante quem (+ LLM harvesting).** ✅ realised — mockup 50.
   A motif in a dated ancient text (Gilgamesh, Rigveda, Homer, Popol Vuh) is *no younger* than the
   source; `atu_refs` is a weak proxy. An LLM can scale the harvest of earliest attestations against a
   curated dated-source set, with verification. **Built** in
   [`mockups/50-dated-attestations`](../../mockups/50-dated-attestations/README.md) using Berezkin's *own*
   dated literate traditions as the corpora (15: Sumer, Egypt, Hittite, Ugarit, Vedic, Early Chinese, … →
   Aztec): **707 motifs floored** in calendar years, **329 of them not reachable by any barrier** (total
   absolute-floored 1284 → 1613); the oldest documented (Egypt ~2350 BCE) are the celestial substrate,
   recorded independently across up to 9 corpora. *Critique confirmed:* strong literacy bias — documented age
   is **flat against M17 depth (r = 0.02)**, so it is a hard-anchor layer, not a universal clock; lumped
   corpora (Vedic + Purana) over-state the old end (flagged); mixed corpora (Korea) excluded to avoid
   false-ageing.
6. **Ancestral-state stochastic mapping (SIMMAP / Mk).** ✅ realised — mockup 28.
   Given a *dated* backbone (from 1/3/4), a continuous-time Markov (Mk) gain/loss model with marginal
   ancestral-state reconstruction yields a per-motif origin estimate — the principled replacement for the
   breadth proxy. **Built** in [`mockups/28-likelihood-asr`](../../mockups/28-likelihood-asr/README.md):
   loss-biased (Dollo-flavoured) Mk, run on both the undated tree (reproduces parsimony, corr 0.91) and the
   **M30-dated family-scaled tree**. Full stochastic tip-dated *posterior* (real BEAST) stays future.
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

> **Two more effort/mode confounds, tested and recorded (mockups 52/54 arc).**
> - **Serial-founder / out-of-Africa** (would date an *origin* by diversity decline): naively **fails** — per-tradition
>   richness *is* cataloguing effort, so the best-declining "origin" is the **Levant** (r = −0.44), i.e. the
>   over-studied Old-World literate zone, not Africa (E-Africa only −0.27). Needs an effort-rarefied diversity to
>   test properly; the effort-robust **beta-turnover** (mockup 52) instead shows Europe homogenised, Africa/Tibet
>   divergent — a real signal but about homogenisation, not origin.
> - **Rate-by-stratum / "old = conserved"** (§Q9): a naive homoplasy conservation index gives the *opposite* —
>   deep (M17) motifs look **more** homoplastic (0.65 vs 0.49, corr +0.39) — but only because "deep" here means
>   *areal / cross-family*, which is high-homoplasy on a language tree by construction. The measure conflates
>   areality with volatility, so it cannot test mutation rate; **Q9 stays unresolved** by the same descent-vs-areal
>   confound that limits everything else.

**Meta-conclusion (absolute).** Years only via external calibration, and the datable fraction is
limited on clinal data. The recommended chain — **2** (how much is datable) → **1** (year-floors on the
substrate) → **3/4** (calibrate the vertical fraction) → optionally **10/6** (coherent dated posterior) —
is **already largely built**: methods 1, 2, 3, 6 are realised (mockups 49, 18/28, 30, 28) and 4 partially
(31/36). The **union of the two calendar routes** — M30 language-family ages (451) + mockup-50 textual floors
(707), overlap only 40 — gives **~1118 motifs** a calendar estimate, all mutually consistent. The remaining
open work is the top of the ladder: **method 10** (a single FBD/tip-dating model folding barrier bounds +
textual termini + family ages + iconographic fossils into one dated posterior with uncertainty) and a real
BEAST phylogeography (M31's stated future). Everything below method 6 in the ranking (drift, seriation,
fossils, glottochronology) remains a sanity-check tier, not a build target.

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

### Realised — mockup 49 "Chronology"

Built as [`mockups/49-chronology`](../../mockups/49-chronology/README.md), one page with three linked
views: **① datability** (the NRI route partition — barrier/tree/weak), **② barrier floors** (trans-Beringian
≥ 15 ka, pan-American ≥ 13 ka, Sahul ≥ 50 ka contested), and **③ pseudo-chronology** (CA seriation +
diffusion pseudotime + M17 + prevalence, rooted by barrier anchors, with agreement bands).

The result confirmed the honest ceiling this note predicted. The **coarse** polarity is validated —
barrier-anchor motifs land old (mean consensus rank 0.69), ATU tales land young (0.33). But there is **no
robust fine-grained order**: CA seriation and diffusion pseudotime agree (0.94) only because the **dominant
ordination axis is geography, not time** (their correlation with New-World share is 0.87 / 0.84); the
age-oriented heuristics (M17, prevalence) agree only weakly; mean agreement is 0.63. Naive ordination
recovers *space* readily and *time* only coarsely — exactly the polarity/interpretation trap flagged in §B2.
The mockup surfaces this rather than hiding it. (NeighborNet was substituted by the diffusion-map pseudotime;
outgroup rooting by the barrier anchors — both are the tractable equivalents on our data.)

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
