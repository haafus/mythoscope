---
title: "Mythoscope — a new lens on the world's myths"
description: "Mythoscope is a live tool and a research programme for the large-scale, sampling-corrected comparative study of the world's folklore motifs."
url: /
tier: A
---

# The geography of a myth is written in where it is attested, not in what it says.

A folklore motif is a small, portable unit of narrative — the swan-maiden trapped when
a man hides her feather cloak, the theft of fire from its first jealous owner, the sun and
moon imagined as siblings. Such units recur across the world's traditions with a
stubbornness that has fascinated comparative scholarship for two centuries. They turn up
among peoples who, as far as any record shows, never met. **Why?**

Mythoscope is built to take that question seriously — at scale, and with the honesty the
question demands. It is two things at once: a **live tool** you can open and explore right
now, and a **research programme** that uses it to ask what the world's myths are actually
consistent with.

## What Mythoscope is

Mythoscope is a computational framework for comparative mythology. It assembles a corpus
of myth and folklore texts, turns them into an explorable **semantic space**, and joins
that to a cross-linked **motif database** integrating the three great folklore
indexes — Thompson's *Motif-Index* (TMI), the Aarne–Thompson–Uther tale-type index (ATU),
and Yuri Berezkin's areal catalogue of motif distributions. Everything is served through
one web interface.

Two layers work side by side:

- **An unsupervised layer** — whole-corpus embeddings projected into an interactive map of
  meaning, full-text **search by meaning**, and per-text character, place, and time
  **graphs** extracted by large language models. This layer lets the material cluster on
  its own terms, before any category is imposed.
- **A curated layer** — the integrated motif catalogue, with an automatic **crosswalk**
  linking a motif in one index to its counterpart in the others, plus lexical and semantic
  parallel-finding on top.

The wager behind all of it is simple to state. A motif is never just present or absent in
the world; it is present in a *pattern* — concentrated or scattered, confined to one
continent or straddling several, clustered on a language tree or smeared across it. Those
patterns are the only direct evidence we have of how a motif came to recur: whether it was
**inherited** down a lineage, **diffused** sideways between neighbours, or **reinvented**
independently because it answers to something general about human minds and environments.
The shape of a distribution is where the history hides.

## Explore the live views

You can browse the whole apparatus without reading a line of theory.

- **Atlas** — a geographic view of the traditions in the corpus, on the map.
  *Explore the live Atlas.*
- **Similarity** — the semantic space as an interactive scatter you can colour by tradition
  and region, with nearest-neighbour "similar fragments" and search by meaning.
  *Open the Similarity view.*
- **Motifs** — the browsable, cross-linked catalogue of TMI, ATU, and Berezkin, with
  clickable crosswalk links between the indexes. *Open the Motifs browser.*
- **Graphs** — per-text character, place, and timeline graphs (Ages, Realms, Beings).

## Read the research

Underneath the tool is an argument, assembled honestly and reported with its limits in view.

- **[How it works](how-it-works.md)** — the pipeline from corpus to embeddings to
  projections to graphs, the motif crosswalk, and the natural-history stance that organises
  the whole thing.
- **[What we found](what-we-found.md)** — the headline results: areal diffusion dominates,
  a small descent minority tracks language families, and a faint deep substrate is real but
  small — with the clean negatives reported alongside the positives.
- **[The crosswalk](crosswalk.md)** — how three catalogues built on incompatible principles
  are linked into one navigable whole.
- **[About](about.md)** — the vision behind Mythoscope: *Collaborative Semantic
  Archaeology*, and why a shift from testing theories to discovering patterns needs open
  infrastructure.

## An honest note up front

Mythoscope is early research software. Its central results rest on the already-curated
indexes — chiefly Berezkin's coded distributions — not on anything read automatically from
raw text. The machinery to **induce motifs directly from text** is built, but the task is
one of the field's genuinely open problems, and its output is not yet validated at scale.
Where the data speaks clearly, we report it; where it cannot tell two histories apart, we
say so and mark the boundary. The negatives are part of the contribution.
