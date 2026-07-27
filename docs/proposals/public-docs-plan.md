# Public documentation section — composition plan

A plan for the project's public-facing documentation on the website: clear, vivid,
representative, engaging to specialists (computational folklorists, comparative
mythologists, digital-humanities researchers), SEO-aware — but deliberately *not*
bloated. The public layer is **English** (Element and the surveys are already
English; the Russian source docs are flagged for translation below).

Extracted public-site copy from the Figma mockup is preserved verbatim in
[`figma-mythosemantic-copy.md`](figma-mythosemantic-copy.md) and mapped onto sections in §14.

## Decisions & open questions (register)

**Decided:**
1. **Public-layer language: English.** (§1, §7)
2. **Delivery: hybrid** — the interactive app stays an SPA; public docs (Tiers A/B) + the
   landing are static pages at clean URLs. (§8)
3. **Static precompile (SSG) is primary, not on-request SSR.** SSR only as an optional
   `--watch` dev preview. (§8, §12.2)
4. **Build via `scripts/build_docs.py`** (a standalone offline script, not a `mytho` CLI
   subcommand). (§12.2)
5. **Output directly under the web root** `src/server/web/` (next to `index.html`/`assets/`),
   **not** `outputs/` and **no `site/` wrapper**; served by extending the existing startup
   mount in `create_app`. (§12.2, §12.5)

6. **Positioning register (A):** Vision/About carries the manifesto; "What we found" carries
   results; soften "we don't know what structures exist" to "map the space of deep
   structures" so it doesn't undercut the Element's honesty. (§14.1)
7. **Newsletter provider (B): Buttondown** — privacy-respecting, embeddable, cheap, developer-
   ergonomic; matches the audience. (Substack only if a public publication presence is wanted.)
   (§10)
8. **Contact (C): a visible role email, not a form.** One public inbox at launch —
   **`hello@mythoscope.io`** — with topical aliases (`research@`, `corpora@`, …) forwarding to
   it, added later. Domain is **mythoscope.io** (not `.org`). (§10, §14.3)
9. **Generated HTML in git (E): committed.** The server just serves files; deploy needs no CI
   rebuild; fits the ephemeral-container model (clone → already serves). (§12.2)
10. **Nav-hub label (D): "Research ▾"** — the word on the docs entry in the top nav (replaces
    the bare "i"), opening the tiered TOC. (§9)
11. **API: no product API now.** The server's auto-generated OpenAPI (`/docs`, `/redoc`,
    `/openapi.json`) is exposed read-only and linked from Resources as *experimental — no
    stability guarantees*; investment goes to **bulk data downloads + DOIs**, not an API. (§15)
12. **Citability: create citable objects.** Zenodo DOIs (repo release, the crosswalk dataset,
    each survey), a `CITATION.cff`, a preprint (arXiv cs.CL / SocArXiv / HCommons CORE). Nothing
    is formally citable until these exist. (§15)
13. **Credit & authorship: written policy.** An attribution ladder (acknowledgement → data/tool
    citation → co-authorship, with CRediT roles + criteria; CARE for Indigenous data), a
    `CONTRIBUTORS.md` + `CITATION.cff`, and a public **Credit** page. (§15, C5)
14. **New pages:** **Publications** (C3, the citation hub), **Updates/Notes** (C4, the light
    blog — home of "motif/mockup of the month"), **Credit & authorship** (C5). "Learn"/tutorials
    stay deferred. (§2)
15. **Community/chat: async-first.** GitHub Discussions (owned, indexable) + newsletter +
    quarterly calls are primary; real-time chat is deferred and, when added, **Zulip** (research
    register) or **Discord** (reach) — never an empty server. (GTM §3)

16. **Name spelling: `Mythoscope`** (single capital — matches the microscope/telescope
    instrument lineage the name's meaning rests on; reads as a coined scholarly term, not a
    software brand). "MYTHOSCOPE" only as a logotype; `mythoscope.io` lowercase. **Normalised
    repo-wide** (production + docs; frozen mockups left as-is). (§9)

**Open:** none — all forks resolved. Execution sequence in §16.

