# Digitized editions of the TMI and ATU indexes

A survey of the most popular, complete, and respected digital versions of the
**Thompson Motif-Index (TMI)** and the **Aarne-Thompson-Uther (ATU)** tale-type
index, across languages — with format, edition basis, license, and a note on
each one's suitability as a source for this project.

Compiled 2026-07. Companion to `motif-index-data-sources.md` (what we actually
use) and `proposals/tmi-mellmann-migration.md` (a proposed TMI source change).

## How to read the "suitability" column

- **source-grade** — clean, complete, machine-readable; usable as a pipeline input.
- **reference** — authoritative for verification/enrichment, but not a bulk data feed.
- **corpus** — links tale *texts* to types/motifs, not the index itself.
- **archival** — page scans / PDF; ground truth for spot-checking, not parsing.

---

## 1. Thompson Motif-Index (TMI)

All the serious digital TMI editions ultimately trace to the **revised and
enlarged edition (Thompson 1955–58, 6 vols)**. They differ in *form*, not
content.

| Edition | Form | Basis | Lang | License | Suitability |
|---|---|---|---|---|---|
| **ruthenia.ru/folklore/thompson** | full HTML text, per chapter (`a.htm`–`z.htm`) | revised 1955–58 | English (RU-hosted) | free, no explicit license | reference / de-facto canonical full text |
| **MOMFER** (Meertens/KNAW) | NLP search engine + parsed data | ← ruthenia text | English | code Apache-2.0 | reference; most respected scholarly tool |
| **Mellmann `TMI_as_CSV`** | tabular CSV | revised | English | CC-BY-4.0 | **source-grade** (cleanest data form) |
| **j-hagedorn/trilogy** | tidy CSV (TMI + ATU) | revised | English | CC-BY-SA-4.0 | **source-grade** (our current TMI) |
| **archive.org `Thompson2016MotifIndex`** | 6-vol scan PDF | print original | English | public scan | archival (verification) |
| **HathiTrust** (Indiana Univ. Studies) | scans, partial full-view | 1st / revised | English | mixed access | archival |
| **folklore-and-fairytales.wikidot.com** | browsable wiki list | — | English | community | low (incomplete, hobbyist) |

Links:
- ruthenia: <https://www.ruthenia.ru/folklore/thompson/a.htm>
- MOMFER tool: <https://momfer.meertens.knaw.nl/> — parser/data: <https://github.com/fbkarsdorp/tmi>
- MOMFER paper: Karsdorp, van der Meulen, et al., "MOMFER: A Search Engine of
  Thompson's Motif-Index of Folk Literature", *Folklore* 126:1 (2015),
  <https://doi.org/10.1080/0015587X.2015.1006954>
- Mellmann: <https://github.com/KatjaMellmann/TMI_as_CSV> (OSF DOI `10.17605/OSF.IO/XEB67`)
- Trilogy: <https://github.com/j-hagedorn/trilogy>
- archive.org: <https://archive.org/details/Thompson2016MotifIndex>

### Notes on the leading three

- **ruthenia** is the reference full text everyone else parsed. It reproduces
  the revised edition verbatim, including Thompson's `†` dagger convention and
  the printed division/section headings. No structure, just faithful HTML.
- **MOMFER** is the most cited scholarly digital TMI: it added semantic search
  (query "mythical animals", "mortality") over the parsed index. Its parsed
  data (`fbkarsdorp/tmi`, Apache-2.0) is a credible alternative machine-readable
  source, built from the ruthenia text. **Live** at
  <https://momfer.meertens.knaw.nl> (page title "TMI-search"). Note: ruthenia's
  Thompson index links an older mirror `http://www.momfer.ml/`, which is now
  dead (a reclaimed Freenom `.ml` domain) — use the Meertens URL.
- **Mellmann** is the best *tabular* form (our analysis in
  `proposals/tmi-mellmann-migration.md`): a strict superset of the Trilogy TMI in codes
  and citations, with printed division/section headings and `1st ed.`
  provenance. Recommended future source.

**Bottom line (TMI):** popular + complete + respected = **ruthenia** (canonical
text) → **MOMFER** (scholarly tool + open parse) → **Mellmann** (cleanest data).

---

## 2. Aarne-Thompson-Uther (ATU)

**Caveat up front:** the current ATU standard — **Uther 2004** — is under
copyright (Suomalainen Tiedeakatemia / *FF Communications*). There is **no
complete, freely licensed, structured ATU database** comparable to the TMI
CSVs. Open ATU resources are therefore either tale-text corpora keyed to types,
plain number lists, or (like ours) tidy extractions of uncertain provenance.

| Edition | Form | Basis | Lang | License | Suitability |
|---|---|---|---|---|---|
| **Uther, *Types of International Folktales*, FFC 284–286 (2004)** — rev. & suppl. ed. **2024** | print (scans circulate) | ATU | English (+ German scholarship) | © copyright | reference (the authority) |
| **Multilingual Folk Tale Database — mftd.org** | XML tale corpus, type-tagged | ATU | **multilingual** | site terms | corpus (open, type-linked) |
| **D.L. Ashliman, *Folktexts*** | texts grouped by ATU/AT | ATU/AT | English | educational | corpus (we already use it) |
| **Meertens Nederlandse Volksverhalenbank — verhalenbank.nl** | national DB, ATU-typed | ATU | Dutch | academic terms | corpus / reference |
| **The Gold Scales — oaks.nvg.org/uther.html** | flat number/title list | ATU | English | free | reference (quick lookup) |
| **j-hagedorn/trilogy `atu_df`** | tidy CSV | ATU | English | CC-BY-SA-4.0 | **source-grade** (our current ATU) |
| **Enzyklopädie des Märchens Online** (de Gruyter) | scholarly encyclopedia | — | German | paywalled | reference (infrastructure behind Uther) |

