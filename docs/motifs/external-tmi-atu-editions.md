# Digitized editions of the TMI and ATU indexes

A survey of the most popular, complete, and respected digital versions of the
**Thompson Motif-Index (TMI)** and the **Aarne-Thompson-Uther (ATU)** tale-type
index, across languages — with format, edition basis, license, and a note on
each one's suitability as a source for this project.

Compiled 2026-07. Companion to `motif-index-data-sources.md` (what we actually
use) and `tmi-mellmann-migration.md` (a proposed TMI source change).

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
  source, built from the ruthenia text.
- **Mellmann** is the best *tabular* form (our analysis in
  `tmi-mellmann-migration.md`): a strict superset of the Trilogy TMI in codes
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
provenance is unverified (see `tmi-mellmann-migration.md` §2 on Trilogy being
an independent digitization).

**Bottom line (ATU):** authority = **Uther 2004/2024** (print, copyrighted);
best open text corpora = **MFTD** (multilingual) and **Ashliman**; best open
*type data* = tidy CSVs like **trilogy `atu_df`** — there is no clean,
complete, freely licensed structured ATU to migrate to.

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

## 4. Relevance to this project

- **TMI**: we use **trilogy**; **Mellmann** is the proposed upgrade
  (`tmi-mellmann-migration.md`). **ruthenia** and **MOMFER/`fbkarsdorp/tmi`**
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
