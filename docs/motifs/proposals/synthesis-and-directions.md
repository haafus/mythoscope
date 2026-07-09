# Synthesis & directions — the system as one object, and where it goes next

A joint reading of everything built so far — the program arc
([`analysis-program.md`](analysis-program.md)), the two proposals
([`macro-area-facets.md`](macro-area-facets.md),
[`stratum-derivation.md`](stratum-derivation.md)), the taxonomies, and mockups 01–23. Not a
recap of conclusions (those live in each doc's "cumulative conclusions"); this is the
cross-cutting analysis: **what influences what, what reinforces what, how to combine it, the
alternative hypotheses we should fear, and the highest-leverage moves next.**

## 1. The whole thing is two threads through one matrix

Everything derives from **one measurement** — the attestation matrix `M` (motif × tradition,
binary presence) — plus a few deterministic reads (`area←areal_path`, `theme←motif_group`,
`family←language`) and external joins (`subsistence←D-PLACE`). Drawn as an influence graph,
two things thread through *all* of it:

- **A shared confounder — sampling effort `a(t)`.** It contaminates every count-based
  quantity, not just `stratum`: `theme_profile` (a densely-catalogued corpus looks
  genre-rich), the `theme × area` lift, the `subsistence × theme` gradient, and breadth-as-age
  alike. Mockup 20 showed it thins the "broad areal" class by a third — but it was only ever
  applied to `stratum`. **The same correction belongs everywhere counts are used.** Until it
  is, every positive signal carries the same asterisk.
- **A shared latent — the peopling of the world.** `area` (where a people is *now*), `family`
  (its *language lineage*), and `stratum` (when a motif *arrived*) are not three independent
  axes — they are **three projections of one space-time history**: space, lineage, time.
  That is *why* "the three axes each remove the others' confound" (the recurring conclusion):
  they triangulate one underlying process. This reframes the model — instead of three facets
  to populate separately, there is **one latent phylogeographic history**, and area / family /
  stratum are its observable coordinates.

Everything else is a cross-link between projections: `area → theme_profile` (38% of variance,
mockup 16); `subsistence ↔ theme` (gradient, mockup 22, confounded by area); `theme ↔ theme`
(the A/B co-occurrence blocks, mockup 23); `theme → stratum`-tendency (aggregate prior);
`area → stratum` (Method A dates the areal majority); `family → stratum` (Method B, the ~1%
descent minority).

## 2. What reinforces / refines what (the triangulation map)

The mockups are not independent probes — several measure the same latent from different
angles, and that agreement is the real evidence:

- **The theme axis is triple-confirmed.** Berezkin *declares* A/B; theme co-occurrence
  *recovers* it from correlation alone (23); `theme_profile` clustering (16) and the
  `subsistence × theme` gradient (22) show the same cosmology-vs-tales split organising
  traditions. Four independent routes to one division ⇒ it is real, not editorial.
- **A refines B and B refines A** (stratum): geography dates the areal majority B can't;
  phylogeny filters A's false "deep disjuncts" (the B4 case). Mockup 19 gates them; mockup 20
  shows the gated result survives bias-correction on its deep spine.
- **theme_profile could refine stratum, untested.** If a tradition's genre balance predicts
  *which strata it carries*, then `theme_profile` is a tradition-level prior on the motif-level
  `stratum` — a link we drew but never measured.
- **The crosswalk (TMI/ATU) is unused replication.** A motif attested in all three indexes
  with a consistent map is high-confidence; cross-index *disagreement* localises coding
  artifacts. We have this signal and don't use it (only mockup 17's `xindex` touches it).

## 3. The combination move: one joint model instead of a pipeline

The mockups are a *pipeline of separate estimators* that each re-discover pieces of the same
structure and each re-fight the same confounder. The strongest consolidation is a **single
joint latent-variable model over `M`**:

> Cell probability `P(motif m present in tradition t) = f(tradition factors, motif factors)`
> with a **per-tradition sampling offset** `a(t)` baked in, where tradition factors are
> `area · family · subsistence · latent-history-position` and motif factors are
> `theme · latent-stratum`.

Fitting this once would: (a) factor out sampling **globally** rather than per-mockup;
(b) estimate `stratum` jointly with everything, so `theme`/`area`/`family` act as the
covariates that de-confound it (exactly the "three axes remove each other's confound" claim,
made formal); (c) yield honest posteriors and confidences instead of stacked heuristics. Two
concrete shapes: a **Bayesian hierarchical logistic** (facets as fixed effects, history +
stratum as latents, `a(t)` as offset), or the **reticulate tree+migration** model already
sketched in `stratum-derivation.md` §12.4 (one run partitioning each motif into inherited vs
borrowed shares, A=space and B=tree as two observations). The pipeline mockups become its
validation harness, not its replacement.

