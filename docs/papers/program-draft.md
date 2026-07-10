# A Natural-History Program for Computational Comparative Mythology

*Computational Comparative Mythology — Paper **II of IV · The Program**. Companions: I The Field · III The Machine · IV The Findings — see [README](README.md).*

### Position, methodology, and roadmap

*Working position/methods draft. It states the *stance*, the *method*, and the *roadmap* of the
MythoScope programme; the empirical results that test its assumptions are reported in the findings
draft (`findings-draft.md`), the tooling in the framework draft (`machine-draft.md`), and the field
context in the survey (`field-draft.md`). The design notes it formalises are
`docs/motifs/proposals/{analysis-program, macro-area-facets, stratum-derivation, roadmap}.md`.*

---

## Abstract

Computational comparative mythology has strong tools but a weak methodological spine: analyses are
often run as one-off correlations over a motif catalogue treated as a flat pool, with no explicit
separation of what is observed from what is inferred and no discipline of falsifiable prediction. We
argue that the field should be organised as a **natural-history science** and walk the arc every
observational discipline walked before it had a theory — **collect → describe → classify → explain** —
as a *dependency order*, not a set of phases. We formalise a three-entity data model (tradition,
motif, attestation) in which a motif's time-depth (`stratum`) is the single **inferred, probabilistic**
field, dated by the *shape of its distribution* rather than by any carrier; we make the programme's
**substantive hypotheses and methodological axioms explicit** so each can be attacked on its own; and
we insist on de-confounding sampling at every step and on **pre-registered falsifiable gates** that
license reporting clean negatives. We describe the method (a geographic depth estimator and a
phylogenetic one, gated by mode and calibrated to calendar age) and the external **data-enrichment**
plan that the residual demands, and we close with a roadmap: from a settled systematics and a datable
descent minority to the large, honestly unexplained cross-continental convergence residual that finer
linguistic, genetic, and historical-corridor calibration must next explain.

## 1. Position

Three commitments define the stance.

**(a) Comparative mythology is a natural-history science, and its data is a catalogue.** Biology went
from cabinets of specimens to comparative anatomy to Linnaean systematics to phylogeny; linguistics
from wordlists to grammar to families to reconstruction. A catalogue of ~3,500 motifs across ~1,050
traditions is the same kind of object, and it rewards the same arc. The stages are a **dependency
order**: you cannot classify what you have not described, or explain a distribution you have not
mapped. This ordering — not a taste for tidiness — is why systematics must precede phylogeny.

**(b) Separate the given from the inferred, and attach confidence to the inferred.** Attestation is
*observed*; a tradition's area, family, subsistence and thematic profile are *given or deterministic*;
a motif's `stratum` (time-depth, mode of spread) is *inferred* and is therefore always a hypothesis
with a confidence, never a fact. Most failures in quantitative folkloristics come from letting an
inferred quantity masquerade as data.

**(c) The curated index is the substrate; the object of study is the shape of its distributions.** The
survey's verdict is that motif *detection* from raw text is unsolved and that embeddings are best used
as retrieval and candidate generation over an expert index. We accept that division of labour: we take
the ATU/TMI/Berezkin indices as given and analyse *where and how* motifs are distributed, with
sampling de-confounded and predictions falsifiable.

## 2. The program: a five-stage arc

| Stage | Biological analogue | Question | Given → inferred |
|---|---|---|---|
| 1 Collection & curation | field collection | What do we have, and how was the gathering biased? | raw sources → a clean, provenanced attestation matrix |
| 2 Morphology | comparative anatomy | What is one motif, and how do we measure it? | a motif → definition, cross-index identity, feature vector |
| 3 Systematics | taxonomy | What kinds are there, on which axes? | features → a closed facet space (the entity model) |
| 4 Phylogeny & etiology | phylogenetics, biogeography | How did each distribution arise, and how old is it? | the mapped space → `stratum`, with confidence |
| 5 Synthesis | evolutionary theory | Which regularities survive, and what still resists? | strata → laws + an honest residual |

The critical, non-obvious move is stage 1's insistence that **collection bias be carried forward, not
forgotten**: tradition coverage a(t) spans 1–738 motifs (median 74), so a densely-catalogued tradition
looks "central" for reasons unrelated to age. That single fact becomes the mandatory
attestation-intensity control that recurs in every later stage.

## 3. Methodology: a three-entity model

