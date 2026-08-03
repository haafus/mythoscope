---
title: "Contribute to Mythoscope"
description: "How to help build Mythoscope — corpus, code, data, and community — plus the awesome-computational-mythology list and a no-GPU path to just browse the data."
url: /contribute
tier: C
---

# Contribute

Mythoscope is open research infrastructure, and it is built to be built *with* people
rather than for them. The corpus, the code, the motif crosswalk, and the surrounding
reference material are all meant to be extended, corrected, and reused. This page sets out
the concrete ways to help — from adding a single cleaned text to co-authoring a finding —
and the one path that asks nothing of you but curiosity: just download the data and look.

Contributions are welcome under the project's [Code of
Conduct](https://github.com/haafus/mythoscope/blob/main/CODE_OF_CONDUCT.md), and everything
you add is credited. How credit works — from acknowledgement through data citation to
co-authorship — is written down in [Credit & authorship](credit.md); it is not left to
discretion.

## Just view the data — no GPU, no torch

You do not have to run the full machine to explore what it produces. Mythoscope ships an
**export bundle**: a portable archive of the built outputs — the cleaned corpus, the
character/place/time graphs, the semantic-space projections, and the motif database — that
you can unpack and browse with a lightweight *viewer* install. The viewer has no
heavyweight machine-learning dependencies (no `torch`, no embedding models, no scrapers);
it is a few hundred megabytes rather than several gigabytes, and it runs on a laptop with
no GPU.

```sh
git clone https://github.com/haafus/mythoscope
cd mythoscope
python -m venv .venv && source .venv/bin/activate
pip install -e ".[viewer]"            # lightweight: browse prebuilt data, no torch

# unpack an export bundle produced by the pipeline, then:
mytho server                          # serve the web UI + API at http://localhost:8000
```

In the viewer build you get the reader, the graphs, the semantic-space plots,
nearest-neighbour search over points, the geographic Atlas, and the full motif crosswalk.
The one thing that needs the heavier install is *semantic search by free-text query*, which
requires the embedding-model weights; the interface simply hides that one search box when
the weights are not present. Everything else works offline. Full install profiles and the
end-to-end pipeline are in [How it works](how-it-works.md) and the project's setup guide.

Exploring the data and reporting what looks wrong — a mis-linked motif, a badly cleaned
text, a tradition placed on the wrong coordinates — is itself a contribution. Open an issue
on [GitHub](https://github.com/haafus/mythoscope).

## Ways to help

Mythoscope needs several different kinds of expertise, and they rarely live in one person.
The offerings below are the ones we can honestly support today. (Some things discussed in
early planning — funded fellowships, formal institutional partnerships, a staffed press
operation — are not yet real, and are deliberately left off this list until they are.)

### Contribute corpora and texts

The corpus is the foundation, and it is thin outside the well-combed European material. We
are looking for mythological and folklore texts from **any tradition**, especially:

- vetted translations and critical editions;
- rare and under-documented traditions, regional variants, and oral material;
- sacred narratives where sharing is permitted.

*Ideal for:* philologists, folklorists, anthropologists, religious-studies scholars,
curators, librarians, and knowledge-keepers. Texts enter the pipeline through a simple
catalogue entry (a title, a tradition, and a source URL or local file); public-domain web
sources such as Project Gutenberg are cleaned automatically. See [Resources](resources.md)
for a list of digital text libraries to draw from, and note the licensing point below.

### Provide metadata and annotations

Structured metadata and expert annotation make the corpus usable: motif, theme, and
character tags; cultural and historical context; linguistic markup; variant tracking; and
corrections to the tradition taxonomy and its coordinates.

*Ideal for:* area-studies specialists, linguists, cultural historians, and graduate
students.

### Contribute non-textual datasets

Distributional questions need more than text. Geographic data (origins and transmission
routes), temporal data (dating), archaeological correlates, iconographic databases, audio
recordings of oral traditions, and network data on contact and trade all sharpen the
analysis and help close the *convergence residual* the research programme is organised
around.

*Ideal for:* archaeologists, art historians, ethnomusicologists, geographers, and digital
archivists.

### Develop and refine methods

The computational layer is under active development. There is real work in NLP for ancient
and low-resource languages, clustering and network analysis, multilingual embeddings,
visualisation, and — the principal open problem — **evaluation metrics for motif induction
from raw text**. The infrastructure for inducing motifs directly from text is built; what
is missing is validated output at scale, checked against a gold standard and against the
field's stubborn simple baselines. This is where a methods contributor can have the most
leverage.

*Ideal for:* computer scientists, computational linguists, data scientists, and DH
methodologists.

### Contribute code and infrastructure

Mythoscope is a Python pipeline (FastAPI server, a vanilla-JS single-page app, ChromaDB,
UMAP) with no framework lock-in. Contributions to the platform, the API, the
visualisations, developer tooling, and documentation are all welcome. Start with the setup
guide and the pipeline overview in [How it works](how-it-works.md); the codebase, issues,
and pull-request workflow live on
[GitHub](https://github.com/haafus/mythoscope), with a
[CONTRIBUTING guide](https://github.com/haafus/mythoscope/blob/main/CONTRIBUTING.md).

*Ideal for:* software engineers, web developers, and computer-science students.

### Validate findings and co-author

The computational layer proposes; human judgement disposes. Expert interpretation of the
machine's output — cultural context, critical evaluation, alternative explanations,
theory-building — is where a distributional pattern becomes a finding. Substantial work of
this kind is a route to co-authorship, on the terms set out in [Credit &
authorship](credit.md).

*Ideal for:* senior scholars, theorists, and comparative-literature specialists.

### Curate the awesome-computational-mythology list

A standalone, curated field resource — **awesome-computational-mythology** — collects the
tools, datasets, corpora, papers, and reference works of computational folkloristics and
comparative mythology in one place. It is maintained as its own repository, following the
`awesome` conventions (link-checking, a contributing guide, an open licence). Adding a
resource, fixing a dead link, or proposing a new section is a low-friction first
contribution that helps the whole field, not just this project. The list is linked from
[Resources](resources.md).

### Indigenous knowledge and community partnerships

Some of the material this project touches belongs to living communities, and it is handled
on their terms. We work with cultural protocols and prior, informed consent, following the
**CARE principles** for Indigenous data governance: community control over how a tradition
is represented, the right to review interpretations, proper attribution, benefit-sharing,
and the right to have material removed. The governance detail is in [Credit &
authorship](credit.md).

*Ideal for:* community-nominated representatives and knowledge-keepers, working with the
project on a co-governance basis.

### Join the conversation

Methodology is argued out in the open. Discussion, disagreement about frameworks, and
suggestions for directions happen on GitHub Discussions, on the newsletter, and in periodic
community calls. Real-time chat is deferred until there is a community to fill it — we would
rather point you to an active thread than an empty server.

## How contributions are handled

A few principles govern everything above:

- **Open by default.** Contributions are credited, and outputs are released under open
  licences (see [Resources](resources.md) for the specifics — code MIT, prose CC BY-SA,
  derived datasets CC BY).
- **Attribution is the rule, not a favour.** Every contribution is recorded; see [Credit &
  authorship](credit.md).
- **Provenance travels with the data.** Third-party texts and indexes keep their own terms,
  and per-dataset provenance is preserved.
- **Licensing your texts is on you.** The public web corpus is public-domain (Gutenberg),
  but many source files are not. Local source files are kept out of version control by
  default; if you contribute texts, make sure you have the right to share them.

## Get started

1. **Explore** the live data — install the viewer above, or open the app and look around.
2. **Read** how it works: [How it works](how-it-works.md) and [The crosswalk](crosswalk.md).
3. **Pick a lane** from the list above.
4. **Reach out** at **[hello@mythoscope.io](mailto:hello@mythoscope.io)**, or open an issue
   or discussion on [GitHub](https://github.com/haafus/mythoscope).

---

**See also:** [Resources](resources.md) for data downloads, the API, and licences ·
[Publications](publications.md) for how to cite the project · [Credit &
authorship](credit.md) for the attribution policy.