## 4. Alternative hypotheses we should actively try to confirm

Every headline has a deflationary rival; naming them is the honest move.

1. **It's all sampling.** The subsistence×theme gradient, the theme×area lift, breadth-as-age
   — could be artifacts of collection intensity and Berezkin's own regional focus. *Tested
   (mockup 24):* **3 of 4 survive** effort-correction — the subsistence gradient, theme×area
   lift and A/B co-occurrence blocks hold; only theme_profile's variance-by-area weakens
   (34%→26%), so it was partly over-stated but not manufactured. Alt-hypothesis largely
   **rejected** for the theme findings; breadth-as-age was already handled in mockup 20.
2. **`stratum` isn't one axis.** The A3-vs-K25 residual hints that "depth" may be
   ill-posed — motifs may be **mixtures** of an areal-substrate component, a descent
   component, and a reinvention rate, with no single ordinal "age". *Tested (mockup 27):*
   a per-motif descent/areal/reinvention decomposition **partly upholds** this — most motifs
   are areal-dominant, tales slightly more inheritable, and the continuum beats the binary
   gate — but the residual **does not dissolve**: A3 and K25 get near-identical mixtures, so
   deep-substrate-vs-wide-diffusion stays irreducible from distribution and needs external
   calibration (M30/M31).
3. **Wrong tree, not rare descent.** Method B found ~1% follow the *language* tree — but a
   **population-genetic** or a **cultural** tree might fit better. "Geography is primary" may
   be "language is the wrong lineage." *Test:* re-run Method B on a genetic/admixture tree.
4. **The A/B blocks are corpus-type, not worldview.** Oral-vs-literate collection could
   manufacture the cosmology/tales split (literate corpora over-record adventures). *Test:*
   control for corpus register / `family` religion overlay before reading the blocks.
5. **Reverse causation on subsistence×theme.** Maybe neither causes the other — both are
   downstream of deep history/area. *Tested (mockup 25):* the association **survives**
   restricted permutation within area (p=0.003) and within language family (p=0.006), so
   subsistence carries its own contribution beyond area and shared ancestry individually —
   only jointly controlling both does it attenuate to marginal (low power). Not reducible to
   a pure common cause on the evidence so far.
6. **Africa is a sink, not only a source.** Axiom A8 treats the peopling sequence as a
   one-way pump, so "shared Sub-Saharan Africa ↔ rest" reads as deep out-of-Africa. But
   documented **back-migrations into Africa** (Eurasian back-flow, Afroasiatic /
   Arab-Islamic / colonial spread) mean such a motif can be *recent into Africa*. *First
   probe:* Eurasia-shared motifs skew only slightly more toward the Afroasiatic corridor
   than Africa-endemic ones (6% vs 3% of the African foothold; both ~92% deep-lineage), so
   the family proxy is too blunt to resolve **direction** — which distribution simply cannot
   fix. This is the same direction-underdeterminacy as the A3-vs-K25 residual, on the Africa
   axis, and it weakens the "African substratum = oldest" stratum specifically. *Fix:* a
   reticulate/admixture graph (M32) with the published Eurasian-into-Africa gene flow as
   horizontal edges, plus an Islamicate/Horn-Sahel back-migration mask and a sink-vs-source
   elaboration-asymmetry test (`stratum-derivation.md` §14).

## 5. Highest-leverage next steps (ranked by effect)

1. **Global effort-correction pass (epistemic leverage).** Apply the §5 attestation-intensity
   weighting to *every* count-based mockup (16, 22, 23), not just 20. This is cheap and it
   either validates or kills half of our findings — the single highest-value experiment,
   because it resolves alternative-hypothesis #1 across the board.
