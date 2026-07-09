# Proposal: an entity model for region, culture and time-depth

> Stage 3 (**systematics**) of the overall arc in
> [`analysis-program.md`](analysis-program.md): collect → describe → **classify** → explain.

Extends [`troubleshooting.md`](../troubleshooting.md) §"four macro-region
vocabularies". A first draft of this proposal treated *area · family · transmission*
as three facets **of a tradition**. That was wrong on one point, and fixing it
simplifies the rest: the three things do not live on the same entity.

- **Area** and **culture/family** are properties of a **tradition** (where a people
  lives, what language/religion it has).
- **Time-depth / transmission** is a property of a **motif** — not a tradition. One
  tradition carries motifs of many strata at once (any Sub-Saharan tradition holds
  both a deep African-substratum motif *and* a recent Islamic one). A motif is dated
  by the **shape of its areal distribution**, not by any single carrier.

This is exactly why the two non-areal biclusters (literary-epic Asia, Sun-&-Moon)
appeared as *motif-side* structure, not as tradition groups: "literate" and "deep"
describe bundles of motifs. So the model is three **entities**, each with its own
small vocabulary, not three columns on one table.

Evidence base: Berezkin's authoritative 16 macro-areas and their `areal_path`
subregions; the per-tradition `language` families; the 14 biclusters of
[`15-berezkin-clusters-report`](../../../mockups/15-berezkin-clusters-report/); the
four existing schemes (troubleshooting §schemes).

## Berezkin's own method: analyse the catalogue in parts

Berezkin's published position (comparative-mythology work on the peopling of the New
World and the African substratum — **paraphrased; this text is not in our scraped
data**, which holds only the catalogue entries) is that the global motif
distribution must **not** be counted as one pool. The corpus falls into large sets
with different histories — a **Continental** (Afro-Eurasian, later mainland America
via Beringia) set and an **Indo-Pacific / Austro-Melanesian** ("Gondwanan") set — and
these are analysed **separately**, because late areal diffusion otherwise drowns the
thin deep-time signal. Our trans-Pacific Sun-&-Moon cluster is precisely that deep
Circum-Pacific layer, visible only when it is not mixed into the continental mass.

His own words name the primary slicing dimension: statistics over the whole catalogue
serve only very limited tasks, and it is far more effective to process motifs
**separately by category and thematic group (or any combination of them)**. The
"parts" are first of all **thematic** — and that taxonomy is already in our data as
`motif.motif_group` / `motif_group_num`. So the primary slicer is the motif's
**theme**, and area/family/subsistence/stratum are cross-cuts *within* a theme slice.

## The entity schema

