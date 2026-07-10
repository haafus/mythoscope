# Further reading — an annotated orientation

> **What this is.** A *curated, annotated* entry into the canon behind the programme — each work with
> a short "why it matters / where it feeds in." It is **not** the works-cited list: precise citations
> (author, year, venue) live in the reference sections of the four series papers and in
> [`../research/`](../research/). At monograph-assembly time a single deduplicated `references.md` is
> generated from those lists; this file becomes the book's *Further reading* appendix. Earlier
> citation errors have been corrected and the reading list extended to the programme's actual working
> canon (distributional/phylogenetic methods, the curated indices, the external joins).

## I. Foundations — structure of myth and formalisation

**Claude Lévi-Strauss** — *The Structural Study of Myth* (1955); *Mythologiques* (1964–71).
Myth as a system of relations; motifs as elements of structure. The conceptual zero-point: motif-level
retrieval and graph approaches are its heirs.

**Vladimir Propp** — *Morphology of the Folktale* (1928; Eng. 1968). Formal narrative description;
functions as atoms of structure. Feeds narrative graphs, event extraction, sequence modelling — and
the "narrative form" axis of the re-derived theme taxonomy.

**Stith Thompson** — *Motif-Index of Folk-Literature*, 6 vols (**1955–58**; 1st ed. 1932–36). The
first motif ontology, still used as a reference vocabulary. *(Corrects the earlier "1932–1958".)*

**Hans-Jörg Uther** — *The Types of International Folktales* (ATU, 2004, FFC 284–286). The tale-type
index; the "narrative form" logic the data-driven taxonomy turned out to resemble.

**Yuri Berezkin** — *The Analytical Catalogue of World Mythology and Folklore*; "Folklore and mythology
catalogue" (*RMN Newsletter* 10, 2015). The areal catalogue that is the project's primary substrate;
his own method — *analyse the corpus in parts, by thematic group, not as one pool* — is a load-bearing
methodological choice.

**Alan Dundes** — *Structural Forms of Folklore*; "The Motif-Index and the Tale Type Index: A Critique"
(1997). Structure ↔ culture, and the standard critique of the indices (Eurocentric, overlapping) —
required caution when reading any index-derived result.

**Jonathan Z. Smith** — *Imagining Religion*; *Map Is Not Territory*. What it *means* to compare;
guards against naïve similarity — the right frame for interpreting embedding clusters.

## II. Evolutionary and quantitative mythology

**Jamshid Tehrani** — "The Phylogeny of Little Red Riding Hood" (***PLoS ONE* 8(11), 2013**).
**Sara Graça da Silva & Jamshid Tehrani** — "Comparative phylogenetic analyses… Indo-European
folktales" (***Royal Society Open Science* 3, 2016**). Tales carry phylogenetic signal within a
language family; only a handful reconstruct deep. Directly recovered by our Method B (the ~1% broad +
clade-clustered Eurasian märchen). *(Corrects the earlier single "Tehrani et al., Science 2013",
which is not a real citation.)*

**Julien d'Huy** — reconstructions of the Cosmic Hunt and Polyphemus (2013); "Reconstructing Paleolithic
mythology" (*Studia Mythologica Slavica* 18, 2015). Phylogenetic deep-time reconstruction — the
Pleistocene-substrate hypothesis our deep both-hemisphere class engages under sampling controls.

**Thuillard, d'Huy, Le Quellec & Berezkin** — "A Large-Scale Study of World Myths" (*Trames* 22(4),
2018). Phylogenetic networks over Berezkin's catalogue — the closest prior at the same scale.

**Raoul Naroll** — "Two Solutions to Galton's Problem" (*Philosophy of Science* 28, 1961). Spatial
autocorrelation as the foundational confound; the reason our subsistence×theme result is
restricted-permutation controlled.

**Methods borrowed from biology/statistics** — Fitch (1971, parsimony ASR); Pagel (1994, Mk correlated
evolution); Mantel (1967, matrix regression / permutation). The machinery of Method B and the
facet-adequacy tests.

## III. Systematics, de-confounding, dimensionality reduction (the working method)