Links:
- Uther 2024 introductions (open PDF): <https://www.folklorefellows.fi/wp-content/uploads/FFC-284-286-Uther-2024-Introductions.pdf>
- FFC volumes: <https://www.folklorefellows.fi/ffc-editors/recent-volumes/ffc-280-289/ffc-284-286/>
- MFTD: <https://www.mftd.org>
- Ashliman: <https://sites.pitt.edu/~dash/folktexts.html>
- Volksverhalenbank: <https://www.verhalenbank.nl>
- Gold Scales list: <http://oaks.nvg.org/uther.html>
- Wikipedia overview: <https://en.wikipedia.org/wiki/Aarne%E2%80%93Thompson%E2%80%93Uther_Index>

### Lineage (for provenance judgments)

Aarne (1910, German) → Thompson (1928, 1961 English, "AT") → Uther (2004,
"ATU", rev. 2024). A code prefixed `AT` is pre-Uther; `ATU` is the 2004
reorganization. Any open "ATU data" should be checked for which layer it
encodes — our Trilogy `atu_df` is ATU-numbered but its exact transcription
provenance is unverified (see `proposals/tmi-mellmann-migration.md` §2 on Trilogy being
an independent digitization).

Editions: 2004 first ed. → **2011 reprint** → substantially revised & supplemented
**2024** edition. The 2011 three-volume text circulates as PDFs on academia.edu
and Scribd (grey-access — *not* confirmed publisher-authorized open access; the
"publisher made it freely available" claim traces only to a Reddit thread), and
those scans are what many user-made ATU spreadsheets are keyed to. See:
<https://www.folklorefellows.fi/the-types-of-international-folktales-reprinted/>.

**Bottom line (ATU):** authority = **Uther 2004/2011/2024** (print, copyrighted);
best open text corpora = **MFTD** (multilingual) and **Ashliman**; best open
*type data* = tidy CSVs like **trilogy `atu_df`** — there is no clean,
complete, freely licensed structured ATU to migrate to. The most complete
digital ATU in practice is the **2011 PDF** (via grey channels), from which
projects extract number/title/description spreadsheets.

---

## 3. National / other-language catalogues (same ATU frame)

- **СУС — *Сравнительный указатель сюжетов. Восточнославянская сказка*** (Barag,
  Berezovsky, Kabashnikov, Novikov, 1979) — Russian/Ukrainian/Belarusian.
  Digitized with the STARLING database. A bibliographic rarity, the key to East
  Slavic material.
  - <https://www.ruthenia.ru/folklore/sus/index.htm>
  - PDF: <https://biblio.imli.ru/images/abook/folklor/Sravnitelnyj_ukazatel_syuzhetov._Vostochnoslavyanskaya_skazka._1979..pdf>
- **Berezkin & Duvakin**, *Thematic classification and areal distribution of
  folklore-mythological motifs* — Russian, with an English mirror. Our third
  index (2564 motifs, 958 societies).
  - Russian: <http://www.ruthenia.ru/folklore/berezkin/> · <http://areasofmyths.com>
  - English mirror: <https://www.mythologydatabase.com/>
- **Grimm KHM ↔ ATU** concordances, Finnish/German national type-indexes (FFC
  series) — partially digitized, fragmentary; consult per-need, not as feeds.

---

## 4. The wider digital ecosystem (corpora, Linked Data, computational folkloristics)

Sourced from a shared research conversation (retrieved 2026-07 by parsing the
page HTML) and then **independently re-verified via web search** where marked
`[verified]`; items marked `[unverified]` come only from that secondary
conversation and should be checked before being relied on. The central thesis
is worth recording:

> The active center of modern folkloristics is no longer the TMI/ATU
> **catalogues** themselves, but the **national archives** where hundreds of
> thousands of texts are already tagged with ATU/TMI codes. Computational work
> is built on those tagged corpora, not on the bare indexes.

### National folklore archives (ATU/TMI-tagged text corpora)

The most valuable *data* is the tagged corpus, not the index. Leading archives:

- **Finland — SKS / Finna** `[unverified]` — historic home of the AT system;
  hundreds of thousands of records, many with AT/ATU numbers, used to prepare
  new ATU editions; catalogue/bibliography via the Finna portal.
- **Norway — Samla** `[unverified]` — `samla.no/viewer/typekatalog/eventyr/`;
  the most open modern system: national tale catalogue, every text typed,
  AT/ATU-searchable, open web UI, explicitly a development of the AT system.
- **Estonia — Estonian Folklore Archives** `[unverified]` — one of Europe's
  largest; digital collections, much of it type-tagged; active AI auto-indexing.
- **Ireland — National Folklore Collection (UCD)** `[unverified]` — likely the
  largest English-language folk-tradition archive; search built around ATU +
  local indexes.

### National / regional type- and motif-indexes (same AT/ATU frame)

