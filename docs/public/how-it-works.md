---
title: "How Mythoscope works"
description: "The Mythoscope pipeline — corpus, embeddings, projections, graphs, and the motif crosswalk — framed as a natural-history science of the motif."
url: /how-it-works
tier: A
---

# How it works

Mythoscope is built on one organising idea: **comparative mythology is a natural-history
science, and its data is a catalogue.** Biology moved from cabinets of specimens to
comparative anatomy to systematics to phylogeny; historical linguistics moved from
wordlists to grammars to language families to reconstruction. A catalogue of thousands of
motifs distributed across a thousand traditions is the same kind of object, and it rewards
the same arc — **collect, describe, classify, explain.**

That arc is a *dependency order, not a schedule.* You cannot classify what you have not
described, and you cannot explain a distribution you have not first mapped. When the order
is violated — when a striking explanatory story is told about a pattern that has not been
checked for sampling artefacts — the result is the kind of over-reach the field has learned
to distrust. The software is arranged to keep the stages honest and in order.

## The pipeline

The data pipeline is linear, idempotent, and resumable — each stage can be safely
interrupted and will pick up where it left off:

```
corpus → embeddings → { projections, graphs } → server
motifs (independent of the corpus) → server
```

- **Corpus** — download and clean source texts (Project Gutenberg plus local files), and
  write cleaned text with a catalogue of provenance. Gutenberg licence headers and footers
  are stripped automatically.
- **Embeddings** — chunk each text, optionally preprocess the chunks with a language model,
  encode them with a sentence-embedding model (for example `bge-m3`), and store the vectors
  in a local vector database.
- **Projections** — reduce the high-dimensional vectors with UMAP into the interactive
  semantic-space views: the coloured scatter, distance heatmaps, and distribution plots.
- **Graphs** — use large language models to extract, per text, three graphs: characters and
  their relations (*Beings*), places and their adjacency (*Realms*), and a narrative
  timeline of ages (*Ages*), linked in order of appearance.
- **Motifs** — assemble the motif database (below); this runs independently of the corpus.
- **Server** — a single web application reads the built outputs and serves the interactive
  views plus a documented REST/OpenAPI service.

The whole thing runs through one command-line entry point, and a lightweight *viewer*
install lets anyone browse prebuilt data — texts, graphs, projections, and
nearest-neighbour search over points — without the heavy machine-learning dependencies.

*Open the Similarity view to see the semantic space, or explore the live Atlas for the
geographic view.*

## The motif crosswalk

The comparative study of narrative has produced several great reference works, but they
were built on different principles and do not speak to one another. Thompson's
*Motif-Index of Folk-Literature* is an enormous, finely subdivided taxonomy of narrative
elements organised by subject. The Aarne–Thompson–Uther index catalogues whole *tale
types* rather than motifs. Yuri Berezkin's areal catalogue, uniquely, records not just
motifs but their **distribution over ethnographic traditions**, placing each of some three
and a half thousand motifs on a map of roughly a thousand peoples. These indexes carve the
material at different joints, in different languages, with different conventions.

To study distributions across the whole field, they must first be linked: a motif in one
index connected to its counterpart in another wherever such a counterpart exists. Building
and validating that link structure — the **crosswalk** — is a precondition for everything
else. Mythoscope assembles the three catalogues into one machine-readable, browsable whole
and derives the crosswalk automatically: ATU tale types are linked to their constituent
Thompson motifs, Berezkin motifs are joined to ATU through the tale-type references carried
in their titles, and, where curated Thompson identifiers exist, Berezkin is linked to TMI
directly. On top of the recorded links sits a layer of heuristic **lexical and semantic
parallels** — candidate twins that have no recorded connection, surfaced as hints rather
than asserted facts.

*Open the Motifs browser to walk the catalogue and follow the crosswalk between indexes.
[The crosswalk](crosswalk.md) explains how the links are built and validated.*

## Two obstacles the design confronts

A catalogue records what someone has recorded, and coverage is deeply uneven. Europe has
been combed for folklore for two centuries; many traditions have been documented thinly, or
once, or by a single collector with idiosyncratic interests. In this corpus the number of
motifs recorded for a tradition ranges across more than two orders of magnitude — from a
single entry to several hundred. Raw counts therefore confound the history of the myths
with the history of the collecting. **De-confounding sampling is not a robustness check
bolted on at the end; it is a discipline that runs through every stage,** carried forward as
a weight so that densely catalogued corpora do not dominate. A pattern that appears only in
the raw counts and dissolves under the control is not reported as a finding; it is a
description of the archive.

The second obstacle is that the standard way of grouping motifs by subject — cosmogony,
the origin of death, tricksters, and so on — is a scholar's ordering, inherited from the
classical indexes and never tested against the structure the material itself carries. The
unsupervised layer exists in part to let the material answer that question on its own terms.

## Honest scope: motif induction from text

Behind these analyses stands a larger ambition: to **induce motifs directly from raw text**
rather than take them from a curated index. That machinery is *built* — chunking, embedding,
graph extraction, and parallel-finding are all in place — but reading motifs reliably out of
free text is one of the genuinely unsolved problems of the field, and Mythoscope's
validated motif output does not yet exist at scale. Every substantive result therefore rests
on the already-curated indexes, chiefly Berezkin's coded distributions. The induction layer
is described here as built infrastructure and staged as future work, not presented as a
delivered result. The reader is never asked to take an unbuilt thing on faith.

---

**Next:** [What we found](what-we-found.md) reports the results this pipeline produces ·
[About](about.md) sets out the vision behind the project · or open the [live
app](/) and explore it yourself.
