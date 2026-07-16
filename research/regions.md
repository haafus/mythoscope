# The `region` classification — canonical specification

The single top-level classification of mythological and religious traditions for mythoscope. This is
the definitive record: evaluation criteria, the reasoning trail, the compromises and decisions, the
exact final list, and — for each region — a description (what it contains and why it is distinguished)
and the traditions that belong to it.

Field name: **`region`** (14 values). Two-level model: **`region` → `tradition`** (a region groups
many traditions; a tradition is a single mythology such as Greek or Norse). `region` supersedes the
retired `major_tradition` and the Berezkin `area` as the one primary axis. (Alternative field name if
`area` is kept alongside: `sphere`.)

> **Single-axis decision (2026-07).** `region` is the **only** top-level classification of a tradition. The
> multi-facet Tradition model once proposed — `family`, `subsistence`, `theme_profile` facets, see
> [`../docs/proposals/tradition-architecture-unified.md`](../docs/proposals/tradition-architecture-unified.md)
> and [`../docs/proposals/macro-area-facets.md`](../docs/proposals/macro-area-facets.md) — is **not adopted.**
> There is **no facet layer**: no `family`, no `subsistence`. (Motif-level `theme` and `stratum` are properties
> of *motifs*, a separate entity, and are unaffected by this decision. `family`/`subsistence` survive only as
> exploratory facets inside the analysis mockups.)

Companion docs: `research/tradition-classification.md` (criteria + candidate history),
`research/mythology-encyclopedias-survey.md` (how reference works carve the world),
`research/corpus-sourcing-survey.md` (obtainable full text).

---

## 1. Guiding principle — corpus-first

The catalogue is built on an assembled **full-text corpus**, not on Berezkin's motif index.
Consequences:

- **`areal_path` is provisional** — it is Berezkin's areal grouping, a scaffold, not authoritative.
- **"From data" means differences between the texts themselves** (content, language, genre), not
  motif-attestation counts.
- **Re-annotation is allowed.** The scheme serves the corpus; where the corpus needs a different
  partition, traditions are re-annotated.
- **Start from obtainability** — what full text can actually be acquired constrains what fills each
  region first (the literate Old World is build-ready; the oral world needs OCR/curation).

## 2. Evaluation criteria

Every candidate was judged on four criteria, which routinely conflict:

1. **Geography** — does each region map to a compact, unambiguous area on the map?
2. **Cultural commonality** — are the traditions inside a region genuinely kin (language, religion,
   descent, society type), not merely neighbours?
3. **Expressiveness & clarity** — recognizable, intuitive names; a sensible count; no artificial
   merges or index-artifact regions.
4. **Volume of traditions & material** — balance by content: number of traditions *and* actual
   full-text volume; no empty regions, no overloaded heaps. Measured against the assembled corpus,
   **not** the Berezkin index.

Known conflicts: geography vs volume (Europe is small in area, large in text); cultural commonality
vs volume (the literate Old World = few traditions / vast text; the oral world = many traditions /
little text); expressiveness vs volume (balance-driven merges read oddly as sections).

## 3. Reasoning trail — decisions & compromises

The scheme is the **cultural-areal** answer (candidate B), chosen as the navigation backbone over the
two rivals: **A** (volume-balanced by Berezkin motif counts — abandoned once we went corpus-first)
and **C** (encyclopedic/text-weighted — the future shape if the catalogue is re-weighted by text,
splitting the heavyweight literate regions). Key decisions, in order:

- **Europe = one region, not two.** The two-Europe split was an artefact of candidate A (Europe was a
  motif-volume heap). By full text Europe (~2 Mw) is smaller than the single Near East region and
  1/16 of single South Asia; and Sub-Saharan Africa (more internally diverse) is one region. Splitting
  Europe while Africa/Native North America are each one region is Eurocentric over-resolution. The
  Classical/Northern division survives as a **sub-rubric**, not a top-level split.
- **Near East absorbs North Africa and Anatolia.** North Africa (Egypt anchor, Maghreb, Horn) is
  Afroasiatic + Arab-Islamic, tied to the Near East (the MENA grouping); Anatolia/Hittites are the
  Bronze-Age Ancient Near East. Kept **"Near East"** (the scholarly term for this predominantly
  ancient material) over "Middle East" (a modern geopolitical term).