Almost every major tradition built its own index, usually keyed
`local number → ATU → Thompson motifs`. Named in the source `[unverified]`:

- Ørnulf **Hodne**, *The Types of the Norwegian Folktale*
- Reidar Th. **Christiansen**, *The Migratory Legends* (the "ML" index)
- Hassan **El-Shamy**, Arab / Middle-Eastern type & motif indexes
- Japanese, Irish, Spanish, and Baltic national catalogues

(Complements §3's СУС for East Slavic.)

### Semantic / Linked Open Data

- **DFKI — Linked Data for Folktales** `[verified]` — Declerck et al., "Towards a
  Linked Data Access to Folktales classified by Thompson's Motifs and
  Aarne-Thompson-Uther's Types", DH2017. Ports TMI (1977) + Uther 2004 into
  interrelated **OWL/RDF(S)** ontologies: the ID hierarchy becomes an OWL
  subclass tree, and terminal nodes are both a `Motif` instance and an instance
  of their pre-terminal class (encoding "motifs are the leaves"). Aimed at LOD
  access to type/motif-annotated tales.
  - PDF: <https://www.dfki.de/fileadmin/user_upload/import/9028_Dh2017_LOD_TMI-ATU_final.pdf>
  - <https://dh-abstracts.library.virginia.edu/works/4064>
- **BARTOC** `[unverified]` — registers the TMI as a controlled vocabulary with
  its own identifier, linking it into library/DH knowledge infrastructure.

### Computational folkloristics

- **GLOS — Geographic Lens on Stories** `[verified]` — <https://kgeographer.org/glos_jan2025.html>.
  Recent project whose **first phase digitized TMI (Thompson 1966) + ATU
  (Uther 2011)**: OCR → clean → parse into a normalized relational DB, then
  vector embeddings; current work uses LLMs to induce a schema for comparing
  creation myths across cultures. Directly parallel to this project's approach
  (embeddings over motif/type text); worth watching closely.
  Creation-myth schema: <https://kgeographer.org/glos_creation_schema.html>
- **Mark Finlayson (FIU) research program** `[unverified]` — no published full
  TMI database; instead a body of work on automatic motif detection/indexing,
  annotated motif corpora, and LLM motif search. A 2026 study reportedly uses
  the El-Shamy *1001 Nights* index (≈2670 annotated occurrences, 200 motifs,
  58 450 sentences) rather than Thompson — i.e. Finlayson now automates motif
  tagging rather than re-digitizing Thompson.

### Other access points

- **StoryNotes** `[verified]` — <https://psychemedia.github.io/storynotes/> — a
  Pandas-friendly interface over the Mellmann CSV (search by code/word, browse
  levels). Convenient exploration layer, not a separate dataset.
- **Indiana University / InteLex** `[unverified]` — a commercial digital Motif
  Index (subscription; mirrors the print edition), behind a paywall.
- **everything.explained.today / HandWiki** `[unverified]` — encyclopedic
  mirrors of the Motif-Index overview; low value beyond quick reading.

### Strategic note for this project

The source's most useful observation: **almost no existing project treats motifs
as a graph** — they use lists, trees, or (DFKI) an RDF ontology, but nobody
builds the full network `ATU type ⇄ constituent motifs ⇄ attested texts`. That
`type ↔ motif ↔ text` graph, cross-index and corpus-linked, is precisely
Mythoscope's niche; GLOS and DFKI are the nearest neighbours to watch.

Suggested by the source as an unfilled gap worth a dedicated survey: a **map of
all national catalogues** (Russian, Chinese, Japanese, Indian, Arab, Balkan,
Finno-Ugric …) — which are digitized, have APIs, ship XML/CSV, or expose open
ATU/TMI-linked corpora. No such consolidated overview currently exists.

## 5. Relevance to this project

- **TMI**: we use **trilogy**; **Mellmann** is the proposed upgrade
  (`proposals/tmi-mellmann-migration.md`). **ruthenia** and **MOMFER/`fbkarsdorp/tmi`**
  are the authoritative texts to verify against; **archive.org** scans are the
  final ground truth for disputed codes.
- **ATU**: we use **trilogy `atu_df`** + **Ashliman** for text coverage. No
  clean open structured ATU exists to switch to; **Uther 2004/2024** is the
  reference for manual verification only.
- **Berezkin**: we use areasofmyths.com; the **mythologydatabase.com** English
  mirror is a cross-check.

### Quick-reference: canonical verification targets

| need | go to |
|---|---|
| exact TMI motif wording / dagger / heading | ruthenia → archive.org scan |
| TMI semantic search across motifs | MOMFER |
| clean TMI tabular data | Mellmann CSV |
| exact ATU type wording | Uther 2004/2024 (print/scan) |
| tale texts for a type, multilingual | MFTD |
| tale texts for a type, English | Ashliman |
| East Slavic type equivalents | СУС |
| TMI/ATU as RDF/OWL linked data | DFKI ontology (DH2017) |
| embeddings/LLM over folktale indexes (prior art) | GLOS |
| large ATU/TMI-tagged text corpus | national archives (Samla, SKS/Finna, …) |

## 6. Validated data inventory (2026-07 audit)

Four parallel agents live-checked every resource on 2026-07-06 (curl + WebFetch
+ WebSearch; headless browsing unavailable in this environment). This section is
the **authoritative validated layer** over the survey above — where it differs,
trust this. Verdicts weigh usefulness for mythoscope's specific goals (fuller
TMI/ATU data, a TMI↔ATU crosswalk, semantic parallels, and a geography-linked
motif/type atlas).

