# Computational Folkloristics and the Induction of Motifs: A Survey

*Computational Comparative Mythology — Paper **I of IV · The Field**. Companions: II The Program · III The Machine · IV The Findings — see [README](README.md).*

*Working survey draft, assembled from the MythoScope research notes
(`docs/research/computational-folkloristics-survey.md`, `…-landscape.md`,
`motif-induction-review.md`, `motif-induction-survey.md`). It reviews others' work; claims that
could not be independently verified in the source notes are flagged as such, and unresolved caveats
are preserved rather than smoothed over.*

---

## Abstract

The computational study of folk narrative and myth has matured from a manual, index-building craft
into a quantitative discipline, but its central object — the *motif* — remains formally unstable, and
its central task — inducing motifs from text — remains unsolved. We survey the field across two eras:
a **classical era** (c. 2008–2018) that digitised and formalised the Aarne–Thompson–Uther and
Thompson indices and built topic-model motif induction, tale phylogenetics, and character-network
analysis; and a **modern era** (2018–2026) dominated by transformer embeddings, BERTopic-style
clustering, and large-language-model annotation. We organise the work by method family — indices and
ontologies; supervised tale-type classification; topic models; embeddings, retrieval and motif
detection; sequence and network mining transferred from other disciplines; evolutionary/phylogenetic
mythology; and narrative-structure (Propp) extraction — catalogue the open datasets and their
licences, and distil the field's hard lessons: motifs resist crisp boundaries, gold-standard
annotation is scarce and culturally contingent, simple TF-IDF/SVM baselines repeatedly match neural
and LLM systems on small corpora, and LLMs remain prone to hallucinated exemplars and to failure on
structural tasks. We conclude that embeddings are best used as a *retrieval and candidate-generation*
layer over a curated, expert index rather than as an end-to-end motif classifier.

## 1. Introduction

Two overlapping fields share this subject. **Computational folkloristics** — a term popularised by
Tangherlini — is the quantitative and NLP study of folk narrative: tale types, motifs, archives,
variation and geography. **Computational (phylogenetic) mythology** treats myths as evolving lineages
of "mythemes" and reconstructs their ancestry and diffusion with tools borrowed from evolutionary
biology. Both rest on the same mid-twentieth-century reference works and both now confront the same
opportunity — dense semantic representations of text — and the same obstacle: the motif is a slippery
unit, and the largest catalogues are Eurocentric, coarse, and "formally fluid" (Dundes 1997). This
survey maps the methods, resources, and unsolved problems, as background for tools that layer modern
retrieval over the classical indices. The best short entry point to the field is Lauer's 2023 *Fabula*
survey; the 2016 *Journal of American Folklore* "Big Folklore" special issue marks the field's
self-recognition.

## 2. What is a "motif"? Six senses of one word

Methodology follows definition, and "motif" hides at least six distinct objects (motif-induction
review, §Key Findings):

1. **Narratological / folkloristic motif** — Thompson's "smallest element in a tale having a power to
   persist in tradition" (Thompson 1977: 415), indexed in the TMI and ATU.
2. **Recurring textual/sequential pattern** — exact repeated substrings, n-grams, text reuse.
3. **Latent topic** — a distribution over words (LDA and its neural successors).
4. **Embedding-space pattern** — a region or cluster in a dense semantic space.
5. **Time-series/bioinformatics motif** — a recurring subsequence (matrix profile, SAX), transferable
   to token streams.
6. **Network motif** — a recurrent subgraph in a co-occurrence or character graph.

The GOLEM corpus (Yarlott et al. 2024) sharpens sense (1) operationally by annotating not the abstract
motif but its *use* in text, in four classes (Motific / Referential / Eponymic / Unrelated). The
practical consequence: a system's evaluation is only meaningful once its sense of "motif" is fixed.

## 3. Indices and ontologies: the substrate

Almost all computational folkloristics is scaffolded on two reference works. The **Thompson
Motif-Index** (Thompson 1955–58) codes ~46,000 narrative elements alphanumerically in 23 lettered
classes (A Mythology, B Animals, C Tabu, D Magic, …). The **Aarne–Thompson–Uther** type index (Uther
2004) — the fifth revision of Aarne's 1910 index — enumerates ~2,500 international tale types in three
ranges (Animal Tales, Ordinary Folktales, Jokes & Formula Tales) and indexes over 2,000 tales across
200+ societies. **Berezkin's** areal catalogue is a third, mythology-oriented scheme with an episode/
image definition of "motif" and systematic areal distributions. All three are criticised as
Eurocentric and coarse (Dundes 1997; Jason 2006).

