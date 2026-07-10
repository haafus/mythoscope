# Release & dissemination plan

How the *Computational Comparative Mythology* series, its data, and its interactive figures reach the
public. Working plan — sequencing, venues, tooling, and rights. Companion to
[`monograph-outline.md`](monograph-outline.md) (how the parts compose) and [`README.md`](README.md)
(the series index).

## 0. What is being released

| Asset | Form | Home |
|---|---|---|
| The four papers + Part V | Markdown drafts → typeset | `docs/papers/*-draft.md` |
| Interactive figures | ~40 self-contained mockups | `mockups/` (need a build step to publish, `data.js` is git-ignored) |
| Derived data | `narrative_taxonomy.json`, the crosswalk | `mockups/41-…/`, `outputs/` |
| Code / pipeline | `corpus → embeddings → projections → graphs → motifs` | `src/` |

The interactive mockups are the project's distinctive public asset — most papers can't offer live
exploration — so hosting them is a first-class goal, not an afterthought.

## 1. Preprints — how many, where

Do **not** fragment into 4–5 tiny preprints (the program and outlook pieces are too short to stand
alone). Target **2–3 preprints + separate DOIs for data/code**:

- **Umbrella report (whole series)** → **OSF Preprints** or **Zenodo** — one citable DOI for the
  collected work, for the monograph/Element framing. Lowest barrier, any discipline, instant.
- **Findings** (the strongest novel science) → **arXiv** (`stat.AP` / `physics.soc-ph`), aimed at
  *Royal Society Open Science* or *Evolutionary Human Sciences*.
- **Machine / induction** (the NLP+DH systems paper) → **arXiv** `cs.CL` / `cs.DL`, aimed at a DH/NLP
  venue.
- *(optional)* **Survey** → arXiv `cs.DL` or **Humanities Commons**.
- **Dataset** (`narrative_taxonomy.json`, crosswalk) and **code release** → their own **Zenodo DOIs**
  (GitHub↔Zenodo integration mints a DOI per tagged release) — standard practice, separate from the
  paper preprints.

