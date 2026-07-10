# Release & dissemination plan

How the work reaches the public. The backbone is a small set of **academically recognised
publications**. Everything else — the datasets, the code, the live public tool, and the
program/outlook texts — is not a standalone item but a **component or requirement** of one of those
publications. Written to be read by someone who does not know the project.

Companion to [`monograph-outline.md`](monograph-outline.md) (how the parts compose) and
[`README.md`](README.md) (the drafts index).

---

## The releases

Six academic publications. Each block gives its title, where it goes, its goal, its exact contents,
what it needs, and when.

### 1. The survey — *Computational Folkloristics and the Induction of Motifs: A Survey*

- **Where:** preprint on arXiv (digital libraries) or Humanities Commons; submit to a review venue —
  *Journal of Cultural Analytics*, *Fabula*, or *Digital Scholarship in the Humanities* (or *ACM
  Computing Surveys* if the coverage is made broad enough).
- **Goal:** map the field of computational folkloristics and motif induction **for the whole
  community**, as an independent contribution — not as an appendix to this project.
- **Contents:** the two eras of the field (the classical index-and-topic-model era; the modern
  transformer-and-large-language-model era); a taxonomy of method families; tables of the field's
  datasets and methods; the hard lessons (motifs resist crisp boundaries; simple word-frequency
  baselines repeatedly match neural and large-language-model systems; large language models
  hallucinate examples); the conclusion that embeddings are best used as a **search / candidate-
  generation layer over a curated expert index**, not as an end-to-end classifier; and an
  open-problems agenda.
- **Needs, before release:** expand to full survey length; **write it from the field's point of
  view** — this project appears, if at all, as one example among many, not as the subject; clean the
  bibliography (remove the citations currently flagged as unverified).
- **When:** early — it is the lowest-risk, widest-reach piece (it does not depend on any unfinished
  result), and it establishes a presence in the field before the main results land. Out as soon as
  the expansion and citation cleanup are done. It later becomes the field-introduction chapter of the
  book, but goes out first on its own.

### 2. The findings paper — *Geography, Descent, and Genre in the Global Distribution of Folklore Motifs*

- **Where:** preprint on arXiv (statistics, or physics-and-society); submit to *Evolutionary Human
  Sciences* (Cambridge, open access) or *Royal Society Open Science*.
- **Goal:** the main scientific results of the project.
- **Contents:** areal diffusion versus inheritance down the language tree; a motif's time-depth read
  from the **shape of its distribution** rather than its content; two independent axes of theme
  ("what the myth explains" versus "how the tale is built").
- **Published together with it (its data and code backing, each a citable component, not a separate
  release):**
  - a frozen **dataset** on Zenodo — the derived theme taxonomy, the table of links between the three
    catalogues, the external joins (subsistence, language family), and the depth metrics;
  - a frozen **code snapshot** on Zenodo, via a tagged release on GitHub — the full pipeline and the
    analysis bench.
- **When:** now — the data is ready; freeze the dataset first, then post the preprint citing it.

### 3. The resource paper — *A Cross-Indexed Corpus and Analysis Bench for Comparative Mythology*

- **Where:** preprint on arXiv (digital libraries); submit to *Journal of Open Humanities Data* or the
  *Computational Humanities Research* conference.
- **Goal:** describe and formally publish the reusable corpus and the analysis tooling, so others can
  build on them.
- **Contents:** the table of links across the three motif catalogues; the semantic-search layer with
  its recall evaluation; the analysis bench. This paper is what formally publishes the dataset that
  the findings paper depends on.
- **Needs:** the dataset and code snapshots from the findings paper (shared, not duplicated).
- **When:** about a month out.

### 4. The software paper — *MythoScope: an open tool for comparative-mythology corpus analysis*

- **Where:** the *Journal of Open Source Software* — a peer-reviewed journal for research software.
- **Goal:** make the **communal tool itself** citable and peer-reviewed.
- **Its components and requirements:**
  - a live public **portal** (sections: Read · Explore · Programming interface · Data & code · About),
    hosted on Hugging Face Spaces or Fly.io — the interactive figures, a corpus browser, and an open
    programming interface;
  - **self-hostable in one command** (a container image), so the tool survives independently of the
    central instance;
  - the code snapshot, documentation, and tests.
- **When:** about a month out, once the live portal is working.

### 5. The motif-induction paper — *Inducing Motifs from Raw Text: Pipeline and Evaluation*

- **Where:** a natural-language-processing-for-humanities venue — LaTeCH-CLfL, NLP4DH, or the
  *Computational Humanities Research* conference.
- **Goal:** the natural-language contribution — extracting motifs directly from raw source texts.
- **Contents:** the raw-text pipeline, with an evaluation of its output against simple baseline
  methods.
- **Condition to start:** the pipeline must first produce **validated** induced motifs at scale. Until
  that exists, this paper does not go out — it is not written as an unproven architecture.
- **When:** when that validation exists, not before.

### 6. The monograph — *Computational Comparative Mythology*

- **Where:** an online book (assembled with Quarto) carrying one overarching DOI; pitched to
  *Cambridge Elements* or *Language Science Press*.
- **Goal:** consolidate the whole programme into one book.
- **Contents:** the programme-and-method text as the opening; the resource and findings chapters; the
  survey as the field-introduction chapter; a closing chapter on open problems and outlook. **The
  programme text and the outlook text live only here** — they are not released as separate papers.
- **Needs:** the papers above brought to a finished state.
- **When:** after the papers are out.

---

## Not a standalone release

Two texts are deliberately **not** published on their own; they exist only inside the book (release 6):

- the **programme / method / roadmap** text — its empirical support lives entirely in the findings
  paper, so on its own it would be thin; it serves as the book's opening;
- the **outlook** text — it is a closing chapter, not an article.

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
- **Book form:** *Cambridge Elements* (short-form, ~30k words); *Language Science Press* (open access).

---

## Tooling (reference)

- **Quarto book** — the single tool for the monograph and the reading site: from the existing drafts it
  renders one website plus PDF plus ePub. It supports bibliographies, cross-references, and embedded
  interactive figures.
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
