# 4 · The corpus and the bench

*Computational Comparative Mythology: A Natural History of the Motif — Chapter 4 of 10. Draft.*

---

The programme of Chapter 3 is only as good as the material it runs on. This chapter describes that
material and the machinery that assembles it: how three catalogues built on different principles are
brought into one corpus, how they are linked, how every motif is given a machine-readable
representation of its meaning and that representation is checked rather than trusted, and how the
external data is joined. It is the chapter that lets a reader reuse what we built, and it is also the
chapter in which the book is most careful to say which parts of the machine are delivering results
today and which are built but not yet validated.

That distinction runs through everything below, so it is worth stating plainly at the outset. The
project holds **two layers of data**. The first is a **raw-text corpus** — public-domain myths, epics,
cosmogonies, and scriptures, on the order of a hundred works and several million tokens, spanning the
ancient Near East, the Indo-European and Abrahamic worlds, South, Southeast and East Asia, the
indigenous Americas, Africa, Oceania, and the Arctic. The second is the set of **three curated motif
catalogues** that supply an expert vocabulary and, in one case, coded geographic distributions. The
long-term purpose of the machine is to read motifs *out of* the first layer and anchor them to the
second; but that task is unsolved at scale, so every substantive result in this book runs on the
second layer, where the coding already exists. The raw-text induction pipeline is described here as
built infrastructure and returned to, as an open milestone, in Chapter 10. The reader is never asked
to take its output on faith, because at scale that output does not yet exist.

## 4.1 Three catalogues into one attestation matrix

The three reference works carve the material at different joints. Thompson's *Motif-Index of
Folk-Literature* is a vast subject taxonomy of narrative elements — some tens of thousands of
motifs — organised by what a motif is *about*. The Aarne–Thompson–Uther index catalogues whole *tale
types*, around two and a half thousand of them, rather than the elements within a tale. And Yuri
Berezkin's areal catalogue does something neither of the others attempts: for each of roughly three
and a half thousand motifs it records the **set of ethnographic traditions that carry it**, placing
every motif on a map of about a thousand peoples, each located in a four-level areal hierarchy that
rolls up to twelve macro-areas and tagged with a language chain. Berezkin's catalogue is, for the
purposes of this book, the richest of the three, because it is the only one that encodes distribution
directly — and distribution, as Chapter 3 argued, is where the signal lives. Most analyses therefore
run on the Berezkin layer, with the other two indices used to corroborate.

Assembling these into one object means building a single **attestation matrix**: a provenanced record
of which traditions carry which motifs, with every cell traceable back to its source. The corpus
overview — how many texts, traditions, areas, and words the assembled corpus contains, broken down by
region and tradition — is itself a first analytical surface, and one worth inspecting before any
modelling, because it exposes the shape of what is there to be explained (Figure 4.3, Table 4.1).

> **Figure 4.3.** The corpus-overview dashboard: the assembled multilingual corpus by region and
> tradition — texts, traditions, macro-areas, and word counts — the "what is in this corpus?" surface
> that every later analysis is a refinement of.
>
> **Figure 4.4.** The distribution of attestation-intensity a(t), the number of motifs recorded per
> tradition: it ranges from a single entry to over seven hundred, with a median near seventy-five. This
> long right tail is the sampling confound that Chapter 3 insisted be carried forward, and it is the
> single most important fact about the raw matrix.

The same skew shows in the raw-text corpus that feeds the induction pipeline. Its texts span some three
orders of magnitude in length — the King James Bible runs to roughly 790,000 words against a
38,000-word *Beowulf* — and its bulk is dominated by the Abrahamic and Indian scriptural traditions,
which is itself a bias to be carried forward rather than hidden. Even a crude lexical similarity over
these texts, seriated so that related traditions sit adjacent, already recovers sensible groups — an
East-Asian cluster of Confucian, Taoist, and Buddhist texts; a Germanic branch of Anglo-Saxon, Norse,
and Germanic material; the Christianity–Islam pairing; the classical epics — a reassurance that the
corpus carries real structure before any modelling begins. Two
principles govern the assembly. The first is *provenance*: nothing enters the matrix without a record
of where it came from, so that a later result can always be traced to the coding that produced it. The
second is *restraint about categories*: the assembly deliberately does not impose a motif taxonomy or a
narrative schema of its own at construction time. The thematic structure and the distributional
regularities are left to emerge from analysis rather than being written into the data by hand — a
choice that reflects the long-standing tension in folklore studies between predefined analytical
categories and emergent structure, and that becomes load-bearing in Chapter 8, where the theme axis is
re-derived from the material precisely because it was not baked in here.

## 4.2 The cross-catalogue link set

Three catalogues that do not speak to one another are three separate studies. To analyse distributions
across the whole field, a motif in one index must be connected to its counterpart in another wherever
such a counterpart exists — and those connections must be trustworthy, because every later claim of
cross-catalogue corroboration rests on them. Building this link set, the **crosswalk**, is the
morphology stage of Chapter 3's arc made concrete.

The links are drawn on graded evidence rather than a single criterion. Two motifs may be connected
because they share a defining constituent, because their definitions align, because a note or a
summary in one points to the other, or because they cite a common source. Accumulating these yields a
confirmed graph of **7,274 edges** across the three indices, each edge carrying the kind of evidence
that justifies it (Figure 4.1). The graph is not a static appendix; it is a navigable object that can
be filtered by evidence type and explored link by link, and — more importantly for the analyses — it
is **reused as independent corroboration**. When a finding about a Berezkin motif can be echoed by a
linked motif in Thompson's or the tale-type index, that motif is weighted up as replicated; when it
cannot, the finding is treated as resting on a single catalogue's coding and flagged accordingly. The
crosswalk is honest about its own incompleteness. It is partly automated and it undercounts: some real
correspondences are missed — the swan-maiden's tale type was one such miss — so cross-catalogue
corroboration functions as a *lower* bound on agreement and a single-catalogue result as an *upper*
bound on how much depends on one coder's choices. Stating the direction of the error is what lets the
later chapters lean on the replicated core rather than on the whole graph indiscriminately.