### 6.1 Master ranking

**Tier 1 — open, reusable, actionable now**

| Source | Payload | Format / access | Volume | License |
|---|---|---|---|---|
| **Mellmann `TMI_as_CSV` v1.2** | full TMI + printed div/section headings + `1st ed.` provenance + sort key | CSV (raw GitHub / OSF) | **46,302 rows**, 10 cols; 19,839 with 1st-ed | **CC-BY-4.0** |
| **Wikidata P2540 (ATU)** | tale-item ⇄ ATU type ⇄ Wikipedia/authority IDs | **SPARQL**, JSON, RDF; dereferenceable URIs | **1,720 items / 1,294 distinct ATU types** | **CC0** |
| **`fbkarsdorp/tmi` JSON** | TMI motifs with **`locations[]` (geo-parsed)** + **`lemmas[]` (WordNet)** | JSON (raw GitHub) | **46,248 motifs** | **Apache-2.0** |
| **trilogy AFT / "Bag-of-Tales"** | **ATU-labeled full-text tales** (Ashliman-derived) | CSV / Zenodo `10.5281/zenodo.6575263` | **1,518 tales / 182 ATU types** | CC-BY-SA-4.0 |
| **Dúchas / NFC (Ireland)** | ATU-typed items, GeoNames coords, dates, **full text** | REST API `duchas.ie/api/v0.6/` (key) + `/en/aath` | ~15k+ typed items (e.g. AT0300 = 338) | CC-BY-**NC**-4.0 |

**Tier 2 — high value, access friction (contact / scrape / watch)**

| Source | Why | Blocker |
|---|---|---|
| **Meertens Verhalenbank / ISEBEL** | richest ATU + place + full-text, multilingual (NL/DA/DE/IS), **100k+ tales** | no open API (GraphQL 500/404); scrape server-rendered `search.isebel.eu/dataset/…` pages or negotiate a Meertens data agreement; verhalenbank.nl currently throwing an Omeka error |
| **GLOS (Karl Grossner)** | near-identical architecture: parsed TMI (46,234) + ATU (2,232 types) + embeddings + QGIS geo | repo `github.com/kgeographer/glos` public but **no LICENSE** (= all rights reserved); email `karl@kgeographer.org` for reuse + collaboration |
| **Finlayson Arabian Nights corpus** | only motif-level annotated corpus (El-Shamy-keyed): 2,670 expressions / 200 motifs / 58,450 sentences | **embargoed** — code+data promised at `dataverse.fiu.edu` "upon acceptance" (arXiv:2603.19283); watch/email `markaf@fiu.edu` |
| **DFKI TMI-ATU ontology (Declerck DH2017)** | *exactly* the TMI↔ATU crosswalk: 14,937 classes / 2,802 ATU / `linkToTMI` properties, 15.4 MB OWL | **never released** — placeholder namespace, no SPARQL/GitHub/Zenodo; only path is emailing Thierry Declerck (DFKI) |

**Tier 3 — reference / enrichment (not a bulk corpus)**

| Source | Use | Note |
|---|---|---|
| **Finna API (SKS, Finland)** | discovery/enrichment; metadata **CC0**, open JSON API `api.finna.fi/v1` | 19.7M records but ATU-as-subject sparse (~483); not a typed corpus |
| **Ashliman folktexts** | ATU-organized variant texts, scrapeable | **© no open license** — link/reference, don't redistribute |
| **BARTOC node 1711** | stable authority URIs for TMI + Wikidata QID `Q19062048` | record JSON/RDF (PDDL-1.0); no motif content |
| **ruthenia / MOMFER / StoryNotes** | verification full-text / search UI / join-recipe | MOMFER has **no API** (SPA; data = `fbkarsdorp/tmi`); StoryNotes = Mellmann+MOMFER→SQLite FTS blueprint |

**Tier 4 — low / offline / print-only**

- **MFTD** — currently **offline** ("security issues"); static TEI-XML still served but ATU fields mostly empty.
- **Samla (Norway)** — OAI-PMH (`samla.no/viewer/oai`, mets/marcxml/dc) but AT (Hodne)↔text links are **not** machine-exposed; much closed-access.
- **Estonia folklore.ee** — static HTML type list with **counts only** (last updated 2004); DBs UI-only, restricted.
- **InteLex Motif-Index** (Indiana) — paywalled, no export.
- **Print-only type-indexes** — Hodne, Christiansen ML, El-Shamy (Arab / 1001 Nights), Ting (Chinese), Ikeda (Japanese), Thompson-Balys (Indian), Balys (Lithuanian). Scans on archive.org for some (OCR effort); no structured data.

### 6.2 Corrections & key discoveries vs §1–4

- **`fbkarsdorp/tmi` carries geo + lemmas** — its JSON has `locations[]`
  (geo-parsed places) and WordNet `lemmas[]` per motif: a ready **geography +
  semantic layer** absent from Mellmann and trilogy (Apache-2.0). Dirty
  diacritics; join on motif code to Mellmann's clean text.
- **Wikidata P2540 is the best *open* ATU** — 1,294 distinct types vs trilogy's
  182, CC0, SPARQL, with text/authority links. Corrects §2's "no clean open
  structured ATU": there is no open *Uther catalogue*, but Wikidata is an open,
  queryable ATU **crosswalk**.