Digital re-use began with **MOMFER** (Karsdorp, van der Meulen, Meder & van den Bosch 2015), a search
engine over the TMI that adds WordNet-based semantic query expansion — the single most direct
precedent for semantic (not string) search over a motif index. **Declerck** and colleagues (Declerck
& Lendvai 2011 onward) converted TMI/ATU into multilingual OWL/RDF(S)/SKOS with a Proppian-function
ontology; *caveat:* the source notes could not verify any public RDF file or SPARQL endpoint for this
line, so it may require contacting DFKI directly. For a single mythology, the **Ontology of Greek
Mythology** (Pastor-Sánchez et al. 2021, built from 5,377 Wikidata items and explicitly representing
contradictions) and **Digital LIMC** provide RDF knowledge graphs.

## 4. Supervised classification of tale types and motifs

Learning-to-rank and classifiers assign ATU types to tales: Meder et al. (2016) on the Dutch Folktale
Database; Eklund, Hagedorn & Darányi (2023) with an SVM over TF-IDF on the ten best-populated classes
of the Annotated Folktales collection (F ≈ 0.8–1.0, no baseline reported); Meaney, Alex & Lamb (2024)
comparing mBERT/XLM-R/gaBERT against an SVM for Gaelic. The **recurring lesson** across Eklund (2023),
Meaney (2024) and Lô et al. (2020, where a bag-of-words MLP beat an LSTM on West-African tales) is
that **non-contextual baselines repeatedly rival or beat neural/LLM approaches on small folktale
corpora** — a warning that shapes any honest evaluation design.

## 5. Topic models to BERTopic

Karsdorp & van den Bosch (2013) originated motif induction as latent-topic discovery (LDA; Blei et
al. 2003), treating motifs as word distributions with a TF-IDF baseline. The neural successor —
**BERTopic** (Grootendorst 2022: embeddings → UMAP → HDBSCAN → class-based TF-IDF) — was applied by
**Tangherlini & Chen (2024)** with a fine-tuned nineteenth-century Danish embedding model to map
intertextuality across Andersen's tales and travel writing, with KeyBERT labelling and outlier
reduction. This embeddings→UMAP→HDBSCAN→c-TF-IDF pattern is now the field's default clustering recipe.

## 6. Embeddings, retrieval, and motif detection

Dense embeddings enable cross-lingual similarity and candidate generation. Karsdorp & Fonteyn (2019)
showed cultural entrenchment of tales is encoded in language; Karsdorp et al. (2015) found word2vec
alone near-optimal for animacy detection with interpretable semantic maps. For *detection* proper,
Yarlott & Finlayson (2016) proposed a formal motif model, and "Finding Trolls Under Bridges" (Yarlott
et al. 2022) built a prototype detector whose off-the-shelf metaphor feature reached only F1 ≈ 0.35 —
illustrating how hard the task is. The key modern resource is **GOLEM** (Yarlott et al. 2024): 7,955
articles, 26,078 motif candidates over 34 types across three cultural groups, annotated for use-type
(Fleiss κ > 0.55); few-shot classification of use-type peaked at only 41%. **MIME** (Acharya et al.
2024) extracts a motif's implicit meaning and concludes that explicit information from culture-bearers
is critical. On the LLM frontier, **Arčon et al. (2025)** used GPT-4.5 zero-shot motif-presence checks
on Cinderella (ATU 510A) plus LaBSE + HDBSCAN, cross-lingually; and the best published narrative-motif
detector to date is a **fine-tuned Llama-3 reaching ≈0.85 F1 on the *Arabian Nights*** (Alyami &
Finlayson 2026, per the review). The honest state of the art: LLMs work for *presence checks against a
known checklist* but are not validated for open-vocabulary motif discovery, and remain prone to
hallucinated exemplars.

## 7. Sequence and network mining, transferred

