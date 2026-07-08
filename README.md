# Toward a Computational Framework for Comparative Mythology

**MythoScope** is a computational framework for comparative mythology. It builds a
corpus of myth and folklore texts, embeds them, and turns the result into an
explorable **semantic space** — with character / place / time **graphs** extracted
per text by LLMs, a **geographic** view, and full-text **search by meaning**.
Alongside this unsupervised layer it assembles a **motif database** that integrates
the three traditional folklore indexes — Thompson (TMI), Aarne–Thompson–Uther (ATU)
and Berezkin's areal catalogue — into one cross-linked, browsable whole, with an
automatic **cross-walk** between them and lexical/semantic **parallel-finding** on
top. Everything is served through one web UI; the long-term aim is to relate what
the embeddings surface to the traditional indexes and expose cross-cultural motif
parallels at scale.

### Documentation

- **[How to](docs/how_to.md)** — setup, CLI, and the end-to-end pipeline. Start here.
- **[Research context](docs/research/)** — surveys of the field this sits in (computational folkloristics, motif induction).
- **[Motif indexes](docs/motifs/)** — how TMI, ATU and Berezkin are sourced, parsed and cross-linked.
- **[Paper](docs/paper/)** — the working paper draft and bibliography.
- **[Reviews](docs/reviews/)** — point-in-time code audits.
- **[Mockups](mockups/)** — standalone feature prototypes over the motif data.

### Basic Pipeline

1. Download and clean text corpora
2. Build sentence and chunk embeddings
3. Build vector index and retrieval
4. Reduce embeddings dimensions with autoencoder and/or UMAP
5. Display colored semantic space
6. Extract ontology with Wikontic

### Experiments / Roadmap / Backlog

1. Relate unsupervised results to traditional motif indexes
2. Query index by traditional motives and freeform text
3. Research traditional motives operationalization
4. Research traditions proximity / compound metrics and tools
5. Build exploratory UI with clusters visualization, adaptable threshold and freeform proximity / parallels query
6. Make the research UI publicly available online
7. Integrate traditional indexes (ATU, Berezkin?) for interactive research and scaling?
8. Initiate worldwide community corpora & computational methods project?
9. Create and maintain **awesome-computational-mythology**?
10. Try AE / VAE / SAE?
11. Try hierarchical chunking / embeddings?
12. Research narrative and network extraction methods?
13. ...

### Potential Data Sources

1. [Internet Sacred Text Archive](https://sacred-texts.com/index.htm)
2. [The Database of Religious History](https://religiondatabase.org/landing) (including corpora)
3. [Seshat Global History Databank](https://seshatdatabank.info/)
4. [Motif Indexes](https://ctsf.ru/ukazateli)
5. [Re3Data, Ancient Cultures](https://www.re3data.org/search?query=&subjects%5B%5D=111)
6. [eHRAF World Cultures](https://ehrafworldcultures.yale.edu) (proprietary)
7. [Multilingual Folk Tale Database](http://www.mftd.org)
8. [Theoi Project](https://www.theoi.com/Library.html)

### Potential Future Colabs & Benchmarks

1. [DeepMind, Aeneas / Ithaca](https://predictingthepast.com)
2. [Max Planck Evo Anthro](https://www.eva.mpg.de/linguistic-and-cultural-evolution/index/)
3. [Oxford - Institute of Cognitive & Evolutionary Anthropology](https://www.anthro.ox.ac.uk/cognitive-evolutionary-anthropology-0) (Harvey Whitehouse)
4. Cambridge - DH / CST bridge: [CDH](https://www.cdh.cam.ac.uk), [CST](https://www.cst.cam.ac.uk)
5. [Durham University - Cultural evolution & folklore tradition](https://www.durham.ac.uk/research/institutes-and-centres/cultural-evolution/) (Jamshid Tehrani)
6. [Stanford - Literary Lab](https://litlab.stanford.edu) (Franco Moretti)
7. [Ecole Normale Superieure / CNRS - Structural mythology tradition](https://college-de-france.academia.edu/JuliendHuy) (Julien d'Huy)
8. [IACM](https://www.compmyth.org) (Michael Witzel - Harvard, Natalya Yanchevskaya - Princeton, Steve Farmer)
9. [Лаборатория Ненужных Вещей](https://7seminarov.com) (Брагинская, Александрова, Чегодаев, Березкин и др.)

### Potential Submission Targets

1. Journal/Conference: [Computational Humanities Research (CHR)](https://computational-humanities-research.org/)
2. Journal: [Digital Scholarship in the Humanities (DSH)](https://academic.oup.com/dsh)
3. Journal: [Cultural Analytics (CA)](https://culturalanalytics.org/)
4. Journal/Conference: [Computational Literary Studies (JCLS)](https://jcls.io)
5. Journal/Conference: [International Association for Comparative Mythology (IACM)](https://www.compmyth.org/conferences/)
6. Journal: [Digital Humanities Quarterly (DHQ)](https://dhq.digitalhumanities.org)
7. Workshop: [ACL Natural Language Processing for Digital Humanities (NLP4DH)](https://www.nlp4dh.com)
8. Workshop: [ACL SIG on Humanities (SIGHUM)](https://sighum.wordpress.com)
9. Workshop: [Digital Methods For Mythological Research (dm4myth)](https://dm4myth.github.io)
