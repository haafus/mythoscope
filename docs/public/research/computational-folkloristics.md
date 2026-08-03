---
title: "Computational folkloristics: a field survey"
description: "A specialist survey of computational folkloristics and computational mythology — the two eras of the field, its core methods, and the landmark work behind each."
url: /research/computational-folkloristics
tier: B
---

# Computational folkloristics: the two eras of a quiet field

Computational folkloristics is the quantitative and computational study of folk
narrative — tale types, motifs, archives, variation, and the geography of their spread.
The term was popularised by Timothy Tangherlini, and the programme was set out most
sharply in Abello, Broadwell & Tangherlini's 2012 *Communications of the ACM* paper of the
same name: folklore treated as data, at the scale of whole archives rather than single
texts. Alongside it runs a second, partly overlapping tradition — **computational or
statistical mythology** — which treats myths as evolving lineages of "mythemes" and
reconstructs their ancestry and diffusion with tools borrowed from evolutionary biology.

This page surveys both. It is organised around the field's own periodisation into two eras,
then walks through the methods that define it and the landmark work behind each. A
companion page maps [the people, labs, journals, and conferences](landscape.md) that carry
the work; two further pages cover [where the corpora come from](corpus-sourcing.md) and
[how the great encyclopedias carve the world](encyclopedias.md). For how these ideas are
assembled into a working tool, see [How it works](../how-it-works.md).

## Two eras

The field splits cleanly into two periods.

