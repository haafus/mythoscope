# Proposal: an entity model for region, culture and time-depth

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

This directly favours the entity model: **slice by motif stratum first, then analyse
areas within a slice** — instead of one flat region list doing everything.

## The entity schema

| Entity | Properties |
|---|---|
| **Tradition** | `area` (12, geographic) · `family` (~10, language/religion) · `subsistence` (4, economy) · coordinates · raw `language` list · `areal_id` / `areal_path` · attestation richness |
| **Motif** | `stratum` (7, time-depth / transmission) · theme group (chapter) · definition · cross-index links |
| **Attestation** (motif × tradition) | the bare presence — the raw material from which a motif's `stratum` is inferred |

Expressiveness is now **multiplicative and cross-entity**: a tradition's profile is
`area × family × subsistence` (≈ 12 × 10 × 4), and each attested motif adds its
`stratum`. That is why no single axis needs to be fine — the previous draft's 18
areas can drop to 12.

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

## Motif · `stratum` — time-depth / transmission (7)

The motif's temporal layer, oldest → latest. The first four are prehistoric
substrata (dated by areal shape); the last three are historical channels. A motif
gets a primary stratum, optionally secondaries.

| # | Stratum | What it is | Signature cluster |
|---|---|---|---|
| 1 | African substratum | pan-human, shared Sub-Saharan ↔ rest; oldest | — |
| 2 | Indo-Pacific / Austro-Melanesian | Sahul + Melanesia + S-American Pacific rim; early coastal | 8 (partly) |
| 3 | Continental Eurasian (boreal) | northern Eurasia, into America via Beringia | 3 |
| 4 | Circum-Pacific / trans-Pacific | celestial etiologies (Sun-&-Moon, monster's eyes) | 6 |
| 5 | post-Neolithic / agrarian-state | fertility & state cosmologies | 4, 11 |
| 6 | axial / literate-civilisational | Abrahamic, Dharmic, Sinic book traditions & epics | 2 |
| 7 | colonial / modern diaspora | slave trade, missions, print (Afro-Caribbean, Ibero-American) | ATU tails |

Berezkin's "analyse in parts" = analyse `area` within a fixed `stratum` slice.

## Canonical value catalogue

The complete, closed value sets — human-readable label + `slug` — ready to become
enums in `region_facets.py`.

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

- **`area`** — pure function of `areal_path` (no network / credentials, like
  `_CANONICAL_AREAS`): `areal_path[0]` → area, with the `[1]` moves above.
- **`family`** — seed from `language[0]` via a ~25-row map, then a small curated
  religion overlay (the literate corpora).
- **`subsistence`** — curated (~dozens of rows keyed by area/subregion/language).
- **`stratum`** — inferred from a motif's attestation set (which sets/areas it spans),
  with curation for the diagnostic layers; not per-tradition.

Only the overlay, `subsistence`, and `stratum` curation are hand-authored (dozens of
rows); `area` and the `family` seed are computed.

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

**Motifs** → `stratum`

| Motif | Stratum |
|---|---|
| A11C Sun, Moon & monster's eyes | Circum-Pacific / trans-Pacific |
| K25a5 Two brothers & the swan-maidens | Continental Eurasian (boreal) |
| B4 The fished-out earth | Indo-Pacific / Austro-Melanesian |
| H36D Death and the hare (origin of death) | African substratum |
| K27z2 Princess averts incest (jātaka-type) | axial / literate-civilisational |
| M182 The tar-baby (US South) | colonial / modern diaspora |

## What it resolves

- **#1 vs #3** collapse into `area` — one areal vocabulary from `areal_path`, so the
  overview chart and the Traditions section stop disagreeing on one page.
- **#2** (TMI) resolves onto the same three tradition properties via the gazetteer,
  so Berezkin and TMI overviews cross-reference per property, not per rogue list.
- **#4** is `family` — no longer a fourth "region", just the culture axis restricted
  to our corpus.
- Clusters 2 and 6 were never areas; they are motif `stratum` values (6 and 4).

## Implementation sketch (not built)

- `region_facets.py`: `area(areal_path)`, `family(language, name)`,
  `subsistence(name)` on traditions; `stratum(motif)` on motifs.
- `_berezkin_region` → `area()`; `culture_dict._REGION` → the TMI-label bridge onto
  the same properties; `config/traditions.json` families → `family` for the corpus.
- Overviews expose grouping by **Area / Family / Subsistence** for traditions and a
  **Stratum** slicer for motifs — replacing the one ambiguous "region" control, and
  letting a view fix a stratum before grouping by area (Berezkin's method).
