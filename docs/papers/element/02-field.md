# 2 · The field and its unsolved task

*Computational Comparative Mythology: A Natural History of the Motif — Chapter 2 of 10. Draft.*

---

Before the programme of the following chapters can be justified, the reader needs the field it sits in.
This chapter gives it in full: the two research traditions that share the subject, the instability of
the object they study, the families of method each era produced — with the specific systems and the
numbers they reported — the open datasets and their licences, and the hard lessons the field has learned
about its own central object. Those lessons are the reason this book takes the shape it does: why it
treats a curated index as its substrate rather than reading motifs from raw text, and why it uses machine
representations of meaning as a search tool rather than as an oracle.

Two overlapping fields share the subject. **Computational folkloristics** — the term popularised by
Timothy Tangherlini — is the quantitative and natural-language-processing study of folk narrative: tale
types, motifs, archives, variation, and geography. **Computational, or phylogenetic, mythology** treats
myths as evolving lineages of "mythemes" and reconstructs their ancestry and diffusion with tools
borrowed from evolutionary biology. Both rest on the same mid-twentieth-century reference works, both now
confront the same opportunity — dense semantic representations of text — and both run up against the same
obstacle: the motif is a slippery unit, and the largest catalogues are Eurocentric, coarse, and, in Alan
Dundes's word, "formally fluid."

## 2.1 What is a "motif"? Six senses of one word

Method follows definition, and "motif" hides at least six distinct objects. There is the
**narratological** motif of Thompson — "the smallest element in a tale having a power to persist in
tradition" — indexed in the Motif-Index and the tale-type index. There is the **recurring textual
pattern** — an exact repeated substring, an n-gram, a passage of text reuse. There is the **latent
topic** — a distribution over words, as in topic modelling. There is the **embedding-space pattern** — a
region or cluster in a dense semantic space. There is the **time-series motif** borrowed from
bioinformatics — a recurring subsequence, transferable to a stream of tokens. And there is the **network
motif** — a recurrent subgraph in a co-occurrence or character graph. These are not synonyms; each
demands a different evaluation metric, and a system's results are only interpretable once it has fixed
which sense it means. The sharpest recent work operationalises the first sense by annotating not the
abstract motif but its *use* in a given text — is an occurrence genuinely motific, or merely referential,
or eponymic? — because that distinction is precisely where automatic detection succeeds or fails. This
instability of the object is the field's founding difficulty, and it never fully goes away.

## 2.2 The classical era

The first era, roughly 2008 to 2018, digitised and formalised the reference works and built the first
generation of quantitative methods on them. Almost everything is scaffolded on three indices (Table 2.1):
Thompson's *Motif-Index*, which codes some 46,000 narrative elements alphanumerically in lettered
classes; the Aarne–Thompson–Uther type index, which enumerates around 2,500 international tale types; and
Berezkin's areal catalogue, the one that uniquely records systematic geographic distributions. Digital
re-use began with search: MOMFER put a WordNet-based semantic query-expansion engine over the
Motif-Index — the most direct precedent for meaning-based rather than string-based search over a motif
catalogue — and parallel efforts by Declerck and colleagues converted the indices into machine-readable
ontologies, with a dedicated Ontology of Greek Mythology following for a single tradition.

On this substrate the era built four lines of method. **Supervised classification** learned to assign
tale types to texts: Meder and colleagues on the Dutch Folktale Database, and a recurring
finding — across Eklund's support-vector classifier on the best-populated tale-type classes, Meaney's
comparison of multilingual transformers against a support-vector baseline for Gaelic, and a West-African
study where a bag-of-words model beat a recurrent network — that **non-contextual baselines repeatedly
rival or beat neural systems** on the small corpora folklore actually provides. **Topic-model induction**
began with treating motifs as latent word distributions and matured into the now-standard recipe of
embeddings, dimensionality reduction, density clustering, and keyword labelling, applied for instance to
map intertextuality across Andersen's tales. **Phylogenetic mythology** coded the presence and absence of
types or motifs across cultures and ran the matrix through the machinery of evolutionary biology: da
Silva and Tehrani coded 275 magic-tale types across fifty Indo-European populations and found, after
controls for horizontal transmission, that a hundred patterned by linguistic relatedness while only one —
"The Smith and the Devil" — reconstructed robustly to Proto-Indo-European; d'Huy reconstructed the Cosmic
Hunt and the Polyphemus tale with Bayesian phylogenetics; and a striking cross-import applied ecological
unseen-species estimators to quantify the lost diversity of medieval narrative. **Network analysis**
treated characters and co-occurrences as graphs, importing the machinery of network science to
mythological corpora.

The phylogenetic line is the direct ancestor of Chapter 6's descent analysis, and its persistent
bottleneck is worth naming now, because the whole present book is downstream of it: the hard part of
phylogenetic mythology is *the coding itself*, the presence/absence matrix, which is exactly the
motif-induction problem the rest of the field is trying to automate.

## 2.3 The modern era

The second era, from around 2018, is dominated by transformer embeddings and large language models.
Dense multilingual embeddings opened cross-lingual similarity and candidate generation at a scale the
topic-model era could not reach. And large language models arrived promising open-vocabulary motif
detection — check whether a motif is present in a text, or discover motifs outright.

