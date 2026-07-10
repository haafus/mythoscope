# Release & dissemination plan

How the work reaches the public. The backbone is a small set of **academically recognised
publications**. Everything else — the datasets, the code, the live public tool, and the
program/outlook texts — is not a standalone item but a **component or requirement** of one of those
publications. Written to be read by someone who does not know the project.

Companion to [`monograph-outline.md`](monograph-outline.md) (how the parts would compose into a book,
later) and [`README.md`](README.md) (the drafts index).

---

## The releases

Five academic publications. Each block gives its exact title, where it goes, its goal, the exact list
of what it must cover and include, what it needs, and when.

### 1. The survey — *Computational Folkloristics and the Induction of Motifs: A Survey*

- **Where:** preprint on arXiv (digital libraries) or Humanities Commons; submit to a review venue —
  *Journal of Cultural Analytics*, *Fabula*, or *Digital Scholarship in the Humanities* (or *ACM
  Computing Surveys* if the coverage is made broad enough).
- **Goal:** map the field of computational folkloristics and motif induction **for the whole
  community**, as an independent contribution — not as an appendix to this project.
- **Must cover and include:**
  1. a definition of the motif and a statement of why it is formally unstable, framing the survey;
  2. the **classical era** (c. 2008–2018): digitisation and formalisation of the Aarne–Thompson–Uther
     and Thompson indices; topic-model motif induction; word-sense semantic search over the
     Motif-Index; interoperable ontologies; tale and myth phylogenetics; character and motif networks;
  3. the **modern era** (2018–2026): transformer embeddings and clustering; large-language-model motif
     and tale-type annotation; the repeated finding that simple word-frequency baselines match neural
     and large-language-model systems on small corpora;
  4. an organisation **by method family**: (a) indices and ontologies; (b) supervised tale-type
     classification; (c) topic models; (d) embeddings, retrieval and motif detection; (e) sequence and
     network mining; (f) evolutionary / phylogenetic mythology; (g) narrative-structure (Propp)
     extraction;
  5. a **catalogue of the open datasets** in the field with their licences;
  6. the field's **hard lessons**: motifs resist crisp boundaries; gold-standard annotation is scarce
     and culturally contingent; baselines match neural systems; large language models hallucinate
     exemplars and fail on structural tasks;
  7. the **conclusion**: embeddings are best used as a search / candidate-generation layer over a
     curated expert index, not as an end-to-end classifier;
  8. an **open-problems agenda** for the field.
- **Needs, before release:** expand to full survey length; **written from the field's point of view**
  — this project appears, if at all, as one example among many, not as the subject; clean the
  bibliography (remove the citations currently flagged as unverified).
- **When:** early — the lowest-risk, widest-reach piece (it depends on no unfinished result) and it
  establishes a presence in the field before the main results land. Out as soon as the expansion and
  citation cleanup are done.

### 2. The findings paper — *Geography, Descent, and Genre in the Global Distribution of Folklore Motifs*

- **Where:** preprint on arXiv (statistics, or physics-and-society); submit to *Evolutionary Human
  Sciences* (Cambridge, open access) or *Royal Society Open Science*.