**Preprint service rules to respect (all services):** hold the rights or apply a licence (default
**CC-BY** for reach; verify against the target journal's policy via SHERPA/RoMEO); co-author consent;
no third-party copyrighted data beyond its licence (**Berezkin — access via its query engine, don't
redistribute raw**); label "working draft, not peer-reviewed"; posts are versioned and cannot be fully
deleted (withdrawal leaves a tombstone). **arXiv specifically** needs an **endorsement** for a first
submission to a category and moderates topic fit; LaTeX preferred (it compiles), PDF accepted.

### 1.1 Why not a personal site only

A personal-site URL is fine for "let people read it," but it does not close two functions a deposit
with a DOI does — so **do both** (site as the shopfront, a DOI deposit as the vault), not site-only:

| Function | Personal site | Deposit + DOI |
|---|---|---|
| People read it | ✅ | ✅ |
| Citability (stable reference) | ⚠️ weak | ✅ |
| **Priority** (proof of "I was first") | ⚠️ weak | ✅ strong |
| Permanence (outlives the hosting) | ❌ | ✅ |
| Discoverability (Scholar, indexing) | ⚠️ | ✅ |

- **Timestamp you control is weak evidence.** A date on your own site is set by *you*, so it counts for
  little in a priority dispute (**scooping** — someone publishing your openly-posted idea first). An
  independent timestamp — a preprint/repository DOI, or at least public git history — is stamped by a
  third party and is what actually protects priority. Posting openly *helps* priority; posting only
  where you control the clock does not.
- **Link rot.** Personal sites are the shortest-lived category of scholarly link; most are dead within
  5–10 years. A repository (Zenodo, CERN-backed) survives a domain/host change; a DOI resolves even
  after the file moves.

**Verdict:** site-only is reasonable for early sharing, not safe for priority or longevity. Landing on
GitHub Pages **plus** a Zenodo DOI per notable version (GitHub↔Zenodo, see §4) gets both at ~no cost.

## 2. Target venues by discipline

- **Computational / Digital Humanities:** *Journal of Cultural Analytics*; *Digital Scholarship in the
  Humanities*; **Computational Humanities Research (CHR)** — best overall fit.
- **Computational folkloristics:** *Fabula*; *Journal of American Folklore* ("Big Folklore"); *Journal
  of Folklore Research*.
- **Cultural evolution / quantitative:** **Evolutionary Human Sciences** (Cambridge, open access) —
  direct analogue, where folktale phylogenetics appears; *Cliodynamics*.
- **General-science (for a single strong finding):** *Royal Society Open Science*; *PLoS ONE*;
  *Humanities & Social Sciences Communications*.
- **NLP/DH (machine paper):** LaTeCH-CLfL; NLP4DH; CHR proceedings.
- **Book form:** **Cambridge Elements** (short-form ~30k words — the current volume is close to a fit);
  *Language Science Press* (open access).

**Split strategy:** Findings → RSOS / EHS; Machine → DH/NLP venue; Survey → Fabula / review venue;
and/or the whole as a **Cambridge Element**.

## 3. Volume note

~15k words / ~30 typeset pages across the four papers + Part V. That is: article-sized for *Machine*
and *Findings*; short for *Program* and *Field*; and **far below a full monograph** (70–120k). So the
current object is a **paper series / short book (Element)**, not yet a monograph; "monograph" is the
target shape, requiring ~4–8× expansion (fuller methods, per-result chapters with figures, case
studies, appendices).

## 4. Dissemination tooling

- **Quarto book** — the single tool of choice. From the existing Markdown it renders **one website +
  PDF + ePub**: `_quarto.yml` (`project: type: book`, `book.chapters:` = the `*-draft.md` files),
  `quarto render`, then `quarto publish gh-pages`. Supports BibTeX+CSL citations (turn the unified
  reference list into `references.bib`), cross-refs, and **embedded HTML/iframes** for the live
  mockups.
- **GitHub Pages** — free static hosting: *Settings → Pages*, deploy from `/docs`, a `gh-pages`
  branch, or a **GitHub Action**. URL `https://haafus.github.io/mythoscope/`. A landing page links the
  papers + the live mockups. **Caveat:** mockup `data.js` is git-ignored, so publishing the mockups
  needs a build step (a CI job that runs the needed `build_data.py` and deploys the output), or
  committing the built `data.js` for the chosen public mockups only.
- **DOIs** — arXiv (auto), OSF (auto), Zenodo (per GitHub release) for citability.
- **Reproducibility** — Binder/Colab "reproduce in one command"; the export bundle.
- **Popular layer** — a long-form essay for a general audience (the deep celestial substrate; the
  swan-maiden; the two theme axes) + a data-viz essay built on the mockups; a CHR/DH talk.

## 5. Sequencing

1. **Now** — keep drafts public and clearly marked; finish the unified `references.bib`.
2. **Scaffold** — add `_quarto.yml` + a Pages/CI workflow (render Quarto **and** build the public
   mockups' `data.js`); do it on a branch/PR so `main` stays intact.
3. **Interactive site live** — papers + mockups on GitHub Pages; landing page.
4. **DOIs** — Zenodo release for data+code; OSF/Zenodo umbrella report.
5. **Preprints** — arXiv Findings and Machine once submission-ready (secure an arXiv endorsement early).
6. **Submit** — to the chosen venues; check each journal's preprint policy first.

## 6. Rights & licensing checklist

- Text/figures: **CC-BY** (unless a target journal forbids prior CC posting).
- Code: an OSI licence (MIT/Apache-2.0).
- Derived data (`narrative_taxonomy.json`): open, with provenance.
- Third-party indices: **do not redistribute raw Berezkin/aggregator data**; ship the pipeline +
  derived analyses with access notes (documented in `docs/research/` and `docs/motifs/`).
