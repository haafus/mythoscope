# The `region` classification — canonical specification

The single top-level classification of mythological and religious traditions for mythoscope. This is
the definitive record: evaluation criteria, the reasoning trail, the compromises and decisions, the
exact final list, and — for each region — a description (what it contains and why it is distinguished)
and the traditions that belong to it.

Field name: **`region`** (14 values). Two-level model: **`region` → `tradition`** (a region groups
many traditions; a tradition is a single mythology such as Greek or Norse). `region` supersedes the
retired `major_tradition` and the Berezkin `area` as the one primary axis. (Alternative field name if
`area` is kept alongside: `sphere`.)

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

## 4. Ordering — the out-of-Africa arc

Ordered as a human-dispersal arc: cradle → exit corridor → the whole contiguous Old World → the one
deliberate seam → the Americas, ending at the terminal tip of settlement. Every Old-World transition
is geographically contiguous; the single seam is `Papua & Aboriginal Australia → Circumpolar North`.

---

## 5. The 14 regions

### 1. Sub-Saharan Africa
**Description.** The mythologies of Africa south of the Sahara — the world's densest concentration of
distinct oral traditions, spanning several unrelated language phyla. Distinguished as one region
because Berezkin does not subdivide it and both candidate halves (West/Central vs East/Southern) are
text-thin; encyclopedias treat "Black Africa" as one. Predominantly oral; the open textual assets are
the Yoruba Ifá corpus and Ethiopian Ge'ez (boundary — Semitic/Christian).
**Traditions.** Yoruba · Igbo · Akan/Ashanti · Fon (Dahomey) · Dogon · Bambara · Serer · Kongo ·
Yombe · Zulu · Xhosa · Shona · Kikuyu · Baganda · Luba · Fang · Dinka · Nuer · Maasai · Azande · San
(Bushman) · Khoekhoe · Mbuti · (Ethiopian/Amhara — boundary with Near East).

### 2. Near East & North Africa
**Description.** The Ancient Near East plus North Africa and the Abrahamic homelands — the earliest
literate mythologies (cuneiform, hieroglyphic) and the source region of the three Abrahamic religions.
Distinguished as the Bronze-Age/antiquity core of the Old World, anchored by written text. Includes
Anatolia (Hittite) and the Maghreb; "Near East" chosen over "Middle East" for its ancient material.
**Traditions.** Sumerian · Akkadian · Babylonian · Assyrian · Egyptian · Hittite · Hurrian ·
Ugaritic/Canaanite · Phoenician · Elamite · pre-Islamic Arabian · Jewish · Christian · Islamic ·
Berber (Amazigh).

### 3. Europe
**Description.** The mythologies of Europe — predominantly Indo-European (with Uralic Finno-Ugric),
sharing deep Proto-Indo-European roots. One region (not split) because by text it is lighter than the
single Near East region and internally more uniform than one-region Sub-Saharan Africa. The
Classical Mediterranean vs Northern/Eastern division is a **sub-rubric**.
**Traditions.** Greek · Roman · Etruscan · Celtic (Irish, Welsh, Gaulish, Breton) · Norse ·
Anglo-Saxon · Continental Germanic · Slavic (Russian, Polish, South Slavic) · Baltic (Lithuanian,
Latvian, Prussian) · Finnish · Estonian · Sami · Hungarian · Mordvin/Mari · Basque.

### 4. Caucasus & Iran
**Description.** The Iranian/Persianate world plus the Caucasus — bound by Iranian cultural and
linguistic threads (Zoroastrian, Scythian-Alan, Persianate). The Caucasus does not stand alone (a
thin, internally diverse shatter zone) but its autochthonous Nart-epic peoples and its Christian
literate peoples (Armenian, Georgian) attach here, following the Haussig "Caucasian and Iranian"
pairing and the Iranian–Alan core of the Nart sagas.
**Traditions.** Persian/Zoroastrian · Scythian · Sogdian · Ossetian (Nart) · Armenian · Georgian ·
Circassian (Nart) · Chechen/Vainakh (Nart) · Dagestani peoples · (Kurdish · Azeri).

### 5. Inner Asia
**Description.** The Turco-Mongol nomadic steppe — the pastoralist, shamanic, Tengrist interior of
Asia, with its own great oral epics. "Inner Asia" (not "Central Asia") because Iran/the Persianate
oasis is in #4; this region is specifically the nomadic steppe belt. Tibet is a boundary case (Bon /
Tibeto-Mongolian Vajrayana) placed here for its Inner-Asian Buddhist ties.
**Traditions.** Turkic/Tengrist · Kyrgyz (Manas) · Kazakh · Uyghur · Yakut/Sakha · Mongol (Geser,
Tengri) · Buryat · Kalmyk (Jangar) · Tuvan · Altai · Tibetan (Bon; boundary) · Manchu (boundary).

### 6. South Asia
**Description.** The Indian subcontinent — the single largest textual tradition on Earth (the Vedic
corpus, Sanskrit epics, the Puranas, the Buddhist and Jain canons). Its own region on the strength of
both volume (crit 4) and civilizational distinctness (crit 2); India is the source of the Indosphere,
distinct from its Indianized periphery.
**Traditions.** Vedic · Hindu · Buddhist · Jain · Dravidian (Tamil, Telugu, Kannada, Malayalam) ·
Munda/Santal · Gond · Bhil · Sinhalese · Newar/Nepali · Sikh · Kashmiri.