Two mature toolkits arrive from adjacent disciplines. **Pattern/sequence mining** — suffix structures
(Ukkonen 1995), sequential pattern mining (GSP, SPADE, PrefixSpan), and association measures — yields
surface, exact, reproducible patterns without semantics; Darányi's "narrative DNA" and Ofek et al.
(2013) learned tale types from motif *sequences*. **Time-series transfer** — the Matrix Profile (Yeh
et al. 2016) and SAX (Lin et al. 2003), the latter designed to bring text algorithms to series and
thus reversible onto token streams. **Network motifs** — mfinder (Milo et al. 2002) and FANMOD —
applied to character and co-occurrence graphs (Elson et al. 2010; survey: Labatut & Bost 2019).

## 8. Evolutionary and phylogenetic mythology

Treating tales as lineages, presence/absence of types or motifs across cultures is coded and run
through Bayesian/parsimony phylogenetics. **da Silva & Tehrani (2016)** coded 275 magic-tale types
across 50 Indo-European populations; after horizontal-transmission controls, 100 patterned by
linguistic relatedness and only ATU 330 "The Smith and the Devil" reconstructed robustly to
Proto-Indo-European. **d'Huy (2013)** reconstructed the Cosmic Hunt and Polyphemus with BEAST/MrBayes/
NeighborNet; **Thuillard, d'Huy, Le Quellec & Berezkin (2018)** built phylogenetic networks over
Berezkin's ~2,264 motifs and 934 peoples; **Sakamoto Martini et al. (2023)** produced a phylomemetic
Cinderella. A striking cross-import is **Kestemont et al. (2022)**, applying ecological unseen-species
estimators to quantify lost medieval narrative diversity. The persistent **bottleneck is the coding
itself** — the presence/absence matrix — which is exactly the induction problem the rest of the field
is trying to automate.

## 9. Narrative structure and Propp-function extraction

The hardest structural task. Finlayson's **Analogical Story Merging** (thesis 2011; *JAF* 2016)
learned a substantive portion of Propp's morphology from 15 deeply-annotated Russian tales (Rand
index 0.511 vs Propp's functions) — "the first demonstration of a system learning a real theory of
narrative structure" — supported by the ProppLearner corpus and the Story Workbench. In sharp
contrast, 2024 attempts to tag Propp functions with LLMs reported **largely negative results**,
confirming that current models do not reliably recover narrative structure zero/few-shot.

## 10. Datasets and resources

| Resource | Scale | Format / access | Licence |
|---|---|---|---|
| **FairytaleQA** | 278 stories, 10,580 QA pairs, 7 narrative-element types | CSV/Parquet (GitHub, HF) | Apache-2.0 (verify raw CSVs) |
| **Annotated Folktales ("trilogy" / aft)** | 1,518 tales, 182 ATU types; `tmi`/`atu`/`aft` frames | R/CSV, Zenodo | **CC-BY-SA 4.0** |
| **GOLEM** | 7,955 articles, 26,078 motif candidates, 34 types, use-type labels | annotated corpus (LREC-COLING 2024) | per publication |
| **Dutch Folktale DB (Verhalenbank)** | 100,000+ ATU/TMI-typed tales | web; research access | restricted |
| **ISEBEL** | 70,000+ belief legends (NL/FR/DA/DE + Icelandic) | unified search + geoviz; property-graph | publication CC-BY |
| **MFTD** | ATU-tagged multilingual tales | XML, no schema/API | no licence stated |
| **Berezkin catalogue** | ~2,264–2,564 motifs / 934–958 peoples | ruthenia full text; query engine (mythology-queries) | version-dependent |
| **da Silva & Tehrani matrix** | 275 types × 50 populations | supplementary Excel | with paper |
| **Ashliman Folktexts** | ATU-annotated English tales | web | curated |
| **folkloredatabase.com** | 250k+ narratives, 3,494 motifs (claims) | login-gated | **CC-BY-NC-SA; forbids scraping/AI** — not an open source |

**MOMFER** (semantic TMI search) and the OGM SPARQL tool round out the tooling. Licensing discipline
matters: FairytaleQA and the trilogy corpus are safe to build on; folkloredatabase.com explicitly
forbids text/data mining; MFTD has no stated licence; Berezkin is best accessed through its query
engine.

## 11. Evaluation and open problems

- **The unit is unstable.** "Motif" is not formally defined; boundaries overlap; the six senses
  demand different metrics (precision/recall/F1 for classification, AP/nDCG for retrieval, Rand/ARI
  for structure).
