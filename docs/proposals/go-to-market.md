# Go-to-market — acquisition & retention architecture

How Mythoscope reaches and keeps its audience. Companion to
[`public-docs-plan.md`](public-docs-plan.md): that plan builds the public surface; this one
says which channels turn it into a growing community.

## 0. The core principle

Mythoscope is **research infrastructure**, not a consumer app. Its growth engine is **not
virality** — it is **credibility → citation/reference → word-of-mouth in scholarly networks →
collaboration**. The audience (computational folklorists, comparative-mythology and DH
scholars, adjacent NLP/ML people) is small, international, sceptical of hype, and moved by
*substance and citability*, not marketing. Therefore:

**The owned substance IS the advertising.** The surveys, the crosswalk, the case studies, the
open data and API are the acquisition assets. We don't buy attention; we publish things worth
finding, citing, and linking. The honesty/negative-results stance (from the Element) is a
*trust asset* — it is what makes this audience take the project seriously.

## 1. The flywheel

```
      publish reference-grade substance (surveys · crosswalk · case studies · data)
                    │
                    ▼
   found in academic search / cited in papers / linked from Wikipedia & awesome-list
                    │
                    ▼
        specialists arrive → use the live tool → subscribe (newsletter)
                    │
                    ▼
      some contribute (corpus · annotations · code) → co-authorship & attribution
                    │
                    ▼
     their work adds substance + they evangelise in their networks ──┐
                    │                                                 │
                    └─────────────────────────────────────────────────┘
```

Every loop makes the next cheaper. Acquisition (§2) feeds the top; retention (§3) closes it.

## 2. Acquisition architecture — channels by leverage

Ordered by fit for this audience (highest first). Owned > earned > rented; we lean owned.

1. **Owned SEO / citation magnets (the spine).** The public docs — the TMI↔ATU↔Berezkin
   crosswalk (B1), the literature surveys (B3–B5), the corpus-sourcing atlas (B4), the 14
   regions (B6). These rank for the exact queries specialists run ("where to get corpus X",
   "TMI ATU concordance", "computational folkloristics survey") and accrue inbound links.
   *This is the single biggest channel; everything else points into it.*
2. **Academic search + a citable anchor.** A **preprint with a DOI** (Zenodo / arXiv cs.CL or
   the Humanities Commons CORE repository) that links back to the site. Indexed by Google
   Scholar & Semantic Scholar; every citation becomes durable referral + legitimacy. Mint DOIs
   for the crosswalk dataset and each survey too (data/citation, not just the paper).
3. **Scholarly social (where academics actually are now).** **Bluesky** — post-Twitter
   "academic Bluesky" is where DH / folklore / linguistics / comp-ling communities migrated;
   most active channel. **Mastodon / fediverse** — scholarly instances (hcommons.social,
   fedihum.org, scholar.social). Post the surveys, case-study vignettes, and vizzes here.
   X/Twitter: declining for this audience — cross-post, don't invest.
4. **Mailing lists & scholarly networks (unglamorous, high-yield in DH).** The **Humanist
   Discussion Group** (the canonical DH listserv), **Corpora-List**, folk-narrative / **ISFNR**
   networks, area-studies lists. **Humanities Commons** (hcommons.org) — profile, group,
   CORE deposits. A single well-judged post to Humanist reaches the field's core.
