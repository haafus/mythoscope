# Obtainable Full-Text Corpora for World Mythology — A Sourcing Survey

*Prepared 2026-07-15. Scope: where you can actually obtain the PRIMARY TEXTS (myth, epic, scripture, ritual, chronicle) for each major textually-documented tradition, at scale, in machine-readable form — and under what license.*

**How to read the per-tradition entries.** Each lists: **Source(s)** · **Contents & scale** · **Language(s)/translations** · **Format** · **License/access** · **Machine-obtainability** (bulk download / API / scrape-only / not obtainable). The headline verdict for each is EASY / MODERATE / HARD, defined in the ranking table near the end.

A recurring structural fact drives almost every "HARD" verdict: **the original-language critical editions and transliterations are increasingly open, but the readable modern English/European translations are usually still in copyright.** For dead-language traditions the open asset is a transliteration or the original script; for oral traditions the only asset is a translation, and it is often locked.

---

## 1. Classical Mediterranean

### Greek — EASY
- **Perseus Digital Library / canonical-greekLit** — TEI XML source of record. GitHub: `PerseusDL/canonical-greekLit`. Homer, Hesiod, the tragedians, Apollodorus, Pausanias, Hymns, etc., with facing public-domain translations. **License: CC-BY-SA 4.0.** Bulk-cloneable git repo. https://github.com/PerseusDL/canonical-greekLit
- **First1KGreek / Open Greek and Latin** — aims at one edition of every Greek work from Homer to 250 CE not already in Perseus; ~1,000+ works, TEI XML, **CC-BY-SA 4.0**, bulk git clone. https://github.com/OpenGreekAndLatin/First1KGreek
- **Scaife Viewer** — the modern reading interface over these repos (not a separate corpus); CTS API. https://scaife.perseus.org/
- **Theoi Project** — the best *thematically organized* mythology site (translations + source quotations by deity/theme). Translations are mostly public-domain (old Loeb/Frazer), but the **compilation is © Aaron Atsma; no open license, no bulk export → scrape-only, use as an index, source the texts from Perseus.** https://www.theoi.com/
- **TLG (Thesaurus Linguae Graecae)** — the most complete Greek corpus (Homer→1453), but **subscription/paywalled, no bulk export, terms forbid redistribution → not obtainable for corpus-building.** Use Perseus/First1KGreek instead. http://stephanus.tlg.uci.edu/
- **Scale/obtainability:** Greek myth's core is fully open and git-cloneable in TEI, original + PD English. This is the gold-standard case.

### Roman / Latin — EASY
- **Perseus / canonical-latinLit** — Ovid (*Metamorphoses*, *Fasti*), Virgil, Hyginus, etc., TEI XML, **CC-BY-SA 4.0**, bulk git. https://github.com/PerseusDL/canonical-latinLit
- **The Latin Library** — large plain-text/HTML collection of PD Latin texts; convenient but **not critical editions, no explicit license** (effectively PD source texts). A cleaned mirror exists at `cltk/lat_text_latin_library` (scrapeable). https://www.thelatinlibrary.com/ · https://github.com/cltk/lat_text_latin_library
- **PHI Latin Texts (Packard)** — nearly all literary Latin to AD 200; **free to read/search online but no bulk download, no reuse license → scrape-only.** https://latin.packhum.org/
- **Verdict:** Original-language Latin myth (Ovid etc.) is fully open TEI; readable translations vary (Perseus carries PD ones).

---

## 2. Ancient Near East

### Ancient Egyptian — MODERATE
- **Thesaurus Linguae Aegyptiae (TLA)** — the largest lemmatized Egyptian corpus (hieroglyphic/hieratic/Demotic transliteration + German/English translation): Pyramid Texts, Coffin Texts, Book of the Dead, literary and religious texts. Web + API (`textplus.thesaurus-linguae-aegyptiae.de`). **License is mixed:** small extracts free for research; **full sub-corpora released progressively under free licenses.** Datasets published on **Hugging Face under CC-BY-SA 4.0** (e.g. `tla-Earlier_Egyptian_original-v18`), and backend code + Elasticsearch data on GitHub. → **Partially bulk-obtainable now (HF datasets), growing.** https://thesaurus-linguae-aegyptiae.de/info/licenses · https://huggingface.co/thesaurus-linguae-aegyptiae
- **Obstacle:** transliteration/translation is the deliverable; full free-licensed dump is still being rolled out version by version. Older PD English (Budge Book of the Dead, Faulkner is in copyright) available on sacred-texts for a readable but dated layer.

