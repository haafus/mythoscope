# Proposal: wiring `region` into production — the plan

- **Status:** proposal (open, decisions settled). Nothing here is implemented yet.
- **Scope:** the **code layer only** — configs, build, serve, front, embeddings — for the text-processing
  pipeline. Taxonomy and presentation are closed (§0). Supersedes the code sections
  ([`tradition-architecture-unified.md`](tradition-architecture-unified.md) §4/§6).

Grounded in the three field audits ([`../reviews/tradition-review.md`](../reviews/tradition-review.md),
[`../reviews/major-tradition-review.md`](../reviews/major-tradition-review.md),
[`../reviews/color-system-review.md`](../reviews/color-system-review.md)) and the canon
[`research/regions.md`](../../research/regions.md).

---

## 0. Closed decisions (context — not reopened)

- **`region` (14) is the sole classification axis** of a tradition. No facet layer. Canon: `regions.md`.
- **Colour lives only at the region level** — a tradition inherits its region's colour; palette canon
  `regions.md` §8.
- **Out of scope:** motif `theme`/`stratum`, the connectivity axis and dating (science), and the
  motif-areal regions (see 2.5).

---

## 1. Current state (the problem)

The live axis is still `tradition` (free string) → `major_tradition` (derived) → `colour` (random); `region`
is not wired in.

- **Free-string identity & join.** Books hold a hand-written `tradition` string (`config/corpus.json`, 28
  books) joined to `config/traditions.json` by exact string equality — no id, no validation. Misses degrade
  **silently**: `builder.py:210` → `""`; `services/corpus.py:25-26` → `{}` then colour `"#6b7280"`. Strings
  are dirty (`"Australian"` vs `"Australian Aboriginal"`).
- **`major_tradition`** — derived from the `config/traditions.json` tree (`builder.py:152-157,208-213`),
  denormalised onto rows, the file path `corpus/<major>/<tradition>/<title>.txt` (`utils.text_path:63-67`),
  and every chunk (`build_embeddings.py:177-183`); dropped from served `traditions.json` (asymmetry,
  `builder.py:160-181`); dead on `SearchResult.major_tradition` (`schemas.py:30`).
- **`colour`** — `random.randint` unseeded (`utils.py:93-104`), reshuffles each build; stored on
  `traditions.json` **and** denormalised onto `/catalog` rows (`services/corpus.py:29`).
- **`region`** — no such field in `config/` or `src/`. Every `region` in `src/` is the separate Berezkin/
  ATU/TMI *motif-areal* system (`services/motifs.py`, `sources/atu_regions.py`, `sources/culture_dict.py`,
  `page-motifs.js::REGION_COLORS`) — untouched by this work.
- **Divergent defaults** — `""` / `"unknown"` / `"Unknown"` / `"Other"` / `"#6b7280"`; no
  `CATEGORY_NONE`/`UNASSIGNED` in the backend.

---

## 2. Decisions

