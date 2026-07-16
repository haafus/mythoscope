# Proposal: wiring `region` into production — the open code layer

- **Status:** proposal (open). Nothing here is implemented.
- **Scope:** *only the unresolved code layer* — architecture, data flow, algorithms. Taxonomy and
  presentation are **closed** (pointers below); this document does not reopen them.
- **Supersedes:** the code/pipeline sections of
  [`tradition-architecture-unified.md`](tradition-architecture-unified.md) §4 and §6, which still assume the
  multi-facet model (`area`/`family`/`subsistence`, area-gradient colour, facet selector) that decisions
  b/c retired.

Sources folded in — the three field audits
[`../reviews/tradition-review.md`](../reviews/tradition-review.md) (`13039cc`),
[`../reviews/major-tradition-review.md`](../reviews/major-tradition-review.md) (`ba7656a`),
[`../reviews/color-system-review.md`](../reviews/color-system-review.md) (`709c956`); the taxonomy notes
[`tradition-taxonomy-final.md`](tradition-taxonomy-final.md), [`macro-area-facets.md`](macro-area-facets.md);
and the canon [`research/regions.md`](../../research/regions.md).

---

## 0. What is already closed (do not reopen)

- **Taxonomy** — `region` (14 values) is the **sole** classification axis of a tradition. No facet layer;
  `family`/`subsistence`/`theme_profile` are not built. Canon: `research/regions.md`.
- **Presentation** — colour lives **only at the region level** (a tradition inherits its region's colour;
  palette canon = `regions.md` §8, CARTOColors Prism); projection/basemap decided in
  [`map-palette-and-projection.md`](map-palette-and-projection.md); views group by `region`.
- **Out of scope entirely** — motif `theme`/`stratum` (properties of the *motif* entity), the connectivity
  axis and node-level dating (the ~64 % residual, folklore science). This proposal is plumbing, not science.

---

## 1. Current production state (the problem)

The live classification is a three-link chain — **`tradition` (authored free string) → `major_tradition`
(derived) → `colour` (random)** — and **`region` is not wired in at all.** File:line facts:

**1.1 Identity & join — a free string is the identity and the join key.**
- Books carry a hand-written `tradition` string (`config/corpus.json`; 28 books, fields `title`/`tradition`/
  `url`/`description`). It joins to `config/traditions.json` by **exact string equality** only — no id, no
  enum, no validation.
- The join degrades **silently**: `builder.py:210` `trad_major.get(item.get("tradition"), "")` defaults to
  `""` (only a `logger.warning`, `builder.py:211-213`); at serve, `services/corpus.py:25-26`
  `traditions_info.get(row["tradition"], {})` → `{}` then colour → `"#6b7280"`. A typo silently loses major,
  colour, coordinates, and map presence.
- The strings are already dirty: `"Australian"` vs `"Australian Aboriginal"`, self-named major==tradition
  collisions (`"Chinese"`, `"Polynesian"`).

**1.2 `major_tradition` — derived, denormalised, asymmetric, partly dead.**
- Derived at build from the `config/traditions.json` tree (13 hand-authored major nodes, each a
  `{description, coordinates}` dict): `_tradition_major_map` (`builder.py:152-157`), applied `builder.py:208-213`.
- Denormalised onto every corpus row, onto the **file path** `corpus/<major>/<tradition>/<title>.txt`
  (`utils.text_path:63-67`), and onto **every embedding chunk** (`CorpusFileInfo` → chunk metadata,
  `build_embeddings.py:177-183`).
- **Served-store asymmetry:** dropped from built `corpus/traditions.json` (`_update_traditions` flattens the
  tree, `builder.py:160-181`), so `/api/corpus/traditions` never carries it; the front end can only recover
  major from `/catalog` rows. A tradition with no books has no major reachable.
- **Dead payload:** `SearchResult.major_tradition` (`schemas.py:30`) rides through similarity results but no
  front-end file reads it.

**1.3 `colour` — non-deterministic and double-transported.**
- Sole generator `utils.get_tradition_color` (`utils.py:93-104`) = `random.randint(0, 0xFFFFFF)`,
  **unseeded**, not keyed to the tradition — every `mytho corpus` rebuild reshuffles all colours.
- Stored on `corpus/traditions.json` **and** denormalised onto every `/catalog` row
  (`services/corpus.py:29`); the front holds both copies.

**1.4 `region` — zero production wiring.**
- No `region` key exists in `config/` or in any production tradition/corpus/schema/chunk structure. The live
  two-level model is still `major_tradition → tradition`.
