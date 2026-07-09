# Proposal: a three-facet region model (area · family · transmission)

Extends [`troubleshooting.md`](../troubleshooting.md) §"four macro-region
vocabularies". That section shows four incompatible "region" schemes fighting over
one UI slot. The root cause is not that one of them is wrong — it is that **"region"
is being asked to encode three orthogonal things at once**, and no single
mutually-exclusive list can. This proposes splitting them into three facets, each
with its own small vocabulary, plus a deterministic recipe to populate them.

Evidence base: Berezkin's authoritative 16 macro-areas and their `areal_path`
subregions; the per-tradition `language` families; the 14 empirical biclusters of
[`15-berezkin-clusters-report`](../../../mockups/15-berezkin-clusters-report/); and
the four existing schemes (troubleshooting §schemes).

## Why one list cannot work

The 14 biclusters over motif × tradition co-occurrence are the ground truth of "what
groups with what". 12 of them are areal — but **two are not**: cluster 2
(literary-epic Asia) is a *civilisational diffusion channel*, and cluster 6
(Sun-&-Moon) is a *deep-time stratum*. So even the data refuses to reduce to one
axis. Three axes are in play:

- **A · Areal geography** — where a tradition physically sits. Mutually exclusive.
- **B · Culture/linguistic family** — Indo-European, Bantu, Austronesian, plus a
  religion overlay (Abrahamic, Indic/Dharmic, Sinic…). Cuts **across** geography
  (Islam spans the Near East, Maghreb, Central Asia, parts of South/SE Asia).
- **C · Transmission / time-depth** — oral-areal vs literate-civilisational vs
  colonial-diaspora vs deep-time substrate. This is where clusters 2 and 6 live.

A tradition is a *point in all three*, e.g. Anatolian Turks = (Balkans–Caucasus–
Anatolia, Islamicate, oral-areal); a Sanskrit jātaka = (South Asia, Indic,
literate-civilisational).

## Facet A — 18 areal macro-areas

Framework = Berezkin's authoritative 16, with the two most over-lumped cells
split where a subregion boundary marks a real folklore seam, Madagascar folded into
Austronesia, and the non-areal cluster 6 kept **off** this axis. Derivation is
deterministic from `areal_path[0]` (macro) and, for the split cells, `areal_path[1]`
(subregion).

| # | Macro-area | Derived from Berezkin macro / subregion | Cluster | Folklore signature |
|---|---|---|---|---|
| 1 | Northern & Eastern Europe | NORTHERN AND EASTERN EUROPE | 0 | Christian-etiological + Finno-Ugric north |
| 2 | Western & Southern Europe | WESTERN EUROPE/NORTH AFRICA → *Southern & Western Europe, Ancient Greece & Rome* | 0 | märchen + Christian legend |
| 3 | Balkans–Caucasus–Anatolia | WESTERN EUROPE → *Balkan-Carpathians*; SW&C.ASIA → *N./S. Caucasus – Asia Minor* | 1 | tale-type crossroads |
| 4 | Near East & North Africa | SW&C.ASIA → *Near East*; W.EUROPE → *North Africa, Horn of Africa* | 1 | Semito-Mediterranean belt |
| 5 | Iran & Central Asia | SW&C.ASIA → *Iran – Central Asia, Turkestan* | 1/2 | Iranian + Turkic Central Asia |
| 6 | South Asia | SW&C.ASIA → *Aryan & South India*; TIBET-cell → *South Asia* | 2 | Aryan + Dravidian India, Sri Lanka |
| 7 | East Asia | EAST ASIA | 2 | China, Korea, Japan |
| 8 | Tibet & Mainland SE Asia | TIBET-cell → *Tibet/NE India, Burma-Indochina* | 7 | Sino-Tibetan / Austroasiatic uplands |
| 9 | Austronesia & Oceania | OCEANIA; TIBET-cell → *Nusantara*; Madagascar | 8 | island cosmogony, sea-fished land |
| 10 | Siberia | SIBERIA – MONGOLIA | 3 | taiga hunters, shamanic |
| 11 | Arctic & Beringia | BERINGIA | 3/9 | Eskimo-Aleut, the deep-time bridge |
| 12 | Subarctic & NE North America | N.AM NORTH&WEST → *Subarctic, The Northeast* | 9 | boreal Algonquian/Athabaskan trickster |
| 13 | Northwest Coast & Plateau | N.AM NORTH&WEST → *Northwest Coast, Coast-Plateau* | 5 | Raven cycle |
| 14 | Western & Southwestern N. America | N.AM NORTH&WEST → *California, Great Basin, Great Southwest* | 4 | Pueblo/California emergence |
| 15 | Plains, Woodlands & Southeast | PLAINS AND SOUTHEAST; N.AM NORTH&WEST → *Midwest* | 4 | agro-Woodland origins |
| 16 | Mesoamerica & Central Andes | MEXICO – CENTRAL ANDES | 6-core | high-culture cosmogony |
| 17 | Amazonia & Guiana | EASTERN S.AM → *Antilles-Guiana, all Amazonia, Llanos, Montaña* | 10 | tropical-forest craft origins |
| 18 | Central & Eastern Brazil (Gê–Xingu) | EASTERN S.AM → *Eastern & Southeastern Brazil* | 11 | gender/men's-house complex |
| 19 | Southern South America | SOUTHERN SOUTH AMERICA (+ Chaco) | — | Chaco & Southern Cone |
| 20 | Sub-Saharan Africa | Sub-Saharan Africa | 12/13 | Bantu + West-African trickster |
| 21 | Aboriginal Australia | AUSTRALIA | — | Dreaming |