- **Gold data is scarce and culturally contingent.** Annotation is expensive and, as MIME argues,
  needs culture-bearers; GOLEM's low use-type accuracy shows even labelling motif *use* is hard.
- **Baselines are stubborn.** TF-IDF/SVM repeatedly match neural/LLM systems on small corpora —
  always ship a baseline; failure to beat it is signal.
- **LLMs hallucinate and destabilise.** They generate phantom exemplars and vary run-to-run; they
  fail on Propp-structure tagging; and aligned models risk "flattening" thematic/affective variation.
- **Eurocentrism** in the indices propagates into every downstream analysis.
- **Coding is the phylogenetic bottleneck.** Evolutionary methods need pre-coded matrices; automating
  that coding is where induction meets phylogenetics.

## 12. People, labs, and venues

**People/labs:** Tangherlini (Berkeley; computational folkloristics, WitchHunter/ISEBEL); the Meertens
Institute group — Karsdorp, Meder, van der Meulen, Nguyen (MOMFER, Dutch Folktale DB); Finlayson (FIU;
motif detection, ProppLearner, GOLEM); the phylogenetic-mythology group — d'Huy, Le Quellec,
Thuillard, Berezkin; Tehrani (Durham) & da Silva; Grossner (GLOS — embeddings + LLM over TMI/ATU +
geography, the nearest architectural neighbour); Declerck (DFKI; LOD ontologies); Lauer (Mainz;
large-scale folktale ML, the 2023 survey); Mac Carron & Kenna (Coventry; network mythology); Kestemont
(Antwerp; unseen-species). **Venues:** *Fabula*, *Journal of American Folklore* (2016 "Big Folklore"),
*Folklore*, *Journal of Open Humanities Data*; *Computational Humanities Research* (CHR), *Journal of
Cultural Analytics*, LaTeCH-CLfL, NLP4DH/LLM4DH, the Workshop on Computational Models of Narrative,
and *Communications of the ACM* (Abello, Broadwell & Tangherlini 2012).

## 13. Synthesis and outlook

The field's trajectory is clear: from hand-built indices, through topic-model and phylogenetic
quantification, to embedding-based retrieval and LLM annotation. Its honest verdict is equally clear —
motif *detection* from raw text is not solved, and the reliable value of modern methods is as a
**semantic retrieval and candidate-generation layer over a curated, expert index**, validated against
strong classical baselines and confirmed by human culture-bearers. The most promising near-term
directions are cross-lingual embedding alignment of the existing indices (upgrading MOMFER's WordNet
expansion to dense retrieval), automating the presence/absence coding that bottlenecks phylogenetics,
and adding cheap, interpretable network and geographic views. A system built on these principles — a
controlled ATU/TMI/Berezkin label space, multilingual embeddings for retrieval, LLMs as
candidate-generators not classifiers, always with a baseline — is the field's current sweet spot.

## References

- Abello, J., Broadwell, P., & Tangherlini, T. R. (2012). Computational folkloristics.
  *Communications of the ACM* 55(7), 60–70.
- Acharya, A., et al. (2024). MIME: discovering implicit meanings of cultural motifs from text.
  *NLP+CSS workshop*, 46–56.
- Alyami, S., & Finlayson, M. A. (2026, preprint per review). Fine-tuned LLM narrative-motif detection
  on the *Arabian Nights* (≈0.85 F1).
- Arčon, I., Robnik-Šikonja, M., & Tratnik, P. (2025). Large language models for folktale type
  automation based on motifs: a Cinderella case study. *arXiv:2510.18561* (*Fabula*).
- Blei, D. M., Ng, A. Y., & Jordan, M. I. (2003). Latent Dirichlet Allocation. *JMLR* 3, 993–1022.
- da Silva, S. G., & Tehrani, J. J. (2016). Comparative phylogenetic analyses uncover the ancient roots
  of Indo-European folktales. *Royal Society Open Science* 3, 150645.
- Declerck, T., & Lendvai, P. (2011). Towards a standardized linguistic annotation of labels in
  knowledge-representation systems. *LREC*.
- d'Huy, J. (2013). A phylogenetic approach to mythology and its archaeological consequences.
  *Rock Art Research* 30(1), 115–118.
- Dundes, A. (1997). The motif-index and the tale type index: a critique. *Journal of Folklore
  Research* 34(3), 195–202.
