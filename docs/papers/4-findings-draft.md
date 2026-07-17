# Geography, Descent, and Genre in the Global Distribution of Folklore Motifs

*Computational Comparative Mythology — Paper **IV of IV · The Findings**. Companions: I The Field · II The Program · III The Machine — see [README](README.md).*

### A computational re-analysis of a cross-indexed mythological motif corpus

*Working draft — synthesises the MythoScope analysis arc (prototype series `mockups/15–44` and
the `docs/proposals/` design notes). Numbers are from self-contained research prototypes
built on the assembled corpus; each carries the documented limits restated in §8.*

---

## Abstract

Comparative mythology has long asked why a narrative motif — the swan-maiden, the theft of fire,
the sun and moon as kin — recurs across cultures that never met: shared descent from a common
ancestral tradition, areal diffusion between neighbours, or independent reinvention. We operationalise
this question on a large, cross-indexed corpus that unifies three standard catalogues — Thompson's
*Motif-Index* (TMI), the Aarne–Thompson–Uther tale-type index (ATU), and Berezkin's areal catalogue
of ~3,500 motifs distributed over ~1,050 ethnographic traditions — linked by a 7,274-edge crosswalk
and embedded with a multilingual transformer (BGE-M3). Working through a collect→describe→classify→
explain program, we find: (i) the catalogues carry genuine, region-coherent cultural structure that
survives de-confounding from catalogue sampling density; (ii) a motif's *time-depth* is legible only
from the **shape of its distribution**, not its content — meaning predicts a motif's theme (58% vs
20% chance) but not its age (breadth r≈0.28); (iii) **areal diffusion dominates**: only ~1% of motifs
are simultaneously widespread and phylogenetically clustered on the language tree (a Eurasian
fairy-tale core), while cosmological motifs are pan-global but areally diffused; (iv) a deep,
trans-hemispheric substrate — chiefly celestial cosmology — is **real but small**, surviving sampling
and banality controls (320/480 motifs); (v) among the etiological "facets" of a tradition, its
*thematic/genre profile* and its *macro-area* carry the signal, while language family and subsistence
are largely redundant, and the facet set explains only ~36% of motif similarity, leaving a large
cross-continental convergence residual that anisotropic landscape connectivity fails to close but
historical empires partially do. Finally, we re-derive the theme taxonomy directly from motif meaning
and show it is **orthogonal** to the traditional etiological one — "how the tale is built" versus
"what the myth explains" — and that the data-driven scheme is a strictly better descriptor of a
tradition (it reduces unexplained motif-similarity from 64% to 44% and nearly subsumes the hand
themes) while the hand scheme better carries the areal signal. We argue for a two-facet representation
and situate the results against the phylomemetic and Pleistocene-mythology literatures.

---

## 1. Introduction

The distribution of a folklore motif across the world's traditions is a palimpsest of history.
Some motifs are inherited within a language family and track its branching, as fairy tales do within
Indo-European (Tehrani 2013; da Silva & Tehrani 2016); some diffuse between neighbouring peoples
irrespective of language; some appear to be so widespread and so old that they have been proposed as
relics of the initial peopling of the continents (Berezkin 2015; d'Huy 2013). Disentangling these
modes — Galton's problem in its oldest form (Naroll 1961) — is the central analytical task of
comparative mythology, and it is fundamentally a problem about the *shape* of a distribution.

Three obstacles have limited quantitative work. First, the major motif catalogues are not
interoperable: Thompson's *Motif-Index* (Thompson 1955–58), the Aarne–Thompson–Uther tale-type index
(Uther 2004), and Berezkin's areal database (Berezkin & Duvakin, *The Electronic Analytic Catalogue
of Folklore Motifs*) index different units with different conventions. Second, coverage is deeply
uneven: a densely catalogued corpus (Europe) records rare motifs that a thinly catalogued one does
not, so raw counts confound history with sampling effort. Third, the standard thematic taxonomy is a
scholar's etiological ordering, and it has never been checked against the structure the material
itself carries.