- **Goal:** the main scientific results of the project.
- **Must cover and include:**
  1. **Data and materials:** the three catalogues (Thompson's Motif-Index, the Aarne–Thompson–Uther
     tale-type index, and Berezkin's areal catalogue of ~3,500 motifs over ~1,050 traditions); the
     table of ~7,300 confirmed links between them; the multilingual semantic embedding of every motif;
     the external joins (subsistence, language family, historical political boundaries);
  2. **Method:** the collect → describe → classify → explain program; systematics by co-clustering with
     a sampling-corrected block model; the four descriptors of a tradition (area, language family,
     subsistence, theme profile); time-depth from the shape of a distribution and, separately, from the
     language tree by ancestral-state reconstruction; the de-confounding throughout (coverage
     weighting, control for spatial autocorrelation, cross-catalogue replication); the connectivity
     tests (landscape resistance, historical empires, migration corridors); the bottom-up re-derivation
     of the theme axis from motif meaning;
  3. **Results**, each with its de-confounding: (a) the catalogues carry real, region-coherent
     structure that survives sampling correction; (b) the theme axis is data-confirmed and only partly
     geographic, with a subsistence gradient; (c) areal diffusion dominates, the descent minority is
     ~1% (the Eurasian fairy-tale core), and the deep trans-hemispheric substrate is real but small;
     (d) calendar dating of the descent minority; (e) the descriptors are incomplete — they recover
     only about a third of motif similarity — and of the two connectivity axes landscape fails its
     pre-set test while historical empires weakly pass; (f) tradition stratigraphy — deep-substrate-rich
     traditions sit in early-peopled regions; (g) the theme axis re-derived from meaning, shown to be
     orthogonal to the classical one and a better descriptor of a tradition;
  4. **Discussion, related work and contribution, reproducibility, limitations, conclusion.**
- **Published together with it (each a citable component, not a separate release):**
  - a frozen **dataset** on Zenodo — the derived theme taxonomy, the table of links between the three
    catalogues, the external joins, and the depth metrics;
  - a frozen **code snapshot** on Zenodo, via a tagged release on GitHub — the full pipeline and the
    analysis bench.
- **When:** now — the data is ready; freeze the dataset first, then post the preprint citing it.

### 3. The resource paper — *A Cross-Indexed Corpus and Analysis Bench for Comparative Mythology*

- **Where:** preprint on arXiv (digital libraries); submit to *Journal of Open Humanities Data* or the
  *Computational Humanities Research* conference.
- **Goal:** describe and formally publish the reusable corpus and the analysis tooling, so others can
  build on them.
- **Must cover and include:**
  1. **the assembled corpus:** the three catalogues brought into one attestation matrix (which peoples
     carry which motifs), with provenance for every entry;
  2. **the cross-catalogue link set:** ~7,300 confirmed links; the kinds of evidence used to draw them
     (shared constituents, definitions, notes, summaries, citations); the extension layer; its coverage
     and known gaps;
  3. **the semantic-retrieval layer:** motif-level multilingual embeddings; a word-frequency baseline;
     a recall-at-k evaluation against the confirmed links;
  4. **the spatial and coverage layer:** how traditions are placed on the map; how uneven cataloguing
     effort is measured and corrected;
  5. **the analysis bench:** the ~40 self-contained prototypes, the build-then-view pattern, and how
     each is reproduced;
  6. **the external joins** wired in (subsistence, language family, historical boundaries);
  7. **data and code availability:** the dataset and code DOIs; what is included versus regenerated;
  8. **honest scope:** the raw-text induction pipeline is described as built infrastructure, with its
     validated output staged to a later paper.
- **Needs:** the dataset and code snapshots from the findings paper (shared, not duplicated).
- **When:** about a month out.

### 4. The software paper — *MythoScope: an open tool for comparative-mythology corpus analysis*

- **Where:** the *Journal of Open Source Software* — a peer-reviewed journal for research software.
- **Goal:** make the **communal tool itself** citable and peer-reviewed.
- **Must cover and include:**
  1. a **statement of need:** who the tool is for and what gap it fills;
  2. the **live public portal**, with its sections — Read (the papers), Explore (the interactive
     figures and a corpus browser), Programming interface, Data & code, About;
  3. the **open programming interface:** the endpoints for search, retrieval, and browsing the corpus;
  4. **self-hosting:** how to run the whole thing with one command (a container image), and how to
     configure it;
  5. an **architecture summary:** the pipeline, the server, and the analysis bench, and how they fit;
  6. **documentation, automated tests, a contribution guide, and version numbering;**
  7. **worked examples / tutorials;**
  8. **links** to the dataset and code DOIs and to the papers.
- **When:** about a month out, once the live portal is working.

### 5. The motif-induction paper — *Inducing Motifs from Raw Text: Pipeline and Evaluation*

- **Where:** a natural-language-processing-for-humanities venue — LaTeCH-CLfL, NLP4DH, or the
  *Computational Humanities Research* conference.
- **Goal:** the natural-language contribution — extracting motifs directly from raw source texts.
- **Must cover and include:**
  1. **the task:** inducing and detecting motifs from raw multilingual text, and why it is hard;
  2. **the pipeline:** collection and cleaning of source texts; splitting into meaning-coherent units
     and embedding them; dimensionality reduction; knowledge-graph extraction; and **anchoring** the
     candidates to the three curated catalogues (candidate generation over an expert vocabulary);
  3. **the evaluation:** a gold reference set; precision and recall of the induced motifs; comparison
     against simple baseline methods (and, where relevant, large-language-model annotation);
  4. **an error analysis**, including the boundary-instability problem the survey identifies;
  5. **the dataset and code components** for the induction run.
- **Condition to start:** the pipeline must first produce **validated** induced motifs at scale. Until
  that exists, this paper does not go out — it is not written as an unproven architecture.
- **When:** when that validation exists, not before.

---

## Held back for now

Three things are deliberately **not** in the current plan:

- the **monograph** — consolidating everything into one book is a real goal, but it comes only after
  the papers above exist and hold up; there is no point planning the book before surviving the papers;
- the **programme / method / roadmap** text — its empirical support lives entirely in the findings
  paper, so on its own it would be thin; it waits for the eventual book;
- the **outlook** text — a closing chapter, not an article; it also waits for the book.

---

## Where the preprints and DOIs live, and why a personal site alone is not enough

A personal-site link is fine for "let people read it," but it does not do two things a deposit with a
DOI does — so do both: the site is the shopfront, a DOI deposit is the vault.

| Function | Personal site | Deposit + DOI |
|---|---|---|
| People read it | yes | yes |
| Citability (a stable reference) | weak | yes |
| **Priority** (proof of "I was first") | weak | strong |
| Permanence (outlives the hosting) | no | yes |
| Discoverability (scholarly search, indexing) | weak | yes |

- **A timestamp you control is weak evidence.** A date on your own site is set by you, so it counts
  for little in a priority dispute (**scooping** — someone publishing your openly posted idea first).
  An independent timestamp — a preprint or repository DOI, or at least public version history — is
  stamped by a third party and is what actually protects priority. Posting openly *helps* priority;
  posting only where you control the clock does not.
- **Link rot.** Personal sites are the shortest-lived category of scholarly link; most are dead within
  five to ten years. A repository (Zenodo, on long-term infrastructure) survives a change of domain or
  host, and a DOI keeps resolving even after the file moves.

**Practice:** a landing page on GitHub Pages **plus** a Zenodo DOI for each notable version (GitHub and
Zenodo integrate — a tagged release mints a DOI automatically). Both, at essentially no cost.

---

## Target venues by discipline (reference)

- **Computational / digital humanities:** *Journal of Cultural Analytics*; *Digital Scholarship in the
  Humanities*; the *Computational Humanities Research* conference.
- **Computational folkloristics:** *Fabula*; *Journal of American Folklore*; *Journal of Folklore
  Research*.
- **Cultural evolution / quantitative:** *Evolutionary Human Sciences* (Cambridge, open access — where
  folktale phylogenetics appears); *Cliodynamics*.
- **General science, for a single strong result:** *Royal Society Open Science*; *PLoS ONE*;
  *Humanities & Social Sciences Communications*.
- **Natural-language-processing for humanities:** LaTeCH-CLfL; NLP4DH; *Computational Humanities
  Research* proceedings.
- **Research software:** *Journal of Open Source Software*.
- **Open data:** *Journal of Open Humanities Data*.

---

## Tooling (reference)

- **Quarto** — the tool for the reading site: from the existing drafts it renders one website plus PDF
  plus ePub, with bibliographies, cross-references, and embedded interactive figures.
- **GitHub Pages** — free static hosting for the reading site and the interactive figures. Note: the
  figures' data files are not stored in the repository, so publishing them needs a build step (a
  continuous-integration job that generates the data and deploys the result).
- **A dynamic host** (Hugging Face Spaces or Fly.io) — for the live tool in release 4, which is a
  running service and cannot live on static hosting.
- **DOIs** — arXiv and the journals mint them automatically; Zenodo mints one per tagged GitHub release
  for the dataset and the code.

---

## Data and rights

All data used is under open Creative-Commons licences and all original authors are cited; the derived
datasets are released openly with provenance. Code is released under a standard open-source licence.