| Entity | Properties |
|---|---|
| **Tradition** | `area` (12, geographic) · `family` (~10, language/religion) · `subsistence` (4, economy) · `theme_profile` (13-dim thematic composition) · coordinates · raw `language` list · `areal_id` / `areal_path` · attestation richness |
| **Motif** | `theme` (Berezkin's category A/B → 13 groups — **the primary analytical axis**) · `stratum` (7, time-depth) · definition · cross-index links |
| **Attestation** (motif × tradition) | the bare presence — the raw material from which a motif's `stratum` is inferred |

Expressiveness is **multiplicative and cross-entity**: a tradition's profile is
`area × family × subsistence` (≈ 12 × 10 × 4), each attested motif carries its `theme`
and `stratum`, and analysis fixes a `theme` (Berezkin's method) before grouping by the
tradition axes. That is why no single axis needs to be fine — the previous draft's 18
areas can drop to 12.

> **Facet roles & the missing axis (audited, mockup 32 / M32).** The four tradition facets are
> **not co-equal** and the set is **incomplete** — an adequacy audit gives each a distinct role:
> - **`area`, `theme_profile`** — *load-bearing*: they carry the real unique signal (drop-one
>   Δ R² on motif-set similarity = 0.08 and 0.13).
> - **`family`** — *keep, but not as a motif predictor* (unique Δ R² ≈ 0.01, collinear with area,
>   V=0.73). Its job is the **descent backbone** — the tree behind Method B, dating and ASR.
> - **`subsistence`** — *targeted covariate only* for the ecology→theme gradient (survived Galton,
>   mockup 25); the weakest and only external/noisy facet (D-PLACE join) — the **drop-candidate**
>   if that hypothesis fails.
> - **Granularity is right**: 12 areas / 11 families beat both coarser and finer (which overfit).
> - **Missing axis — connectivity.** The facets recover only ~36 % of motif-similarity; the ~64 %
>   residual is a **cross-continental convergence** (contact + deep homology) no current facet
>   captures. The taxonomy therefore *gains* a **connectivity axis** (resistance-distance +
>   historical corridors, roadmap M34 / M35) and a derived per-tradition **stratum-stack** (M39).

## Tradition · `area` — 12 macro-areas

Once `family` and `subsistence` carry the cultural load, `area` only answers "where on
the map", so the 18 collapse to a **continental-plus-necessary-seams** grid of 12.
Kept fine only where language/subsistence can't recover the seam (the Americas).
Derived deterministically from `areal_path[0]`, with a few `areal_path[1]`
reassignments.

| # | Area | From Berezkin macro (with `[1]` moves) |
|---|---|---|
| 1 | Europe | Northern & Eastern Europe; W.Europe/N.Africa → *S.&W. Europe, Balkan-Carpathians, Greece-Rome* |
| 2 | Near East & North Africa | SW&C.Asia → *Near East, N./S. Caucasus – Asia Minor*; W.Europe → *North Africa, Horn of Africa* |
| 3 | Iran, Central & South Asia | SW&C.Asia → *Iran–Central Asia, Turkestan, Aryan & South India*; Tibet-cell → *South Asia* |
| 4 | East & Mainland SE Asia | East Asia; Tibet-cell → *Tibet/NE India, Burma-Indochina* |
| 5 | Austronesia & Oceania | Oceania; Tibet-cell → *Nusantara*; Madagascar |
| 6 | Siberia & Arctic–Beringia | Siberia–Mongolia; Beringia |
| 7 | Northern & Western North America | N.Am North&West → *NW Coast, Coast-Plateau, California, Great Basin, Great Southwest, Subarctic* |
| 8 | Eastern North America | Plains & Southeast; N.Am North&West → *Midwest, The Northeast* |
| 9 | Mesoamerica & Central Andes | Mexico – Central Andes |
| 10 | South America (Amazonia to Southern Cone) | Eastern South America; Southern South America |
| 11 | Sub-Saharan Africa | Sub-Saharan Africa |
| 12 | Aboriginal Australia | Australia |

**Optional finer forks** (only if a view wants them; `subsistence` + `family` already
recover most): Europe → North/East vs West/South; North America 7 → NW-Coast /
Subarctic / Southwest-California (Na-Dene vs Algic vs Uto-Aztecan + fisher/hunter/
farmer split); South America 10 → Amazonia / Gê-Brazil / Southern Cone.

## Tradition · `family` — culture / linguistic family (~10)

Seeded from `language[0]`, then a **religion overlay** for the literate civilisations
(religion trumps linguistics where it reorganises the corpus). A different partition
from `area`.

| Family | Seed / overlay |
|---|---|
| Indo-European | Indoeuropean |
| Abrahamic | overlay: Jewish / Christian / Muslim corpora |
| Indic / Dharmic | overlay: Aryan India + Buddhist |
| Sinic | Sino-Tibetan (Han) + literate overlay |
| Islamicate | overlay: Turkic / Iranian / Arab |
| Uralic & Altaic | Uralic, Altaic |
| Circumpolar / Palaeo-Asiatic | Escoaleut, Chukotko-Kamchatkan, N-isolates |
| Amerindian | Na-Dene, Algic, Uto-Aztecan, Tupian, Carib, Macro-Ge, Salishan, Quechuan… |
| Sub-Saharan | Niger-Congo, Nilo-Saharan, (Afro-Asiatic south) |
| Austronesian & Papuan | Austronesian, Austroasiatic, Papuan |
| Australian | Australian |

(This is scheme #4 generalised from the 12 corpus families to the whole catalogue;
the corpus keeps its own labels as a subset.)

## Tradition · `subsistence` — economy type (4)

New property, curated. The biclusters split neighbours by mode of life, not geography
or language (Northwest-Coast fishers ≠ Subarctic hunters ≠ Pueblo farmers, all
Amerindian). It carries part of the load that let `area` shrink to 12.

`forager` (hunter-gatherer / fisher) · `pastoralist` · `horticulturalist` (swidden) ·
`agrarian-state` (intensive agriculture + literate state).

Not hand-curatable at 1046 rows blindly — but **derivable from an open source**:
[D-PLACE](https://d-place.org/)'s Ethnographic Atlas codes subsistence economy per
society, mapped to Glottocodes, so a tradition → society → subsistence join populates
this (and cross-checks `family`).

## Tradition · `theme_profile` — thematic composition (13-dim)

A derived per-tradition feature: the proportion of a tradition's attested motifs falling
in each of the 13 theme groups (§`motif.theme`). Distinct from the motif's own `theme`
— this is the *genre balance* of a tradition's corpus, its mythological fingerprint.

**It is a strong, partly cross-geographic signal** (measured over the 840 traditions
with ≥30 motifs):
- **38%** of the variance in `theme_profile` is explained by macro-area — a large,
  real regional structure, yet 62% is orthogonal to geography. (Under effort-correction the
  figure drops to **~26%**, mockup 24 — geography's grip on genre balance was partly
  over-stated by catalogue density; still substantial, still mostly orthogonal.)
- k-means over the profiles yields interpretable groups that mix region and worldview:
  a **trickster-first** African profile (group 11 dominant), a **märchen** Eurasian
  profile (10·11·08), an **adventure + cosmology** North-American/Beringian profile
  (with Siberia), and a **cosmology-heavy** cluster that puts Mesoamerica–Andes *with*
  Tibet/SE-Asia — a genuine cross-continental worldview affinity that pure geography or
  language would miss.

Uses: (a) a **clustering / similarity factor** on its own or alongside
`area × family × subsistence`; (b) a **proxy for worldview / mode of life** that
correlates with `subsistence` (foragers etiology-heavy, agrarian-literate societies
adventure/märchen-heavy). Caveat: confounded by attestation intensity (a densely
catalogued corpus reflects what was recorded), so use the bias-corrected weights of
`stratum-derivation.md` §5 when computing it for analysis.

## Motif · `theme` — Berezkin's category & group (2 levels)

The primary analytical axis, per Berezkin's own note. **Already in our data** as
`motif_group` / `motif_group_num` (13 leaf groups); this proposal only adds his
two-level roll-up — **Category A · Cosmology & etiology** (groups 01–09) vs
**Category B · Adventures & tricks** (10–13) — and a residual "mixed" tag. The A/B split
is not just editorial: it **re-emerges from theme co-occurrence across traditions**
(seriated CLR correlation, mockup 23) without using Berezkin's labels — see the
theme × theme signal below.

| Category | Group |
|---|---|
| A · Cosmology & etiology | 01 Sun & Moon · 02 stars & constellations · 03 cosmogony & elements · 04 origin of death & hardship · 05 origin of humans & anatomy · 06 origin of subsistence culture · 07 etiology of plants & animals · 08 monstrous beings & folk beliefs · 09 protagonist identity |
| B · Adventures & tricks | 10 adventures · 11 tricks & competitions · 12 proper names · 13 formulae |

Berezkin's finer splits (not in our snapshot; optional forks): fire out of 03
(`origin_of_fire`), non-subsistence culture out of 06, plants/animals split (07a/07b),
protagonist split (09a/09b), realistic tales out of 10 (`realistic_tales`),
marriage/obscene tricks (50), animal-vs-human actors in 11 (111/112), a `mixed` group
(14). His placement note: 08–09 lean A, 12–13 lean B.

**Theme and stratum are orthogonal — do not read depth off theme.** It is tempting to
equate Category A with the deep mythological layer and Category B with the late
European märchen. The data refutes it: Category B is *not* a European specialty — it
is 51% of North-American attestations and 58% of Sub-Saharan-African ones, and **24%
of all adventure/trick motifs are endemic to the New World** (present in the Americas,
absent from Europe) — a deep indigenous trickster / hero-adventure layer (Raven,
Coyote, Anansi), not the late märchen. The same theme thus sits in *different* strata
in different regions (endemic American adventure = deep; the same genre in Europe =
late; a Sanskrit jātaka = axial/literate). So `stratum` must be **derived from
distribution** (next section), never inferred from `theme` — this case is exactly the
stress-test a naive "B = late" rule fails and the distributional signal passes.

### theme × area and theme × stratum are a signal

The *mapping* of theme groups onto areas, onto each other, and onto depth is itself
informative — theme is a statistical **prior** on stratum (not a substitute; the two stay
orthogonal per motif). Visualised in
[`mockups/23-theme-geography`](../../../mockups/23-theme-geography/) — a lift heatmap, a
seriated theme × theme co-occurrence matrix, a traditions × themes co-cluster map, and a
per-theme picker. Measured over the catalogue:

- **theme × area.** Which themes concentrate where varies strongly: Category B is 74–77%
  of European attestations but 27% in Mesoamerica–Andes; by lift, adventures are
  over-represented in the Eurasian belt (×1.2) and depleted in Australia (×0.3) while
  Sun & Moon inverts (×3.4 in Australia). `theme_profile` clusters regionally (38% of its
  variance is macro-area); cosmology is pan-global (mean ~6 macro-areas per motif), tales
  are regional (adventures ~4.8, formulae ~2.9).
- **theme × theme.** The A/B split is not merely editorial — it **re-emerges from theme
  co-occurrence across traditions**. Correlating theme shares (on the CLR transform, to
  strip the compositional closure) and seriating yields two contiguous blocks: a tales
  block (adventures · tricks · proper names · formulae · protagonist identity, monstrous
  beings adjoining) and a cosmology block (Sun & Moon · cosmogony · origin of humans ·
  subsistence · stars), with a strong negative rectangle between them (cosmogony ×
  adventures ≈ −0.6). Berezkin's Category A vs B falls out of the data without his labels —
  a data-driven confirmation that the theme axis is a natural division.
- **theme × stratum.** Category A (cosmology/etiology) is **broader and more areal**
  (phylo-signal ~0.25 — deep substrate spread by ancient contact); Category B
  (adventures/tricks) is **narrower and more descent-tracking** (~0.36 — younger tales
  riding language expansions). So a motif's theme predicts its *tendency* in breadth and
  depth — a useful covariate for `stratum`, though any one theme still spans strata.

## Motif · `stratum` — time-depth / transmission (7)

The motif's temporal layer, oldest → latest. The first four are prehistoric
substrata (dated by areal shape); the last three are historical channels. A motif
gets a primary stratum, optionally secondaries.

| # | Stratum | What it is | Signature cluster |
|---|---|---|---|
| 1 | African substratum | pan-human, shared Sub-Saharan ↔ rest; oldest — **but** "shared with Africa" ≠ automatically deep: back-migration into Africa can make it recent (see `stratum-derivation.md` A8 caveat, §14) | — |
| 2 | Indo-Pacific / Austro-Melanesian | Sahul + Melanesia + S-American Pacific rim; early coastal | 8 (partly) |
| 3 | Continental Eurasian (boreal) | northern Eurasia, into America via Beringia | 3 |
| 4 | Circum-Pacific / trans-Pacific | celestial etiologies (Sun-&-Moon, monster's eyes) | 6 |
| 5 | post-Neolithic / agrarian-state | fertility & state cosmologies | 4, 11 |
| 6 | axial / literate-civilisational | Abrahamic, Dharmic, Sinic book traditions & epics | 2 |
| 7 | colonial / modern diaspora | slave trade, missions, print (Afro-Caribbean, Ibero-American) | ATU tails |

Berezkin's "analyse in parts" = fix a `theme` (his primary slice), then group the
attesting traditions by `area` / `family` / `subsistence`, optionally within a
`stratum`.

**Correction from mockups 18–19 — these 7 are the interpretive band, not the computed
primitive.** The estimator natively emits a **`mode`** ∈ {`local`, `areal-recent`,
`areal-broad`, `areal-deep`, `descent`} + a depth score + confidence; the 7 named strata
are a *(mode × area × family) → band* mapping on top. Two honest limits this exposes:
only the **prehistoric strata 1–4** are derivable from distribution; the **axial/literate
(6)** and **colonial/modern (7)** layers are transmission channels read from
`family`/religion + recency, a separate path, not an A × B output. And the **African
substratum (1)** has no distinct distributional signature yet (Africa folds into the
Continental mega-set). See [`stratum-derivation.md` §8, §14](stratum-derivation.md).

## Deriving `stratum` ourselves (not from Berezkin's labels)

> Full method — theory, features, both algorithms, controls, validation, schema — in
> [`stratum-derivation.md`](stratum-derivation.md). Summary below.

`stratum` is the one field that is **inferred, not given** — so if we want it as a key
divider we must compute it reproducibly and honestly. The premise (areal folkloristics
+ phylogeography): a motif spreads by descent or by contact, so its distribution shape
dates it — **but only under a model**, and distribution alone cannot separate deep
inheritance from independent reinvention or diffusion-then-loss (homoplasy, Galton's
problem). Every stratum is therefore a hypothesis with uncertainty, not a fact.

**Founding assumptions (enumerated in full at
[`stratum-derivation.md` §0](stratum-derivation.md)).** The computation rests on
*substantive hypotheses* — distribution dates a motif; spread is descent-or-diffusion;
breadth + cross-barrier disjunction ⇒ old; the language tree proxies descent lineages;
geographic span maps to time via the known **peopling sequence** (Africa → Sahul →
Eurasia → Beringia → Americas); homoplasy mimics depth; theme is orthogonal to depth per
motif — and *methodological axioms* that keep it honest — effort-correct absence, count
independent (not raw) spread, define the geography ourselves, use anchors to orient not
train, **keep theme out of the estimator** (anti-circularity), and emit a confidence, not
a class. A single linear score and "Category B = late" are both explicitly tested and
rejected.

**Per-motif features, all computable from our data** (attestation matrix + `areal_path`
+ coordinates + `language` + crosswalk): global prevalence (# traditions / macro-areas
/ **language families**); areal dispersion (mean pairwise distance, # disjoint
components); **cross-barrier disjunction** (present in X and Z with a gap in the
connecting Y — the strongest "old" signal); membership in self-defined geographic sets
(Continental / Indo-Pacific / New-World-only); **language-clade coherence** (confined
to one clade = young; spread across unrelated clades with disjunction = old);
cross-index breadth (independently attested in TMI/ATU/Berezkin).

**Two methods.**
- *Heuristic depth index (now):* combine the features into one depth score (or its
  first principal component), rank all motifs, and let strata **emerge** (cluster in
  feature space / cut the axis), interpreting post-hoc.
- *Model-based (the rigorous goal):* map motif presence/absence onto a **dated language
  phylogeny** and run ancestral-state reconstruction with a gain/loss model
  (phylomemetics, à la Tehrani/d'Huy). Reconstruction to deep nodes = old; the model
  also **counts independent gains**, so it handles homoplasy. Needs one external
  resource — a dated language tree — that we do not yet have.

**Validation stress-test (already available):** the endemic-vs-shared split of the
adventure/trick corpus. A naive "B = late" rule mislabels the 451 New-World-endemic
adventure motifs; the distributional signal (endemism + disjunction) correctly ranks
them as a deep regional layer distinct from the European märchen. Our biclustering
already surfaced the deepest layer (trans-Pacific Sun-&-Moon) from co-occurrence alone,
without any Berezkin label — proof the signal is in the data.

**Required controls** (non-negotiable if `stratum` becomes a key divider): model
**attestation intensity** per tradition (uneven coverage → absence ≠ real absence);
down-weight **banal / cognitively trivial** motifs (easy to reinvent); define the
geographic sets ourselves, not from his labels; calibrate direction against a few
uncontroversial anchors (world-religion = late, earth-diver / cosmic-egg = deep);
attach a **confidence** to every motif.

**Consequence for the schema:** store `stratum` as a **continuous depth score plus an
optional binning**, produced by a **separate offline pipeline**, with per-motif
confidence — not as hard classes handed down a priori.

## Canonical value catalogue

The complete, closed value sets — human-readable label + `slug` — ready to become
enums in `region_facets.py`.

> **Post-audit status (mockup 32 / M32).** The four facets below **stay**, but not co-equal:
> `area` + `theme_profile` are load-bearing, `family` is the descent backbone (not a motif
> predictor), and `subsistence` is a provisional, external-data covariate (**drop-candidate**).
> The catalogue is **incomplete** — a **connectivity** axis (resistance-distance + historical
> corridors, roadmap M34/M35) and a derived per-tradition **stratum-stack** (M39) are the missing
> value sets, not yet enumerated here because they are not closed until those mockups land.

### `tradition.area` (12)

| Label | Slug |
|---|---|
| Europe | `europe` |
| Near East & North Africa | `near_east_n_africa` |
| Iran, Central & South Asia | `iran_c_s_asia` |
| East & Southeast Asia | `east_se_asia` |
| Austronesia & Oceania | `austronesia_oceania` |
| Siberia & Beringia | `siberia_beringia` |
| Northern & Western North America | `nw_north_america` |
| Eastern North America | `e_north_america` |
| Mesoamerica & the Andes | `mesoamerica_andes` |
| South America | `south_america` |
| Sub-Saharan Africa | `sub_saharan_africa` |
| Aboriginal Australia | `australia` |

Optional finer forks (off by default):

| Parent | Label | Slug |
|---|---|---|
| europe | Northern & Eastern Europe | `n_e_europe` |
| europe | Western & Southern Europe | `w_s_europe` |
| nw_north_america | Northwest Coast & Plateau | `nw_coast_plateau` |
| nw_north_america | Subarctic & Northeast | `subarctic_ne` |
| nw_north_america | Southwest & California | `southwest_california` |
| south_america | Amazonia & Guiana | `amazonia_guiana` |
| south_america | Central & Eastern Brazil (Gê–Xingu) | `east_brazil_ge` |
| south_america | Southern Cone & Chaco | `southern_cone` |

### `tradition.family` (11)

| Label | Slug |
|---|---|
| Indo-European | `indo_european` |
| Abrahamic | `abrahamic` |
| Indic / Dharmic | `indic` |
| Sinic | `sinic` |
| Islamicate | `islamicate` |
| Uralic & Altaic | `uralic_altaic` |
| Circumpolar & Palaeo-Asiatic | `circumpolar` |
| Amerindian | `amerindian` |
| Sub-Saharan | `sub_saharan` |
| Austronesian & Papuan | `austronesian_papuan` |
| Australian | `australian` |

### `tradition.subsistence` (4)

| Label | Slug |
|---|---|
| Foragers | `forager` |
| Pastoralists | `pastoralist` |
| Horticulturalists | `horticulturalist` |
| Agrarian states | `agrarian_state` |

### `motif.theme` — category (2) + group (13)

| Category | Slug |
|---|---|
| Cosmology & etiology | `cosmology_etiology` |
| Adventures & tricks | `adventures_tricks` |

| Group (num) | Slug | Category |
|---|---|---|
| Sun & Moon (01) | `sun_moon` | A |
| Stars & constellations (02) | `stars_constellations` | A |
| Cosmogony & elements (03) | `cosmogony_elements` | A |
| Origin of death & hardship (04) | `origin_of_death` | A |
| Origin of humans & anatomy (05) | `origin_of_humans` | A |
| Origin of subsistence culture (06) | `origin_subsistence` | A |
| Etiology of plants & animals (07) | `plants_animals` | A |
| Monstrous beings & folk beliefs (08) | `monstrous_beings` | A |
| Protagonist identity (09) | `protagonist_identity` | A |
| Adventures (10) | `adventures` | B |
| Tricks & competitions (11) | `tricks_competitions` | B |
| Proper names (12) | `proper_names` | B |
| Formulae (13) | `formulae` | B |

### `motif.stratum` (7)

| Label | Slug |
|---|---|
| African substratum | `african_substratum` |
| Indo-Pacific | `indo_pacific` |
| Continental Eurasian | `continental_eurasian` |
| Circum-Pacific | `circum_pacific` |
| Post-Neolithic | `post_neolithic` |
| Axial & literate | `axial_literate` |
| Colonial & modern | `colonial_modern` |

## Deterministic population recipe

- **`theme`** — already in the data: `motif_group_num` → group slug, plus a fixed
  01–09 → A / 10–13 → B roll-up. Zero curation.
- **`area`** — pure function of `areal_path` (no network / credentials, like
  `_CANONICAL_AREAS`): `areal_path[0]` → area, with the `[1]` moves above.
- **`family`** — seed from `language[0]` via a ~25-row map, then a small curated
  religion overlay (the literate corpora).
- **`subsistence`** — curated (~dozens of rows keyed by area/subregion/language).
- **`stratum`** — derived from the motif's **distribution** (see "Deriving `stratum`
  ourselves"): a depth score over the attestation features, not read off `theme`; a
  separate offline pipeline, with per-motif confidence. Not per-tradition.

Only the overlay, `subsistence`, and `stratum` curation are hand-authored (dozens of
rows); `theme`, `area`, and the `family` seed are computed.

## Samples

**Traditions** → `area · family · subsistence`

| Tradition | Area | Family | Subsistence |
|---|---|---|---|
| Lithuanians | Europe | Indo-European | agrarian-state |
| Anatolia Turks | Near East & N. Africa | Islamicate | agrarian-state |
| Mongols (Khalkha) | Siberia & Arctic–Beringia | Uralic & Altaic | pastoralist |
| Han Chinese | East & Mainland SE Asia | Sinic | agrarian-state |
| Ifugao | Austronesia & Oceania | Austronesian | horticulturalist |
| Nanai | Siberia & Arctic–Beringia | Uralic & Altaic (Tungusic) | forager |
| Tlingit | N. & W. North America | Amerindian (Na-Dene) | forager (fisher) |
| Navajo | N. & W. North America | Amerindian (Na-Dene) | horticulturalist |
| Menominee | Eastern North America | Amerindian (Algic) | forager |
| Bororo | South America | Amerindian (Macro-Ge) | horticulturalist |
| Hausa | Sub-Saharan Africa | Sub-Saharan | agrarian-state |
| Aranda | Aboriginal Australia | Australian | forager |

**Motifs** → `theme` · `stratum`

| Motif | Theme (category / group) | Stratum |
|---|---|---|
| A11C Sun, Moon & monster's eyes | A / Sun & Moon | Circum-Pacific / trans-Pacific |
| K25a5 Two brothers & the swan-maidens | A / origin of humans | Continental Eurasian (boreal) |
| B4 The fished-out earth | A / cosmogony & elements | Indo-Pacific / Austro-Melanesian |
| H36D Death and the hare (origin of death) | A / origin of death | African substratum |
| K27z2 Princess averts incest (jātaka-type) | B / adventures | axial / literate-civilisational |
| M182 The tar-baby (US South) | B / tricks & competitions | colonial / modern diaspora |

## What it resolves

- **#1 vs #3** collapse into `area` — one areal vocabulary from `areal_path`, so the
  overview chart and the Traditions section stop disagreeing on one page.
- **#2** (TMI) resolves onto the same three tradition properties via the gazetteer,
  so Berezkin and TMI overviews cross-reference per property, not per rogue list.
- **#4** is `family` — no longer a fourth "region", just the culture axis restricted
  to our corpus.
- Clusters 2 and 6 were never areas; they are motif `stratum` values (6 and 4).

## Cumulative conclusions

The whole investigation, in one place (prototypes: mockups 15–29; method detail in
[`stratum-derivation.md`](stratum-derivation.md) §12–14; the overall arc in
[`analysis-program.md`](analysis-program.md); forward directions in
[`synthesis-and-directions.md`](synthesis-and-directions.md)):

1. **"Region" was three axes crammed into one.** Split cleanly into **entities**: a
   *tradition* carries `area` (12, from `areal_path`), `family` (from `language` +
   religion), `subsistence` (4) and a derived `theme_profile`; a *motif* carries `theme`
   (given — Berezkin's category A/B → 13 groups, the primary analytical slicer) and
   `stratum` (computed). Expressiveness is multiplicative across entities, so `area`
   shrinks from 18 to 12.
2. **Berezkin's own rule holds:** don't pool the catalogue — fix a `theme`, then analyse.
   Theme is first-class and already in our data (`motif_group`); and the A/B split is
   **independently recovered** — it re-emerges from theme co-occurrence across traditions
   (seriated CLR correlation, mockup 23) without his labels.
3. **Time-depth is a motif property, inferred, not a tradition facet.** Distribution
   dates a motif, but only under a model and never perfectly (homoplasy, loss, sampling).
4. **Theme ≠ depth per motif, but predicts it in aggregate.** Category A (cosmology) is
   broad + areal-deep; Category B (tales) is narrower + more descent-tracking — a prior,
   not a determiner (endemic-American adventures are deep). `theme × area`, `theme × theme`
   (the A/B blocks) and `theme × stratum` are all real signals; so is `subsistence × theme`
   — extractive economies skew cosmological, intensive/mobile ones tale-heavy (mockup 22).
   The area confound on that last one was **tested** (mockup 25): it survives controlling for
   area (p=0.003) and for language family / Galton (p=0.006), so subsistence carries its own
   contribution, only partly entangled with geography.
5. **Geography is primary; language and time are separate computed layers.** Method B
   shows only ~1% of motifs follow language descent (Eurasian fairy tales); the rest
   spread areally — so `area` carries most of the structure, while `stratum` is a
   gated **A × B** estimate (geography dates the areal majority, phylogeny the descent
   minority), reported as a continuous score with confidence.
6. **The findings held under a skeptical battery.** They are not sampling artifacts:
   effort-correction leaves 3 of 4 theme findings standing (only `theme_profile` variance-
   by-area softens, 38%→~26%, mockup 24), and a degree-corrected block model halves the
   catalogue-density artifact that naive clustering carries (mockup 26). They are not mere
   autocorrelation: `subsistence × theme` survives Galton and area controls individually
   (mockup 25). Content corroborates the split — embeddings predict `theme` (58% vs 20%
   chance) but not depth (mockup 29). And the honest residual is confirmed irreducible: a
   descent/areal/reinvention mixture models the continuum but still cannot separate deep
   substrate (A3) from wide diffusion (K25) from distribution alone (mockup 27) — which,
   with the finding that likelihood ASR ≈ parsimony on an *undated* tree (mockup 28), is
   the standing argument for wiring a **dated phylogeny** (the next capability, M30–M31).
7. **The facet set is non-redundant but incomplete (mockup 32, M32).** An adequacy audit of the
   tradition facets on the 910 traditions carrying all four: they are **not orthogonal**
   (Cramér's V(area,family)=0.73, (area,subsistence)=0.59). Each carries a *non-zero* unique
   contribution, but only **`theme_profile` (drop-one Δ R²=0.13) and `area` (0.08)** are
   load-bearing; **`family` (0.01) and `subsistence` (0.01) are nearly redundant** *as motif
   predictors* — they keep their place for other jobs (`family` = the **descent backbone** of
   Method B / dating; `subsistence` = a **targeted ecology→theme covariate**, the weakest and only
   external facet, a drop-candidate). **Granularity is right** — 12 areas / 11 families beat both
   coarser and finer (which overfit held-out attestation). But the set is **incomplete**: the
   facets recover only ~36 % of motif-similarity (block ARI and continuous R² agree), leaving a
   large ~64 % **cross-continental convergence residual** — the **missing axis is connectivity**
   (resistance-distance + historical corridors, M34/M35) plus a derived per-tradition
   **stratum-stack** (M39). So the taxonomy keeps all four facets (reweighted, not co-equal) and
   gains a connectivity axis.
8. **The big axes are confounded, so a mode is separable only where classifications disagree
   (mockup 33, M33).** Large `area`, large genetic lineages and large language families strongly
   co-vary (V(area,family)=0.73; a continental genetic tree is essentially `area` re-nested). So
   swapping the language tree for a continental genetic tree is really the **language-vs-geography**
   contrast (Method B vs A), *not* an independent axis, and comparing the two only yields signal in
   the **off-diagonal**: a motif that tracks a family **across** areas (Indo-European, Altaic) is
   language-descent geography can't make; a motif that tracks an area **across** families is areal.
   Where family = area (the correlated core) descent and diffusion are **confounded and inseparable
   from distribution** — this is the same deep-vs-diffuse residual as A3-vs-K25 (mockup 27), and no
   coarse reclassification dissolves it. **Method consequence:** a genuinely third, de-confounding
   axis must decouple from *both* area and family — **fine SNP genetics** (ancestry ≠ geography
   under admixture, M36) and the **connectivity corridors** (routes that are neither flat area nor
   family, M34/M35). This is *why* those are the next builds.

## Implementation sketch (not built)

- `region_facets.py`: `area(areal_path)`, `family(language, name)`,
  `subsistence(name)` on traditions; `theme(motif_group_num)`, `stratum(motif)` on
  motifs.
- `_berezkin_region` → `area()`; `culture_dict._REGION` → the TMI-label bridge onto
  the same properties; `config/traditions.json` families → `family` for the corpus.
- Overviews lead with a **Theme** slicer (category A/B → group — Berezkin's primary
  cut), then group the attesting traditions by **Area / Family / Subsistence**, with
  an optional **Stratum** filter — replacing the one ambiguous "region" control.