We assemble the three catalogues into one cross-indexed corpus, add a multilingual semantic embedding
of every motif, and join external ethnographic (D-PLACE), linguistic (Glottolog) and historical
(political-boundary) data. We then run a staged analysis — systematics, phylogeny/etiology, facet
adequacy, connectivity, and a data-driven re-derivation of the theme axis — with de-confounding
controls at each step. This paper synthesises the findings.

## 2. Data and materials

**Motif catalogues.** TMI (~46k motifs), ATU (~2,200 tale types), and Berezkin (3,488 motifs over
1,046 traditions, each placed in a four-level areal hierarchy of 12 macro-areas and carrying a
language chain). A curated crosswalk links the three by constituent, defining, note, summary and
citation evidence, yielding 7,274 confirmed edges; an inferred-triangle layer extends it. Most
analyses use the Berezkin catalogue because it uniquely carries systematic areal distributions.

**Semantic embeddings.** Every motif's name + definition is embedded with BGE-M3 (Chen et al. 2024),
a 1,024-dimensional multilingual model; the Berezkin text is ~96% English (with a ~4% Russian tail).
Recall@k on the confirmed crosswalk validates these against a lexical (LSA) baseline.

**External joins.** Subsistence from D-PLACE / the Ethnographic Atlas (Murdock 1967; Kirby et al.
2016), nearest-society within 600 km; language family and expansion dates from Glottolog (Hammarström
et al. 2023) via a name-first join; pre-colonial political boundaries from historical-basemaps for the
empire-corridor test. Traditions lack coordinates in the source data and are resolved to areal-
subregion centroids — a coarse approximation used only to place points, and a limit on all spatial
results.

## 3. Methods

We follow a four-stage program (collect → describe → classify → explain).

**Systematics.** Motif × tradition incidence is co-clustered (spectral co-clustering; a generative
degree-corrected block model for de-confounding) to recover "for these peoples, these motifs" blocks,
per-index and combined.

**The tradition entity and its facets.** A tradition is modelled by four facets — macro-area, language
family, subsistence, and thematic (genre) profile over 13 groups. We audit whether these are the
right, non-redundant, and complete descriptors (Cramér's V association; drop-one variation
partitioning of pairwise motif-set Jaccard; residual clustering; a granularity curve).

**Depth from distribution (Method A) and from phylogeny (Method B).** Method A scores a motif's
time-depth from the shape of its areal footprint (prevalence, spread, spatial fragmentation, language-
family span, and the number of continental "mega-sets" it touches), emphasising cross-continental
*disjunction* over raw prevalence. Method B places each motif on the language-classification tree and
runs ancestral-state reconstruction — Fitch parsimony (Fitch 1971), upgraded to a two-state Mk
gain/loss model with marginal reconstruction (Pagel 1994) — and measures the **phylogenetic signal**
(observed versus label-permuted gains) to separate descent (clustered on the tree) from diffusion
(scattered). A gated combination lets B pick the *mode* and the mode pick the dating instrument;
theme is deliberately excluded as an input and retained as an independent cross-check. Ordinal clade
depth is calibrated to calendar age with published family-expansion dates.

