---
title: "Corpus-sourcing atlas: where to obtain full-text world mythology, and under what licence"
description: "A tradition-by-tradition reference on where the primary texts of ~40 mythological traditions can actually be obtained at scale, in machine-readable form, with EASY/MODERATE/HARD verdicts and licences."
url: /research/corpus-sourcing
tier: B
---

# Corpus-sourcing atlas: where the texts actually are

Comparative mythology at scale runs on a prosaic prerequisite: you have to get the texts.
Not a bibliography, not a reading list — the **primary texts** (myth, epic, scripture,
ritual, chronicle) for each documented tradition, at scale, in machine-readable form, and
under a licence that lets you use them. This page is the reference we wished existed when we
started: for roughly forty textually-documented traditions, *where do I get corpus X, in
what format, and what does the licence permit?*

Each tradition carries a headline verdict — **EASY**, **MODERATE**, or **HARD** — defined
in the [ranking table](#obtainability-ranking) below. The verdict is about *machine-obtainability
under a usable licence*, not about the richness of the mythology.

## The one fact that drives almost every HARD verdict

A single structural asymmetry runs through the whole survey:

> **The original-language critical editions and transliterations are increasingly open, but
> the readable modern English or European translations are usually still in copyright.**

For **dead-language** traditions the open asset is a transliteration or the original script;
the readable translation is the copyrighted part. For **oral** traditions the only asset is a
translation, and it is often locked — either in copyright or surviving only as an un-OCR'd
public-domain scan. Budget accordingly: TEI/JSON ingestion for the EASY tier, OCR pipelines
for the ethnographic and hagiographic tier, and licensing or commissioned translation for the
copyright-blocked tier.

**How to read the per-tradition entries.** Each records: source(s); contents and scale;
language(s) and translations; format; licence/access; and machine-obtainability (bulk
download / API / scrape-only / not obtainable).

---

## 1. Classical Mediterranean

### Greek — EASY
- **Perseus Digital Library / `canonical-greekLit`** — TEI XML source of record. Homer,
  Hesiod, the tragedians, Apollodorus, Pausanias, the Hymns, with facing public-domain
  translations. **CC-BY-SA 4.0**; bulk-cloneable git repo. (`github.com/PerseusDL/canonical-greekLit`)
- **First1KGreek / Open Greek and Latin** — aims at one edition of every Greek work from
  Homer to 250 CE not already in Perseus; ~1,000+ works, TEI XML, **CC-BY-SA 4.0**, bulk git
  clone.
- **Scaife Viewer** — the modern reading interface over these repos (CTS API), not a separate
  corpus.
- **Theoi Project** — the best *thematically organized* mythology site, but the compilation is
  © Aaron Atsma with no open licence and no bulk export → **scrape-only; use as an index and
  source the texts from Perseus.**
- **TLG (Thesaurus Linguae Graecae)** — the most complete Greek corpus (Homer→1453), but
  subscription-paywalled with redistribution forbidden → **not obtainable for corpus-building.**
- **Verdict:** Greek myth's core is fully open and git-cloneable in TEI, original + PD English.
  The gold-standard case.

### Roman / Latin — EASY
- **Perseus / `canonical-latinLit`** — Ovid (*Metamorphoses*, *Fasti*), Virgil, Hyginus, etc.,
  TEI XML, **CC-BY-SA 4.0**, bulk git.
- **The Latin Library** — large plain-text PD collection; convenient but not critical editions
  and with no explicit licence (effectively PD source texts). Cleaned mirror at
  `cltk/lat_text_latin_library`.
- **PHI Latin Texts (Packard)** — nearly all literary Latin to AD 200; free to read but no bulk
  download and no reuse licence → **scrape-only.**
- **Verdict:** Original-language Latin myth (Ovid etc.) is fully open TEI; readable translations
  vary (Perseus carries PD ones).

---

## 2. Ancient Near East

### Ancient Egyptian — MODERATE
- **Thesaurus Linguae Aegyptiae (TLA)** — the largest lemmatized Egyptian corpus
  (hieroglyphic/hieratic/Demotic transliteration + German/English): Pyramid Texts, Coffin
  Texts, Book of the Dead, literary and religious texts. Web + API. Licence is **mixed**: small
  extracts free; **full sub-corpora released progressively under free licences**, with datasets
  on **Hugging Face under CC-BY-SA 4.0** and backend code + data on GitHub. → **Partially
  bulk-obtainable now (HF datasets), growing.**
- **Obstacle:** the transliteration/translation is the deliverable; a full free-licensed dump is
  still being rolled out version by version. Older PD English (Budge) gives a readable but dated
  layer via sacred-texts.

### Mesopotamian — Sumerian & Akkadian — EASY (original) / MODERATE (translations)
- **ETCSL (Oxford)** — ~400 Sumerian literary works (Gilgamesh cycle, Inanna, Enki, etc.):
  Sumerian transliteration + English prose, TEI XML. **CC-BY-NC-SA 3.0.** Frozen but fully
  downloadable → **bulk download.**
- **ORACC** — actively maintained cuneiform corpora (SAAo, RINAP, literary projects). **Open
  data as JSON** (ATF transliteration, lemmatization, English) with per-project zips; licensing
  **CC0 / CC-BY-SA** depending on project → **bulk download + documented JSON.**
- **SEAL (Sources of Early Akkadian Literature)** — ~900+ early Akkadian/bilingual compositions;
  open-access, but per-record/scrape rather than a single dump.
- **Verdict:** Sumerian/Akkadian *original + scholarly English* is one of the best-served ancient
  traditions for open machine-readable data (ETCSL + ORACC).

### Hittite / Anatolian — MODERATE
- **Hethitologie-Portal Mainz (HPM)** — critical editions, catalogues, bibliography. Portal
  content **CC-BY-SA 4.0**; the **TLHdig XML dataset released on Zenodo** → bulk-obtainable
  transliterations. Translations mostly German.
- **Obstacle:** transliteration-centric; English myth translations (Hoffner's *Hittite Myths*)
  are in copyright.

### Ugaritic / Canaanite — HARD
- Core myths (Baal Cycle, Kirta, Aqhat) survive as the **KTU corpus**; the standard edition is
  **copyrighted (De Gruyter)** with no open TEI corpus. Transliterations circulate in scattered
  PDFs; KTU on the Internet Archive is scan-only.
- **Obstacle:** the authoritative transliteration and every modern translation are in copyright;
  building requires assembling from older PD editions or licensing.

---

## 3. Northern & Western Europe

### Norse — EASY
- **Icelandic Saga Database (sagadb.org)** — all extant Íslendingasögur in modernized Icelandic
  plus PD English/other translations where they exist; EPUB/PDF/HTML/plain text; **stated public
  domain** → bulk download.
- **heimskringla.no** — large Old Norse archive (Eddas, sagas, skaldic); free to read but
  scrape-oriented, effectively PD source texts.
- **Poetic & Prose Edda** — PD translations (Bellows, Thorpe, Brodeur) on sacred-texts,
  Wikisource, Gutenberg; Old Norse originals on Wikisource/heimskringla → bulk via
  Gutenberg/Wikisource.
- **Verdict:** Original Old Norse is open; readable modern English (Larrington, Faulkes) is in
  copyright, but solid PD translations exist.

### Celtic — MODERATE
- **CELT (Corpus of Electronic Texts, UCC Cork)** — 1,600+ documents / 18M+ words of Irish +
  Hiberno-Latin + English, TEI XML + HTML: *Táin*, the mythological cycle, *Lebor Gabála*. Free,
  **but per-text copyright varies** (some reusable, some restricted) → **mixed-licence
  scrape/download; check each header.**
- **Mabinogion** — Lady Charlotte Guest's PD translation; Welsh originals partly on Wikisource →
  bulk via Gutenberg/Wikisource.

### Finnish / Baltic / Slavic — MODERATE
- **Kalevala** — Crawford (1888) and Kirby (1907) English translations are **PD on Project
  Gutenberg**; Finnish original also on Gutenberg/Wikisource → clean bulk.
- **Slavic / Baltic** — no single canonical myth corpus (paganism poorly attested textually).
  Byliny, the *Primary Chronicle*, Baltic folklore survive as scattered PD translations →
  scrape/assemble, translation-only.

---

## 4. South Asia

### Vedic / Hindu Sanskrit — EASY (original) / MODERATE (translations)
- **GRETIL (Göttingen)** — the largest machine-readable Sanskrit/Indic register: Vedas, epics
  (*Mahābhārata*, *Rāmāyaṇa*), Purāṇas, and much more. Plain text (multiple encodings),
  converting toward TEI; cumulative ZIP downloads via DARIAH-DE. Licence is **heterogeneous /
  per-text** (no blanket licence) but freely downloadable → **bulk download, check each header.**
- **SARIT** — TEI-XML śāstric + literary texts; **all texts under a Creative Commons licence**,
  downloadable as XML/EPUB/PDF → clean bulk.
- **Digital Corpus of Sanskrit (DCS)** — lemmatized, POS-tagged, NLP-oriented → bulk.
- **Muktabodha** — large plain-text library incl. manuscript transcriptions; tantra-heavy →
  mostly scrape.
- **sacred-texts.com** — PD English (Griffith, Ganguli, Müller's SBE) → bulk.
- **Verdict:** Sanskrit *originals* are extremely well-served and openly downloadable
  (GRETIL/SARIT/DCS). Modern scholarly translations are in copyright, but comprehensive PD
  English exists.

### Buddhist — EASY (Chinese/Pali) / MODERATE (Tibetan translations)
- **CBETA** — Chinese Buddhist canon (Taishō 1–55, 85 + Zokuzōkyō 1–90), TEI P5 XML. Taishō
  1–55 **Creative Commons, non-profit**; XML on GitHub (`cbeta-org/xml-p5`) → bulk download.
- **SAT Daizōkyō (U. Tokyo)** — full Taishō online, some features login-gated; overlaps CBETA →
  use CBETA for bulk.
- **SuttaCentral / bilara-data** — Pāli Tipiṭaka (Mahāsaṅgīti root text) plus modern
  translations, **all CC0**, segment-aligned JSON on GitHub → clean bulk, best-in-class licence.
- **Tipitaka.org (VRI)** — Chaṭṭha Saṅgāyana Pāli in many scripts; scrape-oriented.
- **Tibetan Kangyur/Tengyur:** **84000** — English Kangyur translations (~25%+ done), but text
  is **CC-BY-NC-ND** (NoDerivatives blocks re-segmentation); metadata/glossary CC-BY 4.0; API by
  written agreement only → **readable but ND-locked.** **BDRC** — vast scanned + some etext
  Tibetan, images + OCR, API/partnerships.
- **Verdict:** Pāli (SuttaCentral, CC0) and Chinese (CBETA, CC) are ideal. Tibetan *translations*
  are the weak point — 84000 is free-to-read but ND-locked.

### Jain — HARD
- **JAINpedia** — Śvetāmbara Āgama manuscript images, themes, e-library; **manuscript-image and
  curated content, not a clean text corpus.** Āgama texts (Ardhamāgadhī Prakrit) exist as
  scattered editions; some transliterations at GRETIL and jainelibrary.org (free-to-read, no open
  licence); PD English (Jacobi in SBE) on sacred-texts.
- **Obstacle:** no unified machine-readable Āgama corpus; digitization is manuscript-image-centric.

---

## 5. Iran & the Zoroastrian world

### Zoroastrian / Iranian — MODERATE
- **Avesta.org** — complete extant Avesta + many Middle Persian (Pahlavi) scriptures, in
  transliteration + PD English (Darmesteter, Mills, West). HTML; effectively PD content but
  scrape-oriented (no bulk dump / explicit licence).
- **TITUS (Frankfurt)** — scholarly Avestan/Old Iranian database; free to consult, no open
  licence, not bulk-downloadable → scrape.
- **Avestan Digital Archive (ADA)** — ~200 manuscript images (not text).
- **Shahnameh** — Firdawsī: Persian on Wikisource/Ganjoor; PD English (Warner & Warner,
  Atkinson) on Gutenberg/sacred-texts → bulk via Gutenberg/Ganjoor.
- **Verdict:** Original + PD translation obtainable by scraping Avesta.org/TITUS; no packaged
  open corpus.

---

## 6. Jewish & Christian

### Jewish — EASY
- **Sefaria** — Tanakh, Mishnah, Talmud, Midrash, halakha, kabbalah with Hebrew/Aramaic +
  English. **Full data dump (~26 GB, ~85k files, JSON + TXT) on Google Cloud Storage, no auth**;
  public REST API. Licences per-text (PD, CC0, CC-BY, some CC-BY-NC), nearly all reusable →
  **best-in-class: bulk download AND API.**
- **Verdict:** the model example — machine-readable, documented, mostly openly licensed, both
  bulk and API.

### Christian — EASY (Bible) / MODERATE (apocrypha) / HARD (hagiography)
- **Bible** — enormous open supply: original languages (SBLGNT, open Hebrew MT via
  Sefaria/STEP; Vulgate on Perseus/Latin sources) and PD English (KJV, ASV, Douay) everywhere
  (Gutenberg, Sefaria, ebible.org) → clean bulk. Modern translations (NRSV/NIV) are copyright.
- **Apocrypha / Pseudepigrapha** — **Online Critical Pseudepigrapha (OCP)**: free-access critical
  editions (mostly original-language); check reuse terms. PD English (Charles's 1913 *APOT*) on
  sacred-texts/archive.org.
- **Hagiography — Acta Sanctorum** — the Bollandist Lives of the Saints. The digital database is
  **ProQuest, subscription-paywalled → not obtainable**; the original 68-volume Latin print is PD
  and **scanned on Internet Archive (image PDF, needs OCR).**
- **Obstacle (hagiography):** the searchable full text is proprietary; the free version is
  un-OCR'd Latin page-scans.

---

## 7. Islamic

### Islamic — EASY (Quran) / MODERATE (Hadith)
- **Tanzil** — verified Uthmani/simple Quran text in XML/plain UTF-8; verbatim redistribution
  permitted with attribution (**no modification of text**) → bulk download.
- **Quranic Arabic Corpus** — morphological/syntactic annotation on Tanzil text; morphology
  under GNU licence, email-gated download.
- **Translations** — PD English (Yusuf Ali, Pickthall, Rodwell) widely available.
- **Hadith — Sunnah.com** — the major English hadith site (Bukhari, Muslim, the Nine Books,
  Arabic + English). **API exists but key-gated; offline dump "not available yet"; no explicit
  open-data licence** → effectively scrape or gated API. Community mirrors exist
  (`AhmedBaset/hadith-json`, MIT re-hosts).
- **Verdict:** Quran is trivially obtainable; hadith's friction is licence/dump availability.

---

## 8. East Asia (China, Japan, Korea)

### Chinese — MODERATE
- **Chinese Text Project (ctext.org)** — the largest pre-modern Chinese corpus: *Shanhaijing*,
  *Shujing*, *Chuci*, Daoist & Confucian classics, dynastic texts. Read free; **API/whole-text
  download restricted to academic keys**; Linked-Open-Data/RDF under **CC-BY-NC-SA 3.0**. Python
  wrapper (`ctext`, MIT) → **gated API + partial LOD; not a single open bulk dump.**
- **Daozang (Taoist canon)** — no single open full-text corpus. **Kanseki Repository (Kanripo)**
  hosts much classical Chinese incl. Daoist texts as git-backed text → Kanripo git for texts.
- **Shanhaijing** — original on ctext/Wikisource; older partial English translations PD (Birrell
  is copyright).
- **Verdict:** Originals broadly obtainable (ctext gated-API, Kanripo git, Wikisource); friction
  is licensing and the absence of a clean bulk dump.

### Japanese — MODERATE
- **Kojiki / Nihon Shoki** — Chamberlain's *Kojiki* (1882) and Aston's *Nihongi* (1896) are
  **PD** (sacred-texts, Gutenberg, archive.org) → bulk.
- **Japanese Text Initiative (U. Virginia)** — classical Japanese in original + translation,
  HTML/some TEI; scrape-oriented.
- **Original classical Japanese** also via J-TEXTS and **Aozora Bunko** (PD, bulk-downloadable)
  for later material.
- **Verdict:** Foundational myth texts (Kojiki/Nihongi) obtainable in PD English + originals; no
  single packaged corpus.

### Korean — HARD
- **Samguk Yusa** (Iryeon) — the myth-bearing source (Dangun, Three Kingdoms legends). Written in
  **Classical Chinese (hanmun)**; original available via Korean digital classics portals
  (db.itkc.or.kr / krpia — free-to-read, scrape). **Every full English translation (Ha & Mintz
  1972; recent annotated) is in copyright → HARD.**
- **Obstacle:** no PD English; the original is hanmun requiring specialist handling.

---

## 9. Caucasus, Africa, and the wider textual world

### Armenian / Georgian — MODERATE/HARD
- **Armenian** — Moses of Khorene's *History* and epic material; partial PD English + originals
  on **TITUS** and Wikisource; scholarly translations copyright → scrape/assemble.
- **Georgian** — *Knight in the Panther's Skin* (Rustaveli) PD translations on archive.org;
  myth/folklore sparse → assemble.

### Ethiopian — MODERATE
- **Kebra Nagast** — Budge's 1922 English is **PD**, full text on sacred-texts + archive.org;
  Gəʿəz original in scholarly (copyright) editions. *Book of Enoch* (Ethiopic) via Charles PD →
  bulk via sacred-texts.

### Yoruba (Ifá) — HARD
- Ifá corpus (odù) — **no authoritative open full-text corpus**; material scattered across
  ethnographies (Bascom, Abimbola — copyright), with some PD colonial-era collections on
  archive.org. Oral/performance tradition → assemble, mostly copyright-locked.

### Mesoamerican — MODERATE/HARD
- **Maya — Popol Vuh:** original K'iche' + Spanish transcription openly available (World Digital
  Library / OMNIKA facsimile); PD English (Goetz–Morley, 1950) borderline; recent translations
  (Christenson, Tedlock) copyright → original obtainable, readable modern English mostly copyright.
- **Chilam Balam** — Yucatec Maya colonial books; Roys's *Chumayel* (1933) older (archive.org),
  status varies → assemble.
- **Aztec/Nahua — Florentine Codex:** **Getty Digital Florentine Codex** — full Nahuatl + Spanish
  transcriptions, English + Spanish translations, images. Landmark resource; **check Getty reuse
  terms; no single bulk text dump advertised.**
- **Cantares Mexicanos** — Nahuatl source via **UNAM under CC-BY-NC-ND 4.0** (ND blocks
  derivatives); Bierhorst's English is copyright.
- **Obstacle:** originals increasingly digitized, but ND licensing and copyrighted modern
  translations limit reuse.

### Andean — HARD
- **Huarochirí Manuscript** — the great Quechua myth text; original Quechua + Spanish in scholarly
  editions; **standard English (Salomon & Urioste 1991) is copyright** → assemble/partial.
- Colonial chronicles (Guamán Poma) — the **Guaman Poma Website (Royal Library, Copenhagen)**
  offers full facsimile + transcription, free.

### Polynesian — MODERATE
- PD ethnographic translations abundant on **sacred-texts.com Pacific section** (Grey, Fornander,
  Malo, Beckwith) + archive.org. Translation-only, dated, but bulk-downloadable.

---

## 10. The oral / ethnographic world — HARD

Sub-Saharan Africa, Native North America, Amazonia, Siberia, Aboriginal Australia, Melanesia:
there is **no native "canon."** The texts exist only as recorded/translated performances scattered
across ethnographies. Where to find them:

- **Bureau of American Ethnology (BAE) Annual Reports & Bulletins** — the single richest PD trove
  for Native North America: Mooney's *Myths of the Cherokee*, Boas's *Tsimshian Mythology*,
  Stevenson's *Zuñi*. **All PD (US government pre-1929)**, scanned on Internet Archive /
  Smithsonian / Biodiversity Heritage Library → **bulk-downloadable but image-PDF needing OCR**
  (some have OCR/djvu.txt layers).
- **sacred-texts.com regional sections** — Africa, Native America, Australia, Pacific: curated PD
  ethnographic translations already as HTML text → bulk via download package.
- **Internet Archive ethnographies** — vast PD anthropology (Frazer, Rattray, Callaway, Radin,
  Curtin); mixed OCR quality.
- **Folklore journals** — *Journal of American Folklore*, *Folk-Lore* — older volumes PD.
- **Siberia/Central Asia** — Radloff, Chadwick collections PD; modern epic recordings (Manas etc.)
  mostly copyright.
- **Aboriginal Australia / Melanesia** — Spencer & Gillen, Strehlow, Malinowski — much is
  copyright and/or **culturally restricted** (AIATSIS and communities place access controls;
  not free-to-redistribute even when digitized).

**Reality:** translation-only, dated, scattered across thousands of PDFs, requiring **OCR + heavy
curation**, and some carrying ethical/access restrictions independent of copyright.

---

## The big aggregators

| Aggregator | Holds | Licence | Obtainability |
|---|---|---|---|
| **sacred-texts.com** | Broad, dated PD translations across *every* tradition | PD content; site "package" freely copyable | **Bulk download** + scrape |
| **Project Gutenberg** | PD translations (Kalevala, Eddas, Quran, Kojiki, Mahabharata) | PD (US) | **Bulk** (per-book + mirrors) |
| **Internet Archive** | Scanned ethnographies, BAE reports, old critical editions | PD (varies); some in-copyright lending | **Bulk** (PD items); many need OCR |
| **Wikisource** | PD source texts + translations, lightly TEI-ish | CC-BY-SA / PD | **Bulk** (dumps + API) |
| **HathiTrust** | Massive scanned corpus | Mostly in-copyright, gated; PD subset downloadable | PD subset only; else **restricted** |
| **Perseus / Scaife** | Greek/Latin TEI + PD translations | CC-BY-SA | **Bulk git** |
| **GRETIL** | Indic-language texts (originals) | Per-text/mixed, freely downloadable | **Bulk ZIP** (check headers) |
| **ctext.org** | Pre-modern Chinese | Read free; API gated; RDF CC-BY-NC-SA | **Gated API / partial** |
| **Sefaria** | Jewish canon | PD/CC0/CC-BY/CC-BY-NC | **Bulk dump + API** |
| **SuttaCentral** | Pāli + translations | **CC0** | **Bulk git** |
| **CBETA** | Chinese Buddhist canon | CC (non-profit) | **Bulk git (XML)** |

---

## Obtainability ranking

The consolidated verdict per tradition, with the best open source, format, licence, and how to
get it.

| Tradition | Verdict | Best open source | Format | Licence | How to get |
|---|---|---|---|---|---|
| Greek | **EASY** | Perseus + First1KGreek | TEI XML | CC-BY-SA 4.0 | git clone |
| Latin/Roman | **EASY** | Perseus canonical-latinLit | TEI XML | CC-BY-SA 4.0 | git clone |
| Jewish | **EASY** | Sefaria-Export | JSON/TXT | PD/CC0/CC-BY(-NC) | GCS dump + API |
| Buddhist – Pāli | **EASY** | SuttaCentral bilara-data | JSON | CC0 | git clone |
| Buddhist – Chinese | **EASY** | CBETA xml-p5 | TEI P5 XML | CC (non-profit) | git clone |
| Christian – Bible | **EASY** | SBLGNT/Sefaria/ebible/Gutenberg | XML/USFM/TXT | PD/CC-BY | bulk |
| Islamic – Quran | **EASY** | Tanzil | XML/TXT | free w/ attribution | bulk download |
| Sumerian/Akkadian | **EASY** | ETCSL + ORACC | TEI XML / JSON | CC-BY-NC-SA / CC0 | bulk download |
| Hindu/Sanskrit (orig.) | **EASY→MOD** | GRETIL / SARIT / DCS | TXT / TEI | mixed / CC | bulk ZIP (check headers) |
| Norse | **EASY→MOD** | sagadb.org + Gutenberg/Wikisource | TXT/EPUB/XML | PD | bulk |
| Finnish (Kalevala) | **EASY** | Project Gutenberg | TXT | PD | bulk |
| Ancient Egyptian | **MODERATE** | TLA (HF datasets) | JSON/TSV | CC-BY-SA (rolling) | HF bulk (partial) |
| Hittite | **MODERATE** | HPM / TLHdig | XML | CC-BY-SA 4.0 | Zenodo bulk |
| Celtic | **MODERATE** | CELT | TEI XML | per-text mixed | download (check each) |
| Zoroastrian | **MODERATE** | Avesta.org / TITUS | HTML | PD content / no licence | scrape |
| Chinese | **MODERATE** | ctext.org / Kanripo | HTML/RDF/git | gated / CC-BY-NC-SA | gated API / git |
| Japanese | **MODERATE** | sacred-texts + JTI/Aozora | HTML/TXT | PD | bulk |
| Islamic – Hadith | **MODERATE** | Sunnah.com (+ mirrors) | JSON/HTML | gated / unclear | gated API / scrape |
| Christian – Pseudepigrapha | **MODERATE** | OCP + Charles (PD) | HTML/TXT | free / PD | scrape/assemble |
| Polynesian | **MODERATE** | sacred-texts Pacific | HTML | PD | bulk |
| Ethiopian (Kebra Nagast) | **MODERATE** | sacred-texts (Budge) | HTML | PD | bulk |
| Mesoamerican (Nahua/Maya) | **MOD→HARD** | Getty Florentine Codex; UNAM Cantares | HTML/images | ND-restricted / CC-BY-NC-ND | web / partial |
| Buddhist – Tibetan | **HARD** | 84000 | HTML/PDF | CC-BY-NC-**ND** | read-only (ND blocks reuse) |
| Jain | **HARD** | JAINpedia + GRETIL scraps | images/TXT | mixed/none | assemble |
| Ugaritic | **HARD** | KTU (no open corpus) | print/scan | copyright | OCR/license |
| Korean (Samguk Yusa) | **HARD** | hanmun originals only | text | translations copyright | assemble original |
| Andean (Huarochirí) | **HARD** | scholarly eds. | text | copyright | assemble |
| Christian – Hagiography | **HARD** | Acta Sanctorum (ProQuest) | DB / image scan | paywalled / PD-scan | subscription or OCR |
| Yoruba (Ifá) | **HARD** | ethnographies | scans | copyright/PD mix | OCR/assemble |
| Oral world (Africa, N. America, Amazonia, Siberia, Australia, Melanesia) | **HARD** | BAE reports, sacred-texts, IA | HTML/image-PDF | PD (much) but scattered | bulk PD but needs OCR/curation; some culturally restricted |

---

## Build-ready today vs. needs work

**Clean, openly-licensed, machine-readable right now (drop-in):** Greek, Latin, Jewish (Sefaria),
Pāli Buddhist (SuttaCentral CC0), Chinese Buddhist (CBETA), Sumerian/Akkadian (ETCSL + ORACC),
Quran (Tanzil), Kalevala, and the PD-translation layer of Norse. Sanskrit originals via SARIT
(clean CC) and GRETIL (bulk, header-check).

**Available but needs scraping / licence-checking / mixed formats:** Chinese classics (ctext
gated API + Kanripo), Celtic (CELT per-text), Zoroastrian (scrape Avesta/TITUS), Japanese
(assemble sacred-texts + JTI/Aozora), Hadith (gated API/mirrors), Egyptian (HF datasets, rolling),
Hittite (Zenodo), Pseudepigrapha (OCP + PD Charles), Polynesian/Ethiopian (sacred-texts PD).

**Needs OCR:** Acta Sanctorum (PD Latin page-scans), the entire BAE/ethnographic oral-world
corpus (PD but image-PDF), Ugaritic and older ANE editions, many Mesoamerican/Andean colonial
sources.

**Needs licensing or fresh translation (copyright-blocked):** Tibetan Kangyur translations (84000
ND), Korean Samguk Yusa, Andean Huarochirí, Yoruba Ifá, modern Maya/Nahua translations, Ugaritic
KTU, and every tradition's *modern scholarly English* (Larrington, Faulkner, Christenson, Tedlock,
Hoffner, Bierhorst, Salomon). For these you either license, use dated PD translations, or commission
translation.

## The single biggest obstacle per HARD case

- **Tibetan Buddhist:** 84000's translations are free-to-read but **CC-BY-NC-ND** — NoDerivatives
  forbids the segmentation/reformatting a corpus requires. (Metadata is CC-BY; the text is not
  usable as data.)
- **Jain:** **no unified machine-readable Āgama corpus exists** — digitization is
  manuscript-image-centric.
- **Ugaritic/Canaanite:** the **authoritative transliteration (KTU) and all modern translations
  are in copyright**; no open TEI corpus.
- **Korean (Samguk Yusa):** **every English translation is in copyright**; only the
  Classical-Chinese original is free.
- **Andean (Huarochirí):** the **standard English (Salomon & Urioste) is in copyright**; original
  Quechua only in scholarly editions.
- **Christian hagiography (Acta Sanctorum):** the **searchable full text is a ProQuest paywall**;
  the free version is un-OCR'd Latin page-scans.
- **Yoruba (Ifá):** an **oral corpus never systematically transcribed into an open text edition**;
  key collections (Bascom, Abimbola) are copyright.
- **Mesoamerican:** originals are digitized but **ND licensing (Getty/UNAM) and copyrighted modern
  translations** block reuse.
- **Oral world at large:** the material was **never systematically digitized as text** — it
  survives as thousands of PD but un-OCR'd ethnography pages, and some is **culturally
  access-restricted** independent of copyright.

**The pattern to design around:** for *dead-language* traditions the open asset is the
**original-language transliteration/text**; the readable translation is usually copyright. For
*oral* traditions the only asset is a **translation**, and it is usually either copyright or an
un-OCR'd PD scan.

---

## Read on

- [Field survey: computational folkloristics](computational-folkloristics.md) — the methods and
  literature this corpus feeds.
- [Field landscape](landscape.md) — the projects and tools mapped against each other.
- [How the great encyclopedias carve the world](encyclopedias.md) — the reference-work counterpart
  to this atlas, and the literate/oral bias it shares.
- [How it works](../how-it-works.md) — the Mythoscope pipeline from corpus to embeddings to motifs.
- [The 14 regions](../regions.md) — the regional scheme these traditions map onto.