- **DFKI ontology was never published** (only the paper). Do not plan around it.
- **MFTD is offline** and its ATU field was largely empty even when up — demote
  from §2/quick-ref.
- **trilogy already ships an ATU-tagged tale corpus** (AFT / Bag-of-Tales, 1,518
  tales) that we may not be consuming — check `motif-index-data-sources.md`.
- **GLOS is not just prior art** — its repo may hold reusable parsed tables, but
  unlicensed; treat as contact-first.

## 7. Enrichment plan

Phased, cheapest-and-openest first. Each step names payload, license, and the
mythoscope surface it feeds. Respect per-source licenses (esp. Dúchas **NC** and
Ashliman/ISEBEL ©).

### Phase 0 — open data, no outreach (do first)

1. **TMI backbone → Mellmann** (already scoped in `proposals/tmi-mellmann-migration.md`):
   gains printed div/section headings, `1st ed.` provenance, sort key; CC-BY-4.0.
2. **Geo + lemma overlay from `fbkarsdorp/tmi`**: join its JSON on motif code to
   add `locations[]` (feeds the **geography atlas** directly) and `lemmas[]`
   (feeds **semantic parallels**). Keep Mellmann's clean text; take only the
   geo/lemma fields. Apache-2.0.
3. **ATU enrichment from Wikidata P2540** (SPARQL, CC0): pull the 1,294 ATU
   types with labels + Wikipedia + authority IDs; use to (a) widen ATU type
   coverage/labels, (b) add external **type→text** links, (c) mint stable URIs.
4. **Activate trilogy AFT** (1,518 ATU-tagged full-text tales, already in the
   repo we source): a first **text layer per ATU type** at zero new dependency.

### Phase 1 — a real geography-linked corpus

5. **Dúchas API** (Ireland): ATU-typed, GeoNames-coordinate, dated, full-text
   Irish corpus — the first genuine **text ⇄ ATU ⇄ place** layer for the atlas.
   Requires an API key; honor **CC-BY-NC** (non-commercial + attribution).
6. **ISEBEL / Meertens** (100k+ multilingual ATU+place tales): highest-payoff
   corpus. No open API → either respectful scraping of server-rendered
   `search.isebel.eu/dataset/…` pages or a Meertens data-use agreement.

### Phase 2 — outreach & watch (parallel to Phase 1)

7. **Email Thierry Declerck (DFKI)** for the TMI↔ATU `.owl` — if obtained, it is
   a ready-made crosswalk ontology (`linkToTMI`) validating/seeding ours.
8. **Email Karl Grossner (GLOS)** re: data/license + possible collaboration — he
   is building nearly the same system; align rather than duplicate.
9. **Watch `dataverse.fiu.edu`** for the Finlayson Arabian Nights motif corpus
   (the only motif-level annotated training set).

### Phase 3 — reference & authority anchoring

