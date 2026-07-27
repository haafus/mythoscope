# Public documentation section — composition plan

A plan for the project's public-facing documentation on the website: clear, vivid,
representative, engaging to specialists (computational folklorists, comparative
mythologists, digital-humanities researchers), SEO-aware — but deliberately *not*
bloated. The public layer is **English** (Element and the surveys are already
English; the Russian source docs are flagged for translation below).

## 0. Starting picture

- **The site** is a FastAPI-served single-page app. Public nav: Sources · Similarity ·
  Ages · Realms · Beings · Atlas · Motifs · (i) About. There is effectively **no prose
  documentation** on the site yet — three of the four About tabs are literal
  `insert your text` placeholders (`src/server/web/assets/page-about.js`).
- **Almost all the public substance already exists in the repo**, but interleaved with
  internal ADRs, roadmaps, and parsing logs. The job is not to write from scratch — it
  is to **select, strip the internal parts, and translate** the few Russian source docs
  (`docs/how-to.md`, `docs/motifs/motif-index-data-sources.md`, `docs/motifs/crosswalk.md`,
  `docs/research/motif-induction-review.md`).
- A reader-facing narrative already exists: the monograph **"A Natural History of the
  Motif"** (`docs/papers/element/01`–`11`), written "to be read by someone who does not
  know the project." That is the core.

## 1. Composition principles ("vivid, but not excessive")

1. **One canonical public layer.** We do not mirror all of `docs/` onto the site. Publish
   ~10–12 pages; everything reasoning-flavoured (proposals, reviews, known-issues,
   archive, parsing logs) stays in the repo for whoever reaches GitHub.
2. **Specialist-first, with a human entry point.** Top of funnel: a vivid thesis and case
   studies. Depth below: references and surveys that people search for by name.
3. **Honesty as an engagement device.** The project's most distinctive asset is not
   "we found the origin of myth" — it is the *negative results and de-confounding*: "a
   deep inheritance and a wide diffusion cast the same shadow." For an academic audience
   this is a stronger trust signal than any hype.
4. **SEO through surveys and reference, not marketing.** Literature surveys and a
   documented crosswalk are what accumulate inbound links and citations. They *are* the
   landing pages.
5. **The live tool is part of the docs.** The unique edge over a paper: next to a
   "what we found" page sits a "go turn the knobs yourself" button (Atlas / Similarity /
   Motifs). That is dwell time and retention.

## 2. Proposed composition — 3 tiers, ~12 pages

### Tier A — The argument (human entry, narrative)

| Page | What | Source | Readiness |
|---|---|---|---|
| A1 | **Overview — "A Natural History of the Motif."** H1 = the thesis: *"The geography of a myth is written in where it is attested, not in what it says."* What MythoScope is (tool + programme), one screen, CTA into the live views. | README + Element 01 | near-ready |
| A2 | **What we found.** Distilled results: areal diffusion dominates (2,311/2,775 motifs), a datable ~1% "fairy-tale core" ≈5,500 BP, a small deep substrate (320/480), the irreducibility limit. Stat tiles + the honest framing. | Element 06/10, 4-findings | light edit |
| A3 | **Three motifs through the machine.** Case studies: the swan-maiden, sun-and-moon-as-kin, the fished-up earth. Vivid, shareable vignettes. | Element 09 | near-ready |
| A4 | **How it works.** The pipeline corpus→embeddings→projections→graphs + the motif crosswalk; the natural-history framing; honest scope (induction is built but not yet validated at scale). | Element 03 + how-to + proposals | assembly |

### Tier B — Reference & surveys (SEO and citation magnets — the specialist draw)

| Page | What | Source | Readiness |
|---|---|---|---|
| B1 | **The motif crosswalk (TMI ↔ ATU ↔ Berezkin).** Flagship. ~7,300 confirmed cross-index edges + hypothesis layers; how it is built, how to use and cite. Almost no open-access equivalent exists (the nearest, the DFKI ontology, "was never released"). | crosswalk.md + link-accounting | edit + **translate** |
| B2 | **The three indexes.** Reference pages for TMI / ATU / Berezkin (structure, composition, provenance). The Berezkin one in English is rare. | tmi/atu/berezkin-reference.md | ready (strip defect logs) |
| B3 | **Field survey: computational folkloristics.** The definitive field survey (two eras) + the "landscape" (people, labs, journals, conferences). A classic link magnet. | comp-folk-survey + landscape | strip internal tail |
| B4 | **Corpus-sourcing atlas.** ~40 traditions × repositories × licences, EASY/MODERATE/HARD verdicts. Exactly the "where do I get corpus X" query DH/NLP people run. | corpus-sourcing-survey | ready |
| B5 | **How the great encyclopedias carve the world.** Survey of 15 reference works + the literate/oral-bias thesis. Broad reach, genuinely novel synthesis. | encyclopedias-survey | strip internal tail |
| B6 | **The 14 regions.** A corpus-first taxonomy of world mythology + the colour system (OKLCH, colour-blind-robust by construction). | regions.md | edit |