**BGE-M3** (Chen et al. 2024) — the multilingual motif embedding. **UMAP** (McInnes et al. 2018) —
the reduction under the theme re-derivation. Degree-corrected block models and Poisson factorization
(Karrer & Newman 2011; Gopalan et al. 2015) — the de-confounding of catalogue sampling that separates
signal from coverage. These are the tools the findings actually stand on.

## IV. Computational folkloristics — indices, retrieval, motif detection

**MOMFER** (Karsdorp, van der Meulen, Meder & van den Bosch, *Folklore* 126:1, 2015) — WordNet-semantic
search over the TMI; the direct precedent for semantic (not string) motif search.
**Tangherlini & Chen** — "Travels with BERT" (*Orbis Litterarum* 79, 2024) — the embeddings→UMAP→HDBSCAN
clustering template. **GOLEM** (Yarlott et al., LREC-COLING 2024) and Yarlott & Finlayson (2016) — the
motif-detection frontier and how hard it is (the honest baseline for Track 2, induction from text).
**Declerck & Lendvai** (2011→) — TMI/ATU as Linked Open Data. Karsdorp & van den Bosch (2013) — motifs
as topics, the induction origin point.

## V. Narrative networks and graph-based mythology

**Franco Moretti** — *Graphs, Maps, Trees*; *Distant Reading*. Literature as network/graph — the
distant-reading stance, and background for the knowledge-graph tooling (a support layer, not the
central result).
**Mac Carron & Kenna** — "Universal Properties of Mythological Networks" (*EPL* 99, 2012). Character
networks of epics — the network view as a cheap, interpretable complement.
**Mark Finlayson** — "Inferring Propp's Functions…" (*JAF* 129, 2016); Analogical Story Merging. The
state of the art in learning narrative structure — and the negative results that bound it.

## VI. Cognitive science of religion (a *designed*, not-yet-run validation)

**Pascal Boyer** — *Religion Explained* (2001); minimally counterintuitive concepts.
**Harvey Whitehouse** — *Modes of Religiosity* (2004). These offer *proposed* extrinsic tests
(do MCI agents or high-arousal ritual narratives form distinct embedding profiles?) — **listed as a
designed evaluation, not a result**; the validation actually performed to date is distributional and
areal (findings paper). *(Reframed from the earlier over-claim that they already map onto motif
frequency / anomaly detection.)*

## VII. Data and external joins

**D-PLACE / Ethnographic Atlas** (Kirby et al. 2016; Murdock 1967) — the subsistence facet.
**Glottolog** (Hammarström et al. 2023) — language family + expansion dates for calendar dating.
**Historical-basemaps** — pre-colonial political boundaries for the empire-corridor test.
**Seshat: Global History Databank** (Turchin et al.) and **ETCSL** (Oxford, Sumerian corpus) — adjacent
structured/textual resources for future linkage and philological rigour respectively.

## VIII. Method and craft (digital humanities / corpus / NLP)

Underwood, *Distant Horizons* (DH methodology, guards against naïve ML); Grimmer, Roberts & Stewart,
*Text as Data*; Egbert, Biber & Gray, *Designing and Evaluating Language Corpora* (representativeness —
directly relevant to the sampling controls); Hirst, *Embeddings in NLP*; Liu, Lin & Sun, *Representation
Learning for NLP*; Sommerschield et al., "Machine Learning for Ancient Languages: A Survey" (ACL 2023);
Kenna, MacCarron & MacCarron, *Maths Meets Myths*.

## IX. The core dozen (must-know)

Berezkin (catalogue & method) · Thompson (*Motif-Index*) · Uther (ATU) · Lévi-Strauss (*Structural
Study*) · Propp (*Morphology*) · Tehrani (2013) and da Silva & Tehrani (2016, phylogenetics) · d'Huy
(deep-time reconstruction) · Naroll (Galton's problem) · MOMFER / Tangherlini & Chen (retrieval &
clustering) · GOLEM / Finlayson (motif detection) · D-PLACE + Glottolog (the external joins) · UMAP +
BGE-M3 (the representation).
