---
title: "Resources & downloads"
description: "Bulk data downloads, DOIs (forthcoming), the experimental read-only API, the repository, the awesome-list, licences, and digital text libraries for comparative mythology."
url: /resources
tier: C
---

# Resources

Everything Mythoscope produces is meant to be taken away and reused: the corpus, the motif
crosswalk, the graphs, and the projections. This page is the practical index — where to get
the data, how it is licensed, what the experimental API offers, and which external text
libraries feed the corpus. For how to *cite* any of it, see [Publications](publications.md).

## Bulk data downloads

Researchers reuse data dumps, not API clients, so the primary distribution channel is a
**bulk export bundle**: a portable archive of the built outputs — the cleaned corpus with
provenance, the character/place/time graphs, the semantic-space projections, and the full
motif database (the TMI, ATU, and Berezkin indexes plus the derived crosswalk and the
lexical/semantic parallels). Unpack it and browse it with the lightweight *viewer* install,
no GPU required; see [Contribute](contribute.md#just-view-the-data--no-gpu-no-torch) for the
one-command setup.

The single most novel artifact is the **motif crosswalk dataset** — the machine-readable
TMI ↔ ATU ↔ Berezkin link structure, released as CSV/JSON with a datasheet. How it is built
and validated is documented in [The crosswalk](crosswalk.md).

### DOIs — forthcoming

Persistent identifiers are being minted, not invented. **No DOI exists yet.** On the first
archived release, the following will each receive a citable DOI (via Zenodo) and appear
here and on [Publications](publications.md):

- a **software / release DOI** for the repository (with a concept-DOI covering all
  versions);
- a **dataset DOI** for the motif crosswalk (CSV/JSON + datasheet);
- **per-survey DOIs** for the reference surveys, so their "How to cite" blocks resolve.

Until those are archived, cite the repository and the specific version you used, following
[Publications](publications.md). Do not cite a DOI here — there is not one to cite.

## The read-only API — experimental

The Mythoscope server is a FastAPI application, and FastAPI generates interactive API
documentation for free from the response schemas. It is exposed **read-only** so you can
inspect and script against the same endpoints the web app uses:

- `/docs` — Swagger UI (interactive endpoint testing);
- `/redoc` — ReDoc (a readable reference);
- `/openapi.json` — the OpenAPI schema (for code generation or Postman).

The endpoints cover the corpus catalogue and documents, the traditions, the graphs, the
motif indexes and crosswalk, and the similarity/projection data.

> **Experimental — no stability guarantees.** This is the server's auto-generated OpenAPI
> surface, not a supported product API. Endpoints, parameters, and response shapes may
> change or disappear without notice or versioning. For anything durable, use the **bulk
> data downloads** above, which are versioned and (soon) DOI'd. A supported public API is
> not planned for the near term.

## Code, repository, and the awesome-list

- **Repository** — [github.com/haafus/mythoscope](https://github.com/haafus/mythoscope).
  Source, issues, discussions, and the contribution workflow. Star it to follow along.
- **awesome-computational-mythology** — a standalone, curated list of the tools, datasets,
  corpora, papers, and reference works of the field, maintained as its own repository
  following the `awesome` conventions. It is the fastest way to survey what exists in
  computational folkloristics and comparative mythology — and an easy place to make a first
  contribution (see [Contribute](contribute.md#curate-the-awesome-computational-mythology-list)).

## Licences

Mythoscope is licensed by layer, so that each part can be reused on terms appropriate to it:

| What | Licence |
|---|---|
| **Source code** | MIT |
| **Documentation and prose** | CC BY-SA 4.0 |
| **Derived datasets** (e.g. the motif crosswalk) | CC BY 4.0 |
| **Third-party source texts and indexes** | retain their own terms |

The last row matters: the public web corpus is public-domain (Project Gutenberg), but
individual source texts and the upstream motif indexes carry their own licences and
provenance, which travel with the data. Berezkin's catalogue and the TMI/ATU data derived
from the `trilogy` project (CC BY-SA 4.0) are used under their respective terms. Full
details are in the repository's [`LICENSE`](https://github.com/haafus/mythoscope/blob/main/LICENSE).

## Digital text libraries

The corpus is assembled from open digital text collections. The list below — a starting
map of where mythological and folklore texts can be sourced — is offered for anyone
building or extending a corpus of their own:

- **Perseus Digital Library** — Greek and Latin
- **Internet Sacred Text Archive** — cross-tradition sacred and mythological texts
- **Electronic Text Corpus of Sumerian Literature (ETCSL)**
- **Thesaurus Linguae Aegyptiae** — Egyptian
- **The Sanskrit Library** and **GRETIL** (Göttingen Register of Electronic Texts in Indian
  Languages)
- **Chinese Text Project**
- **National Institute of Japanese Literature** database
- **Internet Archive**, **Project Gutenberg**, **HathiTrust** — general full-text
- **Fordham Internet History Sourcebooks**
- **Open Islamicate Texts Initiative (OpenITI)**
- **TITUS Project** — Indo-European and Caucasian texts
- **Finnish Literature Society (SKS)** folklore archive
- **American Folklife Center** (Library of Congress)
- **World Oral Literature Project**
- **Native American Ethnography** database (Alexander Street)
- **Polynesian Texts Collection** (University of Auckland)
- **Buddhist Digital Resource Center**

For a fuller treatment — which of roughly forty traditions can be sourced from which
repositories, under which licences, with EASY/MODERATE/HARD sourcing verdicts — see the
**corpus-sourcing atlas** in the research surveys, rather than repeating that detail here.

---

**See also:** [Publications](publications.md) for how to cite · [Contribute](contribute.md)
for how to add to any of the above · [Credit & authorship](credit.md) for the attribution
policy · [How it works](how-it-works.md) for the pipeline behind the data.