2. **Wire the dated phylogeny (capability leverage).** Glottolog CLDF + the Bouckaert/EDGE
   dated global tree turns `stratum` from an *ordinal mode* into an *absolute age*, and opens
   external validation against published phylomemetic dates. This is the one missing external
   resource that unlocks a genuinely new class of conclusion (§14 build-task #3).
3. **Within-area partial correlations (decisiveness leverage).** Recompute subsistence×theme
   and theme×stratum *within* each macro-area (or as partial correlations controlling for
   area). Cheap, and it decisively separates the signals we keep flagging as area-confounded.
4. **Motif content × stratum (independent-signal leverage).** *Done (mockup 29):* content
   (BGE-M3) predicts **theme** strongly (nearest-by-meaning share theme 58% vs 20% chance) but
   **depth** only weakly (breadth corr 0.28) — an independent confirmation that stratum is
   distributional, not semantic. The content-banality idea was an honest negative (embedding
   density flags near-duplicates, not homoplasy).

## 6. New ideas that would push the work forward

- **Tradition stratigraphy.** Turn `stratum` around: profile each *tradition* as a stack of
  strata (its share of African-substratum / Indo-Pacific / … / colonial motifs) — a
  geological-column view of a corpus. "Which traditions are deep-substrate-rich vs
  recent-heavy" is a new, directly-mappable tradition facet, and a strong check (deep-rich
  traditions should cluster in refugia / early-peopled regions).
- **Descent–diffusion as a continuum, not a gate.** Replace mockup 19's binary mode switch
  with a per-motif **inherited-share ∈ [0,1]** from the reticulate model — most motifs are
  mixtures, and the gate currently forces a false dichotomy.
- **Phylogeographic reconstruction (the visual capstone).** Animate each deep motif's inferred
  spread over the peopling map (origin node → range) — the etiology stage made legible, and a
  powerful validation surface (does the reconstruction respect known migration routes?).
- **Connectivity-aware geography (two layers).** Method A currently measures geography as
  *isotropic* great-circle distance — 500 km of steppe, ocean and Himalaya count the same.
  Replace it with **connectivity**, in two composable layers:
  - **Physical, always-on, valid at all depths — landscape permeability.** A friction surface
    from terrain + biome + hydrography → **resistance / least-cost distance** between
    traditions ("isolation by resistance", not by distance). Low-friction corridors (the
    Eurasian steppe, navigable rivers, coastlines) explain far-but-connected sharing that
    isotropic distance mis-files as *deep*; barriers make close-but-separated sharing *more*
    surprising. This is the physical substrate the human corridors ride on, and — being
    time-stable — the one connectivity layer that also speaks to the **deep** residual.
    Roadmap **M37**.
  - **Human, dated, shallow — historical corridors.** Explicit edges: empire footprints, the
    Silk Road, maritime trade, missions, the slave trade — this is what actually dates the
    axial/literate and colonial strata that distribution shape *cannot* reach (the §14 open
    question of whether the historical strata even belong on the same axis). Roadmap **M38**.
  Both feed a connectivity-aware Method A and a connectivity-aware Galton null; the deepest
  questions want a *time-sliced* friction surface (paleo-coastlines, the green Sahara).
- **Cross-index arbitration.** Use TMI+ATU as a replication vote: promote motifs consistent
  across indexes, flag Berezkin-only ones as coding-dependent — a confidence multiplier we
  already have the data for.

## 7. Data that would unlock new strong conclusions

Ranked by what each *newly enables*, not by ease:

| Data | License | Unlocks |
|---|---|---|
| **Glottolog CLDF** (tree + tip coords) | CC-BY | descent on a real classification; join key for everything below |
| **Bouckaert/EDGE dated phylogeny** | open | absolute node **ages** → ordinal stratum becomes calendar time |
| **Human genetic / admixture data** | open (published) | an *alternative descent tree* to test "wrong tree vs rare descent" (alt-hyp #3) |
| **D-PLACE beyond subsistence** (settlement, political complexity, kinship) | CC-BY | more tradition covariates → de-confound the theme gradients |
| **Archaeology / paleoclimate** (peopling dates, LGM refugia) | open | *calibration* for the geographic dating backbone (axiom A8) |
| **Full TMI + ATU crosswalk** | mixed | replication vote + a handle on the literate/colonial strata (ATU tails) |
| **The myth texts themselves** (mapsofmyths / corpora) | scrape-dependent | content embeddings → semantic stratum, a principled banality measure, motif-matching |
| **Terrain / biome / hydrography** (SRTM·GEBCO, WWF ecoregions, HydroRIVERS, GSHHG) | open | a **friction surface** → resistance-distance geography for Method A; corridors & barriers at all depths (M37) |
| **Historical polities + contact networks** (historical-basemaps, OWTRAD, Seshat, DARMC; Hellenthal admixture for direction) | open/curated | dated diffusion edges that date the historical strata distribution can't; direction for back-migration (M38) |

> The actionable, significance-ranked sequencing of everything below — as concrete next
> mockups (M24…) — is in [`roadmap.md`](roadmap.md).

## 8. New algorithms that could give strong results

Our current estimators are deliberately simple — Fitch **parsimony** (18), **k-means** /
**spectral co-clustering** (16, 23), **Pearson** correlation (23), a **heuristic gate** (19).
Each has a principled, stronger replacement that also fixes a specific weakness we already
named. Ordered by expected payoff:

1. **Bayesian phylogeography — relaxed-random-walk diffusion on a dated tree** (the core-question
   upgrade). The gold standard from linguistics/epidemiology (BEAST-style): jointly reconstruct
   each motif's **ancestral location and age** as a continuous diffusion over the dated
   phylogeny. Replaces "Method A dates space, Method B dates tree, gate picks one" with a single
   model that dates space *and* tree together, with real uncertainty. Directly yields the
   phylogeographic reconstruction (§6) and absolute ages.
2. **Degree-corrected bipartite stochastic block model** (the co-clustering + sampling upgrade).
   Replaces biclustering (06/07/15) and spectral co-clustering (23) with a *generative* block
   model that (a) selects the number of blocks by evidence instead of a hand-set `k`, (b) gives
   probabilistic membership, and — crucially — (c) the **degree-correction absorbs the `a(t)`
   sampling confounder natively**, so blocks reflect structure, not catalogue density. One model
   that de-confounds and clusters at once.
3. **Hierarchical Poisson / logistic factorization with an exposure offset** (the joint-model of
   §3, made concrete). Factorize `M` into tradition-factors × motif-factors with `a(t)` as a
   per-row **offset**; non-negative latent factors are the emergent themes/strata, effort-corrected
   *globally*. This is the single fit that subsumes mockups 16–23 and resolves alternative-
   hypothesis #1 in one pass.
4. **Phylogenetic mixed models (PGLMM / PGLS)** (the Galton fix). Every correlation we report —
   subsistence×theme (22), theme×area/theme (23) — is currently uncorrected for shared ancestry
   (neighbours aren't independent). A phylogenetic mixed model puts the language/dated tree in as
   the covariance structure and tests these associations **properly**, which is the rigorous
   version of the within-area partial correlations in §5.3. Cheap, decisive, and it directly
   answers "is the gradient real or just Galton + area?"
5. **Likelihood ancestral-state reconstruction (Mk / Dollo + rate heterogeneity)** (the Method-B
   upgrade). Swap parsimony gain-counting for a continuous-time Markov gain/loss model with a
   loss bias (Dollo-like: motifs are lost more easily than independently re-invented) and
   across-motif rate variation. Gives marginal ancestral **probabilities** and a principled
   homoplasy estimate instead of a hard count.
6. **Finite mixture (EM) of descent / areal / reinvention components per motif** (the
   anti-gate). Tests alternative-hypothesis #2: fit each motif as a **mixture** of an
   inherited-along-the-tree component, an areal-diffusion component, and a reinvention rate,
   estimating the **inherited share ∈ [0,1]** instead of forcing a binary mode. Most motifs are
   mixtures; the A3-vs-K25 residual may dissolve into "60% substrate / 40% diffusion."
7. **Occupancy / detection models** (the sampling control, formalised). Mockup 20's coverage
   weighting is a heuristic; an occupancy model states it correctly — *observed* presence =
   *true* presence × detection(effort) — and estimates true range with per-cell uncertainty.
   The statistically honest form of axiom 11.
8. **Structural Topic Model on traditions-as-documents** (the theme-profile upgrade). Treat each
   tradition's motif set as a document; STM estimates theme prevalence **as a function of
   covariates** (`area`, `subsistence`, `family`) with the confounds partialled out by
   construction — the model-based version of mockups 16 and 22 together.

Common thread: each swap trades a descriptive heuristic for a **generative model with an
explicit sampling/ancestry term**, which is exactly where our current results carry their
asterisks. The two with the highest ceiling are #1 (dating) and #3 (the joint effort-corrected
factorization); the two cheapest-yet-decisive are #4 (Galton) and #7 (occupancy).

## The one-line throughline

We have been reconstructing **one latent process — the peopling of the world and the flow of
stories across it — from one biased matrix**. The facets (`area`/`family`/`subsistence`/
`theme`) are its observable projections; `stratum` is the hidden time coordinate. The next
phase is to stop estimating the projections separately and **fit the process once** —
effort-corrected, dated, and content-aware — with the mockups as its validation harness.