- Every `region` identifier in `src/` belongs to a **different entity** — the Berezkin/TMI/ATU *motif-areal*
  macro-regions (`services/motifs.py::_berezkin_region`, `sources/atu_regions.py::_REGION`,
  `sources/culture_dict.py::_REGION`, `page-motifs.js::REGION_COLORS`). None of these matches the 12-area
  scheme or the 14-region canon; they are three separate 13-/13+/~15-key vocabularies.

**1.5 Divergent "no value" defaults.** One situation surfaces as `""` (`builder.py:210`, `schemas.py:30`),
`"unknown"` (`iterator.py:57-58`, `visualization.py`), `"Unknown"` (`schemas.py:29`, front `core.js`),
`"Other"` (front grouping), and `"#6b7280"` (colour). The front unified colour "no-category" to
`CATEGORY_NONE` (color-review) but **the backend has no `CATEGORY_NONE`/`UNASSIGNED` at all**.

**1.6 Chunk metadata stores mutable strings.** Each chunk carries `text_id, major_tradition, tradition, url`
(`build_embeddings.py:177-183`) — display strings, no stable id, no region; `cross_tradition` filtering keys a
Chroma `where` on the raw `tradition` string (`services/similarity.py:34`).

---

## 2. Target architecture (open work)

**2.1 One id-keyed registry.** `config/traditions.json` becomes a flat registry keyed by stable `id` (slug):
`id → { name, region, coordinates }`. **No facets** (no `area`/`family`/`subsistence`). Books in
`config/corpus.json` reference `tradition_id`, not a display string. `name` is display-only; all joins are by
`id`.

**2.2 Kill the silent join — validate at build.** An unknown `tradition_id` (or an unknown `region` on a
registry entry) **fails the build loudly**, replacing the `.get(...)→{}/""` degradations at `builder.py:210`
and `services/corpus.py:25`.

**2.3 `region` on every tradition.** How the value is produced is the central fork — see §4.1/§4.2/§4.3.
Whatever the mechanism, the result is one `region` (of the 14) per tradition, stored on the registry entry.

**2.4 Colour derived from region, not stored.** Drop `get_tradition_color`/`random` and both colour transport
tracks. Colour = `region → base` looked up from the `regions.md` §8 palette (a small static table shipped to
the front, or computed there). This satisfies the closed decision (c): colour only at the region level.

**2.5 Retire `major_tradition`.** Remove the derived field, its denormalisation (rows, file paths, chunks),
the served-store asymmetry, and the dead `SearchResult.major_tradition`. Its geography → `region`; it had no
other job (grouping was the facet idea, now dropped).

**2.6 Served model, normalised.** `/api/corpus/traditions` carries the full set **once per tradition**:
`id → { name, region, colour, coordinates }`. `/catalog` documents carry only `tradition_id`
(+ optionally a denormalised `name` for convenience); the front joins region/colour from the traditions map.

**2.7 Chunk metadata by id.** Store the stable `tradition_id` on each chunk (not the mutable display name);
`region` is resolved from the registry at query time. `cross_tradition` keys on `tradition_id`.

**2.8 One `UNASSIGNED` constant.** A single `UNASSIGNED` id/label across `schemas.py`, `iterator.py`, and the
front end, extending the front's `CATEGORY_NONE` down to the value layer.

---

## 3. Data flow (target)

```
config/traditions.json   (id → {name, region, coordinates})     ── authored/derived (§4)
        │  build: validate every corpus tradition_id ∈ registry (fail loud)
config/corpus.json       (book → tradition_id)
        ▼
outputs/corpus/corpus.json      rows carry tradition_id (+ name); NO major, NO colour
outputs/corpus/traditions.json  id → {name, region, colour(from region), coordinates, books}
outputs/embeddings/*            chunk metadata: text_id, tradition_id, url   (region resolved at query)
        ▼  server
/api/corpus/traditions   id → {name, region, colour, coordinates}
/api/corpus/catalog      documents carry tradition_id (+name); join region/colour on the front
/api/similarity/*        SearchResult: tradition_id (+name); region resolved from registry; no major, no colour
        ▼  front
one legend of 14 regions; grouping by region; colour = region palette
```

Open plumbing questions live in §4 (forks 3, 5, 6).

---

## 4. Key decision-forks

The forks that must be answered before code; each blocks a concrete file.