The **classical era (roughly 2008–2018)** was built on digitising and formalising the two
great mid-twentieth-century reference works — the Aarne–Thompson–Uther tale-type index
(ATU) and the Thompson *Motif-Index of Folk-Literature* (TMI) — and on a first generation
of quantitative methods layered over them: topic-model motif detection (Karsdorp, Meder),
geo-semantic exploration of archives (Tangherlini's WitchHunter), phylogenetics of tales
and myths (Tehrani, d'Huy, Berezkin), and character-network analysis (Mac Carron & Kenna).

The **modern era (2018–2026)** is dominated by transformer embeddings, BERTopic, and
LLM-based motif and type annotation. The methods changed; the substrate did not. Almost all
of the modern work still scaffolds itself on ATU and TMI, and the honest state of the art is
that automatic motif detection remains an open problem — a point returned to at the close.

## The indices are the substrate

Nearly all of computational folkloristics rests on two reference works, plus a third
oriented toward mythology.

The **ATU tale-type index** — Hans-Jörg Uther, *The Types of International Folktales*
(2004, FF Communications 284–286, three volumes) — is the third iteration and fifth
revision of the type index first published by Antti Aarne in 1910. Uther added more than two
hundred and fifty new types over the 1961 Aarne–Thompson index; da Silva & Tehrani describe
it as indexing over 2,000 fairy tales distributed among more than 200 societies.

Stith Thompson's **Motif-Index of Folk-Literature** (1955–58) codes tens of thousands of
narrative elements alphanumerically across classes A–Z. Its unit — the *motif* — is
smaller and more portable than the tale type, and correspondingly harder to pin down.

**Yuri Berezkin's *Analytical Catalogue of World Mythology and Folklore*** is a third,
mythology-oriented scheme with a different (episode/image) definition of "motif" and a
strong areal, distributional emphasis.

These indices give a stable, expert-curated label space and a dense web of cross-cultural
cross-references. They are also widely criticised — as Eurocentric (Dundes 1997; Jason
2006), coarse, and *formally fluid*: motifs overlap, resist crisp boundaries, and, in
Dundes's sharp phrasing, more than half of tale types are effectively a single motif.
Berezkin's incompatible definition of "motif" makes cross-scheme alignment non-trivial. The
carving problem is treated at length in [how the encyclopedias carve the world](encyclopedias.md).

### Ontologies over the indices

A sustained line of work has tried to turn these flat indices into interoperable knowledge.

- **MOMFER** (Karsdorp, van der Meulen, Meder & van den Bosch, *Folklore* 126:1, 2015) is a
  search engine over the TMI that adds **WordNet-based semantic query expansion** — a query
  like `wn:monster` retrieves motifs for dragons, serpents, griffins, werewolves,
  chimeras, and unicorns scattered across TMI subheadings, and extracts each motif's
  attested geographical locations. It is the clearest early precedent for semantic, rather
  than string-based, search over a motif index.
- **Thierry Declerck's ontologies** (DFKI/Saarland) convert TMI and ATU into OWL/RDF(S)/SKOS
  with multilingual labels via the *lemon* model, plus a Proppian-function ontology
  (Declerck & Lendvai 2011; Koleva, Declerck & Krieger 2012; Declerck et al. 2017). The ATU
  ontology comprised 2,802 classes across seven main subclasses matching Uther's hierarchy.
  A caveat for reusers: despite the extensive publication record, no publicly downloadable
  RDF/OWL file or SPARQL endpoint for these ontologies could be verified.
- **The Ontology of Greek Mythology (OGM)** (Pastor-Sánchez et al., *Semantic Web Journal*,
  2021) was built from 5,377 Wikidata items using 34 selected properties, and explicitly
  represents *contradictions* between statements alongside a SPARQL retrieval tool. The
  **Digital LIMC** RDF knowledge graph is a complementary resource (~3,000 figures on
  ~56,000 objects, 40,500 images, 21.6M triples), with FactGrid/Roscher's Lexikon LOD
  project an emerging CC-0 mythology hub.

## Core methods

### Supervised classification of types and motifs

The first practical task is assigning tales to ATU types. Meder, Karsdorp, Nguyen, Theune,
Trieschnigg & Muiser (2016) applied learning-to-rank to story-type classification in the
Dutch Folktale Database. Eklund, Hagedorn & Darányi (2023, *Fabula* 64:1–2) trained an SVM
with TF-IDF over the ten best-populated classes of the Annotated Folktales collection
(1,518 texts, 182 ATU types), reporting F-scores around 0.8–1.0 (no baseline given). Meaney,
Alex & Lamb (2024, NLP4DH) tackled ATU classification and narrator-gender prediction for
Irish and Scottish Gaelic, pitting mBERT/XLM-R/gaBERT against an SVM baseline that remained
competitive.

The recurring finding is consequential: on small, stylistically homogeneous folktale
corpora, non-contextual baselines (SVM + TF-IDF) repeatedly rival or beat neural and LLM
approaches. Lô, de Boer & van Aart (2020), working on a corpus of 742 West African and
Western European tales, likewise found a bag-of-words MLP beating an LSTM. Small-data
caution is a structural feature of the field, not an incidental result.

### Topic modelling: LDA to BERTopic

Karsdorp & van den Bosch (2013, "Identifying Motifs in Folktales Using Topic Models") set
the pattern of treating motifs as latent topics. That approach has now been largely
superseded by **BERTopic** — embeddings, UMAP dimensionality reduction, HDBSCAN clustering,
and class-based TF-IDF for cluster labelling. Tangherlini & Chen (2024, "Travels with
BERT," *Orbis Litterarum* 79:519–562) applied it with a fine-tuned nineteenth-century
Danish embedding model, plus KeyBERT labelling and outlier reduction, to map intertextuality
across Hans Christian Andersen's fairy tales and travel writing — a strong template for
interpretable motif-cluster pipelines.

### Embedding and similarity retrieval

The modern era's signature is dense retrieval. Arčon, Robnik-Šikonja & Tratnik (2025, "Large
language models for folktale type automation based on motifs: Cinderella case study")
combined GPT-4.5 zero-shot motif-presence judgements over ATU 510A with **LaBSE embeddings +
HDBSCAN** for cross-lingual (English + Slovene) semantic similarity across Cinderella
variants. Karsdorp & Fonteyn (2019, "Cultural entrenchment of folktales is encoded in
language," *Palgrave Communications*) and Karsdorp et al. (2015, "Animacy Detection in
Stories") showed that even word2vec/skip-gram embeddings achieve near-optimal animacy
detection and produce interpretable semantic maps of characters, including a distinct
"Supernatural" cluster.

The ceiling is real, however. Yarlott et al. (2021, "Finding Trolls Under Bridges") built a
dedicated motif *detector* whose best off-the-shelf feature reached only F1 ≈ 0.35 on
motifs and a macro-average F1 ≈ 0.21 across four categories — a sobering measure of how hard
open motif detection remains. Hatzel & Biemann (2024, "Story Embeddings") argue that genuine
narrative similarity requires modelling structure beyond keyword or sentence overlap,
setting an upper bound on what similarity search alone can recover.

### Phylogenetic and evolutionary methods

The statistical-mythology strand codes presence/absence of tale types or motifs across
cultures and runs Bayesian or parsimony phylogenetics over the resulting matrices.

- **da Silva & Tehrani (2016)**, "Comparative phylogenetic analyses uncover the ancient
  roots of Indo-European folktales" (*Royal Society Open Science* 3:150645), coded the
  presence/absence of 275 Magic Tale types across 50 Indo-European-speaking populations.
  After two horizontal-transmission tests, 199 tales were discarded, 100 patterned by
  linguistic relatedness, and only ATU 330, "The Smith and the Devil," reconstructed
  robustly to Proto-Indo-European.
- **d'Huy** produced phylogenetic reconstructions of the Cosmic Hunt and of Polyphemus (ATU
  1137), using BEAST, MrBayes, and NeighborNet.
- **Thuillard, d'Huy, Le Quellec & Berezkin (2018)**, "A Large-Scale Study of World Myths"
  (*Trames* 22(4)), ran phylogenetic networks over Berezkin's roughly 2,264 motifs across
  934 peoples.
- **Sakamoto Martini, Kendal & Tehrani (2023)** carried out a phylomemetic Cinderella study
  (ATU 510/511) over 266 versions, with Bayesian inference and NeighborNet.
- **Kestemont, Karsdorp et al. (2022)**, "Forgotten books" (*Science* 375(6582):765–769),
  imported unseen-species (ecology) estimators to model lost medieval narrative diversity —
  a striking cross-disciplinary transfer.

The binding constraint across this strand is that the methods require pre-coded
presence/absence matrices; the coding itself is the bottleneck, and results can be sensitive
to it (as the survival of only ATU 330 through da Silva & Tehrani's controls illustrates).

### Network analysis

Network methods operate at two scales. *Within* a narrative, character-interaction networks
are compared against real and fictional social networks: Mac Carron & Kenna (2012,
"Universal Properties of Mythological Networks," *EPL* 99:28002) analysed the Iliad,
Beowulf, and Táin Bó Cúailnge against controls including *Les Misérables*, *Richard III*,
and *The Fellowship of the Ring*. The Iliad's network was most similar to a real social
network; Beowulf sat between reality and fiction (small-world but disassortative, becoming
assortative once the protagonist is removed); and the Táin was "most fictitious," its
artificiality traceable to six highly-connected characters hypothesised to be amalgams.
Follow-ons include the Odyssey network (*PLoS ONE* 2018), the Kyiv *bylyny* cycle, and
Icelandic sagas.

*Across* a corpus, motif and tale-type networks map the relations among stories themselves —
Abello, Broadwell & Tangherlini's "folklore hairball" work over the 30,000-plus story Evald
Tang Kristensen Danish corpus ("Computational Folkloristics," 2012; "Disentangling the
Folklore Hairball," 2023).

### Narrative structure and Propp functions

Extracting Propp's morphological functions is the hardest structural task in the field. Mark
Finlayson's Analogical Story Merging (2009/2012 MIT thesis; *Journal of American Folklore*
2016) used Bayesian model-merging over fifteen deeply annotated Proppian tales to recover
functions including villainy/lack, struggle/victory, and reward with high accuracy, backed
by the **ProppLearner** corpus and the Story Workbench. Pannach's ProppOntology (2019)
extended an ontology-driven Proppian system to southern African tales. Notably, a 2024
attempt to tag Propp functions with LLMs ("Tagging Narrative with Propp's Character
Functions Using LLMs," CEUR Vol-3671) reported explicitly *negative* results — LLMs do not
yet reliably label Propp functions zero- or few-shot.

### LLM annotation frontiers

LLM zero-shot motif-presence detection works for well-defined motif checklists against a
*known* type (Arčon et al. 2025) but has not been validated for open-vocabulary motif
discovery. A cross-cutting caution attends the whole strand: narrative "flattening" — the
post-training compression of thematic, affective, and stylistic variation — is a documented
risk when aligned LLM embeddings are used on fiction.

## Open datasets and resources

The field's reusable corpora are few and their licences matter.

- **FairytaleQA** — 278 Project Gutenberg stories, 10,580 QA pairs across seven
  narrative-element types (character, setting, action, feeling, causal relationship, outcome
  resolution, prediction). Apache-2.0 (per the Hugging Face tag; verify the GitHub LICENSE
  for raw CSVs). Xu et al., ACL 2022.
- **Annotated Folktales (aft) / the "trilogy" corpus** — 1,518 tales, 182 ATU types, seeded
  from Ashliman's *Folktexts*; includes `tmi`, `atu`, and `aft` dataframes plus an
  ontologies folder. CC-BY-SA 4.0. Hagedorn & Darányi, *JOHD* 8:16, 2022.
- **Dutch Folktale Database (Verhalenbank)** — ~48,000+ narratives (Meertens Instituut);
  research access.
- **MOMFER** — semantic search over the TMI with WordNet expansion.
- **ISEBEL** — over 70,000 belief legends (Dutch, Frisian, Danish, German, plus ~6,000
  Icelandic) with English-language unified search and geovisualisation over a property-graph
  backend, aggregating the Dutch Folktale DB, the Evald Tang Kristensen collection, and
  WossiDia.
- **Multilingual Folk Tale Database (MFTD)** — ATU-tagged multilingual tales as XML, with no
  published schema and no official API or bulk download.
- **Berezkin's Analytical Catalogue** — Russian full text (roughly 2,564 motifs / 958
  societies in recent snapshots), with a machine-readable query engine
  (`macleginn/mythology-queries`). Counts are version-dependent.
- **da Silva & Tehrani (2016) matrix** — the supplementary Excel presence/absence table (275
  tale types × 50 populations) released with the RSOS paper.
- **Ashliman Folktexts** — a curated, ATU-annotated English tale collection (source for aft).

Licensing is uneven and consequential: FairytaleQA (Apache-2.0) and aft (CC-BY-SA) are safe
to build on; some aggregators explicitly forbid scraping and AI training; MFTD carries no
licence or API. Where counts vary across sources — Berezkin motif totals, corpus sizes —
figures are version-dependent snapshots and should be re-verified against the live source.

## The honest state of the art

Three caveats define the field's real frontier, and they should be read together.

**Motif detection is unsolved.** Motifs are formally fluid; there is no large gold-standard
motif-annotated corpus; the reported successes are on narrow, single-type checklists; and
the best dedicated detector (Yarlott et al.) reached only macro-F1 ≈ 0.21. Embeddings are
best understood as a *retrieval and candidate-generation* layer over a curated index, not a
reliable end-to-end motif classifier.

**Small data dominates.** Folktale corpora are small and stylistically homogeneous.
Overfitting and baseline-beating are recurring problems, and a simple TF-IDF/SVM baseline
is the appropriate control for any neural or LLM claim.

**The index is a lens, not ground truth.** ATU and TMI are Eurocentric and coarse; Berezkin
uses an incompatible motif definition; cross-scheme alignment is genuinely hard. Several
high-profile results (Eklund's baseline-free F-scores; phylogenetic reconstructions
sensitive to coding choices) warrant caution, and a number of tools and datasets — Declerck's
ontologies, some LLM-paper code, ProppLearner distributions — have no verified public
download.

---

*Related reading:* [The field landscape — people, labs, journals,
conferences](landscape.md) · [Where the corpora come from](corpus-sourcing.md) · [How the
encyclopedias carve the world](encyclopedias.md) · [How it works](../how-it-works.md)
