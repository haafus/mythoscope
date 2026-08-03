---
title: "Publications & how to cite"
description: "The Mythoscope citation hub — the working paper and forthcoming preprint, planned DOIs, and how-to-cite blocks following the repository's CITATION.cff."
url: /publications
tier: C
---

# Publications

This is the citation hub for Mythoscope: the writing that describes the project, and the
canonical way to cite the software and data. It is deliberately honest about what is and is
not yet formally citable. **Nothing here has a DOI yet.** Persistent identifiers are being
minted for the first archived release; until then, cite the repository and the specific
version you used, as shown below.

For the underlying data and its licences, see [Resources](resources.md); for how
contribution converts into authorship credit, see [Credit & authorship](credit.md).

## The working paper

**Computational Comparative Mythology: A Natural History of the Motif.** A monograph-length
treatment, written to be read by someone who does not already know the project. It builds
the apparatus — corpus, embeddings, projections, graphs, and the motif crosswalk — and
reports what it finds: that geography is the primary signal in a global motif corpus, that
descent is a well-defined minority mode datable to the Eurasian fairy-tale belt around
5,500 years ago, that a small trans-hemispheric substrate (chiefly celestial cosmology) is
real but not datable from distribution alone, and that a large, honestly bounded
*convergence residual* maps the work that remains. The case studies are distilled on
[Three motifs through the machine](cases/); the results on [What we
found](what-we-found.md); the method on [How it works](how-it-works.md).

*Status:* draft. The paper is being prepared for deposit as a **preprint** (targeting a
venue such as arXiv cs.CL, SocArXiv, or Humanities Commons CORE). The preprint and its DOI
are **forthcoming** and will be listed here on deposit.

## Planned citable objects

On the first archived release, each of the following will receive a DOI and appear here.
These do **not** exist yet; the identifiers are **forthcoming**, and none should be cited
until it resolves:

- **Preprint** — the methods and findings paper above (DOI forthcoming).
- **Software / release DOI** — the repository, archived via Zenodo, with a concept-DOI for
  all versions (forthcoming).
- **Dataset DOI** — the motif crosswalk (TMI ↔ ATU ↔ Berezkin), released as CSV/JSON with a
  datasheet (forthcoming).
- **Per-survey DOIs** — for the reference surveys, so their citations resolve independently
  (forthcoming).

## How to cite

The repository carries a
[`CITATION.cff`](https://github.com/haafus/mythoscope/blob/main/CITATION.cff), which GitHub
renders as a **"Cite this repository"** button — the most reliable source, since it is
versioned with the code. The blocks below follow it. Author name(s) and ORCID are finalised
on the first archived release; **fill them from `CITATION.cff`** rather than from this page,
and add the DOI once it is minted.

### Cite the software

> *[Author(s), see `CITATION.cff`]* (2026). *Mythoscope: a computational framework for
> comparative mythology* (Version 0.1.0) [Computer software]. https://mythoscope.io — a DOI
> will be added on the first archived release.

BibTeX:

```bibtex
@software{mythoscope,
  title   = {Mythoscope: a computational framework for comparative mythology},
  author  = {{Mythoscope authors — see CITATION.cff}},
  year    = {2026},
  version = {0.1.0},
  url      = {https://mythoscope.io},
  note    = {DOI forthcoming on first archived release}
}
```

### Cite the crosswalk dataset

Until the dataset DOI is minted, cite the software release above and name the crosswalk and
the version you used (for example, "the Mythoscope motif crosswalk, v0.1.0"). A dedicated
dataset citation with its own DOI will be published on release; see [The
crosswalk](crosswalk.md).

### Cite the paper

Once the preprint is deposited, a citation with its DOI will replace this note. Until then,
if you must reference the argument, cite the software release above and the working-paper
title, and indicate that the preprint is forthcoming.

### Cite the version you used

Mythoscope is versioned with semantic versions. Reproducibility depends on naming the exact
version (and, once available, the version-specific DOI) rather than "the latest" — the data
and links evolve between releases.

## Scholarly profiles

These register profiles will point back to the project once created. They are **placeholders
— not yet live**, listed so the citation graph has somewhere to resolve to:

- **Google Scholar** — *profile forthcoming.*
- **Humanities Commons (CORE)** — *profile / deposit forthcoming.*
- **ORCID** — *author ORCID(s) forthcoming; will be recorded in `CITATION.cff`.*

---

**See also:** [Resources](resources.md) for the downloads and DOIs · [Credit &
authorship](credit.md) for how contributors are credited · [Contribute](contribute.md) to
take part.