- **Caucasus paired with Iran** (not given its own region, not folded into the steppe). The Caucasus
  is a shatter zone — weak on cultural commonality, thin on text — so it does not earn a standalone
  region; but the Caucasus is historically part of the Iranian/Persianate world (the Nart epic has an
  Iranian–Alan core; Haussig's *Wörterbuch* pairs "Caucasian and Iranian peoples"). Armenians and
  Georgians (Christian, textual) sit here; the autochthonous Nart-saga peoples too.
- **Iran leaves "Central Asia"; the steppe becomes "Inner Asia".** With Iran in #4, the residual
  region is the Turco-Mongol nomadic steppe. "Central Asia" strongly connotes the Persianate oasis
  (now in #4), so it would mislead; **"Inner Asia"** (Lattimore) precisely denotes the nomadic
  interior.
- **Asia split by cultural sphere (Indosphere vs Sinosphere).** Mainland SE Asia is Indianized
  (Ramayana, Sanskrit), so it belongs on the Indic side, not with Sinic East Asia. Then **South Asia
  was un-merged** from mainland SE Asia: South Asia is the single largest textual tradition and a
  distinct civilization (crit 4 + 2), so it is its own region, and Mainland Southeast Asia is its own
  (smaller) region. East Asia = the CJK Sinosphere.
- **Vietnam → Mainland Southeast Asia.** Berezkin classes Viet/Muong as Austroasiatic Indochina (892
  attributions); language (Austroasiatic), geography (Indochina), and the standard regional term all
  point to SE Asia. Only the Sino-Vietnamese literary overlay dissents, and it is outweighed. East
  Asia stays the clean CJK core.
- **Austronesia its own region, anchored by Taiwan.** Honouring the cohesive Austronesian cultural
  area (crit 2, re-elevated): one family, one Neolithic maritime expansion from Taiwan through island
  SE Asia to Polynesia and Madagascar. Island SE Asia (Nusantara) sits here — not in a vague
  "Oceania", not split into mainland SE Asia — with the Taiwan Formosan peoples as the homeland
  anchor.
- **Sahul split off — Papua & Aboriginal Australia.** The non-Austronesian deep-Pacific (Papuan New
  Guinea + Aboriginal Australia, the Pleistocene Sahul population) is a distinct culture area from the
  Neolithic Austronesian expansion; splitting it also cures the Aboriginal-Australia singleton.
- **Circumpolar North joins N. Eurasia and N. America across Bering.** The circumpolar Arctic/boreal
  belt (Eskimo-Aleut, palaeo-Asiatic, taiga hunter-shamans) is genuinely continuous; splitting it by
  continent tears a real culture area. It takes the Arctic + boreal taiga + Beringia + Arctic North
  America; the non-Arctic steppe (southern Siberia–Mongolia) stays in Inner Asia.
- **Sub-Saharan Africa = one region.** The West/Central vs East/Southern split was culturally
  motivated but not derivable from `areal_path` (Berezkin's Sub-Saharan Africa is a flat macro) and
  both halves were thin; encyclopedias treat it as one. Re-split later if finer African data arrives.

**Standing compromises:**

- *Granularity vs cohesive areas.* We accepted more regions to honour cohesive cultural areas
  (Austronesia, Sahul) but merged Europe back to one for consistency — so the count settled at 14.
- *The one unavoidable seam.* The Eurasian trunk has two dead-end arms (the southern maritime arm to
  Australia, the northern arm to Bering); a linear list must break once. The break is placed at the
  Old-World/New-World boundary (`Papua & Aboriginal Australia → Circumpolar North`), the most
  meaningful location.
- *Corpus imbalance.* `region` is the cultural-areal navigation backbone; by full text the material
  still concentrates in a few Old-World regions and the oral regions stay text-thin. If the catalogue
  is later re-weighted by text, the heavyweight regions (South Asia, Near East, Europe) would split
  toward scheme C, and the oral regions would stay pooled. That is a re-weighting of the same
  material, not a defect of the backbone.

### The central axis of compromise — distinctiveness vs documentation

Underneath the four criteria sits **one dominant tension**, and it sets the granularity of the whole
scheme. Two forces pull region size in opposite directions:

- **Cultural distinctiveness** would cut finely where diversity is highest — and diversity is highest
  in the **oral** world. Sub-Saharan Africa alone spans three-plus unrelated language phyla; Native
  North America, Circumpolar, and Amazonia are each internally deep.
- **Volume of documentation** (corpus-first, crit 4) would cut finely where the **text** is deepest —
  and text concentrates in the **literate** Old World (South Asia, Near East, East Asia, Europe).

These point *against* each other: the most culturally distinct regions are the least documented, and
the best-documented are internally the most uniform. Where they conflict, **documentation wins the
granularity call**: the literate spheres are split fine (Indosphere/Sinosphere; South / SE / East /
Inner Asia), while the more diverse oral regions stay pooled (one Sub-Saharan Africa, one Lowland South
America) with their internal diversity demoted to sub-rubrics. This asymmetry is deliberate and
load-bearing, not an oversight — **by pure distinctiveness the first region to split would be
Sub-Saharan Africa, not any part of Asia or Europe.** Keeping the axis explicit is what stops the
scheme from being read as a claim that Asia is "more diverse" than Africa; it is only better recorded.

### Clinality — the scheme cuts discrete lines through continua

Mythological and cultural variation is **clinal**: a bundle of overlapping gradients (language,
subsistence, religion, descent, diffusion) that shade continuously into one another, not a mosaic of
sharp-edged cells. Any 14-region partition therefore draws **hard lines across soft gradients**.
Regions are well-founded where several gradients **bundle and steepen together** — a cultural
watershed: the Sahara, the Indosphere/Sinosphere seam, the Austronesian sea-frontier, the Bering
crossing. They are arbitrary where a single gradient is shallow — the Caucasus shatter-zone, the
Cree/Innu taiga, the Andean–Amazon flank, the temperate ↔ Arctic transition. The **boundary cases
(§6)** are not failures but exactly the places where the cline is caught mid-slope — Yakut (Turkic ↔
Arctic), Sami (Finno-Ugric ↔ reindeer), Vietnam (Austroasiatic ↔ Sinic), Anatolia, Ecuador (Andes ↔
Amazon), the Antilles (Arawak/Carib ↔ Mesoamerica). Each is assigned by whichever gradient we
privilege and **flagged**, so the underlying continuity is never mistaken for a wall. On the map this
is why some between-region borders are "harder" than others, and why an internal spread (Europe:
Homer ↔ Kalevala ↔ Basque) can exceed a between-region gap (South Asia ↔ mainland SE Asia, both
Indosphere).

### Strata — a synchronic cut through vertically layered material

The region scheme is a **horizontal slice through a vertically stratified reality.** Every region is a
stack of historical layers — a **substrate → expansion(s) → literate / colonial overlay** sequence,
recorded with datings in each region's **Strata** field (Khoisan forager substrate → Bantu expansion →
Sahelian Islam → Christian overlay; PIE steppe → Classical antiquity → Christianization → Eddic
fixation). Three consequences:

- **The same ground belongs to different regions at different depths.** European Russia is
  Uralic-then-Slavic; the Hexi Corridor is Tibetan/Tocharian-then-Han; the Antilles are
  Arawak-then-colonial. The `areas` map colours the **deepest attested indigenous stratum**, not the
  modern political surface — which is why Madagascar reads Austronesian and the Caribbean reads with
  lowland South America.
- **A region's coherence lives at one particular stratum.** Austronesia coheres at the Neolithic
  maritime-expansion layer, the Near East at the Bronze-Age-and-earlier layer, Europe at the PIE
  layer. Compared at the wrong depth, a grouping can look wrong (e.g. modern Vietnam is Sinicized on
  the surface but Austroasiatic in the substrate).
- **Space and time are two axes of one catalogue.** `region` partitions space; the dated `Strata`
  partition time. The `areas` map is one horizontal cut; a future "strata" view would cut the other
  way, showing how a single region is assembled layer by layer.

## 4. Ordering — the out-of-Africa arc

Ordered as a human-dispersal arc: cradle → exit corridor → the whole contiguous Old World → the one
deliberate seam → the Americas, ending at the terminal tip of settlement. Every Old-World transition
is geographically contiguous; the single seam is `Papua & Aboriginal Australia → Circumpolar North`.

---

## 5. The 14 regions

Each entry: **Description** (what/why) · **Subdivision** (the next level of splitting that makes sense) ·
**Strata** (the historical layers at work, with datings) · **Traditions** · colour (`base`, see §8).

### 1. Sub-Saharan Africa · `#CC503E`
**Description.** The mythologies of Africa south of the Sahara — the world's densest concentration of
distinct oral traditions, spanning several unrelated language phyla. Distinguished as one region
because Berezkin does not subdivide it and both candidate halves (West/Central vs East/Southern) are
text-thin; encyclopedias treat "Black Africa" as one. Predominantly oral; the open textual assets are
the Yoruba Ifá corpus and Ethiopian Ge'ez (boundary — Semitic/Christian).
**Subdivision.** West African (Niger-Congo: Yoruba, Akan, Fon, Igbo) · Central & Southern Bantu ·
Nilotic & Cushitic East Africa · Khoisan foragers.
**Strata.** Khoisan forager substrate (deepest, pre-agricultural, >20 ka) → Bantu expansion carrying
agriculture + iron across Central/Southern Africa (~1000 BCE – 500 CE) → Nilotic pastoralist spread →
Sahelian Islam via the trans-Saharan trade (from ~8th c. CE) → Ethiopian Christian literate layer
(Ge'ez, from 4th c. CE) → colonial/Christian overlay (16th–20th c.).
**Traditions.** Yoruba · Igbo · Akan/Ashanti · Fon (Dahomey) · Dogon · Bambara · Serer · Kongo ·
Yombe · Zulu · Xhosa · Shona · Kikuyu · Baganda · Luba · Fang · Dinka · Nuer · Maasai · Azande · San
(Bushman) · Khoekhoe · Mbuti · (Ethiopian/Amhara — boundary with Near East).

### 2. Near East & North Africa · `#2A4895`
**Description.** The Ancient Near East plus North Africa and the Abrahamic homelands — the earliest
literate mythologies (cuneiform, hieroglyphic) and the source region of the three Abrahamic religions.
Distinguished as the Bronze-Age/antiquity core of the Old World, anchored by written text. Includes
Anatolia (Hittite) and the Maghreb; "Near East" chosen over "Middle East" for its ancient material.
**Subdivision.** Mesopotamian (Sumer/Akkad/Babylon/Assyria) · Egyptian · Levantine-Anatolian (Ugarit,
Hittite, Canaan, Phoenicia) · Arabian · Abrahamic (Judaism/Christianity/Islam) · Maghreb-Berber.
**Strata.** Sumerian (cuneiform from ~3200 BCE) → Akkadian-Babylonian-Assyrian (2nd–1st mill. BCE) →
Egyptian (Pyramid Texts ~2400 BCE) → Hittite (~1650–1180 BCE) & Ugaritic (~1400–1200 BCE) → Iron-Age
Levant / Hebrew (1st mill. BCE) → Abrahamic overlay: Judaism (Second-Temple era), Christianity
(1st c. CE), Islam (7th c. CE) → Arab-Islamic spread (7th–8th c. CE).
**Traditions.** Sumerian · Akkadian · Babylonian · Assyrian · Egyptian · Hittite · Hurrian ·
Ugaritic/Canaanite · Phoenician · Elamite · pre-Islamic Arabian · Jewish · Christian · Islamic ·
Berber (Amazigh).

### 3. Europe · `#EDAD08`
**Description.** The mythologies of Europe — predominantly Indo-European (with Uralic Finno-Ugric),
sharing deep Proto-Indo-European roots. One region (not split) because by text it is lighter than the
single Near East region and internally more uniform than one-region Sub-Saharan Africa. The
Classical Mediterranean vs Northern/Eastern division is a **sub-rubric**.
**Subdivision.** Greco-Roman (Classical Mediterranean) · Celtic · Germanic-Norse · Slavic · Baltic ·
Finno-Ugric / Uralic.
**Strata.** Pre-IE Neolithic-farmer & "Old European" substrate (Basque relic; farmers from ~7000 BCE)
→ Proto-Indo-European steppe expansion (~3000–2500 BCE) branching into the IE mythologies → Classical
antiquity (Greek from 8th c. BCE, then Roman) → Migration Period (Germanic & Slavic expansions,
4th–9th c. CE) → Christianization absorbing the pagan layer (4th–12th c. CE) → late written fixation
(Eddas ~13th c.; Kalevala compiled 1835–49).
**Traditions.** Greek · Roman · Etruscan · Celtic (Irish, Welsh, Gaulish, Breton) · Norse ·
Anglo-Saxon · Continental Germanic · Slavic (Russian, Polish, South Slavic) · Baltic (Lithuanian,
Latvian, Prussian) · Finnish · Estonian · Sami · Hungarian · Mordvin/Mari · Basque.

### 4. Caucasus & Iran · `#6F4070`
**Description.** The Iranian/Persianate world plus the Caucasus — bound by Iranian cultural and
linguistic threads (Zoroastrian, Scythian-Alan, Persianate). The Caucasus does not stand alone (a
thin, internally diverse shatter zone) but its autochthonous Nart-epic peoples and its Christian
literate peoples (Armenian, Georgian) attach here, following the Haussig "Caucasian and Iranian"
pairing and the Iranian–Alan core of the Nart sagas.
**Subdivision.** Iranian (Persian/Zoroastrian, Scythian-Alan, Ossetian) · South Caucasian (Georgian,
Armenian) · North Caucasian (Circassian, Chechen/Vainakh, Dagestani — Nart).
**Strata.** Autochthonous Caucasian Nart substrate → Indo-Iranian / Scythian-Alan layer (1st mill.
BCE; the Iranian core of the Nart sagas) → Zoroastrian (Avesta oral ~1000 BCE; Sasanian codification
3rd–7th c. CE) → Christian Armenia & Georgia (from 4th c. CE) → Islam (7th–8th c. CE) → Persian
literary epic (Shahnameh ~1000 CE).
**Traditions.** Persian/Zoroastrian · Scythian · Sogdian · Ossetian (Nart) · Armenian · Georgian ·
Circassian (Nart) · Chechen/Vainakh (Nart) · Dagestani peoples · (Kurdish · Azeri).

### 5. Inner Asia · `#1D6996`
**Description.** The Turco-Mongol nomadic steppe — the pastoralist, shamanic, Tengrist interior of
Asia, with its own great oral epics. "Inner Asia" (not "Central Asia") because Iran/the Persianate
oasis is in #4; this region is specifically the nomadic steppe belt. Tibet is a boundary case (Bon /
Tibeto-Mongolian Vajrayana) placed here for its Inner-Asian Buddhist ties.
**Subdivision.** Turkic (Kyrgyz/Manas, Kazakh, Yakut, Uyghur) · Mongolic (Mongol/Geser, Buryat,
Kalmyk/Jangar) · Tibetan (Bon / Vajrayana — boundary).
**Strata.** Ancient shamanic-Tengrist substrate → Scythian/Xiongnu nomad era (1st mill. BCE) → Turkic
Khaganates (Old Turkic runic, 6th–8th c. CE) → Mongol Empire spreading the Geser epic cycle (13th c.)
→ Tibetan-Buddhist (Vajrayana) overlay (Mongol conversion 16th c.) → western-Turkestan Islam
(from ~10th c.).
**Traditions.** Turkic/Tengrist · Kyrgyz (Manas) · Kazakh · Uyghur · Yakut/Sakha · Mongol (Geser,
Tengri) · Buryat · Kalmyk (Jangar) · Tuvan · Altai · Tibetan (Bon; boundary) · Manchu (boundary).

### 6. South Asia · `#38A6A5`
**Description.** The Indian subcontinent — the single largest textual tradition on Earth (the Vedic
corpus, Sanskrit epics, the Puranas, the Buddhist and Jain canons). Its own region on the strength of
both volume (crit 4) and civilizational distinctness (crit 2); India is the source of the Indosphere,
distinct from its Indianized periphery.
**Subdivision.** Vedic-Hindu (Indo-Aryan) · Dravidian · Buddhist · Jain · tribal (Munda/Austroasiatic)
· Sinhalese · Himalayan.
**Strata.** Indus-Valley / Harappan + Dravidian & tribal substrate (~2600–1900 BCE) → Vedic
(Indo-Aryan, Rigveda ~1500–1200 BCE) → Buddhism & Jainism (founders ~5th c. BCE) → epic-Puranic
Hinduism (Mahabharata/Ramayana ~400 BCE – 400 CE; Puranas 300–1500 CE) → Bhakti / medieval → Islamic
(from ~11th c.), Sikh (15th c.).
**Traditions.** Vedic · Hindu · Buddhist · Jain · Dravidian (Tamil, Telugu, Kannada, Malayalam) ·
Munda/Santal · Gond · Bhil · Sinhalese · Newar/Nepali · Sikh · Kashmiri.

### 7. Mainland Southeast Asia · `#94346E`
**Description.** The Indianized mainland — Indochina and the Tibeto-Burman/Tai/Austroasiatic hill
peoples whose classical mythology is Hindu-Buddhist (the Ramayana traditions). On the Indic side of
the Indosphere/Sinosphere split, distinct from South Asia proper (periphery, not source) and from
Sinic East Asia. Vietnam is here (Austroasiatic + geography outweigh its Sinic literary overlay).
**Subdivision.** Burmese · Tai (Thai/Lao/Shan) · Khmer · Vietnamese · Tibeto-Burman & Hmong-Mien hill
peoples.
**Strata.** Austroasiatic / animist substrate → Indianization (Hindu-Buddhist states — Funan, Champa,
Angkor 9th–15th c. CE — from ~1st–5th c.) → Sinic overlay in Vietnam (Chinese rule 111 BCE – 938 CE)
→ Tai migrations south (~8th–13th c.) → Theravada-Buddhist dominance (from ~11th c.).
**Traditions.** Burmese · Mon · Thai/Tai · Lao · Shan · Khmer · Vietnamese (Viet/Muong) · Cham
(boundary — Austronesian) · Hmong-Mien · Karen · Tibeto-Burman highlanders.

### 8. East Asia · `#E17C05`
**Description.** The Sinosphere — China, Korea, Japan — sharing the Chinese classical, Taoist,
Confucian and Mahayana-Buddhist textual world. The clean CJK core (Vietnam, though Sinicized, is left
in mainland SE Asia). Ainu is a boundary case (indigenous Japan, Circumpolar affinity).
**Subdivision.** Chinese (Han; Taoist, Confucian, Chinese-Buddhist, folk) · Korean · Japanese (Shinto)
· Ainu (boundary) · Ryukyuan.
**Strata.** Neolithic-shamanic substrate (Shang oracle bones ~1200 BCE) → classical Chinese (Zhou;
Confucianism & Taoism 6th–3rd c. BCE) → Buddhism arrival (China ~1st c. CE, Korea 4th, Japan 6th) →
Shinto codification (Kojiki 712 CE, Nihon Shoki 720 CE) → vernacular-novel fixation (Ming, e.g.
*Journey to the West* 16th c.).
**Traditions.** Chinese (Han; Taoist, Confucian, Chinese folk, Chinese Buddhist) · Korean · Japanese
(Shinto) · Ryukyuan · Ainu (boundary) · southern-China ethnic minorities (Yi; boundary with SE Asia).

### 9. Austronesia · `#0F8554`
**Description.** The Austronesian cultural area — one language family and one Neolithic maritime
expansion, from the Taiwan homeland through island Southeast Asia to the Pacific and Madagascar. Its
own region to keep this cohesive descent-based area intact (crit 2), anchored by the Formosan
peoples. Island SE Asia (Nusantara) sits here, not in mainland SE Asia or a vague "Oceania"; the
Indianized Javanese/Balinese are the literate exception within it.
**Subdivision.** Formosan (Taiwan homeland) · western Malayo-Polynesian (island SE Asia + Madagascar)
· Oceanic (Polynesian, Micronesian, coastal Melanesian).
**Strata.** Austronesian expansion out of Taiwan (~3000 BCE) — the base layer, one language family →
Lapita / Oceanic dispersal into the Pacific (~1500–1000 BCE; Polynesia settled ~900 BCE – 1200 CE) →
Indianization of western Nusantara (Java/Bali Hindu-Buddhist, 4th–15th c. CE) → Islamization of the
Malay world (13th–16th c.) → colonial/Christian (16th c.+).
**Traditions.** Taiwan Formosan (Atayal, Bunun, Paiwan, Ami, Tsou) · Javanese · Balinese · Sundanese ·
Batak · Dayak · Toraja · Filipino (Tagalog, Ifugao) · Malay · Polynesian (Maori, Hawaiian, Tahitian,
Samoan, Tongan, Rapa Nui) · Micronesian · Fijian (coastal Melanesian) · Malagasy.

### 10. Papua & Aboriginal Australia · `#A9773F`
**Description.** The non-Austronesian deep-Pacific — the Pleistocene **Sahul** population: Papuan /
highland New Guinea peoples and Aboriginal Australians (the Dreaming). Distinguished from Austronesia
by descent and antiquity (Sahul was settled ~50 ky ago, long before the Neolithic Austronesian
arrival). "Aboriginal" marks the Indigenous tradition against the modern nation.
**Subdivision.** Aboriginal Australian (many language blocks) · Papuan / highland New Guinea
(Trans-New-Guinea and other phyla) · non-Austronesian Melanesian.
**Strata.** Deep Sahul settlement (~50,000+ BP) — among the oldest continuous living traditions (the
Dreaming) → Australia sea-isolated as sea levels rose (~8000 BCE) → independent New Guinea highland
agriculture (~7000 BCE) → Austronesian coastal contact (from ~1500 BCE; the interior stays Papuan) →
minimal external overlay until colonial contact (recent).
**Traditions.** Aboriginal Australian (Arrernte, Yolngu, Warlpiri, Pitjantjatjara, and many others) ·
Papuan highland groups (Enga, Huli, …) · non-Austronesian Melanesian.

### 11. Circumpolar North · `#5F4690`
**Description.** The continuous circumpolar Arctic/boreal belt spanning both continents across the
Bering Strait — Arctic and Subarctic hunter-shaman cultures that geography joins but the continental
boundary would tear. Includes NE Siberian palaeo-Asiatics, the boreal taiga peoples, Beringia, and
Arctic/Subarctic North America. The Bering bridge into the New World.
**Subdivision.** NE Siberian palaeo-Asiatic (Chukchi, Koryak, Yukaghir, Nivkh) · boreal Tungus &
Uralic Siberian (Evenki, Khanty, Nenets) · Eskimo-Aleut (Inuit/Yupik/Aleut) · Na-Dene / Subarctic
Athabaskan.
**Strata.** Upper-Palaeolithic circumpolar hunter-shaman substrate → Beringian peopling-of-the-Americas
layer (~20,000–15,000 BP crossings) → Na-Dene dispersal → late Eskimo-Aleut / Thule expansion across
Arctic North America to Greenland (~1000 CE) → Russian & colonial contact (recent, 17th c.+).
**Traditions.** Chukchi · Koryak · Yukaghir · Nivkh · Itelmen · Evenki (Tungus) · Even · Khanty ·
Mansi · Nenets · Ket · Inuit/Eskimo (Yupik, Inupiat, Kalaallit) · Aleut · Na-Dene/Athabaskan (Dene) ·
Northern Cree · (Ainu, Sami — boundary affinities).

### 12. Native North America · `#73AF48`
**Description.** Indigenous North America outside the Arctic — the temperate culture areas: Eastern
Woodlands, Plains, Plateau, California, the Southwest, and the Northwest Coast (boundary with
Circumpolar). "Native" distinguishes the Indigenous traditions from the modern nation.
**Subdivision.** Eastern Woodlands (Iroquois, Algonquian) · Plains (Siouan, Caddoan) · Plateau ·
California · Southwest (Pueblo; Athabaskan Navajo/Apache) · Northwest Coast (boundary).
**Strata.** Palaeo-Indian founding (Clovis ~13,000 BP) → Archaic regional differentiation →
agricultural Mississippian mound-builders (~800–1600 CE) → Athabaskan (Navajo/Apache) southward
migration (~1400 CE) → post-contact equestrian Plains transformation (17th–19th c.).
**Traditions.** Iroquois (Haudenosaunee) · Algonquian (Ojibwe, Cree-south, Abenaki) · Lakota/Sioux ·
Cheyenne · Pawnee · Blackfoot · Nez Perce · Salish · Pomo · Miwok · Yokuts · Navajo (Diné) · Hopi ·
Zuni · Pueblo · Apache · Tlingit · Haida · Kwakwaka'wakw · Tsimshian.

### 13. Mesoamerica & the Andes · `#994E95`
**Description.** The high civilizations of the Americas — the two literate/state-level New-World myth
complexes, with codices and colonial chronicles (Popol Vuh, the Florentine Codex, the Huarochirí
Manuscript). Grouped together as the Americas' textual heartland, distinct from the surrounding
tribal lowlands.
**Subdivision.** Mesoamerican (Maya, Aztec/Nahua, Mixtec, Zapotec, Olmec/Toltec) · Andean
(Inca/Quechua, Aymara, Moche, Chibcha/Muisca).
**Strata.** Formative/Preclassic (Olmec ~1500–400 BCE; Andean Chavín ~900–200 BCE) → Classic (Maya
~250–900 CE; Moche, Nazca) → Postclassic (Toltec; Aztec 14th–16th c.; Inca 15th–16th c.) → colonial
written fixation (Popol Vuh, Florentine Codex, Huarochirí Manuscript — 16th c. CE).
**Traditions.** Aztec/Nahua · Maya · Mixtec · Zapotec · Olmec · Toltec · Tarascan (Purépecha) ·
Huichol · Inca/Quechua · Aymara · Moche · Chibcha/Muisca · Nazca.

### 14. Lowland South America · `#2A8A9F`
**Description.** The tropical and temperate lowlands of South America — Amazonia, the Guianas, the
Gran Chaco, and the Southern Cone: the densest concentration of small-scale Amerindian oral
traditions, the terminal end of the human expansion. Distinct from the Andean highlands (#13).
**Subdivision.** Amazonian (Tupí-Guaraní, Carib, Arawak, Ge/Macro-Ge, Tucano, Pano) · Gran Chaco ·
Guiana · Southern Cone / Patagonia (Selk'nam, Tehuelche; Mapuche — boundary).
**Strata.** Deep post-Beringian Amerindian settlement (reaching southern South America ~12,000+ BP) →
Amazonian language-family dispersals (Arawak, Tupí, Carib expansions, ~2000 BCE – 1500 CE) → complex
pre-Columbian Amazonian societies (*terra preta*, ~500 BCE – 1500 CE) → ethnographic recording amid
colonial disruption (19th–20th c.).
**Traditions.** Tupí/Guaraní · Carib · Arawak · Ge (Kayapó, Bororo) · Yanomami · Tucano · Jivaro
(Shuar) · Warao · Mapuche (boundary — sub-Andean) · Selk'nam/Ona · Tehuelche · Guaycuru.

---

## 6. Boundary cases (flagged, not hard-resolved)

- **Tibet** — Inner Asia (Tibeto-Mongolian Vajrayana) vs South Asia (Himalaya) vs East Asia (Sinic).
  Placed in Inner Asia.
- **Ethiopian / Horn of Africa** — Sub-Saharan Africa (geography) vs Near East (Semitic/Christian).
  Placed in Sub-Saharan Africa.
- **Ainu** — East Asia (geography) vs Circumpolar North (culture). Placed in East Asia.
- **Sami** — Europe (Finno-Ugric) vs Circumpolar North (reindeer culture). Placed in Europe.
- **Cham** — Mainland SE Asia (geography) vs Austronesia (language). Placed in Mainland SE Asia.
- **Northwest Coast (Tlingit/Haida)** — Native North America vs Circumpolar North (subarctic Pacific).
  Placed in Native North America.
- **Mapuche** — Lowland South America vs Mesoamerica & the Andes (sub-Andean). Placed in Lowland
  South America.
- **Vietnam** — resolved to Mainland Southeast Asia (see §3).

## 7. Naming conventions

- Add the indigenous qualifier only where the bare name reads as the modern nation: **Native** North
  America, **Aboriginal** Australia — not elsewhere (Mesoamerica, Sub-Saharan Africa need none).
- Prefer common region nouns (East Asia, Sub-Saharan Africa) over ethnolinguistic adjectives, except
  where the cultural area *is* the point: **Austronesia** (region noun, not "Austronesian").
- Chosen over rejected: **Near East** (not Middle East, for ancient material); **Inner Asia** (not
  Central Asia, because Iran/the Persianate is a separate region); **Mainland Southeast Asia** (not
  Indochina, which is colonial-tinged and narrowly read); **Circumpolar North** (not "Circumpolar &
  Arctic", a tautology).

## 8. Colour palette

Built on **CARTOColors Prism** — a cartographer-designed qualitative palette (https://carto.com/carto-colors/).
Prism's 11 coloured hues map onto the arc in spectral order (its 12th, a neutral grey, is dropped); the
3 remaining slots are filled by colours interpolated *in Prism's style* into its two widest hue gaps
(teal↔blue and blue↔purple), leaving the 11 originals untouched. The result is a continuous spectral
ribbon along the out-of-Africa arc — hue carries the sequence, and the map's borders + labels carry the
neighbour distinction (per-pair contrast is deliberately not maximised).

Each region has a **base** (its map colour) plus **light**/**dark** ramp ends.

> **Colour lives only at the region level (2026-07).** A tradition has **no colour of its own** — it takes its
> **region's** colour. There is no per-tradition colour and no within-region gradient keyed to a tradition
> (superseding the earlier "gradient within area" idea in `tradition-architecture-unified.md` §3). The
> `light`/`dark` ramp ends are region-level UI shades (hover, point-on-fill legibility), not tradition
> identities.

**Two swaps break the strict arc for legibility.** The arc's tail (purples→magentas) piled four
similar hues into the New World, where they read as one blur. So two American regions trade colours
with Old-World neighbours whose own clusters were also too tight: **Native North America ↔ Caucasus &
Iran** (green ⇄ dark-purple) and **Lowland South America ↔ Mainland Southeast Asia** (teal ⇄ magenta).
The Americas now carry purple (Circumpolar) · green (N. America) · orchid (Meso & Andes) · teal
(Lowland S. Am.); the swap also loosens the Caucasus/Inner-Asia greens and the South/SE/East-Asia teals.
Because the two hemispheres never share map space, the borrowed hues collide with nothing.

**A third rotation lifts the East-Asian / Pacific cluster,** which had piled blue (East Asia),
dark-blue (Austronesia) and indigo (Papua) into one quadrant. A 3-cycle across East Asia, Austronesia
and West Asia: **East Asia takes orange** (from Near East & North Africa) so it pops among the
surrounding greens/blues/purples; East Asia's medium blue then passes on to **Inner Asia**, and **Near
East & North Africa takes Austronesia's dark-blue**, distinct against its red/yellow/purple
Mediterranean neighbours. This trades away the warm Mediterranean orange, but the East-Asian legibility
is worth it. A final trade — **Austronesia ↔ Inner Asia** (blue ⇄ green) — gives Austronesia the Prism
green, clear across the Sahul seam, and Inner Asia carries the blue among the greens and purples of the
steppe.

**Papua & Aboriginal Australia leaves the arc for a warm ochre** (`#A9773F`). At the blue→purple tail it
was near-indistinguishable from the Near East's dark-blue, and the two are hard to tell apart even far
apart on the map. Moved into the warm gap between the reds/oranges and the greens, it now separates
cleanly from every neighbour (Austronesian green around it, the dark-blue Near East) — and ochre is apt
for the Aboriginal "red centre". This is the one region placed purely for contrast rather than arc
position.

| # | region | base | light | dark | source |
|---|---|---|---|---|---|
| 1 | Sub-Saharan Africa | `#CC503E` | `#D79389` | `#953223` | Prism red |
| 2 | Near East & North Africa | `#2A4895` | `#5473C2` | `#162857` | insert blue↔purple (↔ Austronesia via E. Asia) |
| 3 | Europe | `#EDAD08` | `#EDC55F` | `#9B7208` | Prism gold |
| 4 | Caucasus & Iran | `#6F4070` | `#9F67A0` | `#3C223D` | Prism dark-purple (↔ N. America) |
| 5 | Inner Asia | `#1D6996` | `#3F97CB` | `#0E3A54` | Prism blue (↔ Austronesia) |
| 6 | South Asia | `#38A6A5` | `#70C5C4` | `#216B6A` | Prism teal |
| 7 | Mainland Southeast Asia | `#94346E` | `#BD6299` | `#591D41` | Prism magenta (↔ Lowland S. Am.) |
| 8 | East Asia | `#E17C05` | `#EDA550` | `#8D5007` | Prism orange (↔ Near East) |
| 9 | Austronesia | `#0F8554` | `#26C583` | `#075534` | Prism green (↔ Inner Asia) |
| 10 | Papua & Aboriginal Australia | `#A9773F` | `#C9A578` | `#6E4C24` | warm ochre (off the arc — see note) |
| 11 | Circumpolar North | `#5F4690` | `#8C78B5` | `#3A2A5A` | Prism purple |
| 12 | Native North America | `#73AF48` | `#A2C688` | `#4D772E` | Prism yellow-green (↔ Caucasus) |
| 13 | Mesoamerica & the Andes | `#994E95` | `#B984B7` | `#643162` | Prism orchid |
| 14 | Lowland South America | `#2A8A9F` | `#59B3C7` | `#175361` | insert teal↔blue (↔ Mainland SE Asia) |