**2.1 `region` is authored, not derived.** Every tradition is bound to exactly one of the 14 regions **by
hand** — by a human editor (or by Claude) in config. No `areal_path`-derived function (it yields 12 and can't
express the canon's re-cuts and boundary calls). `regions.md` §5 (the hand list) is the authoring reference.

**2.2 `region` is a stored field, in two config files.**
- **`config/regions.json`** — the 14 regions, the machine-readable projection of `regions.md` §8:
  `region_id → { name, order, colour: { base, light, dark } }`.
- **`config/traditions.json`** — becomes the **id-keyed tradition registry**:
  `tradition_id → { name, region, coordinates }`, where `region` is a `regions.json` id, authored per
  tradition. `name` is display-only; the old `major_tradition` tree is gone (2.4).
- **`config/corpus.json`** — each book references `tradition_id` (not a display string).

**2.3 No catalogue joins — the corpus is the only universe.** The corpus documents and their tradition binding
are correct; only region needs to be set. We do **not** merge or join any other catalogue (the Berezkin 1046,
the 194-curated, TMI/ATU) — those were reference-only and are dropped from this work. The only lookups are the
**registry joins at build/serve**: `tradition_id → traditions.json (region) → regions.json (colour)`. The
config files are the source-of-truth *lookups* (`справочники`); the join runs in the corpus builder (writes
region+colour into served `traditions.json`) and on the front (catalog `tradition_id` → traditions map).

**2.4 `major_tradition` is deleted outright.** It is wrong and has no successor role. Remove the field, its
derivation, its denormalisation (rows, chunks), the `<major>` file-path segment, the served-store asymmetry,
and the dead `SearchResult.major_tradition`. The correct `region` is authored for every corpus tradition in
its place.

**2.5 Motif-index regions are not touched.** This task collects `region` in the **text-processing pipeline**
only. The motif-areal regions in `services/motifs.py`, `sources/atu_regions.py`, `sources/culture_dict.py`,
`page-motifs.js` stay exactly as they are; reconciling them to the canon is a later, separate task.

**2.6 One region palette.** Tradition/region colour comes solely from `config/regions.json` (← `regions.md`
§8). `page-motifs.js::REGION_COLORS` and any other tradition-colour source collapse to this one palette.

**2.7 No re-validation.** The frozen 12-area analysis validations are left as historical; nothing is re-run
against the 14 regions.

**2.8 Accept the `stratum`/`Strata` overload.** The motif `stratum` field and `regions.md` §5's authored
`Strata` share a name; no rename.

**2.9 Plumbing consequences of the above.**
- **Colour is derived from region** at build (`region → colour.base` lookup), not stored per tradition and not
  random. Drop `get_tradition_color`/`random` and both colour transport tracks.
- **Build validation fails loud** on a book `tradition_id` absent from the registry, or a registry `region`
  absent from `regions.json` — replacing the silent `.get(...)` defaults.
- **Chunk metadata carries `tradition_id`** (not the display string); `region` is resolved from the registry
  at query time. `cross_tradition` filters on `tradition_id`.
- **One `UNASSIGNED`** id/label across `schemas.py`, `iterator.py`, and the front end.

---

## 3. Data flow (target)

```
config/regions.json     region_id → {name, order, colour{base,light,dark}}       ── authored (§2.2, ← regions.md §8)
config/traditions.json  tradition_id → {name, region, coordinates}               ── authored region (§2.1)
config/corpus.json      book → tradition_id
        │  build (corpus builder): validate every tradition_id ∈ registry & region ∈ regions.json (fail loud);
        │                          resolve colour = regions[region].colour.base
        ▼
outputs/corpus/corpus.json      rows carry tradition_id (+name); NO major, NO colour
outputs/corpus/traditions.json  tradition_id → {name, region, colour, coordinates, books}
outputs/embeddings/*            chunk metadata: text_id, tradition_id, url   (region resolved at query)
        ▼  server
/api/corpus/traditions   tradition_id → {name, region, colour, coordinates}
/api/corpus/catalog      documents carry tradition_id (+name); front joins region/colour from traditions map
/api/similarity/*        SearchResult: tradition_id (+name); region resolved from registry; no major, no colour
        ▼  front
one 14-region legend; grouping by region; colour = regions.json palette
```

---

## 4. Config shapes (concrete)

```jsonc
// config/regions.json  (14 entries, from regions.md §8)
{
  "sub-saharan-africa": { "name": "Sub-Saharan Africa", "order": 1,
                          "colour": { "base": "#CC503E", "light": "#D79389", "dark": "#953223" } },
  "europe":             { "name": "Europe", "order": 3,
                          "colour": { "base": "#EDAD08", "light": "#EDC55F", "dark": "#9B7208" } }
  // … 12 more …
}

// config/traditions.json  (id-keyed registry; region authored per tradition)
{
  "yoruba": { "name": "Yoruba", "region": "sub-saharan-africa", "coordinates": [8, 4] },
  "greek":  { "name": "Greek",  "region": "europe",             "coordinates": [39, 22] }
  // … one per corpus tradition …
}

// config/corpus.json  (book references the registry by id)
{ "title": "…", "tradition_id": "greek", "url": "…", "description": "…" }
```

The tradition→region bindings for the corpus are authored as part of Phase 1/2 (≈ the 23 distinct corpus
traditions).

---

## 5. Migration order (region-only; each phase shippable)

1. **Configs + identity + validation.** Add `config/regions.json` (14 defs + palette); convert
   `config/traditions.json` to the id-keyed registry with an authored `region` per tradition; switch
   `config/corpus.json` books to `tradition_id`; build-time validation (fail loud on unknown id / region);
   `name` display-only. *(Highest value-to-risk — closes the silent string join.)*
2. **Delete `major_tradition`.** Remove the field, its derivation and denormalisation (rows, chunks), the
   `<major>` path segment, the served asymmetry, and the dead `SearchResult.major_tradition`.
3. **Region colour.** Drop `random` colour; resolve `colour = regions[region].colour.base` at build; collapse
   `REGION_COLORS` to the one region palette; one 14-region legend everywhere.
4. **Served + chunk model.** `/api/corpus/traditions` → `tradition_id → {name, region, colour, coordinates}`;
   `/catalog` and `SearchResult` carry `tradition_id` (+name); store `tradition_id` on chunks; resolve region
   at query time.
5. **One `UNASSIGNED`** across `schemas.py`, `iterator.py`, and the front end.

---

## 6. Out of scope

Motif `theme`/`stratum`; the connectivity axis, dating, the residual (science); the motif-areal regions in
the motif indexes (2.5); any facet (`family`/`subsistence`/`theme_profile`); catalogue joins; re-validation.