10. **Finna CC0 API** as a discovery/enrichment lookup (not a corpus).
11. **BARTOC + Wikidata URIs** as stable authority anchors for TMI/ATU codes.
12. **Ashliman / ruthenia / MOMFER** as human-facing verification/reference
    links (no redistribution of Ashliman's ©).

### Licensing watch

Mixed licenses compose but constrain: CC0 (Wikidata, Finna metadata) and
CC-BY (Mellmann) are free; Apache-2.0 (fbkarsdorp) is free; **CC-BY-SA-4.0**
(trilogy) obliges share-alike on its portions; **CC-BY-NC-4.0** (Dúchas) blocks
commercial use of that corpus; Ashliman and ISEBEL are ©/unclear (reference,
don't redistribute). Keep attribution per-source; never let one license line
imply terms over the whole set.

## 8. Extractable layers & features

What each dataset can actually add to mythoscope's surfaces (catalog, cross-walk,
semantic parallels, geography atlas, ages/realms/beings graphs). Effort tags:
**S**=small (join/ingest), **M**=medium (parse+model+UI), **L**=large (new subsystem).

### 8.1 From Tier 1 (open — buildable now)

**Mellmann CSV** → `[S–M]`
- **Classification tree** — the printed `division1–3` + `section` headings become
  a navigable hierarchy above motifs (fixes the long-missing heading layer; retires
  our `.0`/`level_N` reconstruction).
- **Edition-provenance filter** — `1st ed.` splits motifs into 1936-original vs
  revised-edition additions → a "growth of the index" toggle/timeline.
- **Cleaner embeddings input** — definition already split from citations → less
  parser noise into BGE-M3.

**`fbkarsdorp/tmi` JSON** → `[S–M]`
- **Motif geography** — `locations[]` (geo-parsed attestation places) plots
  **motifs** on the atlas, not just Berezkin areas → "where is this motif attested."
- **Concept/lemma layer** — WordNet `lemmas[]` enables concept faceting ("all
  motifs about *death*/*ring*/*deception*") and a lexical bridge across TMI↔ATU↔
  Berezkin that corroborates the BGE-M3 semantic parallels (we already found
  lexical and semantic parallels are complementary; lemmas formalize the lexical side).

**Wikidata P2540** → `[S–M]`
- **Example tales per ATU type** — links each type to named works (Grimm, etc.)
  and Wikipedia → an "attested tales / read more" panel on ATU pages.
- **Multilingual type labels** — ATU type names in many languages for free.
- **Authority URIs** — QIDs to anchor ATU codes; groundwork for a linked-data export.

**trilogy AFT (Bag-of-Tales)** → `[S]`
- **Text layer per ATU type** — 1,518 real tale texts attached to types → example
  texts on ATU pages, plus **tale-level embeddings** (similar tales across
  cultures) and a way to validate the ATU→TMI crosswalk against real narratives.

**Composite Tier-1 features** (combining the above):
- **Motif/type geography atlas** = fbkarsdorp `locations[]` + AFT provenance,
  layered onto the existing Berezkin map → the atlas becomes motif- and type-aware.
- **Concept explorer** = lemmas as a cross-index facet spanning all three indexes.
- **"Examples everywhere"** = AFT + Wikidata tales surfaced on every type/motif page.
- **Provenance/time view** = Mellmann `1st ed.` (index growth) as a first temporal axis.

### 8.2 From Tier 2 (if access / license / data are secured)

**Meertens Verhalenbank / ISEBEL** (100k+ ATU+place+full-text, multilingual) → `[L]`
- **Dense spatiotemporal atlas** — 100k tales with place + date → real distribution
  and **diffusion maps** of tale types across NW Europe (heat maps, over time).
- **The `type ⇄ motif ⇄ text` graph** — co-occurrence of motifs/types in real
  texts builds the knowledge graph we noted *nobody* has (mythoscope's niche).
- **Cross-lingual parallels** — same type across NL/DA/DE/IS → translation-invariant
  motif matching and multilingual embeddings.
- **Social/temporal dimension** — narrator + date metadata → who told what, when.

**GLOS** (parsed TMI 46,234 + ATU 2,232 + embeddings + CreationSchema) → `[M]`
- **Fuller ATU** — 2,232 Uther-2011 types vs our 182 (if reuse is licensed).
- **CreationSchema layer** — controlled-vocab structured fields for creation myths
  (primordial state, creation sequence, cosmic structure, dualities), LLM-extracted
  → directly enriches the **ages / realms / beings** graphs and the A-chapter myths.
- **Cross-validation** — their embeddings + tables as an independent check on ours.

**Finlayson Arabian Nights corpus** (2,670 motif spans / 200 motifs) → `[M–L]`
- **Automatic motif tagger** — training data to build a model that tags *our* texts
  (AFT, Dúchas, ISEBEL) with motifs → closes the loop: any tale → its motifs.
- **Sentence-level motif spans** — fine-grained "motif highlighted in text."
- **El-Shamy Arab-world index** — a fourth motif dimension beyond TMI/ATU/Berezkin.

**DFKI TMI-ATU ontology** (14,937 classes, `linkToTMI`, 2,802 ATU) → `[S–M]`
- **Gold-standard crosswalk** — its `linkToTMI`/`linkFromTMIToATU` properties are
  an independent TMI↔ATU mapping to validate/seed ours (we build ours from
  `atu_seq`; this is a second opinion).
- **RDF/OWL export** — publish mythoscope as linked data (SPARQL-queryable),
  reusing its OWL subclass hierarchy for TMI.

**Dúchas** (Tier-1 license, Tier-2 effort: keyed API) → `[M]`
- **Coordinate-grade type atlas** — ATU types on a real GeoNames map with dates →
  the first genuine **text ⇄ ATU ⇄ place ⇄ time** layer (Ireland), a template for ISEBEL.

**Flagship if Tier 2 unlocks:** ISEBEL (scale + geography) + Finlayson (auto-tagging)
+ DFKI (crosswalk) + GLOS (schema) together yield the full
**type ⇄ motif ⇄ text ⇄ place ⇄ time knowledge graph** — the thing the survey
found no existing project builds, and mythoscope's strongest differentiator.

### 8.3 Feature → source → surface map

| Feature | Source(s) | mythoscope surface | Tier / effort |
|---|---|---|---|
| Classification/heading tree | Mellmann | catalog | 1 / S–M |
| Edition + time provenance | Mellmann `1st ed.` (+ Dúchas/ISEBEL dates) | catalog, atlas | 1 / S |
| Motif geography | fbkarsdorp `locations[]` | atlas | 1 / S–M |
| Concept/lemma facet | fbkarsdorp `lemmas[]` | catalog, parallels | 1 / M |
| Example tales per type/motif | AFT + Wikidata (+ Dúchas/ISEBEL) | catalog | 1 / S |
| Multilingual labels + URIs | Wikidata, BARTOC | catalog, LD export | 1 / S |
| Coordinate type atlas | Dúchas → ISEBEL | atlas | 1–2 / M–L |
| Diffusion/heat maps over time | ISEBEL | atlas | 2 / L |
| type⇄motif⇄text graph | ISEBEL + crosswalk + AFT | new graph view | 2 / L |
| Cross-lingual parallels | ISEBEL | parallels | 2 / M |
| Auto motif tagger | Finlayson corpus | pipeline | 2 / M–L |
| Creation-myth schema | GLOS | ages/realms/beings | 2 / M |
| Gold-standard TMI↔ATU crosswalk | DFKI ontology | cross-walk | 2 / S–M |
| Linked-data / SPARQL export | DFKI + Wikidata/BARTOC | interop | 2 / M |

## 9. Open-data roadmap (licenses-permitting, Tier 2 excluded)

Scope: only sources whose license and access are **already clear and open** —
Mellmann (CC-BY-4.0), `fbkarsdorp/tmi` (Apache-2.0), Wikidata P2540 (CC0),
trilogy AFT (CC-BY-SA-4.0), Finna metadata (CC0). Tier-2 corpora (ISEBEL, GLOS,
Finlayson, DFKI) are **out of scope until access/license are secured** — they
re-enter via the §7 outreach track. Dúchas is openly *licensed* but **CC-BY-NC**
(+ keyed API), so it appears here only as a clearly-flagged conditional item.

Ordering principle: **additive, join-on-code overlays first** (low risk, no
source swap, each enriches a core surface independently), then the foundational
Mellmann migration (bigger, riskier, already planned), then polish.

### Priority 1 — quick, additive, low-risk (no migration required)

- **R1 · Motif geography overlay** — join `fbkarsdorp/tmi` `locations[]` on motif
  code → plot **motifs** on the atlas. *Source:* fbkarsdorp (Apache-2.0). *Effort:*
  S–M (join is trivial; normalizing its NER'd, diacritic-damaged place strings to
  our `culture_dict` regions is the real work). *Surface:* geography atlas.
  *Deps:* none. *Value:* HIGH — unique geo data for motifs, our highest-profile
  surface. **Start here.**
- **R2 · Text layer per ATU type (trilogy AFT)** — ingest the AFT / annotated-
  folktales dataset (1,518 ATU-tagged full-text tales) — it ships in the trilogy
  repo we already source but is **not** in `config/motifs.json`. *License:*
  CC-BY-SA-4.0 (already in use). *Effort:* S. *Surface:* catalog (example tales) +
  parallels (tale-level embeddings) + crosswalk validation. *Deps:* none.
  *Value:* HIGH — biggest payoff per unit effort; data is already at hand.
- **R3 · ATU enrichment via Wikidata P2540** — SPARQL-ingest 1,294 ATU types with
  multilingual labels, example works, and QIDs; join on ATU code. *License:* CC0.
  *Effort:* S–M. *Surface:* catalog (labels + example tales) + interop (URIs).
  *Deps:* none. *Value:* MEDIUM-HIGH — widens ATU, adds external text links.

### Priority 2 — foundational (medium effort/risk)

- **R4 · TMI source → Mellmann (+ classification tree + provenance)** — the
  migration already scoped in `proposals/tmi-mellmann-migration.md`: printed `division1–3`/
  `section` headings become a real classification tree; `1st ed.` becomes an
  edition-provenance filter; retires the `.0`/`level_N` repair. *License:* CC-BY-4.0.
  *Effort:* M. *Surface:* catalog. *Deps:* none technically, but R1/R3 join on code
  so they survive the swap — do them first so the migration diff is isolated.
  *Risk:* MEDIUM (crosswalk join drift, embedding re-run — see migration doc §7,13).
  *Value:* HIGH — foundational hierarchy + provenance.
- **R5 · Concept/lemma facet** — expose `fbkarsdorp` `lemmas[]` (WordNet) as a
  cross-index concept facet and a lexical-parallel corroboration signal alongside
  BGE-M3. *License:* Apache-2.0. *Effort:* M. *Surface:* catalog + parallels.
  *Deps:* reuses R1's ingest of the same JSON. *Value:* MEDIUM.

### Priority 3 — polish / conditional

- **R6 · Authority URIs & linked-data groundwork** — attach Wikidata QIDs (R3) +
  BARTOC node 1711 URIs to TMI/ATU codes; lays track for a future RDF export.
  *License:* CC0 / PDDL-1.0. *Effort:* S. *Value:* LOW-MEDIUM (interop, future-proofing).
- **R7 · Finna discovery enrichment** — optional CC0 API lookups. *Effort:* M for
  thin payoff (ATU tagging sparse). *Value:* LOW — defer.
- **R8 · Dúchas coordinate type-atlas (CONDITIONAL)** — ATU-typed, GeoNames-
  coordinate, dated Irish full-text corpus via keyed API. *License:* **CC-BY-NC**
  → only if mythoscope stays non-commercial (or per-use agreement) — decide the
  NC posture before building. *Effort:* M. *Surface:* atlas (first real
  text⇄ATU⇄place⇄time layer). *Value:* HIGH but **gated on the NC decision**;
  treat as the bridge into the Tier-2 geography work.

### Sequencing

R1, R2, R3 are independent and parallelizable — ship them as three small,
additive overlays first (each is a visible win and none touches the TMI source).
Then R4 (Mellmann migration) with R1/R3 already in place so its diff stays
isolated; R5 rides on R1's ingest. R6 is a cheap follow-on to R3. R7 defer; R8
only after an explicit NC/commercial decision.

**Recommended start:** **R2** (zero new dependency, data already in hand) in
parallel with **R1** (highest-visibility atlas win). Both are pure additive
overlays that survive the later Mellmann migration untouched.

## 10. Measured dataset quality & completeness (head-to-head)

All numbers below were **measured** against the live datasets (2026-07): our
built `tmi.json`/`atu.json`, the Trilogy and Mellmann CSVs, the `fbkarsdorp/tmi`
JSON, and Wikidata SPARQL. This is the empirical backing for §2–§6.

### 10.1 TMI motif composition — Trilogy vs fbkarsdorp vs Mellmann

| dataset | rows | distinct codes | dup-codes | extra |
|---|---|---|---|---|
| **Trilogy** | 46,230 | 46,222 | 8 | — |
| **fbkarsdorp** | 46,248 | 46,225 | 23 | +6 parse artifacts |
| **Mellmann** | 46,242 | 46,236 | 6 | +60 first-edition "ghost" rows |

- **Common core: 46,215 codes** shared by all three (the real Thompson motifs —
  headings, `.0` interpolations, leaves). Every difference is at the margins.
- **Trilogy-only: 0.** **fbkarsdorp-only: 6**, all artifacts (`+A800`,
  `W.  W. Traits of character`, …). **Mellmann-only: 10** real (7 leaves + 3
  headings; e.g. `X751`, `C867.2`, `Z356.1`).
- **Richest by real motifs = Mellmann** (46,236): it recovers ~7 dropped motifs
  and splits Thompson's own dup codes into distinct suffixed codes. fbkarsdorp's
  higher *row* count is **noise** — 23 dup codes (only 4 are Thompson's real
  dups; ~19 are identical-row artifacts, e.g. `A12` twice) + 6 junk codes.
- **Duplicate sets differ.** Ours (8) ∩ Mellmann (6) = only 4 (`E755.2.8,
  K561.1.1, S222, Z64`). We handle `B172.2/M202.1/N591` as dups; Mellmann
  disambiguates them into suffixed codes. On the 4 shared dups, our `notes` are
  **equal or fuller** than Mellmann's `bibliographies` (e.g. Z64: 146 vs 22
  bytes) — collapsing/suffixing lost nothing.

### 10.2 Fidelity & non-derivable data — Trilogy vs fbkarsdorp

Both are independent digitizations of the same printed index; fbkarsdorp is the
lower-fidelity one:

| axis | Trilogy | fbkarsdorp |
|---|---|---|
| diacritics | preserved (Müller, Métraux; **10,680** rows non-ASCII) | **all stripped — 0 non-ASCII**; `Müller → "M ller"` |
| `†` daggers | **7,024** | **0** |
| unique fields | recursive `level_N` hierarchy (derivable from codes) | `locations[]` (geo NER, 69%), `lemmas[]` (WordNet, 99%) — both **derivable** from the text |

**Non-derivable loss** (the Mellmann-style test): dropping **fbkarsdorp** loses
essentially nothing (its `locations`/`lemmas` are recomputable, and cleaner from
Trilogy's diacritic-preserving text); dropping **Trilogy** loses the diacritics
(10,680 rows) irrecoverably. So Trilogy is the better **base**; fbkarsdorp's value
is the *pre-computed* geo/lemma overlays, not unique content. (`fb.description` =
our `motif_name` on 44,530 rows; `additional_description` = our `definition`.)

### 10.3 Cultures vs fbkarsdorp locations (same source, different extraction)

- Ours: **34,749** motifs (75%) have `cultures`, **1,799** distinct labels.
- fbkarsdorp: **32,106** (69%) have `locations[]`, **925** tokens.
- **Exact-token overlap: 153** — surfaces differ (ours keeps citation labels
  incl. non-geographic `Jewish`/`Buddhist myth`/`Irish myth`; fbkarsdorp
  NER-normalizes to countries `Ireland`/`Iceland`/`Mexico`).
- **Complementary:** 889 motifs have an fb-location but no our-culture; 3,544 the
  reverse. → use fb `locations` as a geocodable overlay, not a replacement.

### 10.4 ATU examples — Ashliman vs Wikidata P2540

**P2540 fields** (per Wikidata item): ATU number, `instance of` (tale type /
fairy tale / literary work…), title + multilingual label/description, author
(P50), language, genre, country of origin, catalogue codes (P528) & authority IDs
(VIAF/GND), image, Wikipedia sitelinks, Wikisource full text. Full tale *text* is
**not** in Wikidata — only via linked Wikisource/Wikipedia.

| source | what | count | types |
|---|---|---|---|
| **Ashliman `tales`** (used) | full readable text (pitt.edu) | 1,457 | 172 |
| **P2540 → Wikisource** (now used) | full primary text | 385 works / 808 links | 242 (223 mapped) |
| **P2540 → Wikipedia** (used) | encyclopedic summary | — | 265 |
| **P2540 works total** | named work entities | 1,794 | 1,294 |

- Wikisource adds full texts on **143 types Ashliman doesn't cover** (212 texts);
  union of full-text coverage = **315 types**.
- The ~550 individual P2540 *work* items (Grimm tales etc.) are **not** yet
  surfaced as example tales — the untapped part of P2540.

### 10.5 Mellmann `1st ed.` provenance (edition history)

`1st ed.` is a **column on every motif row** (not a separate table), filled on
**19,779 / 46,242 (42%)** — the motifs present in the 1936 first edition (empty =
added in the 1955–58 revision). It holds **codes only**: 18,603 unchanged, **1,166
renumbered** (current ≠ 1936 code, e.g. `A13.1.1` was `A14`), **10 with multiple
codes** (a revised motif that merged 2+ first-edition ones). Plus **60 blank-code
"ghost" rows** documenting first-edition motifs *dropped* in the revision. The
renumber map resolves ATU references citing pre-revision numbers (`A14→A13.1.1`,
`B478→B495.1`) — a follow-on enrichment (not yet applied).
