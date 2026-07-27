# Awesome Computational Mythology [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)

> A curated list of resources for the computational, comparative, and quantitative study of
> myth, folklore, and traditional narrative — indexes, corpora, datasets, methods, tools,
> ontologies, key papers, scholars, venues, and text libraries.

Maintained alongside [Mythoscope](https://mythoscope.io). Contributions welcome.

**Scope.** Resources for studying myth/folklore/traditional narrative *computationally,
comparatively, or quantitatively*. **In:** indexes, corpora, datasets, methods, tools,
ontologies, quantitative/DH studies, text libraries. **Out:** general mythology retellings,
single-tradition popularizations, and non-computational reference works (unless a standard
apparatus like TMI/ATU). This is a **neutral community list** — Mythoscope is listed as one
project among many, not featured.

**⚠ Draft.** Assembled from the Mythoscope research surveys (`docs/research/`, `docs/motifs/`)
and source lists. **Links must be verified before this is published as a public list.** Papers
are given by author / venue / year (resolve via Google Scholar / Semantic Scholar / DOI).

## Contents

- [Motif & tale-type indexes](#motif--tale-type-indexes)
- [Corpora & annotated datasets](#corpora--annotated-datasets)
- [Cross-cultural & areal databases](#cross-cultural--areal-databases)
- [Digital text libraries](#digital-text-libraries)
- [Encyclopedias & reference works](#encyclopedias--reference-works)
- [Ontologies & linked open data](#ontologies--linked-open-data)
- [Methods & techniques](#methods--techniques)
- [Tools & software](#tools--software)
- [Landmark papers](#landmark-papers)
- [Scholars & labs](#scholars--labs)
- [Venues & journals](#venues--journals)
- [Projects](#projects)

## Motif & tale-type indexes

- **Thompson Motif-Index (TMI)** — Stith Thompson, *Motif-Index of Folk-Literature*, rev. ed.
  1955–58. ~46,000 narrative motifs, place-value taxonomy (A–Z). Digital: the *Trilogy* CSVs
  (j-hagedorn), Katja Mellmann's `TMI_as_CSV`, fbkarsdorp/tmi, folkmasa.org.
- **Aarne–Thompson–Uther (ATU)** — Hans-Jörg Uther, *The Types of International Folktales*,
  FFC 284–286, Helsinki 2004. 2,247 tale types. (Successor to Aarne–Thompson AaTh/AT.)
- **Berezkin & Duvakin — Analytical Catalogue of World Mythology and Folklore** — ~3,500 areal
  motifs across ~65 world macro-regions. (areasofmyths.com / mapsofmyths.com.)
- **El-Shamy — *Motif Index of the Thousand and One Nights*** and *Folk Traditions of the Arab
  World*.
- **Christiansen — *The Migratory Legends* (ML)** — the migratory-legend type index.
- **СУС (Sravnitel'nyj Ukazatel' Sjuzhetov)** — the East-Slavic comparative tale-type index.
- **Perry Index** — Aesopic fable types.
- **ATU-adjacent / national indexes** — Grimm KHM numbering; Hodne (Norwegian); regional
  catalogues surveyed in `docs/motifs/external-tmi-atu-editions.md`.

## Corpora & annotated datasets

- **GOLEM** (Yarlott et al., LREC-COLING 2024) — gold-standard motif corpus, 26k candidates /
  34 motif types; a hard benchmark (LLMs ~41% accuracy).
- **Annotated Folktales / "Trilogy"** (Hagedorn & Darányi, 2022) — open ATU-annotated corpus
  (CC-BY-SA); SVM baselines reach F1 0.8–1.0.
- **MOMFER** — the Meertens Motif Finder over the *Dutch Folktale Database*.
- **Dutch Folktale Database (Verhalenbank)** — the Meertens Institute folktale collection.
- **ISEBEL** — cross-archive search over multiple European folk-narrative databases.
- **FairytaleQA** — QA dataset over fairy tales (education/NLP).
- **Multilingual Folk Tale Database (MFTD)** — multilingual tale collection.
- **Ashliman's Folktexts** — D. L. Ashliman's folklore text archive (ATU-organized).
- **ProppLearner** — Proppian-function-annotated Russian folktales (Finlayson).
- **Evald Tang Kristensen corpus** — the Danish collector's folklore (Tangherlini's work).
- **Kestemont et al. "Forgotten Books"** (Science, 2022) — survival estimation of medieval
  narrative.

## Cross-cultural & areal databases

- **D-PLACE** — Database of Places, Language, Culture and Environment (incl. the *Ethnographic
  Atlas*; subsistence, social structure). d-place.org
- **Glottolog** — language classification + family metadata. glottolog.org
- **Seshat: Global History Databank** — seshatdatabank.info
- **Database of Religious History (DRH)** — religiondatabase.org
- **eHRAF World Cultures** — ethnography (Yale HRAF; proprietary).
- **MANTO** — Greek myth entities/relations database. manto-myth.org
- **Theoi Greek Mythology** — theoi.com

## Digital text libraries

- **Perseus Digital Library** — perseus.tufts.edu (+ First1KGreek)
- **Internet Sacred Text Archive** — sacred-texts.com
- **ETCSL** — Electronic Text Corpus of Sumerian Literature — etcsl.orinst.ox.ac.uk
- **ORACC** — Open Richly Annotated Cuneiform Corpus — oracc.museum.upenn.edu
- **Thesaurus Linguae Aegyptiae** — thesaurus-linguae-aegyptiae.de
- **GRETIL** — Göttingen Register of Electronic Texts in Indian Languages — gretil.sub.uni-goettingen.de
- **Sanskrit Library** — sanskritlibrary.org
- **SARIT** — Search and Retrieval of Indic Texts
- **Chinese Text Project (ctext)** — ctext.org
- **CBETA** — Chinese Buddhist Electronic Text Association — cbeta.org
- **SuttaCentral** — early Buddhist texts — suttacentral.net
- **Sefaria** — Jewish texts — sefaria.org
- **Tanzil** — Quran text — tanzil.net
- **CELT** — Corpus of Electronic Texts (Irish) — celt.ucc.ie
- **Dúchas / National Folklore Collection (Ireland)** — duchas.ie
- **Finnish Literature Society (SKS) folklore archive** — finlit.fi
- **World Oral Literature Project** — oralliterature.org
- **Fordham Internet History Sourcebooks** — sourcebooks.fordham.edu
- **OpenITI** — Open Islamicate Texts Initiative — openiti.org
- **TITUS** — Thesaurus Indogermanischer Text- und Sprachmaterialien — titus.uni-frankfurt.de
- **Project Gutenberg** — gutenberg.org · **Internet Archive** — archive.org · **HathiTrust** — hathitrust.org
- **Buddhist Digital Resource Center** — bdrc.io

## Encyclopedias & reference works

*(Surveyed in `docs/research/mythology-encyclopedias-survey.md`.)*

- **The Mythology of All Races** (Gray/Moore, 13 vols).
- **Encyclopedia of Religion** (Eliade, ed.; 2nd ed. Jones).
- **Мифы народов мира** (Tokarev, ed.) — the two-volume Soviet mythological encyclopedia.
- **Dictionary of Mythology** (Bonnefoy, *Mythologies*).
- **New Larousse Encyclopedia of Mythology** (Guirand / Graves intro).
- **Wörterbuch der Mythologie** (Haussig, ed.).
- **Enzyklopädie des Märchens** — the reference encyclopedia of the folktale.
- **ARAS** — Archive for Research in Archetypal Symbolism.
- **Meletinsky**, *The Poetics of Myth*; **Ivanov & Toporov** (structuralist mythology).

## Ontologies & linked open data

- **DFKI Linked Data for Folktales** (Declerck et al.) — OWL/RDF/SKOS + lemon modelling of
  ATU/TMI. (Note: several endpoints unreleased — verify availability.)
- **Ontology of Greek Mythology (OGM)**.
- **GLOS — Geographic Lens on Stories** (Grossner et al.) — place-based narrative.
- Vocabularies: **SKOS**, **lemon**, **CIDOC-CRM** (heritage), **Wikidata** (P2540 = ATU
  tale-type ID).

## Methods & techniques

- **Motif induction / detection from text** — the open problem; formally fluid motifs, weak
  detectors (macro-F1 low), classical baselines competitive with LLMs.
- **Tale-type / narrative classification** — SVM+TF-IDF, transformers, story embeddings.
- **Topic modeling** — LDA, Labeled-LDA, BERTopic (+ c-TF-IDF, KeyBERT).
- **Embeddings** — word2vec, SBERT/Sentence-Transformers, LaBSE, BGE-M3, E5, sentence-t5;
  **story embeddings** (plot- not style-similarity).
- **Dimensionality reduction & clustering** — UMAP, t-SNE, PCA; HDBSCAN; NeighborNet.
- **Phylogenetics of narrative** — Bayesian phylogenetics (BEAST, MrBayes), maximum-parsimony,
  ancestral-state reconstruction, phylomemetics; tip-dating / fossilized birth–death.
- **Seriation & pseudo-time** — correspondence-analysis seriation (Petrie–Robinson–Brainerd);
  single-cell pseudotime (DPT, Slingshot, Monocle) applied to motif ordering.
- **Networks** — character-interaction networks; network motifs (mfinder, FANMOD); block models
  (degree-corrected SBM); nestedness (NODF).
- **Sequence/pattern mining** — matrix profile, SAX, suffix trees, PrefixSpan/SPADE/GSP.
- **Cross-cultural statistics** — Galton's problem, restricted-permutation nulls, isolation by
  distance, Mantel tests, F_st; resistance/least-cost surfaces.
- **Narrative structure** — Propp's morphology / functions; Analogical Story Merging (Bayesian
  model merging); GraphRAG extraction of characters/places/times.

## Tools & software

- **MOMFER** — motif finder over the Dutch Folktale Database.
- **Sentence-Transformers**, **Hugging Face**, **vLLM** — embedding/LLM infrastructure.
- **BERTopic** — topic modeling.
- **SplitsTree / NeighborNet**, **BEAST2**, **MrBayes** — phylogenetics.
- **Gephi**, **igraph/NetworkX**, **mfinder / FANMOD** — networks.
- **Story Workbench / ProppLearner**, **MIME**, **GOLEM** tooling — narrative annotation.
- **`uhhlt/story-emb`** — story-similarity embedding model (Hatzel & Biemann).
- **Mythoscope** — this project: corpus → embeddings → motif crosswalk → interactive views.

## Landmark papers

- Mac Carron & Kenna — *Universal Properties of Mythological Networks* (EPL, 2012).
- Abello, Broadwell & Tangherlini — *Computational Folkloristics* (CACM, 2012).
- da Silva & Tehrani — *Comparative phylogenetic analyses uncover the ancient roots of
  Indo-European folktales* (R. Soc. Open Sci., 2016) — "The Smith and the Devil", ATU 330.
- Tehrani — *The Phylogeny of Little Red Riding Hood* (PLoS ONE, 2013).
- d'Huy — *Cosmic Hunt* / phylogenetic mythology (Les Mythes, 2013–).
- Karsdorp, van den Bosch, et al. — folk-narrative NLP & "Bearing a Bag-of-Tales".
- Hatzel & Biemann — *Story Embeddings* (EMNLP 2024).
- Yarlott et al. — *GOLEM* (LREC-COLING 2024).
- Alyami & Finlayson — *Automated Motif Indexing on the Arabian Nights* (2026).
- Bei et al. — *BERT encodes narrative dimensions* (CMN 2026).
- Journal of American Folklore — *Big Folklore* special issue (2016).
- Lauer — *A Very Brief History of Computational Folkloristics* (Fabula, 2023).

## Scholars & labs

Timothy Tangherlini · Folgert Karsdorp · Theo Meder · Antal van den Bosch · Dong Nguyen ·
Mark Finlayson · W. Victor Yarlott · Julien d'Huy · Jean-Loïc Le Quellec · Marc Thuillard ·
Yuri Berezkin · Jamshid Tehrani · Sara Graça da Silva · Mike Kestemont · Ralph Kenna ·
Pádraig Mac Carron · Thierry Declerck · Gerhard Lauer · Emese Ilyefalvi · Peter Broadwell ·
James Abello · Karl Grossner. (Foundational: Stith Thompson, Antti Aarne, Hans-Jörg Uther,
Vladimir Propp, Alan Dundes, Claude Lévi-Strauss.)

## Venues & journals

- **CHR** — Computational Humanities Research.
- **ADHO Digital Humanities (DH)** conference.
- **LaTeCH-CLfL** — Workshop on NLP for Cultural Heritage, Social Sciences & Literature.
- **ISFNR** — International Society for Folk Narrative Research.
- **CMN** — Computational Models of Narrative.
- **Fabula** · **Journal of American Folklore** · **Journal of Cultural Analytics** ·
  **Digital Scholarship in the Humanities (DSH)** · **Humanities Commons**.

## Projects

- **Mythoscope** — mythoscope.io — comparative-mythology framework: semantic space + LLM
  graphs + a TMI↔ATU↔Berezkin motif crosswalk.
- **GOLEM**, **MIME**, **GLOS**, **MANTO**, **DRH** — see above.

---

## See also

Related curated lists to cross-link with (reciprocal links aid discovery): *awesome-nlp*,
*awesome-digital-humanities*, *awesome-computational-social-science*,
*awesome-network-analysis*, *awesome-cultural-evolution* (where they exist). Suggest more via PR.

## Recently added

_Newest entries first — a liveliness signal. (Populate on each merge.)_

## Contributing

PRs welcome. **Entry format:** `**Name** — one-line description — link` (papers:
`Author(s) — Title (venue, year)`). **Criteria:** the resource must be real, reachable, in
scope (above), and not a duplicate; keep descriptions neutral and one line. See
[`contributing.md`](contributing.md) and the "Suggest a resource" issue template. By
contributing you agree to the [code of conduct](code-of-conduct.md).

## License & citation

Content released under **CC0** (public domain) — reuse freely. Cite this list via its
[`CITATION.cff`](CITATION.cff) / Zenodo DOI.

---

**Repo setup checklist** (when spun into its own `awesome-computational-mythology` repo, per
`proposals/go-to-market.md`): Awesome badge + pass `awesome-lint`; GitHub topics (`awesome`,
`awesome-list`, `computational-folkloristics`, `digital-humanities`, `folklore`, `mythology`,
`nlp`); repo description + social-preview image; `contributing.md`, `code-of-conduct.md`, PR +
"Suggest a resource" issue templates; CI dead-link check (`lychee`/`awesome_bot`) + `awesome-lint`;
`CITATION.cff` + Zenodo DOI; then submit to `sindresorhus/awesome`.