### 7. Mainland Southeast Asia
**Description.** The Indianized mainland — Indochina and the Tibeto-Burman/Tai/Austroasiatic hill
peoples whose classical mythology is Hindu-Buddhist (the Ramayana traditions). On the Indic side of
the Indosphere/Sinosphere split, distinct from South Asia proper (periphery, not source) and from
Sinic East Asia. Vietnam is here (Austroasiatic + geography outweigh its Sinic literary overlay).
**Traditions.** Burmese · Mon · Thai/Tai · Lao · Shan · Khmer · Vietnamese (Viet/Muong) · Cham
(boundary — Austronesian) · Hmong-Mien · Karen · Tibeto-Burman highlanders.

### 8. East Asia
**Description.** The Sinosphere — China, Korea, Japan — sharing the Chinese classical, Taoist,
Confucian and Mahayana-Buddhist textual world. The clean CJK core (Vietnam, though Sinicized, is left
in mainland SE Asia). Ainu is a boundary case (indigenous Japan, Circumpolar affinity).
**Traditions.** Chinese (Han; Taoist, Confucian, Chinese folk, Chinese Buddhist) · Korean · Japanese
(Shinto) · Ryukyuan · Ainu (boundary) · southern-China ethnic minorities (Yi; boundary with SE Asia).

### 9. Austronesia
**Description.** The Austronesian cultural area — one language family and one Neolithic maritime
expansion, from the Taiwan homeland through island Southeast Asia to the Pacific and Madagascar. Its
own region to keep this cohesive descent-based area intact (crit 2), anchored by the Formosan
peoples. Island SE Asia (Nusantara) sits here, not in mainland SE Asia or a vague "Oceania"; the
Indianized Javanese/Balinese are the literate exception within it.
**Traditions.** Taiwan Formosan (Atayal, Bunun, Paiwan, Ami, Tsou) · Javanese · Balinese · Sundanese ·
Batak · Dayak · Toraja · Filipino (Tagalog, Ifugao) · Malay · Polynesian (Maori, Hawaiian, Tahitian,
Samoan, Tongan, Rapa Nui) · Micronesian · Fijian (coastal Melanesian) · Malagasy.

### 10. Papua & Aboriginal Australia
**Description.** The non-Austronesian deep-Pacific — the Pleistocene **Sahul** population: Papuan /
highland New Guinea peoples and Aboriginal Australians (the Dreaming). Distinguished from Austronesia
by descent and antiquity (Sahul was settled ~50 ky ago, long before the Neolithic Austronesian
arrival). "Aboriginal" marks the Indigenous tradition against the modern nation.
**Traditions.** Aboriginal Australian (Arrernte, Yolngu, Warlpiri, Pitjantjatjara, and many others) ·
Papuan highland groups (Enga, Huli, …) · non-Austronesian Melanesian.

### 11. Circumpolar North
**Description.** The continuous circumpolar Arctic/boreal belt spanning both continents across the
Bering Strait — Arctic and Subarctic hunter-shaman cultures that geography joins but the continental
boundary would tear. Includes NE Siberian palaeo-Asiatics, the boreal taiga peoples, Beringia, and
Arctic/Subarctic North America. The Bering bridge into the New World.
**Traditions.** Chukchi · Koryak · Yukaghir · Nivkh · Itelmen · Evenki (Tungus) · Even · Khanty ·
Mansi · Nenets · Ket · Inuit/Eskimo (Yupik, Inupiat, Kalaallit) · Aleut · Na-Dene/Athabaskan (Dene) ·
Northern Cree · (Ainu, Sami — boundary affinities).

### 12. Native North America
**Description.** Indigenous North America outside the Arctic — the temperate culture areas: Eastern
Woodlands, Plains, Plateau, California, the Southwest, and the Northwest Coast (boundary with
Circumpolar). "Native" distinguishes the Indigenous traditions from the modern nation.
**Traditions.** Iroquois (Haudenosaunee) · Algonquian (Ojibwe, Cree-south, Abenaki) · Lakota/Sioux ·
Cheyenne · Pawnee · Blackfoot · Nez Perce · Salish · Pomo · Miwok · Yokuts · Navajo (Diné) · Hopi ·
Zuni · Pueblo · Apache · Tlingit · Haida · Kwakwaka'wakw · Tsimshian.

### 13. Mesoamerica & the Andes
**Description.** The high civilizations of the Americas — the two literate/state-level New-World myth
complexes, with codices and colonial chronicles (Popol Vuh, the Florentine Codex, the Huarochirí
Manuscript). Grouped together as the Americas' textual heartland, distinct from the surrounding
tribal lowlands.
**Traditions.** Aztec/Nahua · Maya · Mixtec · Zapotec · Olmec · Toltec · Tarascan (Purépecha) ·
Huichol · Inca/Quechua · Aymara · Moche · Chibcha/Muisca · Nazca.

### 14. Lowland South America
**Description.** The tropical and temperate lowlands of South America — Amazonia, the Guianas, the
Gran Chaco, and the Southern Cone: the densest concentration of small-scale Amerindian oral
traditions, the terminal end of the human expansion. Distinct from the Andean highlands (#13).
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