## 4.3 The retrieval layer and its evaluation

For a motif to be compared with others by meaning, and for the induction pipeline to have any target
to align to, every motif needs a machine-readable representation of what it says. Each motif's name
and definition is embedded with a multilingual transformer model, BGE-M3, into a dense
thousand-dimensional vector; the catalogue text is overwhelmingly English with a small Russian tail,
and the multilingual model handles both. The important methodological point is not that embeddings are
used — that is now routine — but that they are **validated rather than asserted.**

Chapter 2's verdict on the field was that machine reading of motifs from text is best treated as a
*retrieval and candidate-generation* layer over expert judgement, not as a classifier that replaces
it. This book takes that verdict literally, and it holds the embeddings to the standard it implies. On
the confirmed crosswalk — a set of links established independently of any embedding — the transformer
vectors are scored by **recall@k**: given a motif, how often does its known counterpart appear among
the k nearest neighbours by vector similarity? The transformer is measured against a purely lexical
baseline built from word co-occurrence, and it is adopted downstream only because it *wins that
comparison* by a clear margin (Figure 4.2). This is the honest version of the tempting claim that
"meaningful clusters emerge on their own": a number on a held-out link set rather than an impression
from a suggestive picture. A companion retrieval experiment settles a design question the same way —
embedding a motif by its *name alone* against embedding it by *name plus summary*, scored by ranking the
true type among all ~2,240 tale types for some 1,500 real tales with the labels stripped out.
Name-plus-summary roughly *doubles* the mean reciprocal rank over name-only (from about 0.12 to 0.23) and
cuts the median rank of the correct type from around 300 to below 140; representing the text as passages
rather than one vector helps the rank further. That is why every motif is embedded by name *and*
definition, not name alone — the choice is made by a measured retrieval gain, not by taste. Where the
embedding is used later — to re-derive the theme axis in
Chapter 8, for instance — it is used as this validated retrieval layer, never as an independent
oracle about a motif's age or origin, a circularity the programme's axioms explicitly forbid.

> **Figure 4.1.** The cross-catalogue link graph: 7,274 confirmed edges connecting Thompson's
> *Motif-Index*, the tale-type index, and Berezkin's catalogue, filterable by the kind of evidence that
> drew each edge. **Figure 4.2.** The retrieval evaluation: recall@k of the transformer embeddings
> against a lexical baseline on the confirmed crosswalk — the transformer wins, which is why it is
> adopted downstream.

## 4.4 Space, coverage, the bench — and induction, staged

Three further pieces complete the infrastructure.

The **spatial layer** places each tradition on the globe so that distributions can be measured
geographically. The source data does not give true coordinates for the traditions, so a tradition is
resolved to the centroid of its areal subregion where a finer point is unavailable — a coarse
approximation that is used only to place points and that is named, here and wherever it matters, as a
bound on every spatial result. It is better to state the coarseness once and carry it forward than to
present centroid-based maps as if they were survey-grade.

The **coverage layer** is the one Chapter 3 insisted could never be forgotten. The number of motifs
recorded for a tradition ranges from one to more than seven hundred, with a median near seventy-five
(Figure 4.4). This attestation-intensity is not metadata to be noted and set aside; it is carried into
every later analysis in whatever form that analysis needs — as a weight, as a model correction, as an
exposure term — so that the densely catalogued corpora do not masquerade as the central or typical
ones. The coverage layer is what turns the raw matrix into something a distributional claim can safely
be made about.

The **analysis bench** is the form the results actually take. Rather than one monolithic program, the
analyses live as roughly forty self-contained prototypes, each reading only the assembled corpus and
the committed external joins, each producing its figure from a single build step with fixed random
seeds, and each documented on its own. This is the lab bench of the programme: every result chapter of
this book is a written synthesis of a subset of these prototypes, and Appendix D maps each figure back
to the prototype that produces it, so that any number in the book can be regenerated. The external
joins the bench draws on — subsistence economy, language family and its expansion dates, historical
political boundaries, and a proxy for migration direction — are the subject of Chapters 5 through 7;
they are committed alongside the code so that the whole apparatus runs off public sources with no
credentials.

Finally, the **induction pipeline**, described honestly as what it is. Its stages — collecting and
cleaning source texts, splitting them into meaning-coherent chunks and embedding them, reducing and
projecting those embeddings, extracting a knowledge graph, and, at the terminal stage, **aligning the
induced candidate units to the curated vocabulary through the crosswalk** — constitute a machine for
turning raw corpora into candidate motifs anchored to an expert index rather than invented in an open
vocabulary. That machine is built and served through the application. What is *not* yet delivered is
its validated output at scale: induced motifs, checked against a gold standard, with the field's
stubborn baselines beaten. Because motif detection from text is hard to the point of being unsolved
(Chapter 2), the programme stages this deliberately — the pipeline is the standing goal and the main
built infrastructure, the curated-index analysis is where results exist today, and Chapter 10 returns
to the induction milestone as the principal open frontier. Naming that boundary here, in the chapter
that describes the machine, is the point: the infrastructure is real and reusable, and its most
ambitious output is honestly pending rather than quietly assumed.