5. **Conferences & direct scholar outreach (highest-trust).** Demos/posters/papers at **CHR
   (Computational Humanities Research)**, **ADHO DH**, **LaTeCH-CLfL**, **ISFNR** (folk
   narrative), religion venues (AAR/SBL) where relevant. Directly email named nodes from the
   landscape survey (Tangherlini, Karsdorp, Meder, Tehrani, d'Huy, Declerck, Finlayson) for
   feedback/collaboration — their endorsement is worth more than any ad.
6. **GitHub + the awesome-list.** The repo itself (open source = discovery in the CL/DH dev
   community) and a curated **`awesome-computational-mythology`** list — a genuine star/link
   magnet that positions Mythoscope as the hub of its niche.
7. **Reference/authority sites.** Add the crosswalk & surveys as **references/external links on
   Wikipedia** (ATU, Thompson Motif-Index, comparative mythology, computational folkloristics)
   — done properly, not spammily. Durable referral + authority signal.
8. **Enthusiast fringe.** r/mythology, r/folklore, r/DigitalHumanities, r/linguistics, a "Show
   HN" for the tool. Lower-trust, but widens the top of funnel and occasionally reaches a
   scholar or contributor.

## 3. Retention architecture — keeping them

1. **Newsletter (Buttondown) — the retention spine.** Owned, low-frequency: new findings, new
   data, new collaborators, calls to contribute. The one channel we fully control; the footer
   field (plan §10) feeds it. This, not social followers, is the durable relationship.
2. **The living tool as a reason to return.** New data drops, new views, a recurring **"motif
   of the month"** deep-dive linking a case study to the live Atlas/Motifs, saved/shareable
   queries. A paper is read once; a tool with fresh data is revisited.
3. **Community, async-first.** For academics real-time chat is *secondary* to async, so
   **GitHub Discussions** is the primary (owned, indexable, dev-adjacent) + newsletter +
   **quarterly community calls** (open, recorded). **Real-time chat is deferred** — an empty
   server signals worse than none. When there is a community to sustain it, add **Zulip**
   (threaded, topic-organized, open-source, free for open communities — best for the research
   register) or **Discord** (lower friction, more reach if the audience skews students/
   contributors); Matrix/Element if open-source sovereignty is a priority. Chat is a retention
   amplifier, not an acquisition channel.
4. **The contribution loop (the real moat).** Contributors of corpus, annotations, or code
   become invested through **attribution, co-authorship, and citations**. They return, and
   they evangelise. The Contribute page (C1, from the Figma "Join the Collaboration" backbone)
   is the on-ramp; CARE/Open-Science principles keep it trusted.
5. **The citation loop.** Once cited, the citing work drives durable traffic and third-party
   legitimacy — the compounding end-state of the flywheel. The prerequisite is *citable
   objects* — DOIs, `CITATION.cff`, a preprint — and a written *credit & authorship* policy;
   both are specified in `public-docs-plan.md` §15 (Publications page C3, Credit page C5).

## 4. Channel roster — role, ownership, cadence, effort

| Channel | Type | Role | Cadence | Effort |
|---|---|---|---|---|
| Public docs (surveys/crosswalk/cases) | Owned | Acquisition (SEO) | Evergreen + quarterly adds | High once, low upkeep |
| Preprint + DOIs (Zenodo/arXiv/CORE) | Owned/earned | Acquisition + credibility | Per release | Medium |
| Newsletter (Buttondown) | Owned | **Retention** | Monthly light / quarterly heavy | Low |
| Bluesky (primary social) | Rented | Acquisition + reach | Weekly-ish | Low |
| Mastodon/fediverse | Rented | Acquisition | Cross-post | Low |
| Humanist & scholarly lists | Earned | Acquisition (burst) | Per milestone | Low, high-yield |
| Humanities Commons | Owned-ish | Presence + deposits | Per release | Low |
| Conferences / scholar outreach | Earned | **Highest-trust acquisition** | 2–4×/yr | High, high-value |
| GitHub + awesome-list | Owned | Acquisition (dev/CL) | Ongoing | Medium |
| Wikipedia / reference links | Earned | Durable referral + authority | Once + upkeep | Low |
| Reddit / Show HN | Rented | Fringe top-of-funnel | Occasional | Low |
| GitHub Discussions / Discord / calls | Owned | **Retention (community)** | Ongoing / quarterly | Medium |
| Substack (optional) | Rented | Reach + publication presence | Only if wanted | Medium |

**Substack vs the owned newsletter:** the canonical list is Buttondown (owned, embeddable,
privacy-respecting). Add Substack only if a public *publication presence + built-in discovery*
is wanted — in addition to, not instead of, the owned list (see plan §10 rationale).

## 5. Content cadence & formats

Sustainable for a small team — **substance over frequency**, no daily social treadmill:
- **Quarterly (heavy):** a new survey/reference page, a case-study deep-dive, or a data
  release + DOI → announced to lists, socials, newsletter.
- **Monthly (light):** a single finding, a striking viz, a "motif of the month," a
  contributor spotlight → newsletter + socials.
- **Per milestone (burst):** preprint, conference demo, major data drop → the full channel
  set + direct scholar outreach.
- **Evergreen:** the docs and awesome-list, kept current.

**Publishing home:** the canonical home for "motif of the month" / "mockup of the month" and
own-publication announcements is the on-site **Updates/Notes** blog (plan C4) — owned + SEO —
fed to the **newsletter** and cross-posted to Bluesky/Mastodon. Papers/preprints live on the
**Publications** page (C3) with "How to cite" blocks; deposit copies on Zenodo/CORE and list on
Google Scholar / Humanities Commons / ORCID.

Formats that travel: the case-study vignettes (swan-maiden, sun-and-moon, fished-up earth),
stat-tile pull-quotes, interactive-map screenshots/GIFs, and the honest "here's what we
*can't* tell apart" angle (distinctive, credible, shareable).

## 6. GTM sequence (phases)

- **Phase 0 — Be findable & credible.** Public docs live & indexed (crosswalk + ≥2 surveys),
  DOIs minted, newsletter live, GitHub repo + awesome-list, profiles on Bluesky / Mastodon /
  Humanities Commons, `sitemap.xml`/OG in place.
- **Phase 1 — Seed the existing communities.** Announce on Humanist + folklore/corpora lists;
  post surveys/crosswalk to academic Bluesky/Mastodon; submit/seed the awesome-list; add
  Wikipedia references; a Show HN / r/DigitalHumanities post.
- **Phase 2 — Earn the field's endorsement.** Preprint + DOI; a conference demo/poster (CHR /
  DH / ISFNR); direct outreach to named scholars/labs for feedback & collaboration.