**De-confounding.** Attestation intensity a(t) (the number of motifs recorded for a tradition, range
1–738) is treated throughout: as coverage weights `w(t)=min(2, median/a(t))`, as a degree-correction
in the block model, and as an exposure offset in a Poisson factorization of the whole matrix. Spatial
autocorrelation (Galton's problem) is controlled by restricted permutation; cross-index replication
weights guard against single-catalogue coding artifacts.

**Connectivity.** Anisotropic **resistance distance** (least-cost paths over a coarse land/sea/
mountain friction surface, Dijkstra on a 1° grid) is tested against isotropic great-circle distance;
dated empire co-membership and admixture-corridor direction are tested as additional covariates.

**Taxonomy re-derivation.** The theme axis is re-derived bottom-up: motif embeddings → UMAP (McInnes
et al. 2018) → two-level k-means (16 clusters × 61 sub-themes), each hand-named, and compared to the
13 hand themes by silhouette, cohesion, balance, coverage, and adjusted Rand, then head-to-head as a
tradition facet.

## 4. Results

### 4.1 The catalogues carry real, de-confoundable cultural structure

Co-clustering the motif × tradition matrix recovers region-coherent tradition blocks paired with their
characteristic motifs — Amazonian, Northwest-Coast, Siberian, Turkic, and a European tale-type block —
consistently across indexes, with Berezkin giving the crispest areal groups. Naively, such clustering
is contaminated by coverage: raw-count clustering separates traditions by a(t) (η²(a(t)|block)=0.80).
A degree-corrected block model halves this to 0.48 while keeping the interpretable blocks, and BIC
selects nine. The structure is not a sampling artifact.

### 4.2 The theme axis is data-confirmed and only partly geographic

Berezkin's high-level split between cosmological/etiological (Category A) and novelistic/trickster
(Category B) material **re-emerges from theme co-occurrence alone** (seriated CLR correlation across
traditions), without using his labels. Themes concentrate strongly by area (lift up to ×3.4 for
Sun & Moon in Australia; Adventures ×1.2 in the Eurasian belt, ×0.3 in Australia). A tradition's genre
profile is a real signal partly independent of geography: macro-area explains 38% of theme-profile
variance — but this is the one headline finding that **weakens under effort-correction** (to ~26%),
so geography's grip on genre balance was partly over-stated by sampling. The subsistence gradient
predicted by the model holds: cosmology's share is high in extractive economies (foragers 54.7%,
horticulturalists 57.6%) and low in intensive/mobile ones (agrarian states 39.5%, pastoralists
36.2%). It survives restricted-permutation control for area (p=0.003) and for language family
(p=0.006) individually, attenuating to marginal (p=0.065) only when both are controlled at once —
subsistence carries its own, partly entangled, contribution.

### 4.3 Areal diffusion dominates; the deep substrate is real but small

Placing motifs on the language tree, only **~1% are simultaneously broad and clade-clustered**, and
those are Eurasian fairy-tale types (Cinderella, "seven at a blow") — an independent recovery of the
published result that märchen track language phylogeny within Eurasia (Tehrani 2013). Cosmology, the
trickster, and the swan-maiden are broad but areally diffused. Method A and Method B are therefore
complementary: B flags the *mode* and dates the descent minority; geography handles the areal
majority. The gated combination splits the otherwise-unresolvable "broad" motifs three ways
(areal-deep / descent / areal-broad); theme, kept out of the model, corroborates — the Category-A
cosmology share falls from 64% in the deep-areal mode to 24% in descent.

A continuous three-way mixture (descent / areal / reinvention) confirms most motifs are areal-dominant
(2,311/2,775) and that Category B is slightly more inheritable than A — but the diagnostic pair A3
(sun-and-moon) and K25 (swan-maiden) receive **near-identical mixtures** (descent≈0.16). The
distinction between a *deep shared substrate* and a *widely diffused* motif is thus **irreducible from
distribution alone** and requires external calibration — a central negative result. Content does not
supply it: nearest-by-meaning motifs share the theme group 58% of the time (vs 20% chance) but content
barely predicts breadth (r≈0.28) or prevalence (0.18). *What* a motif is about is not *how old* it is.

The deep, trans-hemispheric class is nonetheless real. Under the two mandatory controls — coverage
weighting (breadth shrinks 31%) and a banality/homoplasy proxy — 504 motifs (15%) change mode, mostly
areal-broad → areal-recent, but the deep both-hemisphere spine survives 320/480. Cross-index
replication shows the findings are not a Berezkin coding artifact: 48% of motifs are corroborated by
an independent index, corroboration is theme-blind (cosmology 49% = tales 49%) and higher for broad
motifs (54% vs 20% narrow), so the analysis leans on the replicated core.

### 4.4 Dating the descent minority

Joining traditions to Glottolog and calibrating clade depth with family-expansion dates yields
calendar ages for the **451** descent motifs, concentrated at the Indo-European märchen belt (~5,500
BP); the areal majority (A3, K25) is correctly left undated. Reconstructing each dated motif's origin
(spherical centroid within its family) and mapping its spread places, e.g., the fished-up-earth motif
(B4) in Western Oceania with a ceiling at the Austronesian expansion (≤5,200 BP) and spread lines
fanning across the Pacific. These are family-resolution point estimates, not node-consistent
reconstructions with uncertainty (which would require a dated tree and Bayesian phylogeography — BEAST
— left as future work).