**Tuning forks** (move the count between 18 and 21):
- South America 2 or 3 — merge 18+19 into "East & South Brazil / Southern Cone".
- Africa 1 or 2 — split 20 into West/Central vs East/Southern (Bantu); cluster 13
  (origin-of-death) is more *thematic* than areal, so 1 is the safe default.
- Beringia — fold 11 into 10 (Siberia) as one circumpolar unit, or keep the bridge.

The compact default is **18** (SA=2, Africa=1, Beringia separate).

## Facet B — culture/linguistic family (~10)

Seedable from the per-tradition `language[0]` field, then a **religion overlay** for
the literate civilisations (religion trumps linguistics where it reorganises the
corpus). Not mutually exclusive with A — this is a different partition.

| Family | Seed (`language[0]` / overlay) | Spans areas |
|---|---|---|
| Indo-European (pagan/folk) | Indoeuropean | 1,2,3 (+ diaspora) |
| Abrahamic | overlay (Jewish/Christian/Muslim corpora) | 1,2,4,5,6 |
| Indic / Dharmic | overlay on Aryan India + Buddhist | 6,7,8 |
| Sinic | Sino-Tibetan (Han) + literate overlay | 7 |
| Islamicate | overlay on Turkic/Iranian/Arab | 3,4,5 |
| Uralic & Altaic | Uralic, Altaic | 1,5,10 |
| Circumpolar / Palaeo-Asiatic | Escoaleut, Chukotko-Kamchatkan, isolate-N | 10,11 |
| Amerindian | Na-Dene, Algic, Uto-Aztecan, Tupian, Carib, Macro-Ge, Salishan… | 12–19 |
| Sub-Saharan (Niger-Congo / Nilo-Saharan) | Niger-Kongo, Nilo-Saharan | 20 |
| Austronesian & Papuan | Austronesian, Austroasiatic, Papuan | 9 |
| Australian | Australian | 21 |

(This is scheme #4 generalised from our 12 corpus families to the whole motif
catalogue; the corpus keeps its own labels as a subset.)

## Facet C — transmission / time-depth (4)

| Type | Meaning | Signature cluster |
|---|---|---|
| oral-areal | attested from oral fieldwork; spreads by contact | most (12 of 14) |
| literate-civilisational | book/epic diffusion (Sanskrit, Pali, Chinese, Greek, Arabic) | 2 |
| colonial-diaspora | recent transplant (Afro-Caribbean, Ibero-American) | ATU tails |
| deep-time substrate | Pleistocene-era shared layer, trans-continental | 6 (Sun-&-Moon) |

Most Berezkin traditions are oral-areal; the literate/deep-time tags mark the
handful the co-clustering flagged as non-areal, giving clusters 2 and 6 a home.

