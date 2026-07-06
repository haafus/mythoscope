# Computational folkloristics & computational mythology — landscape

The best labs, people, journals, conferences, and landmark publications in the
computational study of folk narrative and myth — the research community
mythoscope sits inside. Compiled 2026-07 from web validation; companion to
`external-tmi-atu-editions.md` (data sources) and its §6 enrichment plan.

Two overlapping fields:
- **Computational folkloristics** — quantitative/NLP study of folk narrative
  (tale types, motifs, archives, variation, geography). Term popularized by
  Tangherlini.
- **Computational / statistical (phylogenetic) mythology** — treating myths as
  evolving lineages of "mythemes," reconstructing ancestry and diffusion with
  tools borrowed from evolutionary biology.

---

## 1. People & labs (the ones to track)

- **Timothy R. Tangherlini** (UC Berkeley; prev. UCLA) — coined/championed
  *computational folkloristics*. GIS + network + topic-model analysis of Danish
  folklore archives (the "Danish Folklore Nexus"/WitchHunter work); the
  *Folklore Macroscope*. Central figure. UCLA feature:
  <https://newsroom.ucla.edu/stories/stories-storytellers-and-statistics-a-computational-approach-to-the-humanities>
- **Meertens Institute (KNAW), Amsterdam** — the folk-narrative computing hub:
  **Folgert Karsdorp** (head, Ethnology & Oral Culture), **Theo Meder**,
  **Marten van der Meulen**, **Dong Nguyen**. Built **MOMFER**, the **Dutch
  Folktale Database** (100k+ ATU-typed tales), automatic genre classification /
  enrichment, animacy detection. <https://meertens.knaw.nl>
- **Mark A. Finlayson** (Florida International Univ., Cognac Lab) — automatic
  **motif detection & indexing**, ProppLearner, Story Workbench, the (pending)
  Arabian Nights / El-Shamy motif corpus. <https://cognac.cs.fiu.edu>
- **Julien d'Huy**, **Jean-Loïc Le Quellec**, **Marc Thuillard**, **Yuri
  Berezkin** — the phylogenetic-mythology group: myths as evolving mythemes,
  Cosmic Hunt reconstruction, large-scale world-myth mapping. Berezkin's own
  areal motif catalogue is one of mythoscope's three indexes.