### 4.5 Facet adequacy and the connectivity residual

The four tradition facets are **not orthogonal** (V(area, family)=0.73, both tracking one peopling
history). Each is individually non-zero, but **language family and subsistence are nearly redundant**
(unique ΔR²≈0.01); the thematic profile (0.13) and macro-area (0.08) do the work. Critically, the
facet set is **incomplete**: it recovers only ~36% of motif similarity (agreeing across a block-ARI
and a continuous R² estimate), leaving a large cross-continental convergence residual. Two candidate
connectivity axes were tested against this residual. Anisotropic **landscape permeability failed its
falsifiable gate**: out of sample, great-circle distance beat resistance distance across all three sea
regimes (held-out R² 0.158 vs ≤0.110), and adding resistance to great-circle added nothing — either
isolation-by-distance dominates at this scale or a coarse friction surface is inadequate. **Historical
empires** did better, weakly: only ~32% of traditions were ever in a multi-area empire (Old-World
biased), and globally the effect is small (ΔR² +0.011), but the sharp cross-area test is positive —
traditions in *different* macro-areas sharing an empire share ×2.6 more motifs (distance-matched
+0.029). Rome and the Mongol world genuinely moved motifs across boundaries. Testing the direction of
Africa↔Eurasia sharing from within-Africa footprint confirms the back-migration critique: 43% of 836
such motifs sit only in the Eurasian-admixed corridor (corridor-fraction 0.60 vs 0.17 for
Africa-interior motifs, ×3.5), weakening the equation "African substratum = oldest."

A single de-confounded Poisson factorization of the whole matrix, with a(t) as an exposure offset and
cross-index weights, subsumes the piecemeal systematics: in one fit it both **de-confounds** sampling
(η²(log a | component) 0.34, versus 0.67 for naive k-means and ~0.80 for naive co-clustering) and
**recovers geography** (block ARI 0.37 vs 0.08), its 12 emergent components being the 12 macro-areas,
each with a theme profile.

### 4.6 Tradition stratigraphy

Turning depth around — profiling each *tradition* by the share of its motifs that are deep/broad —
yields a falsification test: deep-substrate-rich traditions should sit in early-peopled regions. They
do. The partial correlation between a tradition's deep-share and its region's first-peopling age,
controlling for coverage, is **+0.48** (raw +0.43); the gradient runs Sub-Saharan Africa 63% (~65 ka)
→ early Old World 56–59% → the Americas 48–49% (~14 ka). The coverage confound *masked* the signal
(deep-share correlates −0.30 with a(t)) rather than faking it, so controlling for it strengthens the
result.

### 4.7 The theme axis, re-derived from meaning

