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
- **Gerhard Lauer** (Johannes Gutenberg Univ. Mainz, Institute of Book Science) —
  computational folktale studies at scale (large corpora, fairy tales, ML); wrote
  the 2023 *Fabula* survey that is the field's best short entry point.
- **Emese Ilyefalvi** (Digital Folklore Lab, Hungary) — digital folklore
  databases, metadata & standardization, corpus analysis of archives.
- **Pádraig Mac Carron & Ralph Kenna** (Coventry) — *network mythology*:
  quantitative comparison of epic character networks (Iliad, Beowulf, Táin).
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
- Cross-over venues for the phylogenetic / network papers: **Royal Society Open
  Science**, **PLOS ONE**, **Current Biology**, **EPJ Data Science**, **EPL
  (Europhysics Letters)**.

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
- **ACM/IEEE Joint Conference on Digital Libraries (JCDL)** and the **Association
  for Computers and the Humanities (ACH) Conference** — regular homes for
  archive/tooling and DH-methods work.
- **CLARIN / DARIAH** annual events — European DH research-infrastructure venues
  where folktale-database/tooling work is presented.

Note: there is **no dedicated Computational Folkloristics conference** — the work
is spread across the venues above (DH/ADHO and CHR being the primary two).

---

## 4. Landmark publications (a starter reading list)

**Computational folkloristics — foundational:**
- Abello, Broadwell & Tangherlini, *Computational Folkloristics*, **Communications
  of the ACM** 55(7), 2012 — the discipline-defining programmatic paper
  (folklore-as-data, semantic networks, knowledge graphs, large-scale motif
  analysis, GIS).
- Tangherlini, *The Folklore Macroscope* (2013) — the conceptual shift from
  close reading of single texts to "macroscope" analysis of millions at once.
- *Computing Folklore Studies: Mapping over a Century of Scholarly Production
  through Topics*, **Journal of American Folklore** 126(502):455–475, 2013
  (DOI 10.5406/jamerfolk.126.502.0455) — topic-modeling the field's own history.
- Tangherlini (guest ed.), *Big Folklore: A Special Issue on Computational
  Folkloristics*, **Journal of American Folklore** 129(511), 2016
  (DOI 10.5406/jamerfolk.129.511.0005) — the single best issue to read.
- **Gerhard Lauer, *Computational Folktale Studies: A Very Brief History*,
  Fabula 64(1–2):1–6, 2023 (DOI 10.1515/fabula-2023-0001)** — the best modern
  overview; recommended first read (Aarne → Thompson → ATU → DH → NLP → LLM).
- Emese Ilyefalvi, *The theoretical, methodological and technical issues of
  digital folklore databases and computational folkloristics* (2018) — on
  digital archives, motif databases, and data standardization.
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

**Network mythology:**
- Mac Carron & Kenna, *Universal Properties of Mythological Networks*, **EPL
  (Europhysics Letters)** 99(2), 2012 (arXiv:1205.4324) — character-interaction
  networks of the Iliad, Beowulf, and the Táin compared to real social networks.
- Kenna, Mac Carron et al., *Maths Meets Myths: Quantitative Approaches to
  Ancient Narratives* (2016) — the edited volume of this strand.

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
- **Network mythology** — character-interaction graphs of epics/myths, compared
  to real vs fictional social networks (Mac Carron & Kenna).

**Active frontiers in computational mythology** (where the field is heading):
phylogenetic reconstruction of myths; knowledge graphs of gods / characters /
motifs; automatic motif extraction; semantic embeddings of mythological
characters; narrative graphs; LLM-based comparison of mythological corpora;
large motif graphs (GraphRAG-style); and multimodal myth-story databases. The
common thread — and mythoscope's own bet — is the move **from static motif
catalogues to dynamic semantic networks** linking motifs, plots, characters, and
the geography of their spread.

---

## 6. Where mythoscope sits

mythoscope overlaps the **Meertens/GLOS** cluster (embeddings + cross-index +
geography over TMI/ATU/Berezkin) and the **Berezkin/d'Huy** areal-mythology
cluster. Its differentiator — the survey found no one else builds it — is a
**cross-index `type ⇄ motif ⇄ text ⇄ place` graph** spanning all three indexes.

The corpora these groups repeatedly test on (detailed in
`external-tmi-atu-editions.md`): **Nederlandse Volksverhalenbank** / ISEBEL,
Iceland's **Sagnagrunnur**, Germany's **WossiDiA**, Estonia's **ETKSpace**
(folklore.ee), and Tangherlini's **Danish Folklore Nexus**.

Practical hooks:
- **Publish** the dataset/method at **CHR** or in **JOHD** (open-data) / **Journal
  of Cultural Analytics**; the trilogy corpus already set the JOHD precedent.
- **Cite/align** with MOMFER (semantic motif search), the phylogenetic-myth
  papers (Berezkin areal data we already use), and DFKI's LOD crosswalk design.
- **Watch** CHR 2027, the ISFNR/AI4DH workshops, and FIU Dataverse (Finlayson
  corpus) — the live edges of the field, per the §6 outreach track.