*(B2 can be one page with three sections; B3 can be the survey + landscape as two linked pages.)*

### Tier C — Participate (engagement & contributors)

| Page | What | Source | Readiness |
|---|---|---|---|
| C1 | **Contribute.** How to help: corpus, code, data, community; the **awesome-computational-mythology** idea; the "just view the data" path (export bundle, no torch). | net-new + README roadmap + how-to | to write |
| C2 | **Resources.** Data (export bundles), the live **API `/docs` (OpenAPI)**, GitHub, preprints + bibliography, licences. | net-new + how-to | to write |

## 3. Where it lives

Recommendation: **do not stand up a separate docs engine** (mkdocs / docusaurus is itself
the "excess"). Extend the existing scaffold instead — promote `/about` into a full **"Docs"**
hub inside the same SPA, with a left table of contents over the three tiers (A/B/C) and
content as server-rendered markdown pages. Tier A maps straight onto the current About tabs
(Vision→A1, Methodology→A4), Contribute→C1, Resources→C2; the Tier-B pages are added as hub
entries.

Alternative, if maximum SEO/citability is the priority: publish the surveys (B3–B5) and the
crosswalk (B1) as **standalone static URLs** with clean paths and full `<title>`/`<meta>`
— crawlers handle these better than SPA hash routing. This is the one real fork to settle
before starting (see §7).

## 4. SEO layer

- **Magnets** are B1 and B3–B5. Give them canonical titles and keyword clusters:
  - domain: *computational folkloristics, comparative mythology, cultural evolution,
    folktale phylogenetics, digital humanities*;
  - indexes/names (high domain-SEO): *Thompson Motif-Index (TMI), Aarne–Thompson–Uther
    (ATU), Berezkin areal catalogue, Uther, Aarne, Stith Thompson, Yuri Berezkin,
    Julien d'Huy, Jamshid Tehrani*;
  - methods: *BGE-M3, UMAP, ancestral-state reconstruction, Galton's problem, areal
    diffusion, degree-corrected block model, motif induction*.
- **Internal linking via the hub:** A-pages link down to B/reference; B-pages cross-link
  (survey↔landscape↔atlas↔encyclopedias form one coherent "Research" cluster).
- **Citability:** a "How to cite" block + DOI (Zenodo/arXiv preprint from `release-plan`)
  on B1 and the surveys, linking back to the site.
- **Live views = unique content** for queries like "interactive motif map / semantic space
  of mythology" — which text-only competitors do not have.

## 5. Engagement layer

- **Pull-quotes / tiles** from the ready-made phrasings: *"a spine, not a skeleton"*,
  *"what a motif is about is not how old it is"*, *"neither camp was wrong; each described
  a different one percent"*, *"depth is a property of a distribution, not of meaning"*, and
  the numbers (2,311/2,775; ×2.6; r=+0.48; 53% of the catalogue in two catch-alls).
- **Case studies (A3)** are the most shareable format; each ends in a button into the live
  Atlas/Motifs.
- **Honesty as a trust anchor:** the results page states the irreducibility limit and that
  induction-from-text is not yet validated — that is what hooks the sceptical specialist.
- **Clear CTAs:** "Explore the live data", "Read the paper", "Contribute a corpus",
  "Star on GitHub / join the awesome-list".

## 6. What we deliberately do **not** publish (the "not excessive" discipline)

Stays internal, in the repo: all `docs/proposals/*` and `archive/*` (ADRs/roadmaps),
`docs/reviews/*`, `known-issues.md`, `stage-iv-validation.md`, `embeddings-gpu-howto.md`,
`docs/motifs/discovery-and-parsing.md`, `docs/motifs/crosswalk/berezkin-unresolved-citations.md`,
`link-accounting.md`/`parallels_report.md`, `release-plan.md`, `monograph-outline.md`, and
the internal "tails" of the surveys (the "Implications for mythoscope…" sections, mockup
numbers, unpublished metrics in `dating-and-chronology-methods.md`). The `papers/1`–`5`
drafts are not published separately — they are already distilled into the Element.

## 7. Order and open decisions

- **Phase 1 (minimum, mostly ready):** A1, A2, A3 + B1 (crosswalk) + one magnet survey
  (B4 corpus-sourcing — ready and already English). Plus fill the empty About tabs.
- **Phase 2:** the remaining surveys B3/B5, references B2, regions B6, methodology A4.
- **Phase 3:** Contribute/Resources (C1/C2), the awesome-list, DOI preprints.

**Translation debt:** B1 and `motif-index-data-sources`, `how-to`, `motif-induction-review`
are in Russian; the public layer ships in English (Element and the surveys are already
English).

Open fork to settle before starting: **the surveys/crosswalk inside the SPA vs. as
standalone static URLs for SEO** (§3). The public-layer language is decided: English.