Clustering motifs by embedding rather than by a scholar's etiology recovers a **different** taxonomy.
It is far more coherent in content space (silhouette −0.03 for the 13 hand themes → +0.28 for 16
data clusters), more balanced (effective groups 7.4 → 12.1; no 1,243-motif catch-all), and complete
(the 141 un-grouped motifs all receive a theme). Agreement with the hand scheme is only moderate
(ARI 0.12): the celestial/cosmogonic/formulaic block is recovered cleanly and the data even isolates
tight micro-complexes the hand scheme buries (Formulae 100% pure; the African death-messenger complex;
the trickster's zoological *casting* split from trickster *plots*), while the two genre catch-alls —
Adventures (1,243) and Tricks (620) — **dissolve** into narrative complexes (magic-wife, ogre-escape,
animal-fable, revenge) that cut straight across the Adventures/Tricks line.

The two schemes index **orthogonal** things: *etiological function* ("what the myth explains", the
inheritance of the Aarne–Thompson chapter logic) versus *narrative form* ("how the tale is built",
closer to the ATU tale-type and to Propp's functions). Head-to-head as a tradition facet, the
data-driven scheme wins decisively as a descriptor — reproducing the hand theme's published unique
ΔR²=0.125 exactly, then improving it to 0.191 (16 clusters) and 0.321 (61 sub-themes), shrinking the
64% unexplained motif-similarity to 57% and 44%, and nearly **subsuming** the hand theme (whose unique
contribution collapses to 0.003 when both are in the model, versus the narrative facet's 0.069). As a
tradition profile it is even more geography-orthogonal (macro-area explains 31% of its variance vs
38%) and recovers the same cross-continental worldview clusters — a celestial profile linking Cherokee,
Ancient Italy, southeastern Australia and the Netsilik. But as an **areal marker** it is worse at the
coarse level (Cramér's V of theme×area 0.102 vs 0.125), recovering only at the 61-sub-theme
resolution: the hand scheme's areal signal is carried precisely by its etiological categories, which
the broad narrative clusters dilute. Finally, running depth on the narrative taxonomy exposes a
gradient the flat catch-alls averaged away: narrative clusters range from cross-continental span 1.00
(Formulae) to 2.10 (death-messenger); deep clusters are etiological (0–32% drawn from the catch-alls),
shallow ones are märchen (82–90%), and — the payoff — the swallowing-monster/body complex is deep
(span 1.80) yet 53% built from motifs Berezkin filed under Adventures/Tricks, a deep stratum the flat
category hid.

## 5. Discussion

Three conclusions cut across the results.

**Geography is primary; descent is a minority mode; deep inheritance is real but small.** The dominant
signal in a global motif corpus is areal — isolation-by-distance and neighbour diffusion — with a
well-defined but ~1% descent minority (the Eurasian märchen) that tracks language and can be dated,
and a small trans-hemispheric substrate (chiefly celestial cosmology) that survives de-confounding and
aligns with peopling age. This is consistent with, and quantifies, both the phylomemetic programme
(Tehrani 2013; da Silva & Tehrani 2016) and Berezkin's and d'Huy's Pleistocene-substrate hypotheses,
while showing that the two operate on largely disjoint slices of the corpus.

**Depth is a property of distribution, not of meaning — and it is only partly recoverable.** No linear
score, no embedding, and no single facet dates a motif; the diagnostic contrast between a deep shared
substrate and a widely diffused innovation (A3 vs K25) is irreducible from distribution and demands
external calibration. Honest connectivity modelling matters here: a coarse landscape-friction model
*fails* a pre-registered gate, and only dated historical corridors add real cross-area signal. The
discipline of falsifiable gates — reporting the clean negatives — is what keeps such a program from
over-fitting a compelling story.

**A catalogue's theme axis encodes a choice, and there are two good ones.** The traditional taxonomy
orders motifs by what they explain; a bottom-up taxonomy orders them by how the story is built. Neither
is "correct": they are orthogonal projections, and they are each better at a different job — narrative
form for describing a tradition and for resolving the depth hidden inside genre catch-alls, etiological
function for reading geography. The practical implication is a **two-facet** representation rather than
a replacement.

## 6. Related work and contribution

Computational folkloristics falls into two eras (the full landscape is surveyed in
`docs/research/`). The **classical era** (c. 2008–2018) digitised and formalised the ATU and Thompson
indices, induced motifs with topic models (Karsdorp & van den Bosch 2013), added WordNet-based
semantic search over the Motif-Index (MOMFER: Karsdorp et al. 2015) and interoperable OWL/RDF
ontologies (Declerck & Lendvai 2011), ran phylogenetics of tales and myths (da Silva & Tehrani 2016;
d'Huy 2013; Thuillard, d'Huy, Le Quellec & Berezkin 2018), and analysed character and motif networks
(Mac Carron & Kenna 2012; Abello, Broadwell & Tangherlini 2012). The **modern era** (2018–2026) is
dominated by transformer embeddings and BERTopic-style clustering (Tangherlini & Chen 2024) and by
LLM motif/type annotation (Arčon et al. 2025) — which is repeatedly matched by simple TF-IDF/SVM
baselines (Eklund et al. 2023; Meaney et al. 2024), so motif *detection* from raw text remains
unsolved and is best treated as candidate generation over a curated index.

Our contribution is orthogonal to that detection problem: we take the **curated index as given** and
analyse the *shape of its distributions*. Relative to the phylomemetic programme — which codes
presence/absence over a **curated tale-type set within a single family** and runs Bayesian
phylogenetics (da Silva & Tehrani 2016; Sakamoto Martini, Kendal & Tehrani 2023) — we (i) work over a
**whole areal catalogue** rather than a hand-picked subset, (ii) add an explicit **areal-diffusion
mode** and a gated descent/areal/reinvention decomposition rather than assuming a tree, (iii) carry
**sampling and banality de-confounding** throughout (Galton's problem: Naroll 1961), and (iv) insist on
the **irreducibility** of the deep-substrate-vs-wide-diffusion contrast without external calibration.
The deep-substrate results engage Berezkin (2015) and d'Huy (2013) under these controls. The
re-derived theme taxonomy connects the etiological logic of Thompson (1955–58) with the tale-type logic
of Uther (2004) and the morphological tradition of Propp (1928) and Lévi-Strauss (1955); the recovered
trickster-casting and death-messenger complexes echo Boas (1916), Radin (1956) and Abrahamsson (1951).
This paper is the *findings* companion to the infrastructure/framework draft
(`docs/papers/3-machine-draft.md`); the full theme re-derivation and the field survey live separately in
`docs/proposals/archive/theme-taxonomy-comparison.md` and `docs/research/`.

## 7. Reproducibility

Every result is produced by a self-contained prototype (`build_data.py` → static viewer) reading only
the assembled corpus and the committed external joins; clustering and factorization use fixed random
seeds. The re-derived taxonomy is exported as a per-motif facet (`narrative_taxonomy.json`) consumed by
the downstream comparisons. The full method for each figure is in the corresponding `mockups/*/README`.

## 8. Limitations

(i) Traditions are placed at areal-subregion centroids, not true coordinates, bounding all spatial
results. (ii) "Depth" is a breadth/disjunction proxy that conflates ancient descent with wide
diffusion; only the ~13% descent minority is calendar-dated, at family (not node) resolution. (iii) The
crosswalk is partly automated and under-counts links (the swan-maiden's ATU 400 was missed), so
cross-index corroboration is a lower bound and berezkin-only an upper bound on coding dependence. (iv)
Embedding-based clustering reflects catalogue phrasing (name+definition), depends on model and UMAP
hyper-parameters and seed, and must not be used as an axis independent of content (it is circular by
construction). (v) The landscape-friction surface is coarse; a fine GIS raster and wired trade-route
data (OWTRAD) could revisit the negative connectivity gate. (vi) The joint factorization is a MAP/NMF
core, not a full Bayesian model with uncertainty. (vii) These are research prototypes, not a frozen
released dataset; numbers may shift as the corpus is refined.

## 9. Conclusion

On a large cross-indexed global motif corpus, the geography of a myth is written primarily in *where*
it is attested, not in *what* it says: areal diffusion dominates, a datable fairy-tale descent minority
tracks language, and a small trans-hemispheric cosmological substrate survives every control and aligns
with the peopling of the continents. A tradition is best described by its macro-area and by the
*narrative form* of its corpus — a data-derived axis that outperforms and nearly subsumes the classical
etiological themes as a descriptor — while those etiological themes remain the better instrument for
reading geography. Two orthogonal theme axes, one deep-substrate spine, and a large, honestly
unexplained convergence residual: that is the current shape of myth in this corpus, and the residual is
the map of what a finer linguistic, genetic, and historical-corridor calibration must next explain.

---

## References

- Abello, J., Broadwell, P., & Tangherlini, T. R. (2012). Computational folkloristics.
  *Communications of the ACM* 55(7), 60–70.
- Abrahamsson, H. (1951). *The Origin of Death: Studies in African Mythology*. Uppsala.
- Arčon, I., Robnik-Šikonja, M., & Tratnik, P. (2025). Large language models for folktale type
  automation based on motifs: a Cinderella case study. *arXiv:2510.18561* (*Fabula*).
- Berezkin, Yu. E. (2015). Folklore and mythology catalogue: its lay-out and potential for research.
  *Retrospective Methods Network Newsletter* 10, 56–70.
- Berezkin, Yu. E., & Duvakin, E. N. *The Electronic Analytic Catalogue of Folklore Motifs* (Tales of
  the Peoples of the World / ruthenia mythology database).
- Boas, F. (1916). *Tsimshian Mythology*. Bureau of American Ethnology.
- Chen, J., Xiao, S., Zhang, P., Luo, K., Lian, D., & Liu, Z. (2024). BGE M3-Embedding: Multi-lingual,
  multi-functionality, multi-granularity text embeddings. *arXiv:2402.03216*.
- d'Huy, J. (2013). A phylogenetic approach to mythology and its archaeological consequences.
  *Rock Art Research* 30(1), 115–118.
- da Silva, S. G., & Tehrani, J. J. (2016). Comparative phylogenetic analyses uncover the ancient roots
  of Indo-European folktales. *Royal Society Open Science* 3, 150645.
- Declerck, T., & Lendvai, P. (2011). Towards a standardized linguistic annotation of the textual
  content of labels in knowledge representation systems. *LREC*.
- Eklund, J., Hagedorn, J., & Darányi, S. (2023). Teaching tale types to a computer. *Fabula* 64(1–2),
  92–106.
- Fitch, W. M. (1971). Toward defining the course of evolution: minimum change for a specific tree
  topology. *Systematic Zoology* 20(4), 406–416.
- Gopalan, P., Hofman, J. M., & Blei, D. M. (2015). Scalable recommendation with hierarchical Poisson
  factorization. *UAI*.
- Hammarström, H., Forkel, R., Haspelmath, M., & Bank, S. (2023). *Glottolog 4.8*. MPI-EVA.
- Karsdorp, F., & van den Bosch, A. (2013). Identifying motifs in folktales using topic models.
  *BENELEARN*.
- Karsdorp, F., van der Meulen, M., Meder, T., & van den Bosch, A. (2015). MOMFER: a search engine of
  Thompson's Motif-Index of Folk Literature. *Folklore* 126(1), 37–52.
- Kirby, K. R., et al. (2016). D-PLACE: A global database of cultural, linguistic and environmental
  diversity. *PLoS ONE* 11(7), e0158391.
- Lévi-Strauss, C. (1955). The structural study of myth. *Journal of American Folklore* 68, 428–444.
- Mac Carron, P., & Kenna, R. (2012). Universal properties of mythological networks. *EPL* 99, 28002.
- Mantel, N. (1967). The detection of disease clustering and a generalized regression approach.
  *Cancer Research* 27, 209–220.
- McInnes, L., Healy, J., & Melville, J. (2018). UMAP: Uniform Manifold Approximation and Projection.
  *arXiv:1802.03426*.
- Meaney, C., Alex, B., & Lamb, W. (2024). Classification of tale types and narrator gender in Gaelic
  folktales. *NLP4DH*.
- Murdock, G. P. (1967). *Ethnographic Atlas*. University of Pittsburgh Press.
- Naroll, R. (1961). Two solutions to Galton's problem. *Philosophy of Science* 28(1), 15–39.
- Pagel, M. (1994). Detecting correlated evolution on phylogenies: a general method for the comparative
  analysis of discrete characters. *Proc. R. Soc. B* 255, 37–45.
- Propp, V. (1928). *Morphology of the Folktale* (Eng. trans. 1968). University of Texas Press.
- Radin, P. (1956). *The Trickster: A Study in American Indian Mythology*. Philosophical Library.
- Sakamoto Martini, S., Kendal, J., & Tehrani, J. J. (2023). A phylomemetic analysis of Cinderella
  (ATU 510/511). (Bayesian inference + NeighborNet, 266 versions).
- Tangherlini, T. R., & Chen, J. (2024). Travels with BERT: mapping intertextuality in Andersen.
  *Orbis Litterarum* 79, 519–562.
- Tehrani, J. J. (2013). The phylogeny of Little Red Riding Hood. *PLoS ONE* 8(11), e78871.
- Thompson, S. (1955–58). *Motif-Index of Folk-Literature* (6 vols). Indiana University Press.
- Thuillard, M., d'Huy, J., Le Quellec, J.-L., & Berezkin, Yu. E. (2018). A large-scale study of world
  myths. *Trames* 22(4), 407–424.
- Uther, H.-J. (2004). *The Types of International Folktales* (ATU). FF Communications 284–286.
