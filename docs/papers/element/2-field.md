# 2 · The field and its unsolved task

*Computational Comparative Mythology: A Natural History of the Motif — Chapter 2 of 10. Draft.*

---

Before the programme of the following chapters can be justified, the reader needs the field it sits in,
and needs it in one sitting rather than as a scattered set of references. This chapter gives it: the
two eras of computational folkloristics, the families of method each produced, and the hard lessons the
field has learned about its own central object. Those lessons are not incidental background. They are
the reason this book takes the shape it does — why it treats a curated index as its substrate rather
than reading motifs from raw text, and why it uses machine representations of meaning as a search tool
rather than as an oracle. (A fuller, field-facing survey is published separately; this chapter is its
compression into the argument of the book.)

Two overlapping fields share the subject. **Computational folkloristics** is the quantitative and
natural-language-processing study of folk narrative — tale types, motifs, archives, variation, and
geography. **Computational, or phylogenetic, mythology** treats myths as evolving lineages and
reconstructs their ancestry and diffusion with tools borrowed from evolutionary biology. Both rest on
the same mid-twentieth-century reference works, both now confront the same opportunity — dense semantic
representations of text — and both run up against the same obstacle: the motif is a slippery unit, and
the largest catalogues are Eurocentric, coarse, and formally fluid. Indeed, "motif" hides at least six
distinct objects — the folkloristic motif of the indices, an exact repeated textual pattern, a latent
topic, a region in an embedding space, a recurring subsequence borrowed from time-series analysis, and
a network subgraph — and a system's evaluation is only meaningful once it fixes which one it means.
This instability of the object is the field's founding difficulty, and it never fully goes away.

## 2.1 The classical era

The first era, roughly 2008 to 2018, digitised and formalised the reference works and built the first
generation of quantitative methods on them. Almost everything is scaffolded on two indices: Thompson's
*Motif-Index*, which codes some 46,000 narrative elements alphanumerically, and the
Aarne–Thompson–Uther type index, which enumerates around 2,500 international tale types; Berezkin's
areal catalogue is a third, mythology-oriented scheme that uniquely records systematic geographic
distributions (Table 2.1). Digital re-use of these began with search: MOMFER put a semantic
query-expansion engine over the Motif-Index, the most direct precedent for meaning-based rather than
string-based search over a motif catalogue, and parallel efforts converted the indices into
machine-readable ontologies.

On this substrate the era built three lines of method. **Supervised classification** learned to assign
tale types to texts. **Topic-model induction** originated with treating motifs as latent word
distributions, the ancestor of every clustering approach since. And **phylogenetic mythology** coded the
presence and absence of types or motifs across cultures and ran the matrix through the machinery of
evolutionary biology — most influentially the demonstration that a substantial fraction of
Indo-European magic tales pattern by linguistic relatedness, with a handful reconstructing to deep
ancestral nodes. This last line is the direct ancestor of Chapter 6's descent analysis, and its
persistent bottleneck is worth naming now because the whole present book is downstream of it: the hard
part of phylogenetic mythology is *the coding itself*, the presence/absence matrix, which is exactly
the motif-induction problem the rest of the field is trying to automate.

## 2.2 The modern era

The second era, from around 2018, is dominated by transformer embeddings and large language models.
The default clustering recipe became embeddings followed by dimensionality reduction, density
clustering, and class-based keyword labelling — the pattern this book itself uses in Chapter 8 to
re-derive the theme axis. Dense multilingual embeddings opened cross-lingual similarity and candidate
generation at a scale the topic-model era could not reach. And large language models arrived promising
open-vocabulary motif detection: check whether a motif is present in a text, or discover motifs
outright.

The modern resources sharpened the task even as the methods advanced. Annotated corpora began to label
not the abstract motif but its *use* in a specific text, distinguishing a genuine motific instance from
a mere reference or an eponym — because that distinction turns out to be where detection actually
succeeds or fails. And the honest state of the art, on the field's own reported numbers, is narrower
than the promise: large language models work well for *presence checks against a known checklist* — the
best published narrative-motif detectors reach high accuracy when told what to look for — but they are
not validated for open-vocabulary motif *discovery*, and they remain prone to hallucinated exemplars,
inventing plausible motifs that are not there. Few-shot use-type classification on the sharpest modern
benchmark peaked around 41%. Detection from scratch remains hard.

## 2.3 The hard lessons

Across both eras the field has learned a small set of lessons that any honest programme has to build
around, and this book builds around all of them.

The first is that **the motif resists crisp boundaries.** It is formally fluid by its nature, and no
computational sharpening has changed that; a system that assumes a clean partition of narrative into
discrete motifs is assuming away the object's defining property. The second is that **gold-standard
annotation is scarce and culturally contingent** — reliable labelled data is expensive, exists for few
traditions, and encodes the annotator's cultural frame, so supervised methods are perpetually
data-starved and skewed toward the well-documented (largely European) corpora. The third is the one the
field keeps rediscovering with some embarrassment: **simple baselines repeatedly match neural and
large-language-model systems** on the small corpora that folklore actually provides. Non-contextual
word-frequency classifiers rival or beat transformers and language models on tale-type classification
again and again, which is a standing warning against mistaking a sophisticated method for a validated
one. And the fourth is that **large language models fail on structural tasks** and hallucinate
exemplars, so their fluent output cannot be trusted without a check against an expert vocabulary.

## 2.4 The verdict: embeddings as a retrieval layer

Taken together, these lessons point to one conclusion, and it is the conclusion this book adopts as a
premise. Machine representations of meaning are genuinely powerful — for search, for cross-lingual
matching, for generating candidates and organising a space — but they are not, on the current evidence,
a replacement for expert judgement about what a motif *is*. The right division of labour is to use
embeddings as a **retrieval and candidate-generation layer over a curated, expert index**, not as an
end-to-end classifier that induces motifs from raw text unaided.

This verdict is why the present book is shaped as it is. It takes the curated indices — Thompson,
Aarne–Thompson–Uther, Berezkin — as given, and analyses the *shape of their distributions*, rather than
staking its results on an unsolved detection problem. Its embeddings are validated as a retrieval layer
(Chapter 4) and used as one (Chapter 8), never as an independent authority on a motif's age or origin.
And the raw-text induction pipeline that would eventually close the loop — reading motifs out of text
and anchoring them to the indices — is described as built infrastructure and staged as future work
(Chapters 4 and 10), precisely because the field's hard lessons say that task is not yet solved.
Placing the book in its field, in other words, is not throat-clearing; it is what licenses the book's
central methodological choice. With the field mapped and its verdict adopted, the next chapter sets out
the programme that turns that choice into a method.