### Mesopotamian — Sumerian & Akkadian — EASY (original) / MODERATE (translations)
- **ETCSL (Oxford)** — ~400 Sumerian literary works (Gilgamesh cycle, Enûma-adjacent myths, Inanna, Enki, etc.): **Sumerian transliteration + English prose translation**, TEI XML. **License: CC-BY-NC-SA 3.0.** Project is finished/frozen but fully downloadable (site + Oxford Text Archive). → **bulk download.** https://etcsl.orinst.ox.ac.uk/
- **ORACC** — actively maintained cuneiform corpora (SAAo, RINAP, literary projects). **Open data as JSON** (ATF transliteration, lemmatization, English translation) with per-project zips; **licensing CC0 / CC-BY-SA depending on project.** → **bulk download + documented JSON format.** https://oracc.museum.upenn.edu/doc/opendata/json/
- **SEAL (Sources of Early Akkadian Literature)** — ~900+ early Akkadian/bilingual literary compositions, many transliterated, translated, lemmatized; web database. Open-access but **download model is per-record/scrape rather than a single dump.** https://seal.huji.ac.il/
- **Verdict:** Sumerian/Akkadian *original + scholarly English translation* is one of the best-served ancient traditions for open machine-readable data (ETCSL + ORACC).

### Hittite / Anatolian — MODERATE
- **Hethitologie-Portal Mainz (HPM)** — critical editions of Hittite cuneiform texts, catalogues, bibliography. Open-access; **portal content CC-BY-SA 4.0**, and the **TLHdig XML dataset released on Zenodo** → bulk-obtainable transliterations. Translations are mostly German. https://www.hethport.uni-wuerzburg.de/HPM/
- **Obstacle:** transliteration-centric; English myth translations (Hoffner's *Hittite Myths*) are in copyright.

### Ugaritic / Canaanite — HARD
- Core myths (Baal Cycle, Kirta, Aqhat) survive as the **KTU corpus** — the standard edition (*Die keilalphabetischen Texte aus Ugarit*) is **copyrighted (De Gruyter)**; no open TEI corpus. Transliterations circulate in scattered academic PDFs; small digital efforts exist (Digital Semitics Online Library; ETANA tools). No clean bulk-downloadable licensed corpus. https://etana.org/ · KTU on Internet Archive (scan only).
- **Obstacle:** the authoritative transliteration and every modern translation are in copyright; would require assembling from PD older editions or licensing.

---

## 3. Northern & Western Europe

### Norse — EASY
- **Icelandic Saga Database (sagadb.org)** — all extant Íslendingasögur in modernized Icelandic **plus PD English/other translations where they exist**; EPUB/PDF/HTML/plain text; **stated public domain.** → bulk download. https://sagadb.org/downloads
- **heimskringla.no** — large Old Norse text archive (Eddas, sagas, skaldic) in Old Norse and Scandinavian languages; free to read, **scrape-oriented (no bulk dump/explicit open license), effectively PD source texts.** https://heimskringla.no/
- **Poetic & Prose Edda** — PD translations (Bellows, Thorpe, Brodeur) on sacred-texts, Wikisource, Gutenberg; Old Norse originals on Wikisource/heimskringla. → bulk via Gutenberg/Wikisource.
- **Verdict:** Original Old Norse is open; readable modern English (Larrington, Faulkes) is in copyright, but solid PD translations exist.

### Celtic — MODERATE
- **CELT (Corpus of Electronic Texts, UCC Cork)** — 1,600+ documents / 18M+ words of Irish + Hiberno-Latin + English, TEI XML + HTML: *Táin*, mythological cycle, *Lebor Gabála*, etc. Free; **but per-text copyright varies (many texts marked reusable, some restricted); TEI files downloadable → mixed-license scrape/download.** https://celt.ucc.ie/
- **Mabinogion** — Lady Charlotte Guest's PD translation (Wikisource/Gutenberg/sacred-texts); Welsh originals (*Llyfr Coch/Llyfr Gwyn*) partly on Wikisource. → bulk via Gutenberg/Wikisource.
- **Obstacle:** CELT is the corpus but license is text-by-text; check each header before redistributing.

### Finnish / Baltic / Slavic — MODERATE
- **Kalevala** — Crawford (1888) and Kirby (1907) English translations are **PD on Project Gutenberg**; Finnish original also on Gutenberg/Wikisource. → clean bulk. https://www.gutenberg.org/ (search "Kalevala")
- **Slavic / Baltic** — no single canonical myth corpus (paganism poorly attested textually). Byliny, the *Primary Chronicle*, Baltic folklore survive as scattered PD translations on sacred-texts, Gutenberg, Internet Archive. → scrape/assemble, translation-only.

---

## 4. South Asia

### Vedic / Hindu Sanskrit — EASY (original) / MODERATE (translations)
- **GRETIL (Göttingen)** — the largest machine-readable Sanskrit/Indic text register: Vedas, epics (*Mahābhārata*, *Rāmāyaṇa*), Purāṇas, much more. Plain text (multiple encodings), converting toward TEI; **cumulative ZIP downloads via DARIAH-DE.** **License is heterogeneous / per-text (no single blanket license); freely downloadable, generally usable for non-commercial research — must check each file's header.** → bulk download (with license caveat). https://gretil.sub.uni-goettingen.de/gretil.html
- **SARIT** — TEI-XML śāstric + literary texts; **all texts under a Creative Commons license**, downloadable as XML/EPUB/PDF. → clean bulk. https://sarit.indology.info/
- **Digital Corpus of Sanskrit (DCS)** — lemmatized, POS-tagged corpus (Hellwig); downloadable data, oriented to NLP. → bulk. http://www.sanskrit-linguistics.org/dcs/
- **Muktabodha** — large plain-text digital library incl. unpublished-manuscript transcriptions; searchable, tantra-heavy. → mostly scrape. https://muktabodha.org/
- **sacred-texts.com** — PD English translations (Griffith's Rig Veda & Ramayana, Ganguli Mahabharata, Müller SBE). → bulk via sacred-texts download.
- **Verdict:** Sanskrit *originals* are extremely well-served and openly downloadable (GRETIL/SARIT/DCS). Modern scholarly translations are in copyright, but comprehensive PD English exists.

### Buddhist — EASY (Chinese/Pali) / MODERATE (Tibetan translations)
- **CBETA** — Chinese Buddhist canon (Taishō vols. 1–55, 85 + Zokuzōkyō 1–90), TEI P5 XML. **Taishō 1–55 released under Creative Commons; non-profit use.** XML on GitHub (`cbeta-org/xml-p5`). → bulk download. https://github.com/cbeta-org/xml-p5
- **SAT Daizōkyō (U. Tokyo)** — full Taishō (85 vols.) online; searchable; some features gated by login. Overlaps CBETA; **use CBETA for bulk.** https://21dzk.l.u-tokyo.ac.jp/SAT/
- **SuttaCentral / bilara-data** — Pāli Tipiṭaka (Mahāsaṅgīti root text) **plus modern translations, all under CC0**, segment-aligned JSON on GitHub (`suttacentral/bilara-data`). → clean bulk, best-in-class license. https://github.com/suttacentral/bilara-data
- **Tipitaka.org (VRI)** — Chaṭṭha Saṅgāyana Pāli in many scripts; free, scrape-oriented.
- **Tibetan Kangyur/Tengyur:**
  - **84000** — English translations of the Kangyur (~25%+ done). **Translations are CC-BY-NC-ND (no derivatives → cannot be modified/re-segmented); metadata/glossary/TM is CC-BY 4.0; API only by written agreement.** → readable (HTML/PDF/ePub) but **NoDerivatives blocks corpus reuse.** https://84000.co/documents/terms-of-use
  - **BDRC** — vast scanned + some etext Tibetan canon; open-source ethos, images + OCR; API/partnerships. Original-language Tibetan. https://www.bdrc.io/
- **Verdict:** Pāli (SuttaCentral, CC0) and Chinese (CBETA, CC) are ideal. Tibetan *translations* are the weak point — 84000 is free-to-read but ND-locked.

### Jain — HARD
- **JAINpedia** — Śvetāmbara Āgama manuscripts (images), themes, e-library; **manuscript images and curated content, not a clean text corpus; no bulk open text dump.** https://jainpedia.org/
- Āgama texts (Ardhamāgadhī Prakrit) exist as scattered editions; some transliterations at GRETIL and jainelibrary.org (free-to-read, no open license). PD English translations (Jacobi in Sacred Books of the East) on sacred-texts. → assemble from GRETIL + sacred-texts; no single corpus.
- **Obstacle:** no unified machine-readable Āgama corpus; digitization is manuscript-image-centric.

---

## 5. Iran & the Zoroastrian world

### Zoroastrian / Iranian — MODERATE
- **Avesta.org** — complete extant Avesta + many Middle Persian (Pahlavi) scriptures, in transliteration + PD English translations (Darmesteter, Mills, West from Sacred Books of the East). HTML; **free, effectively PD content, scrape-oriented (no bulk dump/explicit license).** https://www.avesta.org/
- **TITUS (Frankfurt)** — scholarly Avestan/Old Iranian text database (transliterated originals); free to consult, **no open license / not bulk-downloadable → scrape.** https://titus.uni-frankfurt.de/
- **Avestan Digital Archive (ADA)** — ~200 manuscript images (not text).
- **Shahnameh** — Firdawsī: Persian text on Wikisource/Ganjoor (ganjoor.net, Persian poetry corpus, open-ish); PD English (Warner & Warner, Atkinson) on Gutenberg/sacred-texts. → bulk via Gutenberg/Ganjoor.
- **Verdict:** Original + PD translation obtainable by scraping Avesta.org/TITUS; no packaged open corpus.

---

## 6. Jewish & Christian

### Jewish — EASY
- **Sefaria** — Tanakh, Mishnah, Talmud, Midrash, halakha, kabbalah with Hebrew/Aramaic + English. **Full data dump (~26 GB, ~85k files, JSON + TXT) on Google Cloud Storage, no auth needed; public REST API.** **Licenses per-text: public domain, CC0, CC-BY, some CC-BY-NC** (nearly all reusable). → best-in-class: bulk download AND API. https://github.com/Sefaria/Sefaria-Export · https://developers.sefaria.org/
- **Verdict:** the model example — machine-readable, documented, mostly openly licensed, both bulk and API.

### Christian — EASY (Bible) / MODERATE (apocrypha) / HARD (hagiography)
- **Bible** — enormous open supply: original languages (SBLGNT, open Hebrew MT via Sefaria/STEP/Unicode; Vulgate on Perseus/Latin sources), and PD English (KJV, ASV, Douay) everywhere (Gutenberg, `Sefaria`, ebible.org, `openbible`). → clean bulk. Note modern translations (NRSV/NIV) are copyright.
- **Apocrypha / Pseudepigrapha** — **Online Critical Pseudepigrapha (OCP)**: free-access critical editions (mostly original-language Greek/etc.). Free but **check reuse terms; oriented to reading.** PD English (Charles's 1913 *APOT*) on sacred-texts/archive.org. https://pseudepigrapha.org/
- **Hagiography — Acta Sanctorum** — the Bollandist Lives of the Saints. **The digital *Acta Sanctorum* database is ProQuest, subscription/paywalled → not obtainable.** Original 68-vol. Latin print is PD and **scanned on Internet Archive (image PDF, needs OCR).** https://archive.org/details/actasanctorum25unse · (paywall) https://about.proquest.com/en/products-services/acta/
- **Obstacle (hagiography):** the searchable full-text version is proprietary; the free version is un-OCR'd Latin page-scans.

---

## 7. Islamic

### Islamic — EASY (Quran) / MODERATE (Hadith)
- **Tanzil** — verified Uthmani/simple Quran text in XML/plain UTF-8; **verbatim redistribution permitted with attribution + link (free-but-restricted: no modification of text).** → bulk download. https://tanzil.net/download/
- **Quranic Arabic Corpus** — morphological/syntactic annotation on Tanzil text; **v0.4 morphology under GNU license**, email-gated download. https://corpus.quran.com/download/
- **Translations** — PD English (Yusuf Ali, Pickthall, Rodwell) widely available (Gutenberg, tanzil, sacred-texts).
- **Hadith — Sunnah.com** — the major English hadith site (Bukhari, Muslim, the Nine Books, Arabic + English). **API exists but key-gated (request via GitHub issue); offline dump "not available yet"; no explicit open-data license → effectively scrape or gated API.** Community mirrors exist (`AhmedBaset/hadith-json`, various MIT-licensed re-hosts). https://github.com/sunnah-com/api
- **Qiṣaṣ al-Anbiyāʾ** ("Tales of the Prophets", al-Kisāʾī/al-Thaʿlabī) — Arabic editions scattered; PD English partial. → assemble.
- **Verdict:** Quran is trivially obtainable; hadith is available but license/dump is the friction point.

---

## 8. East Asia (China, Japan, Korea)

### Chinese — MODERATE
- **Chinese Text Project (ctext.org)** — the largest pre-modern Chinese corpus: *Shanhaijing*, *Shujing*, *Chuci*, Daoist & Confucian classics, dynastic texts. Read free; **API for structured access/whole-text download is restricted to academic API keys; Linked-Open-Data/RDF under CC-BY-NC-SA 3.0.** Python wrapper (`ctext`, MIT) eases access. → **API (gated) + partial LOD; not a single open bulk dump.** https://ctext.org/tools/api
- **Daozang (Taoist canon)** — no single open full-text corpus. **Kanseki Repository (Kanripo, kanripo.org)** hosts much classical Chinese incl. Daoist texts as git-backed text; scholarly Schipper–Verellen *companion* is a reference book, not the texts. → Kanripo git for texts; otherwise scattered. https://www.kanripo.org/
- **Shanhaijing (Classic of Mountains and Seas)** — original on ctext/Wikisource; PD-ish English (Birrell is copyright; older partial translations PD).
- **Verdict:** Originals broadly obtainable (ctext gated-API, Kanripo git, Wikisource); the friction is licensing and the absence of a clean bulk dump.

### Japanese — MODERATE
- **Kojiki / Nihon Shoki** — Chamberlain's *Kojiki* (1882) and Aston's *Nihongi* (1896) English translations are **PD** (sacred-texts, Gutenberg, archive.org). → bulk via sacred-texts/Gutenberg.
- **Japanese Text Initiative (U. Virginia)** — classical Japanese literature in original + translation, HTML/some TEI; free, scrape-oriented. https://jti.lib.virginia.edu/
- **Original classical Japanese** (kanbun/old Japanese) also via J-TEXTS (j-texts.com) and Aozora Bunko (aozora.gr.jp, PD, bulk-downloadable) for later material.
- **Verdict:** Foundational myth texts (Kojiki/Nihongi) obtainable in PD English + originals; no single packaged corpus.

### Korean — HARD
- **Samguk Yusa** (Iryeon) — the myth-bearing source (Dangun, Three Kingdoms legends). Written in **Classical Chinese (hanmun)**; original available via Korean digital classics portals (db.itkc.or.kr / krpia — free-to-read, scrape). **Every full English translation (Ha & Mintz 1972; recent Brill/annotated) is in copyright → HARD.** https://en.wikipedia.org/wiki/Samguk_yusa
- **Obstacle:** no PD English; original is hanmun requiring specialist handling.

---

## 9. Caucasus, Africa, and the wider textual world

### Armenian / Georgian — MODERATE/HARD
- **Armenian** — Moses of Khorene's *History* and epic material; PD English (partial) + originals on **TITUS** and Wikisource; scholarly translations copyright. Scrape/assemble.
- **Georgian** — *Knight in the Panther's Skin* (Rustaveli) PD translations on archive.org; myth/folklore sparse. Assemble.

### Ethiopian — MODERATE
- **Kebra Nagast** — **Budge's 1922 English translation is PD**, full text on sacred-texts + archive.org; Gəʿəz original in scholarly editions (copyright). *Book of Enoch* (Ethiopic) via Charles PD. → bulk via sacred-texts. https://sacred-texts.com/afr/kn/

### Yoruba (Ifá) — HARD
- Ifá corpus (odù) — no authoritative open full-text corpus; material scattered across ethnographies (Bascom, Abimbola — **copyright**), some PD colonial-era collections on archive.org. Oral/performance tradition, translation-dependent. → assemble, mostly copyright-locked.

### Mesoamerican — MODERATE/HARD
- **Maya — Popol Vuh:** original K'iche' + Spanish facsimile/transcription openly available (World Digital Library / OMNIKA facsimile); **PD English (Goetz–Morley from Recinos, 1950) borderline; recent translations (Christenson, Tedlock) copyright.** → original obtainable; readable modern English mostly copyright.
- **Chilam Balam** — Yucatec Maya colonial books; Roys's *Chumayel* (1933) English is older (archive.org), status varies; originals in facsimile. → assemble.
- **FAMSI** — resources/bibliography and some texts; now largely archival (Mesoweb). Reference more than clean corpus.
- **Aztec/Nahua — Florentine Codex:** **Getty Digital Florentine Codex** — full Nahuatl + Spanish transcriptions, English + Spanish translations, searchable, images. Landmark resource; **check Getty's reuse terms (likely CC-ish for images/data but confirm; oriented to online use, no single bulk text dump advertised).** https://florentinecodex.getty.edu/
- **Cantares Mexicanos** — Nahuatl source via **UNAM (temoa.iib.unam.mx) under CC-BY-NC-ND 4.0** (ND blocks derivatives); Bierhorst's English is copyright. https://en.wikipedia.org/wiki/Cantares_Mexicanos
- **Obstacle:** originals increasingly digitized, but ND licensing and copyrighted modern translations limit reuse.

### Andean — HARD
- **Huarochirí Manuscript** — the great Quechua myth text; original Quechua + Spanish exists in scholarly editions; **standard English (Salomon & Urioste 1991) is copyright.** Original transcription available in academic sources; no clean open corpus. → assemble/partial.
- Colonial chronicles (Guamán Poma) — **the Guaman Poma Website (Royal Library, Copenhagen)** offers full facsimile + transcription, free. Otherwise scattered.

### Polynesian — MODERATE
- PD ethnographic translations abundant on **sacred-texts.com Pacific section** (Grey's *Polynesian Mythology*, Fornander, Malo's *Hawaiian Antiquities*, Beckwith) + archive.org. Translation-only, dated, but bulk-downloadable via sacred-texts. https://sacred-texts.com/pac/

---

## 10. The oral / ethnographic world (Sub-Saharan Africa, Native North America, Amazonia, Siberia, Aboriginal Australia, Melanesia) — HARD

There is **no native "canon"**; the texts exist only as recorded/translated performances scattered across ethnographies. Where to find them:

- **Bureau of American Ethnology (BAE) Annual Reports & Bulletins** — the single richest PD trove for Native North America: Mooney *Myths of the Cherokee*, Boas *Tsimshian Mythology*, Stevenson *Zuñi*, etc. **All PD (US government pre-1929), scanned on Internet Archive / Smithsonian / Biodiversity Heritage Library → bulk-downloadable but image-PDF needing OCR** (some already have OCR text layers / djvu.txt). https://archive.org/details/annualreportofbu191smit · http://rla.unc.edu/archives/BAE-Pubs.html
- **sacred-texts.com regional sections** — Africa, Native America, Australia, Pacific: curated PD ethnographic translations, already as HTML text (bulk via download package). https://sacred-texts.com/
- **Internet Archive ethnographies** — vast PD anthropology (Frazer, Rattray *Ashanti*, Callaway *Zulu*, Radin, Curtin); mixed OCR quality.
- **Folklore journals** — *Journal of American Folklore*, *Folk-Lore* — older volumes PD on JSTOR-Early/archive.org.
- **Siberia/Central Asia** — Radloff, Chadwick collections PD; modern epic recordings (Manas etc.) mostly copyright.
- **Aboriginal Australia / Melanesia** — Spencer & Gillen, Strehlow (older PD), Malinowski — but much is copyright and/or **culturally restricted** (many Indigenous communities and archives like AIATSIS place access controls; not free-to-redistribute even when digitized).

**Reality:** these traditions are translation-only, dated, scattered across thousands of PDFs, requiring **OCR + heavy curation**, and some carry ethical/access restrictions independent of copyright.

---

## 11. The big aggregators (what each holds, license)

| Aggregator | Holds | License | Obtainability |
|---|---|---|---|
| **sacred-texts.com** | Broad, dated PD translations across *every* tradition | PD content; site "package" freely copyable | **Bulk download** (download page) + scrape |
| **Project Gutenberg** | PD translations (Kalevala, Eddas, Quran, Kojiki, Mahabharata, etc.) | PD (US) | **Bulk** (per-book + mirrors) |
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

## 12. Synthesis

### 12a. Obtainability ranking table

| Tradition | Verdict | Best open source | Format | License | How to get |
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
| Zoroastrian | **MODERATE** | Avesta.org / TITUS | HTML | PD content / no license | scrape |
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
| Oral world (Africa, N.America, Amazonia, Siberia, Australia, Melanesia) | **HARD** | BAE reports, sacred-texts, IA | HTML/image-PDF | PD (much) but scattered | bulk PD but needs OCR/curation; some culturally restricted |

### 12b. Which traditions are "build-ready" today vs. need work

**Clean, openly-licensed, machine-readable RIGHT NOW (drop-in):**
Greek, Latin, Jewish (Sefaria), Pāli Buddhist (SuttaCentral CC0), Chinese Buddhist (CBETA), Sumerian/Akkadian (ETCSL+ORACC), Quran (Tanzil), Kalevala, and the PD-translation layer of Norse. Sanskrit originals via SARIT (clean CC) and GRETIL (bulk, header-check).

**Available but needs scraping / license-checking / mixed formats:**
Chinese classics (ctext gated API + Kanripo), Celtic (CELT per-text), Zoroastrian (scrape Avesta/TITUS), Japanese (assemble sacred-texts + JTI/Aozora), Hadith (gated API/mirrors), Egyptian (HF datasets, rolling), Hittite (Zenodo), Pseudepigrapha (OCP + PD Charles), Polynesian/Ethiopian (sacred-texts PD).

**Needs OCR:**
Acta Sanctorum (PD Latin page-scans), the entire BAE/ethnographic oral-world corpus (PD but image-PDF), Ugaritic/older ANE editions, many Mesoamerican/Andean colonial sources.

**Needs licensing or fresh translation (copyright-blocked):**
Tibetan Kangyur translations (84000 ND), Korean Samguk Yusa, Andean Huarochirí, Yoruba Ifá, modern Maya/Nahua translations, Ugaritic KTU, and every tradition's *modern scholarly English* (Larrington, Faulkner, Christenson, Tedlock, Hoffner, Bierhorst, Salomon). For these you either license, use dated PD translations, or commission translation.

### 12c. Single biggest obstacle per HARD case

- **Tibetan Buddhist:** 84000's translations are free-to-read but **CC-BY-NC-ND — NoDerivatives forbids the segmentation/reformatting a corpus requires.** (Metadata is CC-BY; text is not usable as data.)
- **Jain:** **no unified machine-readable Āgama corpus exists** — digitization is manuscript-image-centric (JAINpedia).
- **Ugaritic/Canaanite:** the **authoritative transliteration (KTU) and all modern translations are in copyright**; no open TEI corpus.
- **Korean (Samguk Yusa):** **every English translation is in copyright**; only the Classical-Chinese original is free.
- **Andean (Huarochirí):** the **standard English (Salomon & Urioste) is in copyright**; original Quechua only in scholarly editions.
- **Christian hagiography (Acta Sanctorum):** the **searchable full text is a ProQuest paywall**; the free version is un-OCR'd Latin page-scans.
- **Yoruba (Ifá):** an **oral corpus never systematically transcribed into an open text edition**; key collections (Bascom, Abimbola) are copyright.
- **Mesoamerican:** originals are digitized but **ND licensing (Getty/UNAM) and copyrighted modern translations** block reuse.
- **Oral world at large:** the material was **never systematically digitized as text** — it survives as thousands of PD but un-OCR'd ethnography pages, and some is **culturally access-restricted** independent of copyright.

**Overarching pattern to design around:** for *dead-language* traditions the open asset is the **original-language transliteration/text**; the readable translation is usually copyright. For *oral* traditions the only asset is a **translation**, and it is usually either copyright or an un-OCR'd PD scan. Budget accordingly: TEI/JSON ingestion for the EASY tier, OCR pipelines for the ethnographic/hagiographic tier, and licensing/commissioned-translation for the copyright-blocked tier.

## Implication for the classification

The obtainability tiers reshape criterion 4 (volume of traditions & material) once more: the sections
we can actually **fill with open full text today** are the EASY-tier literate traditions — Greek,
Latin, Jewish, Buddhist (Pāli + Chinese), Mesopotamian, Quran, Sanskrit, Norse. The oral-world
sections are not just thin by text (as the volume analysis showed) but **HARD to obtain even as
translation** (OCR + curation + access restrictions). So a corpus-first classification should launch
from the ~10 build-ready literate traditions and treat the oral world as a later OCR/curation phase.

## Sources

See per-section URLs above; principal open corpora: Perseus (github.com/PerseusDL), First1KGreek,
Sefaria-Export, SuttaCentral bilara-data, CBETA xml-p5, ETCSL, ORACC, Tanzil, GRETIL, SARIT,
Project Gutenberg, sacred-texts.com, Internet Archive, Wikisource.