**Companion:** the acquisition/retention strategy lives in [`go-to-market.md`](go-to-market.md);
the field resource list in [`../awesome-computational-mythology.md`](../awesome-computational-mythology.md).

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
   ~16 pages; everything reasoning-flavoured (proposals, reviews, known-issues,
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

## 2. Proposed composition — 3 tiers, ~16 pages

### Tier A — The argument (human entry, narrative)

| Page | What | Source | Readiness |
|---|---|---|---|
| A1 | **Overview (landing, `/`).** H1 = the thesis: *"The geography of a myth is written in where it is attested, not in what it says."* What Mythoscope is (tool + programme), one screen, CTA into the live views. | README + Element 01 + Figma vision pitch | near-ready |
| A2 | **What we found.** Distilled results: areal diffusion dominates (2,311/2,775 motifs), a datable ~1% "fairy-tale core" ≈5,500 BP, a small deep substrate (320/480), the irreducibility limit. Stat tiles + the honest framing. | Element 06/10, 4-findings | light edit |
| A3 | **Three motifs through the machine.** Case studies: the swan-maiden, sun-and-moon-as-kin, the fished-up earth. Vivid, shareable vignettes. | Element 09 | near-ready |
| A4 | **How it works.** The pipeline corpus→embeddings→projections→graphs + the motif crosswalk; the natural-history framing; honest scope (induction is built but not yet validated at scale). | Element 03 + how-to + proposals | assembly |
| A5 | **About / Vision.** "Collaborative Semantic Archaeology"; the *why* — the "Why collaborative infrastructure for theory discovery" manifesto (scale/algorithms/collaboration/open-infra, deductive→inductive); the `-scope` name story (telescope/microscope → new lens). Absorbs the current About tabs. Reconcile register per §14.1. | Figma (§14) + Element 01 | assembly + **translate** |

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
| C1 | **Contribute.** How to help: corpus, code, data, community; the **awesome-computational-mythology** list; the "just view the data" path (export bundle, no torch). Backbone = the Figma "Join the Collaboration" page (15 collaboration types), trimmed to real offerings. | Figma (§14) + README roadmap + how-to | trim/adapt |
| C2 | **Resources.** Data downloads + DOIs, the read-only **OpenAPI** (`/docs`, marked experimental — §15), GitHub, the awesome-list, licences; digital text-library list from Figma (dedupe vs B4). | Figma (§14) + how-to | to write |
| C3 | **Publications.** The citation hub: papers, preprints, DOIs, each with a "How to cite" block; links to Scholar / HCommons / ORCID. Maps to the Figma sitemap's Research→Publications. | §15 + release-plan | to write |
| C4 | **Updates / Notes.** A light blog — home of "**motif of the month**" and "**mockup of the month**"; fed to the newsletter and cross-posted (GTM). The return-visit hook. | net-new + mockups + Element | to write |
| C5 | **Credit & authorship.** The attribution ladder (acknowledgement → data/tool citation → co-authorship), CRediT roles + criteria, CARE for Indigenous data; mirrors `CONTRIBUTORS.md`/`CITATION.cff`. | §15 | to write |

**Out of initial scope (kept lean):** *Learn* (tutorials/workshops) is deferred — net-new,
not needed for the specialist/SEO launch. *Team / Partners* pages wait until they are real
(§14.3). (The Figma sitemap's "News & Events" is covered by C4 Updates/Notes.)

## 3. Where it lives (decided in §8 — hybrid)

**No separate docs engine** (mkdocs / docusaurus is itself the "excess"). The delivery was
worked through and **decided in §8**: the interactive app stays an SPA (moved to `/app`), and
the public docs (Tiers A/B/C) + the landing are **statically pre-rendered pages at clean
URLs**, built from a curated markdown tree through one shared shell template and served as
plain files (§12). The three-tier table of contents is reached from a **"Research ▾"** nav hub
(§9); the current About-tab copy (Vision, Methodology, Contribute, Resources) is absorbed into
Tier A/C pages. Full URL map, rendering pipeline, and phasing are in §12; navigation in §9.

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

The public-layer language is decided: English. The SPA-vs-static-URL fork raised in §3 is
resolved in §8 (hybrid). Navigation/entry, chrome (footer/social/newsletter/contact), and
copy-sourcing from Figma are worked out in §9–§11.

## 8. Delivery: SPA vs. standalone static URLs — **DECIDED: hybrid**

**Decision (accepted).** The hybrid is adopted: the interactive app stays an SPA; the
public documentation (Tiers A/B) and the overview landing are **statically pre-rendered
(SSG) pages at clean URLs**, English, generated at build time from a curated markdown tree
through one shared shell template, and served as plain files. Implementation is specified
in §12. The rest of this section is the reasoning behind the choice.

**Why precompile rather than render-on-request.** For documentation — content that changes
rarely, is identical for every visitor, and does not depend on live data — static
generation is the right default, not a later optimisation. It makes the *runtime simpler*
(serve files via the existing `StaticFiles` mount; no markdown renderer or template engine
in the request path), and it is the only path that yields the §13 payoffs (rich OG cards,
low TTFB, CDN cacheability). The renderer work is *identical* to SSR — the same md→template→
HTML step — it just runs at build time instead of per request, so precompiling is "the same
code, run earlier," not more code. The one real cost is **build discipline**: a content edit
requires a rebuild (`scripts/build_docs.py`, ideally wired to CI so a push regenerates the site),
and any live figure (e.g. crosswalk edge counts) must be **injected at build time** from
`outputs/`, not rendered at runtime — an acceptable snapshot for these pages. On-request SSR
is kept only as an optional local `--watch` authoring preview, never in production.

The current site is an SPA with **hash routing** (`#/corpus`, `#/about`). To a crawler,
everything after `#` is one page — no per-URL `<title>`/`<meta>`, no separate index entry.
For the *app* (interactive views) that is fine; they need not be indexed. For the *docs* it
is fatal: the surveys and the crosswalk — the whole reason for the SEO effort — would be
invisible.

What each option buys:

| Axis | Inside the SPA (as today) | Standalone static URLs (SSR/prerender) |
|---|---|---|
| **Indexing / SEO** | Poor: hash content is barely crawled; even History-API routing needs server HTML per URL | **Good**: real HTML, own `<title>/<meta>/OG` per page |
| **Citability / links** | Ugly, fragile `#/…` URLs — bad in a footnote | **Stable clean paths** (`/crosswalk`, `/research/…`); OG cards |
| **Build cost** | Cheap: fill tabs, reuse styling | Moderate: markdown→HTML render + template + `sitemap.xml`. But docs are *already* markdown and FastAPI *already* serves static — an addition, not a rewrite |
| **Content upkeep** | Awkward: prose as HTML in JS template strings (see `page-about.js`) | **Easy**: edit `.md`, server renders |
| **UX / unity** | One shell, instant transitions, live views at hand | Pages must inherit the same header/CSS or feel like a different site (solved with a shared template) |

**Resolution — hybrid.** Draw the line by the nature of the content, not by convenience:

- **The app stays an SPA.** Sources / Similarity / Ages / Realms / Beings / Atlas / Motifs
  are a tool; they need no indexing. Untouched.
- **Public docs (Tiers A and B) become server-rendered static pages at clean paths**,
  rendered by FastAPI from the existing markdown, with a shared template (same
  header/nav/CSS/theme) so it reads as one site. Per page: `<title>`,
  `<meta name="description">`, OG tags; plus `sitemap.xml` and canonical links.

Why not "all SPA" (magnets B1/B3–B5 would be unindexed — §4 collapses) and not a separate
docs engine (docusaurus/mkdocs is the "excess" we are avoiding; markdown and the server
already exist). Cost is small and one-off: one markdown→HTML route, one wrapper template,
a generated `sitemap.xml`; after that, adding a page = drop a `.md` file. A later
build-time precompile of those `.md` to static `.html` (richer OG, faster TTFB, CDN cache)
is an optimisation, not a blocker.

## 9. Navigation and the entry point

The lone unlabelled **"i"** at the end of the nav is the weakest possible door to the
section the whole specialist/SEO bet rests on: no label (low affordance), "info/about"
semantics rather than "read/research", and a tail position that reads as a footer
afterthought. But the main row is already dense (7 tool tabs), so the goal is **not an 8th
equal button** — it is to separate two different layers: *tools* (app) and *reading*
(docs).

Recommended combination (not a single trick):

- **A labelled hub with a dropdown as the primary entry.** Replace "i" with **"Research ▾"**
  (or "Docs ▾") that expands the tiered TOC (Argument / Reference & Surveys / Participate).
  The main row gains only one labelled slot; the whole section lives behind it. The section
  already has internal tabs (Vision|Methodology|Contribute|Resources), so a second nav level
  is natural.
- **Two visual zones.** Tools left, "Research" as a separate right-aligned group (divider or
  different weight): "turn the data on the left, read on the right."
- **Logo → home/overview (almost free, do regardless).** Clicking the logo lands on the
  overview page — a standard convention that makes the docs entry the largest element on the
  page without adding a nav item.
- **Contextual "learn more" from the views (complement, not replacement).** Motifs → the
  crosswalk page, Atlas → "14 regions", Similarity → methodology. Distributes discovery to
  where curiosity strikes and doubles as the §4 internal linking.

Naming (decided D): the hub is labelled **"Research ▾"** — not "About"/"Docs"; for an academic
audience "Research" signals substance. A tiny separate **"About"** (vision/project, = page A5)
stays distinct from the Research hub (surveys + crosswalk) — different promises.

The deeper fix behind the "it feels hidden" feeling: the root route is `/corpus`, so a cold
visitor lands **straight in a data table with no framing**. The site has no front door at
all. Making the overview landing the root (tools behind an "Explore" CTA) inverts the
funnel — docs become the door, not a back alley — and matches the static-landing choice in
§8.

**Final nav structure (decided):** the concrete header/nav diagram lives in the canonical map
[`public-docs-structure.md`](public-docs-structure.md) (kept single-source to avoid drift). In
short:

- **Two hubs, one row:** **Explore ▾** = the live SPA views (the tool); **Research ▾** = the
  static docs TOC (Tiers A–C). Plus a small **About** and a **GitHub** star icon. The seven
  tool tabs collapse into the one Explore dropdown, freeing the row.
- **Landing `/`** is Overview (A1); the logo returns there.
- **Contextual links** from the views into the docs (Motifs→Crosswalk, Atlas→14 regions,
  Similarity→How it works) close the loop.

## 10. Chrome: footer, social, newsletter, contact, copyright

The site currently has **no footer** (in `index.html`, `#app` follows `<nav>` directly).
Introduce one; it absorbs most of this. Principle — **three zones, each with one job** — so
nothing here bloats the main nav:

- **Header** stays minimal: nav + a single **GitHub icon** (a live "Star on GitHub" CTA for
  an open-source research tool) + the Research entry. Nothing else.
- **Footer** is the home for everything administrative/contact: copyright + licence, socials,
  contact email, a compact newsletter field. In the SPA it lives **outside `#app`** (static
  in `index.html`), so it persists across routes, never re-renders, and gives crawlers a
  stable site-wide link block (an SEO plus).
- **Resources / Contribute page** holds the "rich" versions: the full newsletter form, a
  cite block, the complete contact + social set, data/API links.

Placement per element:

| Element | Primary place | Reinforcement |
|---|---|---|
| **Copyright + licence** | Footer, one line: `© 2026 Mythoscope · CC-BY-SA` (+ data-licence link) | — |
| **GitHub** | **Header icon** (live CTA) | Again in the footer social set |
| **Other socials** | Footer (icon set) | Resources page |
| **Contact email** | Footer (`mailto:hello@mythoscope.io`) — one public inbox; topical aliases (`research@`, `corpora@`…) forward to it, added later | Contribute/Resources — where collaborators look |
| **Newsletter** | **Compact field in the footer** ("Get updates on new findings — email → Subscribe"), posting to **Buttondown** | Full block on Resources + a soft CTA at the end of warm pages (What we found / case studies) |

Two caveats:
- **Full-bleed views.** Atlas/Similarity are full-height flex workspaces; a full footer
  fights the app feel. Use a thin one-line footer on document pages and hide it (or keep it
  ultra-slim) on the interactive views — footer split by route nature, like the docs
  themselves.
- **Newsletter is not just UI.** A working subscription needs a backend/provider — **decided:
  Buttondown** (the form posts to its API). For this audience avoid pop-up modals (specialists
  find them abrasive) — an unobtrusive footer field plus a warm end-of-page CTA.

**Final footer contents (decided):** three compact columns + a bottom line.
- **Explore / Read:** Overview · What we found · Crosswalk · Surveys · Contribute · Publications
  (quick links into the docs).
- **Connect (socials, from the Figma set):** GitHub · Bluesky · Mastodon · YouTube · Substack ·
  Discord *(when live)* · `hello@mythoscope.io`. *(X optional; Discord only once the community
  exists — §GTM.)*
- **Get updates:** the compact **Buttondown** newsletter field.
- **Bottom line:** `© 2026 Mythoscope · content CC-BY-SA · data CC-BY · code MIT` · **Cite**
  (→ Publications) · **API** (`/docs`, experimental) · **awesome-computational-mythology**.
- Thin/one-line on `/app` views; full on document pages (persistent, outside `#app`).

## 11. Sourcing copy from a Figma mockup (operational note)

If public copy is drafted in Figma, the reliable extraction path is the **Figma REST API**
(no Figma tool is connected to the working environment; a private file cannot be read from a
public link — it returns an empty JS shell, the same SPA effect as §8). Needed inputs:

1. **File key** — from the URL: `figma.com/design/<FILE_KEY>/…`.
2. **Personal access token** — Figma → Settings → Security → Personal access tokens, scope
   **`file_content:read`** (read-only). A secret: pass it out-of-band so it never lands in a
   commit; used only at request time, never stored or pushed.

Then `GET https://api.figma.com/v1/files/<FILE_KEY>` with header `X-Figma-Token`, walk the
document tree, and collect every `type == "TEXT"` node's `characters` field — verbatim text
with the frame/page hierarchy preserved (exportable to markdown/JSON keyed by frame name).
For a specific frame, pass its `node-id` (from `?node-id=…`) to
`GET /v1/files/<key>/nodes?ids=…`. Outbound HTTPS goes through the proxy — `api.figma.com`
should pass. Avoid screenshots+OCR: it drops diacritics (Ténèze/Polívka), which this corpus
is full of. Alternative to a manual token: connect a Figma connector/MCP (OAuth) to the
session.

## 12. Implementation plan for the hybrid (the accepted delivery)

The current server (`src/server/run_server.py`) mounts `/assets` as static, registers the
API routers, and serves `index.html` (the SPA) at `/`. Hash routes (`#/corpus`, …) live
inside that one HTML entry and **never collide** with real path routes (`/crosswalk`), so
both layers coexist on one origin. The plan adds a documentation layer alongside the SPA;
it does not touch the API or the app's behaviour.

### 12.1 URL map

- **App (SPA, unchanged):** served at **`/app`** (`/app#/corpus`, `/app#/embeddings`, …).
  One HTML entry, hash routing inside. The in-nav links move from `#/corpus` to
  `/app#/corpus`; a one-time find/replace in `index.html`.
- **Landing (static):** **`/`** → the overview page (A1). Inverts the funnel (§9): a cold
  visitor gets framing, not a raw data table, with an "Explore the live data" CTA into
  `/app`.
- **Tier A/B/C (static):** the full per-page URL list is the canonical map in
  [`public-docs-structure.md`](public-docs-structure.md) (single-source, to avoid drift).
- **Machinery:** `/sitemap.xml`, `/robots.txt`.

### 12.2 Rendering pipeline

- **Content source of truth:** a curated `content/` tree of **English** markdown, each file
  with YAML front-matter (`title`, `description`, `keywords`, `og_image`, `canonical`).
  This is a *curated* surface, separate from the internal `docs/` — we select and translate
  into it, we do not mirror `docs/` (keeps the §6 keep-internal discipline intact).
- **Renderer:** markdown → HTML via a Python renderer (e.g. `markdown-it-py` or `mistune`),
  injected into **one Jinja2 shell template** that supplies the shared header/nav, the thin
  footer (§10), the theme CSS, and the per-page `<head>` (title/meta/OG/canonical from
  front-matter). The shell is extracted once so the SPA `index.html` and the doc template
  render an identical header/footer.
- **Build script (not a CLI subcommand):** a standalone **`scripts/build_docs.py`**, in the
  same family as the existing offline scripts (`build_semantic_parallels.py`,
  `build_tmi_bibliography.py`, …) — outside the `mytho` pipeline, so it never touches the
  data-build CLI. It runs the renderer over the whole `content/` tree and writes finished
  `.html` (+ `sitemap.xml`).
- **Output location — the web root itself, not `outputs/`:** `src/server/web/` is already the
  web root (`settings.web_root`) and is already served. The generated pages go **directly
  there**, next to `index.html` and `assets/`, in URL-matching subdirs (`research/`,
  `indexes/`, `cases/`) — no wrapper folder. **Not** `outputs/` (that is for pipeline
  artifacts). CSS/JS/OG images reuse the existing `assets/` served at `/assets`. The generated
  `.html` is **committed** (decision E): the server just serves files, deploy needs no CI
  rebuild, and it fits the ephemeral-container model (clone → already serves).
- **Serving — precompiled static:** wired at server startup in `create_app` — the same place
  the current `/assets` `StaticFiles` mount and the `index.html` response are set up — just
  extended to serve the web-root doc files (or mount the web root as static). The doc pages
  are plain files under the root; no renderer or template engine in the request path, and no
  new runtime machinery — this is what unlocks the §13 payoffs. The tree can equally be handed
  to a CDN / static host; the build is decoupled from the app.
  - **Optional dev preview (not production):** a `--watch` flag on the script re-renders on
    file change for local authoring, so edits are visible without a manual rebuild. Same
    renderer; never on the production request path.

### 12.3 Head, OG, and discovery

- Per page from front-matter: `<title>`, `<meta name="description">`, `<link rel="canonical">`,
  `og:title/description/image/url/type`, and Twitter Card tags — all in the **initial HTML**
  (the reason for static/SSR: social scrapers do not run JS, §13).
- **OG images:** one default site card + custom images for the magnets (an Atlas screenshot;
  a stat/quote graphic). Can be added incrementally.
- `sitemap.xml` lists every static doc URL; `robots.txt` points to it. The `/app` SPA is
  left out of the sitemap (it need not be indexed, §8).

### 12.4 Shared shell wiring (nav, footer, entry point)

- Extract the header (nav + GitHub icon + "Research ▾" hub) and the thin footer (§10) into
  the shared template; the SPA `index.html` includes the same partial so both layers match.
- "Research ▾" links point at the static doc URLs; the app's contextual "learn more" links
  (§9) point from `/app` views into `/crosswalk`, `/regions`, `/how-it-works`.
- Footer lives outside the SPA `#app` (persistent, no re-render); thin/one-line on `/app`
  views, full on document pages.

### 12.5 Phasing (supersedes the phase note in §7 for the delivery mechanics)

1. **Bootstrap:** shell template + the `scripts/build_docs.py` SSG script + `content/` with
   A1 and B4 (both ready, English) + generated `sitemap.xml`/`robots.txt` written directly
   under the web root (`src/server/web/`); extend the startup mount in `create_app` to serve
   them. Move the SPA to `/app`. Static from day one — the §13 payoffs (OG cards, low TTFB)
   are already in place here.
2. **Fill:** the rest of Tier A and the Tier-B magnets (translate B1); wire the hub and
   contextual links; per-page front-matter (title/description/OG). Wire `build_docs.py` into
   CI so a content push regenerates the site.
3. **Optimise (optional):** put the generated subtree behind a CDN; add custom OG images
   (Atlas screenshot, stat/quote graphics) for the magnets.

## 13. Glossary — the Phase-3 payoffs (why precompile to static)

- **Rich OG (Open Graph) previews.** `<head>` meta tags (`og:title/description/image/url`,
  Twitter Card) that Slack/Telegram/Bluesky/X/LinkedIn read to render a **link card** with
  title, description, and image instead of a bare URL. Social scrapers **do not execute JS**,
  so they only see the initial HTML — an SPA that fills these tags after load loses the card.
  Static/SSR HTML is what makes shareable cards work; "rich" = a real preview image (Atlas
  screenshot, a stat/quote graphic), not just text.
- **Low TTFB (Time To First Byte).** Time from the browser's request to the first response
  byte. SSR includes per-request server work (render markdown→HTML); a prebuilt `.html` is
  just a file read (or a CDN hit) → near-minimal TTFB. Lower TTFB = faster perceived load and
  a minor ranking factor (Core Web Vitals adjacent).
- **CDN cache.** A network of edge servers near users (Cloudflare/Fastly/…). Static files
  cache at the edge, so a reader in Tokyo is served from a nearby node, not our origin —
  lower latency, less origin load. Static is trivially cacheable (stable, identical for all);
  dynamic SSR is harder to cache safely. Precompiled static docs = cheap global speed, and it
  matters most for the SEO/citation magnets (crosswalk, surveys).

## 14. Copy from the Figma mockup (`MythoSemantic`) — what to fold in and where

The Figma file `MythoSemantic` (extracted via the REST API) is, in effect, a **design of the
public-site copy**: vision pitches, a "name story" essay, a full "Join the Collaboration"
page, a proposed sitemap, and a resources list. It is a second, independent draft of the same
public layer this plan covers — a rich source, but to be folded in *selectively*, not adopted
whole.

### 14.1 The positioning tension (needs a call)

The Figma copy positions the project **differently** from the repo's Element monograph:
- **Figma:** an aspirational *movement/manifesto* — "we don't know what deep structures exist;
  let's build the instrument to discover them," "infrastructure for **discovery, not
  verification**," inductive-not-deductive.
- **Element:** *results-first and candid* — areal diffusion dominates, the datable ~1% descent
  core, the irreducibility limit; findings already in hand, negative results included.

They are compatible but can jar if placed side by side ("we don't know" vs "we established").
**Resolution (recommended):** Vision/About carries the aspiration/manifesto; "What we found"
(A2) carries the results; soften "we don't know what structures exist" to "map the space of
deep structures" so it does not undercut the Element's honesty. This is the one item to sign
off before writing Tier A.

### 14.2 Mapping — Figma block → plan section → treatment

| Figma content | → Section | Treatment |
|---|---|---|
| Vision pitch, three-layer model (conceptual/methodological/infrastructural), "Semantic Archaeology" tagline | A1 / About | Adopt (English parts ready); "Collaborative Semantic Archaeology" is a strong brand line |
| Manifesto "Why collaborative infrastructure for theory discovery" (scale / algorithms / collaboration / open-infra) + the deductive→inductive diagram | A1, a "Why" sub-block | Adopt — strongest manifesto copy; reconcile "discovery not verification" with A2 per §14.1 |
| The name essay (`-scope` as epistemic lens: telescope/microscope/spectroscope; Foucault/Latour/STS) — Russian | About / name | **Translate to English**; great narrative hook; currently an internal RU memo |
| Embeddings as "interpretive operators" (Proppian/Lévi-Straussian/Jungian lenses); 3-level similarity (lexical/imagistic/structural); narrative function — Russian/mixed | A4 Methodology | Adapt; **mark aspirational vs. implemented** (much is roadmap, not built) |
| Scalable-reading / computational-hermeneutics notes; the "big questions" — Russian | A4 / B3 | Adapt selectively; conceptual framing only |
| "JOIN THE COLLABORATION" full page (15 collaboration types, each with need/gain/ideal-for/contact) | C1 Contribute | **Adopt as the backbone**; trim to real offerings; replace placeholder `*@mythoscope.org` emails; drop unfunded promises |
| Proposed sitemap (Home/About/Explore/Research/Contribute/Learn/News) | §9 Navigation | Reconcile with our IA — their "Explore" = our SPA app, their "Learn" = tutorials (net-new) |
| Digital text-library list (Perseus, Sacred Texts, ETCSL, GRETIL, Chinese Text Project, …) | C2 Resources / B4 | Adopt into Resources; dedupe against the corpus-sourcing atlas |
| Related-work list (GOLEM, Arabian Nights, Cinderella, Story-emb, …) — Russian | B3 | Already covered by the research surveys; merge/dedupe |
| Footer social set: X, Substack, YouTube, Discord, GitHub, Email | §10 | Confirms and concretises the §10 footer/social set |

### 14.3 Keep internal / do not publish as-is

The Russian strategic memos (the positioning note, the name essay — addressed to "ты", i.e.
notes to the founder, not public copy); the Figma placeholder `*@mythoscope.org` addresses —
the real domain is **mythoscope.io** and launch uses one inbox `hello@mythoscope.io` (aliases
forward to it, decision C); unfunded promises (postdoc fellowships, naming opportunities) and
Team/Partners pages until real. The Gita excerpt and the tradition JSON in the file are mockup
sample data, not copy.

### 14.4 Provenance note

Extraction was one-off via the Figma REST API (`GET /v1/files/:key`, `X-Figma-Token`); the
token was used only at request time and never stored in the repo. The raw dump lives outside
the repo (scratchpad). Rotate/revoke the token now that it has been shared in plaintext.

## 15. Citation, credit & API (operational)

The engine in `go-to-market.md` runs on *citability* and *credited contribution*; both need
concrete artifacts, not just pages.

### 15.1 Citability — make citable objects

Nothing is formally citable today (no DOI, no `CITATION.cff`, no versioned release). Create
persistent-identifier objects, most-citable first:
- **The crosswalk dataset** — a versioned, DOI'd data release (Zenodo). The single most novel,
  citable artifact; ship it as CSV/JSON + a datasheet.
- **A `CITATION.cff`** in the repo → GitHub's "Cite this repository" button.
- **A software/release DOI** via the GitHub→Zenodo integration (a DOI per tagged release, plus
  a concept-DOI for "all versions").
- **A preprint** (arXiv cs.CL / SocArXiv / Humanities Commons CORE) for the methods/findings —
  the object cited in prose; from `docs/papers/`.
- **Per-survey DOIs** (Zenodo deposits) so the B3–B5 "How to cite" blocks resolve.
- **Versioning:** semantic versions + "cite the version you used" guidance.
- **Where surfaced:** the **Publications** page (C3) + **Resources** (C2) "How to cite" blocks;
  register profiles (Google Scholar, Humanities Commons, ORCID) that point back.

### 15.2 Credit & authorship — make contribution trustworthy

Academics weigh authorship heavily, so the policy must be written and visible (page C5 +
repo files):
- **The attribution ladder:** acknowledgement (listed contributor) → **data/tool citation**
  (the contributor's dataset/annotation gets its own citable DOI) → **co-authorship** when the
  contribution is substantial (curating a tradition's corpus, a methods contribution).
- **Roles:** the **CRediT** taxonomy (14 contributor roles) for transparent, granular credit.
- **Criteria:** ICMJE-style authorship thresholds, adapted; **CARE principles** + consent/
  co-governance for Indigenous materials (already in the Figma copy).
- **Repo mirror:** `CONTRIBUTORS.md` (everyone credited) + `CITATION.cff` (how to cite the
  software/data). Per-dataset provenance travels with the data.

### 15.3 API — minimal now

No product API at this stage: a supported, versioned public API is a premature maintenance and
stability commitment for a small audience, and researchers reuse **data dumps**, not API
clients. But the server's **OpenAPI is generated for free** (`/docs`, `/redoc`,
`/openapi.json`) — expose it read-only and link it from Resources as *experimental, no
stability guarantees*. Priority is bulk downloads + DOIs (§15.1). A real API is Phase-3+,
demand-driven.

## 16. Execution sequence (the ordered action plan)

The single ordered to-do, consolidating the phasing in §7 / §12.5 and `go-to-market.md` §6.
Each step is independently shippable; earlier steps unblock later ones.

### Step 0 — Groundwork (done / mechanical)
- [x] Decisions settled (register above); name normalised to **Mythoscope**.
- [ ] Reserve handles: GitHub org, Bluesky, Mastodon, YouTube, Substack, `mythoscope.io` email
      (`hello@`), Zenodo + ORCID + Humanities Commons + Google Scholar profiles. (Do early —
      names get taken.)

### Step 1 — Static docs skeleton (the delivery spine, §12)
- [ ] Extract the shared **shell template** (header with Explore ▾ / Research ▾ / About /
      GitHub, thin footer §10) from `index.html`.
- [ ] Write **`scripts/build_docs.py`** (markdown + front-matter → HTML via the shell;
      `--watch` dev mode; emits `sitemap.xml` + `robots.txt`).
- [ ] Create the curated **`content/`** tree (English). Move the SPA to **`/app`**; wire the
      startup mount in `create_app` to serve the generated web-root pages.
- [ ] Ship **A1 Overview** (`/`) + **B4 Corpus atlas** (ready) as the first two pages.

### Step 2 — Fill the tiers (content, §2)
- [ ] Tier A: A2 What-we-found, A3 Case studies, A4 How-it-works, **A5 About/Vision**
      (manifesto + `-scope` story from Figma, register per §14.1).
- [ ] Tier B magnets: **B1 Crosswalk** (translate), B2 Indexes, B3 Field survey, B5
      Encyclopedias, B6 14 regions.
- [ ] Tier C: **C1 Contribute** (Figma backbone, trim placeholders), C2 Resources, **C3
      Publications**, **C4 Updates/Notes**, **C5 Credit** (+ `CONTRIBUTORS.md`, `CITATION.cff`).
- [ ] Footer + nav hubs live; contextual view→doc links; internal cross-links (§4).

### Step 3 — Citability & credit (§15)
- [ ] `CITATION.cff` in the repo; GitHub→**Zenodo** integration (release DOI).
- [ ] DOI the **crosswalk dataset** (CSV/JSON + datasheet) and each survey.
- [ ] A **preprint** (arXiv cs.CL / SocArXiv / HCommons CORE) from `docs/papers/`.
- [ ] "How to cite" blocks on Publications + Resources.

### Step 4 — Retention plumbing
- [ ] **Buttondown** account + footer field + confirm flow.
- [ ] **GitHub Discussions** on; a `CONTRIBUTING.md`.
- [ ] The **awesome-computational-mythology** list — verify links, spin into its own repo with
      the full setup (badge, `awesome-lint` CI, link-checker, `contributing.md`, CC0,
      `CITATION.cff`+DOI, templates), then submit to `sindresorhus/awesome`. Growth playbook in
      `go-to-market.md` §8a; repo-setup checklist in the list file itself.

### Step 5 — Go to market (GTM §6, phased)
- [ ] **Phase 0** — be findable: docs indexed, DOIs, newsletter, profiles, OG images.
- [ ] **Phase 1** — seed communities: Humanist + folklore/corpora lists; academic Bluesky/
      Mastodon; Wikipedia references; Show HN / r/DigitalHumanities.
- [ ] **Phase 2** — earn endorsement: preprint out; a conference demo/poster (CHR / DH / ISFNR);
      direct outreach to named scholars.
- [ ] **Phase 3** — compound: monthly "motif/mockup of the month"; quarterly heavy release;
      grow community (add Zulip/Discord only when there's demand).

### Ongoing
- [ ] Cadence: monthly light (Updates → newsletter → socials), quarterly heavy (survey/release
      + DOI). Track north-star metrics (GTM §7); ignore vanity metrics.

## 17. Repository hygiene for a public academic project

An audit of the repo's own presentation (separate from the docs *site*). A public academic
open-source project needs the standard "community health" files, a license, CI, and a
reader-first README.

**Added now (this pass):**
- **`LICENSE`** — MIT for code (matches `pyproject`; previously the metadata claimed MIT but
  *no license file existed* — legally all-rights-reserved). Notes docs = CC BY-SA 4.0, derived
  data = CC BY 4.0.
- **`CITATION.cff`** — enables GitHub's "Cite this repository"; DOI/author placeholders to fill.
- **`CONTRIBUTING.md`**, **`CODE_OF_CONDUCT.md`** (Contributor Covenant 2.1), **`SECURITY.md`**.
- **`.github/`** — `ci.yml` (ruff + `npm test`), PR template, bug/feature issue templates.
- **`.editorconfig`**; `pyproject` gained `authors` + `[project.urls]`.
- **README** — license/python/CoC badges + Contributing / Citation / License sections.

**Remaining (do later / needs a decision or an external step):**
- [ ] **README restructure for the public.** It currently leads with an internal
      roadmap/backlog + "Potential colabs / submission targets". Lead instead with
      what-it-is + a screenshot/demo GIF + quickstart + docs links; move the roadmap/backlog and
      colab/submission lists into `docs/ROADMAP.md` (internal). (Editorial — the roadmap content
      is the maintainer's to move.)
- [ ] **Full Python test CI** (`python -m pytest`) — needs the install-profile decision (a
      lightweight test extra) since the full deps pull torch/chromadb/umap; the CI stub has a
      TODO. Add coverage once wired.
- [ ] **Zenodo DOI** — connect the repo to Zenodo, cut a release, add the DOI to `CITATION.cff`
      + a badge (see §15.1).
- [ ] **Screenshots / a short demo GIF** of Atlas/Similarity/Motifs in the README.
- [ ] **`.github/FUNDING.yml`** (only if a funding channel exists), **`dependabot.yml`**,
      optional `CHANGELOG.md`.
- [ ] **Fill placeholders:** `OWNER` (GitHub owner) in `CITATION.cff` / `pyproject` URLs, the
      real author name(s)/ORCID and copyright holder in `LICENSE`/`CITATION.cff`, and the
      `security@mythoscope.io` mailbox.
- [ ] **GitHub repo settings** (from the web / About ⚙ — cannot be set via the available
      tooling): **Website = `https://mythoscope.io`** (shown prominently in the About box),
      a one-line **description** (e.g. "Computational framework for comparative mythology —
      semantic space + LLM graphs + a TMI↔ATU↔Berezkin motif crosswalk"), **topics**
      (`computational-folkloristics`, `comparative-mythology`, `digital-humanities`, `nlp`,
      `folklore`), a social-preview image, and enable Discussions.
- [ ] **Branch protection on `main`** (Settings → Branches / Rulesets) — this is what turns the
      CI from advisory into a gate: require the `ci` checks to pass (and, optionally, a PR +
      review) before merging, so a red PR can't reach `main`. The `.github/workflows/ci.yml`
      already runs on `pull_request` (the pre-merge check) + `push` to `main` (a backstop);
      branch protection adds the enforcement. Optional for a solo project; worthwhile once there
      are external contributors.
