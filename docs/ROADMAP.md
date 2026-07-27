# Roadmap & backlog

Working notes on where Mythoscope is headed — experiments, candidate data sources, potential
collaborations, and submission targets. Moved out of the README to keep the front page
reader-first; this is a living, internal-facing list, not a commitment.

## Experiments / roadmap / backlog

1. Relate unsupervised results to traditional motif indexes
2. Query index by traditional motives and freeform text
3. Research traditional motives operationalization
4. Research traditions proximity / compound metrics and tools
5. Build exploratory UI with clusters visualization, adaptable threshold and freeform proximity / parallels query
6. Make the research UI publicly available online
7. Integrate traditional indexes (ATU, Berezkin?) for interactive research and scaling?
8. Initiate worldwide community corpora & computational methods project?
9. Create and maintain **awesome-computational-mythology**
10. Try AE / VAE / SAE?
11. Try hierarchical chunking / embeddings?
12. Research narrative and network extraction methods?
13. Benchmark narrative-similarity embedders on our tasks — take the top systems from **SemEval-2026 Task 4 (Narrative Story Similarity)**, **Qwen3-Embedding** with story-similarity instruction variants, and **`uhhlt/story-emb`**; build embeddings and measure whether they work better for our motif/tradition tasks than the current general embedders
14. Try hierarchical aggregation of chunks — summaries and graphs of characters, epochs and locations — so large texts that don't fit in context still yield an overview-level result (~50–100 key entities, not every entity): extract per chunk (map), then consolidate globally with either an LLM dedup/reduce pass over the candidate list (merge aliases, pick the central ones) or ranking by graph degree centrality
15. Try graph extraction over large context-filling chunks (instead of the current small ~4k-char chunks) — fewer, longer chunks give the model more global salience per call and cut the alias/duplication inflation from over-segmentation; compare quality and cost against the per-chunk approach
16. Try ABTT (All-But-The-Top) embedding post-processing — subtract the common mean and top principal component(s), then renormalize. Our embeddings are strongly anisotropic (measured common-component ‖μ‖ ≈ 0.62–0.89; random-pair cosine 0.39–0.79, e5-large near-degenerate), so a large constant offset inflates every similarity. Expect it to de-hub neighbor lists and, most concretely, make absolute cosine thresholds (e.g. the motif semantic-parallels gate) meaningful; fit μ/PCs once per collection and apply the same transform to stored vectors and queries. Build it as a sibling collection so the raw variant stays for A/B
17. …

## Potential data sources

1. [Internet Sacred Text Archive](https://sacred-texts.com/index.htm)
2. [The Database of Religious History](https://religiondatabase.org/landing) (including corpora)
3. [Seshat Global History Databank](https://seshatdatabank.info/)
4. [Motif Indexes](https://ctsf.ru/ukazateli)
5. [Re3Data, Ancient Cultures](https://www.re3data.org/search?query=&subjects%5B%5D=111)
6. [eHRAF World Cultures](https://ehrafworldcultures.yale.edu) (proprietary)
7. [Multilingual Folk Tale Database](http://www.mftd.org)
8. [Theoi Project](https://www.theoi.com/Library.html)

## Potential future collaborations & benchmarks

1. [DeepMind, Aeneas / Ithaca](https://predictingthepast.com)
2. [Max Planck Evo Anthro](https://www.eva.mpg.de/linguistic-and-cultural-evolution/index/)
3. [Oxford - Institute of Cognitive & Evolutionary Anthropology](https://www.anthro.ox.ac.uk/cognitive-evolutionary-anthropology-0) (Harvey Whitehouse)
4. Cambridge - DH / CST bridge: [CDH](https://www.cdh.cam.ac.uk), [CST](https://www.cst.cam.ac.uk)
5. [Durham University - Cultural evolution & folklore tradition](https://www.durham.ac.uk/research/institutes-and-centres/cultural-evolution/) (Jamshid Tehrani)
6. [Stanford - Literary Lab](https://litlab.stanford.edu) (Franco Moretti)
7. [Ecole Normale Superieure / CNRS - Structural mythology tradition](https://college-de-france.academia.edu/JuliendHuy) (Julien d'Huy)
8. [IACM](https://www.compmyth.org) (Michael Witzel - Harvard, Natalya Yanchevskaya - Princeton, Steve Farmer)
9. [Лаборатория Ненужных Вещей](https://7seminarov.com) (Брагинская, Александрова, Чегодаев, Березкин и др.)

## Potential submission targets

1. Journal/Conference: [Computational Humanities Research (CHR)](https://computational-humanities-research.org/)
2. Journal: [Digital Scholarship in the Humanities (DSH)](https://academic.oup.com/dsh)
3. Journal: [Cultural Analytics (CA)](https://culturalanalytics.org/)
4. Journal/Conference: [Computational Literary Studies (JCLS)](https://jcls.io)
5. Journal/Conference: [International Association for Comparative Mythology (IACM)](https://www.compmyth.org/conferences/)
6. Journal: [Digital Humanities Quarterly (DHQ)](https://dhq.digitalhumanities.org)
7. Workshop: [ACL Natural Language Processing for Digital Humanities (NLP4DH)](https://www.nlp4dh.com)
8. Workshop: [ACL SIG on Humanities (SIGHUM)](https://sighum.wordpress.com)
9. Workshop: [Digital Methods For Mythological Research (dm4myth)](https://dm4myth.github.io)

## Original "Basic Pipeline" sketch (preserved from the README)

1. Download and clean text corpora
2. Build sentence and chunk embeddings
3. Build vector index and retrieval
4. Reduce embeddings dimensions with autoencoder and/or UMAP
5. Display colored semantic space
6. Extract ontology with Wikontic
