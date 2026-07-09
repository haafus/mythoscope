# Proposal: deriving motif `stratum` (time-depth) from distribution

Companion to [`macro-area-facets.md`](macro-area-facets.md). That doc defines a motif's
`stratum` as the one **inferred, probabilistic** field (area/family/subsistence/theme
are given or deterministic; stratum is not). This doc is the full method: the theory
and its limits, the exact per-motif features, two derivation algorithms (a heuristic
depth index and a phylogenetic model), the mandatory controls, validation, and the
output schema. Nothing here is built yet.

## 1. What we are estimating, and why it is hard

`stratum` = the **time-depth** of a motif: how old its shared distribution is. We want
it computed reproducibly from our own data, not read off Berezkin's expert labels.

The premise (areal folkloristics + phylogeography): a motif spreads either by **descent**
from a common ancestor or by **contact diffusion**, so the *shape of its distribution
dates it*. But distribution alone **cannot** separate the three processes that produce
the same map:

1. **Deep shared inheritance** — one old origin, carried by migration/descent.
2. **Independent reinvention (homoplasy)** — cognitively easy motifs arise repeatedly.
3. **Diffusion then loss** — recent spread that has since gone patchy.

Add **sampling bias** (Berezkin's coverage is uneven; absence ≠ real absence) and the
classic **Galton's problem** (neighbouring traditions are not independent samples).

**Consequence:** every stratum estimate is a *hypothesis with uncertainty*, never a
fact. The method's job is to (a) squeeze maximal signal from distribution, (b) quantify
how much of it survives the confounds, and (c) hand back a score **with confidence**,
not a hard class.

## 2. The data available

- **Attestation matrix** `M` — motif × 1046 areal traditions (binary presence).
- **`areal_path`** — Berezkin's 4-level areal hierarchy per tradition (macro → … → id).
- **Coordinates** — lat/lon per tradition (`mapsofmyths_traditions.json`).
- **`language`** — the language-family chain per tradition (e.g. `[Indoeuropean, …]`).
- **Crosswalk** — motif-level links to TMI and ATU (independent attestation).

Everything below is computable from these; Method B additionally needs a language
phylogeny — **available as open data** (§7): [Glottolog](https://glottolog.org/)
(CLDF, CC-BY) for the classification tree and coordinates, a dated global Bayesian
phylogeny (Bouckaert/EDGE, as used by [Grambank](https://grambank.clld.org/) 2023) for
branch dates, and [D-PLACE](https://d-place.org/) (CC-BY) linking societies to
Glottocodes (also seeds `subsistence`).

## 3. Per-motif distributional features

For motif *m* with attesting-tradition set `T(m)`, compute the following. Each line
notes the direction of the **"old" signal**.

| Feature | Definition | Old ↑/↓ |
|---|---|---|
| `n_trad` | #traditions in `T(m)` | ↑ (prevalence) |
| `n_macro` | #distinct macro-areas spanned | ↑ |
| `n_lang` | #distinct top-level language families spanned | ↑ (strong) |
| `dispersion` | mean pairwise great-circle distance over coords of `T(m)` | ↑ |
| `gyration` | radius of gyration about the centroid | ↑ |
| `fragments` | #spatial components (DBSCAN on coords, geo metric) | ↑ (disjunction) |
| `barrier_crossings` | #components separated by a major barrier (ocean / desert / continent gap) | ↑ (strongest) |
| `set_span` | #self-defined mega-sets touched (Continental / Indo-Pacific / New-World) | ↑ |
| `gap_flag` | present in sets X and Z but **absent** in the connecting Y | ↑ (vicariance) |
| `clade_incoherence` | dispersion over the **language tree**: min #independent family-origins to explain `T(m)` (a parsimony gain count) | ↑ |
| `xindex_breadth` | #indexes (TMI/ATU/Berezkin) independently attesting `m` via crosswalk | ↑ (corroboration) |
| `founder_signal` | present in Africa **and** Sahul **and** the Americas at once | ↑ |
| `banality` | reinvention-proneness proxy (see §5) | ↓ (discount) |
| `singleton_scatter` | many isolated single-tradition occurrences vs connected chains | ↓ (looks like reinvention, not descent) |

Key intuition: **prevalence + cross-clade spread + disjunction across barriers** is the
composite fingerprint of an old motif; **compact, single-clade, connected** is young or
locally endemic; **many scattered singletons of a trivial motif** is homoplasy, not age.

## 4. Self-defined geography (no Berezkin labels)

Two features need our own geography, so we don't inherit his partition:

- **Mega-sets.** Cluster the 1046 coordinates into landmasses; group them into three
  sets by our own reading — *Continental* (Afro-Eurasia + Beringian America),
  *Indo-Pacific* (Sunda–Sahul–Melanesia–Polynesia + the S-American Pacific rim),
  *New-World* — used only for `set_span` / `gap_flag`.
- **Barriers.** Precompute a mask of major water/desert barriers; two coordinate
  components are "barrier-separated" if the straight path between their centroids
  crosses one. Feeds `fragments` → `barrier_crossings`.

## 5. Controls (mandatory if `stratum` is a key divider)

These are not optional polish — without them the score measures catalogue density, not
age.

- **Attestation intensity.** Each tradition *t* has an attestation count
  `a(t)` = #motifs recorded for it. Model presence as detection under effort: a motif
  *absent* from a **well-sampled** tradition is a real absence (informative); absent
  from a **poorly-sampled** one is unknown (uninformative). Implement as a per-cell
  **presence weight** `w(m,t)` and use weighted versions of every feature; or an
  occupancy-style correction estimating true presence prob. This is the single biggest
  fix — a densely-catalogued region otherwise always looks "central/old".
- **Banality / cognitive attractors.** Motifs that are easy to reinvent (minimally
  counter-intuitive, structurally simple) inflate `n_macro` by homoplasy, not descent.
  Proxy `banality` from: short/generic definition (embedding "genericness"), high
  `singleton_scatter`, and low internal areal connectivity. Down-weight these before
  scoring.
- **Non-independence (Galton).** Neighbouring traditions co-vary; count **effective**
  spread, not raw counts — `clade_incoherence` (independent gains on the language tree)
  and `barrier_crossings` already do this by rewarding *independent* occurrences.
- **Anchors (direction only).** A tiny labelled seed to orient the axis, not to train:
  late = world-religion / literate-epic motifs; deep = earth-diver, cosmic-egg,
  Sun-&-Moon. Used to fix sign/monotonicity and sanity-check, never as ground truth.

## 6. Method A — heuristic depth index (available now)

Cheap, reproducible, correlational. Produces a continuous `depth_score` and, optionally,
emergent strata.

```
# inputs: M (motif×tradition), coords, language chains, crosswalk, a(t)
1. w = presence_weights(M, a)                 # §5 attestation-intensity
2. for each motif m:
       F[m] = features(T(m), coords, lang, crosswalk, w)   # §3, weighted
3. F = discount(F, banality)                  # §5 down-weight reinvention-prone
4. Z = standardize(F); Z = orient(Z)          # sign every feature toward "old"
5. depth_axis = PCA(Z).PC1                     # or weighted composite
   depth_axis = align_sign(depth_axis, anchors)   # deep anchors must score high
6. strata = emergent_bins(depth_axis)          # GMM/gaps → discrete layers, or quantiles
7. confidence[m] = 1 - bootstrap_std(depth_axis[m])   # resample traditions, recompute
8. emit depth_score, stratum_bin, confidence per motif
```

Notes:
- **PCA vs composite.** PC1 is unsupervised (lets the dominant covariation define
  depth); a hand-weighted composite is more interpretable. Report both; prefer PC1 if
  it aligns with anchors.
- **Emergent strata.** Do **not** force Berezkin's 7. Cluster in feature space and read
  what layers appear; map them onto the named vocabulary post-hoc (§8).
- **Confidence via bootstrap.** Resample traditions (rows) with replacement, recompute
  the score; a motif whose rank is stable across resamples is trustworthy, one that
  jumps is not (typically the sparsely-attested ones).

## 7. Method B — phylogenetic ancestral-state reconstruction (rigorous goal)

The model-based route folklorists actually use to date tales (phylomemetics; Tehrani,
d'Huy, Ross). It handles homoplasy natively because it *counts independent gains*.

**Prototyped** in [`mockups/18-motif-phylostrata`](../../../mockups/18-motif-phylostrata/)
on the interim coarse tree (our `language` chains) with Fitch parsimony + a
phylogenetic-signal test. Key finding: only ~1% of motifs are broad *and* clade-clustered
(genuine descent) — and those are Eurasian fairy-tale types, recovering the published
result — while cosmology/trickster/swan-maiden are broad but areally diffused (low
signal). So B identifies the *mode* of spread (descent vs areal) and dates the
descent-minority; geography (Method A) handles the areal majority. The two are
complementary, not competing.

```
# needs: a dated language phylogeny with our traditions at the tips
1. tree = dated_language_tree(traditions)      # Glottolog topology + node dates
2. for each motif m:
       x = presence_vector(m over tips)         # binary, weighted by detection
3.     fit Mk / gain-loss CTMC (rates q01,q10)  # optionally Dollo (loss-biased) or rate-het
4.     asr = ancestral_state_reconstruction(tree, x, model)   # marginal posteriors at nodes
5.     origin = shallowest node whose inherited-presence best explains the tips
              # = MRCA of the maximal inherited-presence clade, integrating the posterior
6.     age[m] = node_date(origin)               # model-based age
7.     n_gains = expected independent gains     # high ⇒ convergence, flag not-deep
8.     confidence from the posterior / rate uncertainty
```

- **Age.** A motif reconstructed to a deep ancestral node = old stratum; one that arises
  inside a shallow clade = young and *bounded by that clade's dispersal date* (e.g. an
  Austronesian-only motif ≈ Austronesian expansion age).
- **Homoplasy.** If explaining the tips needs many independent gains, there is no single
  deep origin — flag as convergent/banal rather than ancient. This is the piece Method A
  can only approximate with `clade_incoherence`.
- **Data (open, licensed).** Glottolog CLDF (CC-BY) — classification topology + tip
  coordinates, join our traditions to Glottocodes via `language`/name; a dated global
  Bayesian phylogeny (Bouckaert/EDGE, as in the Grambank 2023 analysis) for branch
  dates; D-PLACE (CC-BY) bridges societies↔Glottocodes (and seeds `subsistence`).
- **Interim without the dated tree.** Use the Glottolog classification (or just the
  `language` chain) as a coarse family → subfamily tree and do parsimony gain-counting;
  it yields `clade_incoherence` (Method A) before the dated phylogeny is wired in.

## 8. From score to the named strata

The continuous `depth_score` (or Method-B age) is primary; the 7 named layers of
`macro-area-facets.md` are a **post-hoc labelling** of score bands, cross-checked by
feature signature:

| Named stratum | Expected feature signature |
|---|---|
| African substratum | founder_signal high; Africa+world with disjunction; oldest band |
| Indo-Pacific | Sunda–Sahul–Pacific-rim set; gap across the Pacific |
| Continental Eurasian | broad N-Eurasia + Beringian America; one connected continental sweep |
| Circum-Pacific | disjunct trans-Pacific arc, low prevalence (the Sun-&-Moon signature) |
| Post-Neolithic | mid prevalence, tied to agrarian areas/subsistence |
| Axial / literate | follows literate corpora / language of religion, not areal contiguity |
| Colonial / modern | recent, single-clade or diaspora-shaped, shallow |

Do not hard-wire the mapping; fit the bands, then name them.

## 9. Validation

- **Adventure-endemism stress-test (already computed).** 24% of adventure/trick motifs
  are New-World-endemic (present in the Americas, absent from Europe); Category B is 51%
  of North-American and 58% of Sub-Saharan attestations. A naive "theme B = late" rule
  mislabels the 451 endemic motifs; the distributional score must rank them as a **deep
  regional** layer, not late märchen. This is the primary sanity gate.
- **Anchor recovery.** World-religion/literate motifs land shallow; earth-diver /
  cosmic-egg / Sun-&-Moon land deep.
- **Proof of concept.** Our biclustering already surfaced the deepest layer (trans-
  Pacific Sun-&-Moon, cluster 6) from co-occurrence alone, with no Berezkin label — the
  signal is demonstrably in the data.
- **Cross-index stability.** Recompute on Berezkin-only vs Berezkin+crosswalk; a good
  score should agree on the motifs both cover.
- **Sensitivity.** Vary the bias correction and DBSCAN/`eps`; report how much the strata
  move. Unstable motifs get low confidence, not a confident wrong label.

## 10. Output schema and pipeline

- Per motif: `depth_score` (float, continuous, primary), `stratum` (binned label,
  optional), `stratum_confidence` (0–1).
- A **separate offline pipeline** (a mockup or a `motifs` sub-step), fully reproducible,
  **no credentials** (works off the committed matrix + coords), re-runnable when the
  catalogue grows.
- Surfaced as a **continuous depth slider / binned filter**, never as an authoritative
  a-priori class.

## 11. Honesty — what this cannot do

- It **generates hypotheses**, not proofs; a stratum is a posterior over an unobservable
  history.
- It cannot fully separate deep inheritance from ancient convergence for banal motifs —
  the controls reduce, not eliminate, this.
- Absence is only as trustworthy as attestation intensity allows; sparsely-covered
  regions (parts of Africa, interior Asia) will carry wide confidence bands.
- The named 7 strata are an interpretive overlay; the defensible artefact is the
  **continuous score with confidence**, sliced (per Berezkin) **within a fixed
  `theme`**, since the same theme occupies different depths in different regions.

## 12. Method A × Method B — how they reinforce each other

A (geographic) and B (phylogenetic) are not rivals; each resolves the other's blind
spot. Worked from the tracked motifs (mockups 17–18):

| Motif | A · mega-sets, fragments | A alone | B · phylo-signal | B alone |
|---|---|---|---|---|
| B4 fished-out earth | CONT·IP·NW, 5 | "deep, disjunct" | 0.62 | Austronesian **clade** |
| A3 sun & moon | CONT·IP·NW, 10 | "deep, disjunct" | 0.17 | "areal" (can't date) |
| K25 swan-maiden | CONT·IP·NW, 9 | "deep, disjunct" | 0.16 | "areal" |
| K8aa Jonah | CONT, 4 | "shallow, regional" | 0.15 | "areal" |

1. **B routes, A dates the areal majority.** B only says descent-vs-areal; ~99% are
   areal and B cannot date them (A3 and K8aa are both ≈0.16). A separates them at once —
   A3 spans all three mega-sets with barrier crossings (deep pan-global substrate),
   K8aa is compact in one set (recent borrowing).
2. **B corrects A's false positives.** A would call B4 "deep disjunct" (it touches the
   New World); B shows it is a coherent Austronesian clade plus a stray, not an ancient
   substrate — B filters apparent disjunction that is really "clade + noise".
3. **B de-noises A's breadth-as-age.** Compute A's depth *within* B's areal slice, after
   the descent motifs are removed, so widespread-by-descent no longer inflates
   "widespread = old".
4. **A upgrades B to phylogeography.** A's coordinates turn B from cladistics into joint
   ancestral clade **and range** reconstruction, and model the horizontal (contact) edges
   a pure tree ignores — a reticulate "tree + migration" model then partitions each
   motif into inherited vs borrowed shares.
5. **Agreement = confidence, disagreement = diagnosis.** Both deep → high-confidence
   deep; A-broad but B-areal → confidently *diffused*, not inherited. The disagreement
   pattern is itself a classifier neither method has alone.

**Gated pipeline:** B-signal → mode tag; descent → clade-depth age (A-breadth calibrates
spread within the clade); areal → A disjunction/deep-set age; confidence from A–B
agreement; in the limit, one phylo-geographic-reticulate run with A (space) and B (tree)
as two observations. **Honest residual:** even together, A and B do not separate A3
(deep cosmology) from K25 (widely diffused tale) — both are deep-areal by A and areal by
B; only the **theme** axis (Category A cosmology vs B tale) resolves that. The full model
is A (space) × B (tree) × theme.

## 13. Cumulative conclusions (empirical)

Backed by mockups 16–18 over the Berezkin catalogue:

- **Method A (mockup 17).** Distribution carries a real depth signal — pan-global
  celestial cosmogony tops the ranking, the adventure-endemism stress-test passes — but
  no single linear score works: PC1 conflates old with *widespread*; a
  disjunction-weighted variant triples the endemism separation yet over-penalises
  prevalence (swan-maiden 100→16). Distribution alone is a signal, not a dating.
- **Method B (mockup 18).** A phylogenetic-signal test finds **only ~1% of motifs are
  broad *and* clade-clustered** (genuine descent) — and those are European fairy-tale
  types (Cinderella, "seven at a blow"), independently recovering the published
  phylomemetics result. Cosmology, trickster and the swan-maiden are broad but **areally
  diffused**. So the language tree is the "wrong tree" for most motifs — which is exactly
  why **geography is the primary signal** and language/time are separate computed layers.
- **Theme is a statistical prior on stratum, not a substitute.** Per group, Category A
  (cosmology/etiology) is geographically **broader** (mean ~6 macro-areas) and **more
  areal** (phylo-signal ~0.25 — deep substrate), while Category B (adventures/tricks) is
  **narrower** (~4) and **more descent-tracking** (~0.36 — younger tale diffusion). Theme
  predicts a motif's *tendency* in area and depth, though any one theme still spans strata
  (endemic-American adventures are deep). Use theme as a prior/covariate, never as the
  answer.
- **The model that follows.** Tradition = area × family × subsistence × theme_profile;
  motif = theme (given) × stratum (computed, A×B). Analysis fixes a theme (Berezkin's
  method), then dates within it by the gated A×B pipeline. No single axis suffices; the
  three together (space, tree, theme) each remove the others' confound.