- **Phase 3 — Compound.** Contribution + citation loops turn; sustain the cadence; grow the
  community (Discussions/Discord/calls); expand corpus & coverage from contributors.

## 7. Metrics (and anti-metrics)

**North star:** *returning specialists who contribute or cite* — the deep end of the flywheel.

**Supporting:** referring domains / backlinks to the magnets; Scholar/Semantic-Scholar
citations of the preprint & datasets; newsletter subscribers + open rate; GitHub
stars/forks/**contributors**; corpus/annotation contributions; returning tool users;
conference-/list-driven signups.

**Anti-metrics (do not optimise):** raw pageviews, social follower counts, vanity impressions.
For this audience they mislead.

## 8. Discipline — what NOT to do

- **No paid ads.** They neither reach nor convince academics; spend the effort on substance.
- **No daily social grind.** Cadence beats volume; the team is small.
- **No hype / overclaiming.** It destroys credibility with the exact audience — the honesty
  stance is the asset. Mirror the Element's candour everywhere.
- **No gated content.** Open access is both the ethos and the SEO/citation engine.
- **No consumer-funnel dark patterns** (pop-ups, countdowns). Specialists find them abrasive.

## 8a. Growing the awesome-computational-mythology list

An awesome list is a self-propelled acquisition + community asset with its own well-understood
growth mechanics; it doubles as a **citable object** and a **contribution on-ramp**. Treat it
as a distinct channel, not a docs appendix.

**Promotion playbook:**
1. **Standalone repo** `awesome-computational-mythology` (not buried in mythoscope) so stars,
   forks, topics, and citations accrue to *it*. Host it under a **personal account**, not a
   `mythoscope` org — a personal-account list reads as neutral community curation (convention
   for awesome lists; helps trust and index acceptance), whereas an org repo reads as a company
   asset/ad. Transferable to an org later without losing stars or breaking links. Keep a named
   maintainer line + one tasteful backlink to Mythoscope.
2. **Get into the canonical `sindresorhus/awesome` index** — the single biggest discovery
   driver. It requires meeting the Awesome manifesto (structure, badge, TOC, contribution
   guidelines, license, per-item descriptions, maturity, passes `awesome-lint`). Build the repo
   to that bar from day one so it is submittable.
3. **GitHub discovery:** topics (`awesome`, `awesome-list`, `computational-folkloristics`,
   `digital-humanities`, `folklore`, `mythology`, `nlp`), a crisp repo description, a
   social-preview image.
4. **Seed stars** through the Mythoscope channels (Bluesky, Humanist, r/DigitalHumanities, HN);
   trending + search rank compound from there.
5. **Backlinks:** reciprocal links with related lists (awesome-nlp, awesome-digital-humanities)
   and DH resource pages; cite it from the surveys and the preprint; add to relevant Wikipedia
   "External links".
6. **Neutral curation (credibility guard):** a *community* resource, **not** a Mythoscope ad —
   Mythoscope appears as one project among many. A thinly-veiled ad gets distrusted and rejected
   from the index.
7. **Announce on awesome aggregators** (r/coolgithubprojects, libhunt, awesome newsletters).

**Build into the list so it can grow and stay alive** (see the repo-setup checklist in
`../awesome-computational-mythology.md`): Awesome badge + passes `awesome-lint`; a consistent
entry format; `contributing.md` + `code-of-conduct.md` + PR & "Suggest a resource" templates;
**CC0** content license; CI dead-link check (`lychee`/`awesome_bot`) + `awesome-lint` on PRs;
a scope statement, a "See also", and a "Recently added" changelog; **`CITATION.cff` + a Zenodo
DOI** (rare for an awesome list — lets scholars cite it, feeding the citation loop); a tasteful
single backlink to Mythoscope; a named, responsive maintainer (dead lists get delisted).

**Metrics:** stars, forks, **contributors**, acceptance into `sindresorhus/awesome`, backlinks,
and referral traffic to Mythoscope.

## 9. How it plugs into the docs plan

- The **public docs** (plan Tiers A/B) are the top of funnel — the acquisition assets here.
- The **footer newsletter** (plan §10, Buttondown) + **`hello@mythoscope.io`** are the
  retention/contact spine.
- The **Contribute page** (C1, Figma "Join the Collaboration") is the contribution loop's
  on-ramp.
- The **Resources page** (C2) hosts the API, data/DOIs, and the "cite us" block that powers the
  citation loop.
- The **"Research ▾" hub** (plan §9) is where all of this is reached; the **live views** are the
  return-visit hook (§3.2).