The modern resources sharpened the task even as the methods advanced. The GOLEM corpus annotates tens of
thousands of motif candidates for their *use*-type at respectable inter-annotator agreement, yet few-shot
classification of that use-type peaked at only about 41% — labelling how a motif is *used* is itself
hard. A study of implicit motif meaning concluded that explicit information from culture-bearers is
critical, not optional. On the large-language-model frontier, one system ran zero-shot motif-presence
checks on Cinderella cross-lingually, and the best published narrative-motif detector to date is a
fine-tuned model reaching roughly 0.85 F1 on the *Arabian Nights*. The honest state of the art is
narrower than the promise: large language models work well for **presence checks against a known
checklist** but are not validated for open-vocabulary motif *discovery*, and they remain prone to
hallucinated exemplars — inventing plausible motifs that are not there — and vary from run to run
(Figure 2.1).

## 2.4 Toolkits transferred from adjacent disciplines

Two mature toolkits arrive from outside folkloristics and are worth noting because they offer surface,
reproducible structure without semantics. **Sequence and pattern mining** — suffix structures, sequential
pattern mining, and the symbolic time-series representations designed to bring text algorithms to
numeric series and thus reversible back onto token streams, together with the matrix-profile family for
finding recurring subsequences — yields exact repeated patterns and has been used to learn tale types
from motif *sequences*. **Network-motif detection**, the search for over-represented subgraphs, has been
applied to character and co-occurrence graphs. Neither captures meaning, but both are cheap,
interpretable, and reproducible, and they sit ready as complementary views.

## 2.5 Narrative structure: the hardest task

Extracting narrative *structure* — Propp's functions, the morphology of the folktale — is the hardest
task in the field. The landmark result learned a substantial portion of Propp's morphology from fifteen
deeply annotated Russian tales by analogical story merging, reaching a Rand index of about 0.51 against
Propp's own functions — described as the first demonstration of a system learning a real theory of
narrative structure, supported by the ProppLearner corpus. In sharp contrast, attempts to tag Propp
functions with large language models have reported largely **negative** results, confirming that current
models do not reliably recover narrative structure with zero or few examples. Structure, unlike surface
similarity, still resists automation.

## 2.6 Datasets and their licences

The field's open resources vary widely in scale, format, and — critically for any release — licence
(Table 2.1). Some are safe to build on: a question-answering corpus of annotated stories under a
permissive licence, and an annotated tale-type "trilogy" corpus under a share-alike Creative-Commons
licence. Others are restricted: the large Dutch Folktale Database is research-access only, one
multilingual tale collection states no licence at all, and one large commercial narrative
database — despite advertising hundreds of thousands of narratives and thousands of motifs — **explicitly
forbids text and data mining and machine-learning use**, and is therefore not an open source however
tempting its scale. Berezkin's catalogue is best accessed through its query engine rather than bulk-
scraped. Licensing discipline is not a footnote here: it determines what a reproducible, openly released
study is permitted to build on, and it is one reason this book leans on the openly reusable indices and
cites every source.

## 2.7 The hard lessons

Across both eras the field has learned a small set of lessons that any honest programme has to build
around, and this book builds around all of them.

The first is that **the motif resists crisp boundaries.** It is formally fluid by nature, and no
computational sharpening has changed that; a system that assumes a clean partition of narrative into
discrete motifs is assuming away the object's defining property. The second is that **gold-standard
annotation is scarce and culturally contingent** — reliable labelled data is expensive, exists for few
traditions, and encodes the annotator's cultural frame, so supervised methods are perpetually
data-starved and skewed toward the well-documented, largely European corpora. The third is that **simple
baselines are stubborn** — non-contextual word-frequency classifiers rival or beat transformers and
language models on small folklore corpora again and again, so a study that does not ship and beat a
baseline has shown nothing. The fourth is that **large language models hallucinate and destabilise** —
they generate phantom exemplars, vary run to run, and fail on structural tasks. To these the field adds
two structural cautions: **Eurocentrism** in the indices propagates into every downstream analysis, and
**the coding bottleneck** — the presence/absence matrix that phylogenetic methods require — is exactly
where induction meets phylogenetics, and exactly what remains unautomated.

## 2.8 The verdict: embeddings as a retrieval layer

Taken together, these lessons point to one conclusion, and it is the conclusion this book adopts as a
premise. Machine representations of meaning are genuinely powerful — for search, for cross-lingual
matching, for generating candidates and organising a space — but they are not, on the current evidence, a
replacement for expert judgement about what a motif *is*. The reliable value of modern methods is as a
**semantic retrieval and candidate-generation layer over a curated, expert index**, validated against
strong classical baselines and confirmed, where meaning is at stake, by human culture-bearers.

This verdict is why the present book is shaped as it is. It takes the curated indices — Thompson,
Aarne–Thompson–Uther, Berezkin — as given, and analyses the *shape of their distributions*, rather than
staking its results on an unsolved detection problem. Its embeddings are validated as a retrieval layer
(Chapter 4) and used as one (Chapter 8), never as an independent authority on a motif's age or origin. And
the raw-text induction pipeline that would eventually close the loop — reading motifs out of text and
anchoring them to the indices, automating precisely the coding that bottlenecks phylogenetics — is
described as built infrastructure and staged as future work (Chapters 4 and 10), because the field's hard
lessons say that task is not yet solved. Placing the book in its field, in other words, is not
throat-clearing; it is what licenses the book's central methodological choice. With the field mapped and
its verdict adopted, the next chapter sets out the programme that turns that choice into a method.