## Deterministic population recipe

- **Facet A** — pure function of `areal_path`: map `areal_path[0]` 1:1 to a macro-area,
  except the five split cells (SW&C.Asia, W.Europe/N.Africa, Tibet-cell, N.Am
  North&West, Eastern S.Am) which branch on `areal_path[1]` per the table above. No
  network, no credentials (works off the committed reference like `_CANONICAL_AREAS`).
- **Facet B** — seed from `language[0]` via a ~25-row family map, then apply a small
  curated **religion overlay** list (the literate corpora: Jewish, Christian, Islamic,
  Hindu, Buddhist, …).
- **Facet C** — a short curated set: default `oral-areal`; a literate list (the
  book traditions); a colonial-diaspora list (New-World animal-tale tails); and the
  deep-time tag applied to cluster-6 membership.

Only B's overlay and C are hand-curated (dozens of rows, not 1046); A and B's seed
are computed.

## Sample mapping (`tradition → area · family · transmission`)

| Tradition | Area | Family | Transmission |
|---|---|---|---|
| Lithuanians | N. & E. Europe | Indo-European | oral-areal |
| Germans (NW) | W. & S. Europe | Indo-European | oral-areal |
| Anatolia Turks | Balkans–Caucasus–Anatolia | Islamicate | oral-areal |
| Egyptian (ancient) | Near East & N. Africa | Abrahamic-adjacent | literate-civilisational |
| Mongols (Khalkha) | Siberia | Uralic & Altaic | oral-areal |
| Indian literary | South Asia | Indic / Dharmic | literate-civilisational |
| Han Chinese | East Asia | Sinic | literate-civilisational |
| Mizo (Lushei) | Tibet & Mainland SE Asia | Sino-Tibetan | oral-areal |
| Ifugao | Austronesia & Oceania | Austronesian | oral-areal |
| Nanai | Siberia | Uralic & Altaic (Tungusic) | oral-areal |
| Tlingit | Northwest Coast & Plateau | Amerindian (Na-Dene) | oral-areal |
| Menominee | Subarctic & NE N. America | Amerindian (Algic) | oral-areal |
| Navajo | W. & SW N. America | Amerindian (Na-Dene) | oral-areal |
| Kechua (Quechua) | Mesoamerica & Central Andes | Amerindian (Quechuan) | oral-areal |
| Warao | Amazonia & Guiana | Amerindian (isolate) | oral-areal |
| Bororo | Central & Eastern Brazil | Amerindian (Macro-Ge) | oral-areal |
| Hausa | Sub-Saharan Africa | Sub-Saharan (Afro-Asiatic) | oral-areal |
| Wolof | Sub-Saharan Africa | Sub-Saharan (Niger-Congo) | oral-areal |
| Aranda | Aboriginal Australia | Australian | oral-areal |
| Br'er-Rabbit US South | Plains, Woodlands & SE | Sub-Saharan (diaspora) | colonial-diaspora |
| Toba / Pilaga | Southern South America | Amerindian (Guaicuruan) | deep-time substrate (Sun-Moon) |

## What it resolves

- **Scheme #1 vs #3** (troubleshooting): both collapse into Facet A — one areal
  vocabulary derived from `areal_path`, so the overview chart and the Traditions
  section stop disagreeing on the same page.
- **Scheme #2** (TMI): TMI's culture labels resolve onto the *same* three facets via
  the existing gazetteer, so Berezkin and TMI overviews become cross-referenceable
  per facet instead of per incompatible list.
- **Scheme #4** (corpus families): recognised as Facet B — no longer a rogue fourth
  "region"; it is the culture-family axis restricted to our texts.
- Clusters 2 and 6, homeless in any geographic list, are exactly Facet C's
  literate-civilisational and deep-time-substrate tags.

## Implementation sketch (not built)

- `region_facets.py`: `area(areal_path)`, `family(language, name)`, `transmission(name)`.
- `_berezkin_region` → `area()`; `culture_dict._REGION` → the TMI-label bridge onto the
  same facets; `config/traditions.json` families → Facet B for the corpus.
- Surfaces as three grouping toggles in the overviews (Area / Family / Transmission)
  instead of one ambiguous "region" control.