- Eklund, J., Hagedorn, J., & Darányi, S. (2023). Teaching tale types to a computer. *Fabula* 64(1–2),
  92–106.
- Elson, D. K., Dames, N., & McKeown, K. R. (2010). Extracting social networks from literary fiction.
  *ACL*, 138–147.
- Finlayson, M. A. (2016). Inferring Propp's functions from semantically annotated text. *Journal of
  American Folklore* 129(511), 55–77.
- Grootendorst, M. (2022). BERTopic: neural topic modeling with a class-based TF-IDF procedure.
  *arXiv:2203.05794*.
- Hatzel, H. O., Artemova, E., Stiemer, H., Gius, E., & Biemann, C. (2026). SemEval-2026 Task 4:
  Narrative Story Similarity and Narrative Representation Learning. *SemEval-2026*, 3460–3478.
  https://narrative-similarity-task.github.io
- Karsdorp, F., & van den Bosch, A. (2013). Identifying motifs in folktales using topic models.
  *BENELEARN*.
- Karsdorp, F., & Fonteyn, L. (2019). Cultural entrenchment of folktales is encoded in language.
  *Palgrave Communications* 5, 25.
- Karsdorp, F., van der Meulen, M., Meder, T., & van den Bosch, A. (2015). MOMFER: a search engine of
  Thompson's Motif-Index of Folk Literature. *Folklore* 126(1), 37–52.
- Kestemont, M., Karsdorp, F., et al. (2022). Forgotten books: the application of unseen-species models
  to the survival of culture. *Science* 375(6582), 765–769.
- Labatut, V., & Bost, X. (2019). Extraction and analysis of fictional character networks: a survey.
  *ACM Computing Surveys* 52(5), 89.
- Lauer, G. (2023). Computational folkloristics (survey). *Fabula* 64(1–2).
- Lin, J., Keogh, E., Lonardi, S., & Chiu, B. (2003). A symbolic representation of time series (SAX).
  *DMKD workshop*.
- Lô, G., de Boer, V., & van Aart, C. J. (2020). Exploring West African folk narrative texts using
  machine learning. *Information* 11(5), 236.
- Mac Carron, P., & Kenna, R. (2012). Universal properties of mythological networks. *EPL* 99, 28002.
- Meaney, C., Alex, B., & Lamb, W. (2024). Classification of tale types and narrator gender in Gaelic
  folktales. *NLP4DH*.
- Meder, T., Karsdorp, F., Nguyen, D., Theune, M., Trieschnigg, D., & Muiser, I. (2016). Automatic
  enrichment and classification of folktales in the Dutch Folktale Database. *Journal of American
  Folklore* 129(511), 78–96.
- Milo, R., et al. (2002). Network motifs: simple building blocks of complex networks. *Science*
  298(5594), 824–827.
- Ofek, N., Darányi, S., & Rokach, L. (2013). Motif-based classification of folktale sequences. *CMN*.
- Pastor-Sánchez, J.-A., Kontopoulos, E., Saorín, T., Bebis, H., & Darányi, S. (2021). Ontology of
  Greek Mythology. *Semantic Web Journal*.
- Sakamoto Martini, S., Kendal, J., & Tehrani, J. J. (2023). A phylomemetic analysis of Cinderella.
- Tangherlini, T. R., & Chen, J. (2024). Travels with BERT. *Orbis Litterarum* 79, 519–562.
- Thompson, S. (1955–58). *Motif-Index of Folk-Literature* (6 vols). Indiana University Press.
- Thuillard, M., d'Huy, J., Le Quellec, J.-L., & Berezkin, Yu. E. (2018). A large-scale study of world
  myths. *Trames* 22(4), 407–424.
- Uther, H.-J. (2004). *The Types of International Folktales* (ATU). FF Communications 284–286.
- Yarlott, W. V. H., & Finlayson, M. A. (2016). Learning a better motif index. *CMN*.
- Yarlott, W. V. H., et al. (2022). Finding trolls under bridges. *arXiv:2204.06085* (ACS 2021).
- Yarlott, W. V. H., Acharya, A., Castro Estrada, D., Gomez, D., & Finlayson, M. A. (2024). GOLEM: a
  corpus of cultural motifs. *LREC-COLING*, 7801–7813.
- Yeh, C.-C. M., et al. (2016). Matrix profile I: all pairs similarity joins for time series. *ICDM*.