Time-depth is a property of a **motif**, not of a tradition — one tradition carries motifs of many
strata at once (a Sub-Saharan corpus holds both a deep African-substratum motif and a recent Islamic
one). This dissolves a category error in the first draft of the model and yields three entities, each
with a small vocabulary:

- **Tradition** — `area` (12 macro-areas) · `family` (~10 language/religion) · `subsistence`
  (4 economies) · `theme_profile` (thematic composition) · coordinates · attestation richness.
- **Motif** — `theme` (Berezkin's Category A/B → 13 groups, the **primary analytical axis**) ·
  `stratum` (the one inferred field) · definition · cross-index links.
- **Attestation** (motif × tradition) — the bare presence, the raw material from which `stratum` is
  inferred.

Expressiveness is **multiplicative and cross-entity**: a tradition profile is
`area × family × subsistence`, each attested motif carries `theme` and `stratum`, and — following
Berezkin's own methodological injunction that the catalogue must be *analysed in parts, primarily by
thematic group*, never as one pool — analysis fixes a `theme` slice first and cross-cuts by the
tradition axes within it. No single axis need be fine-grained. (An empirical audit later showed the
facets are entangled and that theme-profile and area carry the signal; see §6 and the findings draft.)

## 4. Assumptions, made explicit and falsifiable

The programme's premises are stated once, so each can be attacked on its own. **Substantive
hypotheses** (empirical, falsifiable claims about how folklore behaves): (A1) *distribution dates a
motif* — the load-bearing premise; (A2) a shared motif spreads by descent or contact diffusion,
possibly mixed; (A3) breadth + cross-clade spread + cross-barrier **disjunction** ⇒ antiquity; (A4)
disjunction outranks mere breadth (vicariance beats contiguous spread, which contact manufactures
quickly); (A5) phylogenetic clustering ⇒ descent, scatter ⇒ areal; (A6) the language tree proxies the
descent lineages (imperfectly — hence geography corrects phylogeny); (A7) clade depth dates a descent
motif; (A8) geographic span dates an areal motif via the archaeological peopling sequence.
**Methodological axioms** (rules imposed to keep the number honest): keep `theme` out of `stratum`
estimation (it is an independent cross-check, not an input, on pain of circularity); carry the
attestation-intensity control; test spatial autocorrelation (Galton's problem); corroborate across
independent indexes.

Stating them this way pays off because several have since been **tested and some revised**: facet
orthogonality was *falsified* (V(area,family)=0.73); the landscape-permeability upgrade *failed its
gate* (great-circle distance wins); the "African substratum = oldest" reading was *weakened* by a
confirmed back-migration signal (A8's honest edge); and the theme cross-check *corroborated* the
strata independently (cosmology share 64%→24% from areal-deep to descent). An assumption that survives
an attack is evidence; one that fails redirects the programme — which is the point of writing them
down.

## 5. Method

**Two estimators, gated by mode.** *Method A* scores time-depth from the shape of a motif's areal
footprint (prevalence, spread, spatial fragmentation, language-family span, and continental
"mega-set" disjunction), orienting every feature toward "old" by A3–A4 and A8. *Method B* places the
motif on the language-classification tree and runs ancestral-state reconstruction (Fitch parsimony,
upgraded to a two-state Mk gain/loss model with marginal reconstruction), measuring the **phylogenetic
signal** against label permutation to separate descent from diffusion (A5). A **gated combination**
lets B pick the *mode* and the mode pick the dating instrument (clade depth for descent, geographic
disjunction for areal), with confidence from A–B agreement; the otherwise-unresolvable "broad" motifs
split three ways (areal-deep / descent / areal-broad). **Calibration** turns ordinal clade depth into
calendar age via published family-expansion dates (A7).

**De-confounding is not optional.** Attestation intensity is treated as coverage weights, as a
degree-correction in block models, and as an exposure offset in a joint Poisson factorization; a
banality/homoplasy proxy flags likely reinvention; restricted permutation controls Galton's problem;
cross-index replication weights guard against single-catalogue coding artifacts. **Falsifiable gates**
are the programme's discipline: a candidate upgrade (e.g. anisotropic connectivity) must beat the
incumbent *out of sample* before adoption, and a clean negative is reported, not buried — it is what
saves the line from over-fitting a compelling story.

**The irreducible limit, stated up front.** From distribution alone, a deep shared substrate and a
widely diffused innovation can be indistinguishable (the diagnostic pair sun-and-moon vs swan-maiden
receive near-identical mixtures). This residual is *not* a bug to be tuned away; it is the boundary
that external calibration — genetics, corridors, node-level dating — must cross.

## 6. Data-enrichment program

Each explanatory axis needs one external join; their status defines the near-term work.

| Axis | Source | Status |
|---|---|---|
| Subsistence economy | D-PLACE / Ethnographic Atlas | **wired**; gradient confirmed, Galton-robust |
| Language family + expansion dates | Glottolog + curated dates | **wired**; 451 descent motifs calendar-dated |
| Historical corridors | pre-colonial political boundaries | **wired**; weak-but-real cross-area empire effect |
| Landscape connectivity | coarse friction surface | **tested, gate failed**; needs a fine GIS raster |
| Admixture direction | within-Africa footprint proxy | **wired**; back-migration confirmed; a fine SNP graph is the mechanistic upgrade |
| Trade routes | OWTRAD | **pending** |
| Node-level ancestral dates | a dated tree + Bayesian phylogeography (BEAST) | **pending**; current dating is family-resolution only |
| Independent genetic axis | fine SNP populations | **pending**; would separate descent from geography where language and area agree |

The pattern is deliberate: geography and language are cheap and load-bearing; the axes that would
*close the residual* — fine genetics, trade routes, node-level Bayesian ages — are the expensive
pending joins.

## 7. Roadmap

**Done.** A de-confoundable systematics (co-clustering → a joint factorization that recovers the 12
macro-areas de-confounded from sampling); the stratum method with its controls (the deep
both-hemisphere spine survives 320/480); calendar dating of the descent minority; a facet-adequacy
audit (facets recover only ~36% of motif similarity — the set is incomplete); two connectivity gates
(landscape negative, empires weak-positive); the back-migration and cross-index audits; a tradition
stratigraphy that passes its falsification test (deep-share vs peopling age, partial r=+0.48); and a
data-driven re-derivation of the theme axis, shown orthogonal to the etiological one and adopted as a
second facet.

**Next.** (i) Close the convergence residual with the pending enrichments (SNP genetics for a true
third axis, OWTRAD trade routes, node-level BEAST dating). (ii) Productionise the two-facet theme
representation (etiological + narrative) into the pipeline. (iii) Re-run the depth analysis on
calibrated node ages to sharpen the breadth/disjunction proxy. (iv) Promote the settled prototypes
into the reproducible pipeline and release corpus, indexes, and tools.

## 8. Reproducibility and principles

One pipeline off committed sources, no credentials; the prototype series is the lab bench, each a
self-contained `build_data.py` → viewer with fixed seeds; the given/inferred separation is enforced in
the schema; every inferred quantity ships with a confidence and its assumptions; and every headline is
carried both raw and de-confounded so a reader can see what sampling explains.

## 9. Conclusion

The tools of computational folkloristics are ready; what has been missing is a spine. Run comparative
mythology as a natural-history science — collect, describe, classify, explain, in dependency order;
separate the given from the inferred; state the assumptions so they can be attacked; de-confound the
sampling; and gate every upgrade on a falsifiable, out-of-sample prediction — and the catalogue yields
a coherent picture: an areal majority, a datable descent minority, a small deep substrate, and a large,
honestly bounded residual that names the next joins to make. The residual is not a failure; it is the
research programme.

## References

- Berezkin, Yu. E. (2015). Folklore and mythology catalogue: its lay-out and potential for research.
  *Retrospective Methods Network Newsletter* 10, 56–70.
- Fitch, W. M. (1971). Toward defining the course of evolution. *Systematic Zoology* 20(4), 406–416.
- Hammarström, H., et al. (2023). *Glottolog 4.8*. MPI-EVA.
- Kirby, K. R., et al. (2016). D-PLACE: a global database of cultural, linguistic and environmental
  diversity. *PLoS ONE* 11(7), e0158391.
- Naroll, R. (1961). Two solutions to Galton's problem. *Philosophy of Science* 28(1), 15–39.
- Pagel, M. (1994). Detecting correlated evolution on phylogenies. *Proc. R. Soc. B* 255, 37–45.
- **MythoScope design notes** — `docs/motifs/proposals/analysis-program.md` (the arc),
  `macro-area-facets.md` (the entity model & assumptions), `stratum-derivation.md` (axioms & method),
  `roadmap.md`; companion papers `machine-draft.md` (framework), `findings-draft.md` (findings),
  `field-draft.md` (survey).