- **Jamshid J. Tehrani** (Durham) & **Sara Graça da Silva** — phylogenetic
  analysis of folktales over the ATU catalogue (Little Red Riding Hood; "Smith
  and the Devil" reconstruction).
- **Karl Grossner** (GLOS — Geographic Lens on Stories) — embeddings + LLM over
  digitized TMI/ATU + geography; mythoscope's nearest architectural neighbour.
- **Thierry Declerck** (DFKI, Saarbrücken) — TMI/ATU as Linked Open Data (OWL/RDF).
- **Berkeley Institute for Data Science (BIDS)** + Slovenian folklore researchers
  — recent AI/LLM-for-folklore collaboration (AI4DH). <https://ai4dh.eu>

---

## 2. Journals

**Field-specific (folk narrative):**
- **Fabula** (De Gruyter, since 1958; organ of the ISFNR) — the journal of
  comparative folk-narrative studies (DE/EN/FR). <https://www.degruyter.com/journal/key/fabl/html>
- **Journal of American Folklore** (American Folklore Society, since 1888) — hosted
  the 2016 special issue **"Big Folklore: A Special Issue on Computational
  Folkloristics"** (guest-ed. Tangherlini). <https://www.jstor.org/journal/jamerfolk>
- **Journal of Folklore Research** (Indiana Univ. Press) — explicitly welcomes
  digital-humanities work. <https://scholarworks.iu.edu/journals/index.php/jfr>
- **Folklore** (Taylor & Francis) — published the **MOMFER** paper (2015).
  <https://www.tandfonline.com/journals/rfol20>
- **Journal of Ethnology and Folkloristics**; **Western Folklore** (2013 "macroscope"-era work).

**Computational / methods venues (where the CS-heavy work lands):**
- **Computational Humanities Research (CHR)** — open-access journal (Cambridge
  Core) + annual conference; the primary home for quantitative humanities.
  <https://www.cambridge.org/core/journals/computational-humanities-research>
- **Journal of Cultural Analytics** — computational study of culture. <https://culturalanalytics.org>
- **Journal of Open Humanities Data (JOHD)** — published the trilogy **"Bearing a
  Bag-of-Tales"** dataset paper (2022). <https://openhumanitiesdata.metajnl.com>
- **Digital Scholarship in the Humanities (DSH)** (Oxford/ADHO) and **Digital
  Humanities Quarterly (DHQ)** — general DH.
- **Communications of the ACM** — carried Abello, Broadwell & Tangherlini,
  *"Computational Folkloristics"* (2012). <https://cacm.acm.org/research/computational-folkloristics/>

**Comparative-mythology / statistical:**
- **Nouvelle Mythologie Comparée / New Comparative Mythology** — d'Huy et al.,
  *"Computational Approaches to Myths Analysis: Cosmic Hunt"* (2018).
- **Trames** — *"A Large-Scale Study of World Myths"* (2018, Thuillard, d'Huy,
  Berezkin, Le Quellec).
- **RMN Newsletter** (Retrospective Methods Network, Helsinki) — statistical
  methods for mythology.
- Cross-over venues for the phylogenetic papers: **Royal Society Open Science**,
  **PLOS ONE**, **Current Biology**.

---

## 3. Conferences & workshops

- **Computational Humanities Research (CHR)** — the key annual venue; proceedings
  on CEUR-WS. Next: **Univ. of Manchester, 5–8 Jan 2027** (submissions due
  2026-08-14). <https://computational-humanities-research.org/conference/>
- **Digital Humanities (DH / ADHO)** — the flagship annual DH conference (where
  DFKI's DH2017 LOD paper appeared).
- **ISFNR Congress** — International Society for Folk Narrative Research; the
  discipline's global meeting. <https://isfnr.org>
- **LaTeCH-CLfL** (Workshop on Language Technology for Cultural Heritage / for
  Computational Linguistics for Literature) — ACL/EACL/COLING-affiliated; the
  main NLP-side workshop for narrative & heritage text.
- **AAAI Workshop on Computational Folkloristics** (2016) — the field's named CS
  workshop (Tangherlini, Broadwell).
- **"AI Methods for Research of Folkloristic Narratives"** — recent international
  workshop (Univ. of Ljubljana, 2025; BIDS + Slovenia). <https://ai4dh.eu/2025/06/23/ai-methods-for-research-of-folkloristic-narratives/>
- **CLARIN / DARIAH** annual events — European DH research-infrastructure venues
  where folktale-database/tooling work is presented.

---

## 4. Landmark publications (a starter reading list)

**Computational folkloristics — foundational:**
- Abello, Broadwell & Tangherlini, *Computational Folkloristics*, **Communications
  of the ACM** 55(7), 2012.
- Tangherlini (guest ed.), *Big Folklore: A Special Issue on Computational
  Folkloristics*, **Journal of American Folklore**, 2016.
- Karsdorp, van der Meulen, Meder & van den Bosch, *MOMFER: A Search Engine of
  Thompson's Motif-Index*, **Folklore** 126(1), 2015.
  <https://doi.org/10.1080/0015587X.2015.1006954>
- Nguyen, Trieschnigg, Meder & Theune — automatic classification/enrichment of
  folk-narrative genres in the Dutch Folktale Database.
- Hagedorn & Darányi, *Bearing a Bag-of-Tales*, **Journal of Open Humanities
  Data**, 2022 — the trilogy corpus. <https://openhumanitiesdata.metajnl.com/articles/10.5334/johd.78>
- Declerck et al., *Towards a Linked Data Access to Folktales classified by
  Thompson's Motifs and ATU Types*, **DH2017**.

**Phylogenetic folktale / myth analysis:**
- Tehrani, *The Phylogeny of Little Red Riding Hood*, **PLOS ONE** 8(11), 2013.
  <https://doi.org/10.1371/journal.pone.0078871>
- da Silva & Tehrani, *Comparative phylogenetic analyses uncover the ancient
  roots of Indo-European folktales*, **Royal Society Open Science** 3(1), 2016
  (ATU 330 "Smith and the Devil"). <https://doi.org/10.1098/rsos.150645>
- Thuillard, Le Quellec, d'Huy, *Computational Approaches to Myths Analysis:
  Cosmic Hunt*, **Nouvelle Mythologie Comparée** 4, 2018. <https://shs.hal.science/halshs-02280068/document>
- Thuillard, d'Huy, Berezkin & Le Quellec, *A Large-Scale Study of World Myths*,
  **Trames** 22(4), 2018 (2,264 motifs / 40,000 myths / 934 cultures).
- Finlayson et al. — motif-detection & the Arabian Nights corpus (arXiv:2603.19283, 2026).

---

## 5. Methods / approaches in play

- **Type/motif classification & auto-tagging** — supervised + LLM classification
  of tales into ATU types / motifs (Meertens, Finlayson).
- **Phylogenetic & network reconstruction** — myths/tales as character matrices;
  trees + phylogenetic networks (d'Huy, Tehrani, Thuillard).
- **Embeddings & semantic search** — vector representations of motif/type text
  (MOMFER, GLOS, and mythoscope's own BGE-M3 parallels).
- **GIS / spatial diffusion** — mapping tale/motif distributions and areal
  clustering (Tangherlini, Berezkin, GLOS).
- **Linked Open Data / ontologies** — TMI/ATU as RDF/OWL, cross-index links (DFKI).
- **Network analysis** — storyteller–story networks, motif co-occurrence.

---

## 6. Where mythoscope sits

mythoscope overlaps the **Meertens/GLOS** cluster (embeddings + cross-index +
geography over TMI/ATU/Berezkin) and the **Berezkin/d'Huy** areal-mythology
cluster. Its differentiator — the survey found no one else builds it — is a
**cross-index `type ⇄ motif ⇄ text ⇄ place` graph** spanning all three indexes.

Practical hooks:
- **Publish** the dataset/method at **CHR** or in **JOHD** (open-data) / **Journal
  of Cultural Analytics**; the trilogy corpus already set the JOHD precedent.
- **Cite/align** with MOMFER (semantic motif search), the phylogenetic-myth
  papers (Berezkin areal data we already use), and DFKI's LOD crosswalk design.
- **Watch** CHR 2027, the ISFNR/AI4DH workshops, and FIU Dataverse (Finlayson
  corpus) — the live edges of the field, per the §6 outreach track.