**4.1 Region population mechanism — authored vs derived vs hybrid.**
- **Authored** (the canon's implied model): `region` is a hand-set field per tradition. `regions.md` calls
  `areal_path` "provisional… a scaffold, not authoritative", permits re-annotation, and assigns boundary
  cases (Tibet, Sami, Ainu, Vietnam, Cham, Mapuche, Ethiopia, NW-Coast — §6) **by hand**.
- **Derived** (the only built approach): a pure function of `areal_path` (mockup 21 `area_of`). But it yields
  **12**, not 14, and cannot express the canon's re-cuts (Circumpolar North spans several Berezkin macros;
  Austronesia vs Papua splits by descent; Caucasus & Iran re-cuts SW/C Asia).
- **Hybrid**: derive a first pass, then apply an authored override table for the re-cuts/boundaries.
- *Consequence:* pure-derived cannot reproduce the canon; the realistic choices are **authored** or **hybrid**.

**4.2 Data model for `region` — stored column vs computed read.** Re-annotation (§1 of the canon) and
boundary overrides force a **stored, editable** value; the old implementation sketches assume a computed
function. Must be settled before writing any `region_facets.py`.

**4.3 Which universe is authored against, and how the others join.** Three disjoint tradition sets, none
identical: the **~28-book production corpus** (no `areal_path`), the **1046-tradition Berezkin catalogue**
(has `areal_path`; the only place a derived recipe can run), and the **`regions.md` hand list**. Which set is
the authoring source of truth, and how do the other two join to it? (Production likely authors `region` on
the ~28 corpus traditions directly; the 1046 catalogue is analysis-only.)

**4.4 Retire `major_tradition` — re-key the 13 tree groups.** The 13 hand `major_tradition` nodes in
`config/traditions.json` must be re-keyed to the 14 `region` values. This mapping table is unbuilt (and is a
concrete, small, authorable artifact).

**4.5 TMI/ATU region reconciliation — collapse vs map-at-display.** Three motif-areal vocabularies
(`culture_dict._REGION` ~13, `atu_regions._REGION` 13 + Central Asia, `page-motifs.js::REGION_COLORS` ~15)
neither match each other nor the 14 canon. Either build the promised bridge onto the 14 regions, or keep them
index-native and map only at display. (These are the *motif* areal system — reconciling is optional for the
tradition axis but was promised in `macro-area-facets.md`.)

**4.6 Colour plumbing.** `page-motifs.js::REGION_COLORS` is a separate motif-level palette; the 14-region
tradition colour must come from `regions.md` §8 (`base`/`light`/`dark`). Ship it as one static table or
compute on the front — and decide whether the two palettes coexist or unify.

**4.7 Re-validation target — 12 vs 14.** The frozen validations (roadmap M32 granularity, M38 ARI-vs-area)
assume **12** areas and mockup 21's `AREAS12`/`area_of`. Re-run them against the 14-region canon, or leave as
historical? Decides whether the 12-area analysis code is retired or kept.

**4.8 Naming collision — `stratum` vs `Strata`.** `regions.md` §5 gives each region an authored **`Strata`**
field (dated historical layers); the motif entity has a computed **`stratum`**. Reserve `stratum` for the
motif and rename/namespace the region field, or accept the overload.

---

## 5. Migration order (region-only; each phase shippable)

1. **Identity + validation.** Add `id` to the registry and `tradition_id` to books; build-time validation;
   `name` → display-only. Highest value-to-risk (closes the silent string join), no behaviour change yet.
2. **Author `region` + retire `major_tradition`.** Resolve fork 4.1/4.2/4.3/4.4: put `region` on each
   registry entry; re-key the 13 major groups to 14 regions; delete the derived `major_tradition` field, its
   denormalisation (rows, paths, chunks), and the dead `SearchResult.major_tradition`.
3. **Region colour.** Replace `random` colour with the `regions.md` §8 region lookup; drop colour storage and
   both transport tracks; one 14-region legend everywhere (fork 4.6).
4. **Served + chunk model.** Normalise `/api/corpus/traditions` to `id → {name, region, colour, coordinates}`;
   `/catalog` and `SearchResult` carry `tradition_id`; store `tradition_id` (not strings) on chunks; resolve
   region at query time.
5. **One `UNASSIGNED`** across `schemas.py`, `iterator.py`, front end.
6. *(optional)* **TMI/ATU reconciliation** (fork 4.5) and **re-validation** (fork 4.7) — only if wanted;
   neither blocks the tradition axis.

---

## 6. Explicitly out of scope

- Motif `theme` roll-up and `stratum` derivation (motif entity; separate milestone).
- Connectivity axis, node-level dating, the ~64 % residual (science).
- The two theme axes (etiological/narrative) UI (motif presentation milestone).
- Any facet (`family`/`subsistence`/`theme_profile`) — dropped by decision, not revisited here.
