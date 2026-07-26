# Motif pipeline — discovery, parsing & assembly

How the three motif indexes (Berezkin, TMI, ATU) and their enrichment layers are **discovered,
fetched, parsed, and linked** into the served data structure — step by step, from raw bytes to the
final JSON the frontend reads. Companion to [`../proposals/motifs-atomisation.md`](../proposals/motifs-atomisation.md)
(the fetch/refresh boundary and its guarantees) and [`../proposals/pipeline-and-incrementality.md`](../proposals/pipeline-and-incrementality.md)
(the stage protocol). This doc owns *what each source contains and how the pieces join*.

All file:line anchors are into `src/motifs/`.

---

## 0. The shape at a glance

Five driver stages, wired in `pipeline/stages/motifs.py::motifs_stages()` (L282-289):

```
source:berezkin ┐
source:tmi      ┼─► crosswalk ─► parallels ─┐
source:atu      ┘        │                  ├─► meta
       └─────────────────┴─► semantic ──────┘
```

Each stage writes an artifact + an fp sidecar `outputs/motifs/.fp.<name>` and is offline (reuses
the pinned raw cache; the networked re-check is `refresh`, not `build`). Output files under
`outputs/motifs/` (`store.py:35-83`):

| file | written by | contents |
|---|---|---|
| `berezkin.json` / `tmi.json` / `atu.json` | the three source stages | one catalogue each (`motifs`/`types` array + legends) |
| `<src>.enrichment.json` (×3) | source stages | per-source enrichment counts (for `meta`) |
| `crosswalk.json` | crosswalk | directed cross-index link maps + inferred edges |
| `parallels.json` | parallels | lexical look-alike suggestions |
| `semantic_parallels.json` | semantic | precomputed BGE-M3 suggestions (copied in) |
| `meta.json` | meta | counts, link tallies, provenance, degradation flags |
| `.discovered.<root>.json`, `.discovery.json` | source/meta | discovery-shrank watch sets |
| `raw/bge_m3.npy` | offline script | semantic embedding cache |

The data flows in three movements: **(A)** each source is fetched + parsed + enriched into its own
catalogue; **(B)** `crosswalk` folds the three catalogues and links them; **(C)** `parallels` /
`semantic` add unlinked-look-alike suggestions and `meta` summarises. The rest of this doc walks
each.

---

## 1. Shared fetch/cache layer

Every remote read goes through one caching layer (`fetch_cache.py`, viewed via `sources/fetch.py`):

- `locator(subdir, base, name)` → `(base/name, raw/<subdir>/name)` — the single URL↔cache scheme
  (`fetch.py:28-32`), used identically by build-time fetch and refresh enumeration.
- `fetch_to_cache` (bytes) / `fetch_text` (decoded str) — a non-empty cached file short-circuits
  unless `force`; `build` never re-fetches present raw.
- `walk_fetchables(subdir, base, …)` — enumerates **files already pinned** under `raw/<subdir>`,
  skipping `.absent` (known-404 marker) and `.partial` (`fetch.py:65-80`). This is the refresh
  page-set for the crawl-discovered sources — and the root of the discovery-on-refresh gap (§ below).

Validators gate *adoption* only, deliberately lenient: `valid_csv`, `valid_html`, `valid_json`
(`fetch.py:41-62`).

---

## 2. The three base indexes (movement A)

Each source stage runs a **base parse** (the motif/type set) then folds in **enrichment layers**
that mutate the records in place, then writes one catalogue JSON. The base set of every index lives
in a **single fetched file** — this is why a new base motif is caught by `refresh --apply` + a
build (the enrichment layers are the crawl-discovered part).

### 2.1 TMI — Thompson Motif-Index (`_build_tmi`, `build_motifs.py`)

**Fetch (single files).** `tmi.csv` from the Trilogy dataset, plus Katja Mellmann's `tmi.csv`
(classification headings) when `mellmann.enabled` (it is). Both via `_read_csv` →
`fetch_to_cache`, parsed by `csv.DictReader`.

**Parse — `trilogy.build_tmi` (trilogy.py:1161).**
1. `_parse_tmi` (trilogy.py:349) — per CSV row → record. Columns map: `id`←`id`, `level`←`int(level)`,
   `parent`←`level_{level-1}`, `notes`←`notes` (de-bled), `name`←`motif_name` (quote reunited),
   `chapter`/`chapter_name`. Then `tmi_notes.parse_notes(notes, code)` (tmi_notes.py:112) splats in
   `definition, cultures, references, see_also, atu_inline` (the "Type N" inline ATU cites).
2. `_mellmann_supplement` (trilogy.py:1108) — adds a whitelisted set of real Thompson motifs the
   Trilogy CSV dropped, join key = motif `id`.
3. `_finalize_tmi` (trilogy.py:227) — dedup codes (`~N` suffixes, `duplicate:True`), fix parents,
   recompute zero-family levels, natural-sort.
4. `_mellmann_classification` + `_assign_tmi_divisions` (trilogy.py:950, 980) — parse Mellmann's
   `division1/2/3` + `section` headings and attach per-motif `division/sub_division/division3/section`
   (+ `_range`) **by code-range containment**, and build four browse lists.
5. `_mellmann_first_edition` (trilogy.py:1136) — `former_ids` per motif + top-level `aliases`
   (old→current renumbers).

**Record shape** (trilogy.py:362-371): `{id, code, chapter, chapter_name, name, notes, definition,
cultures, references, see_also, atu_inline, level, parent, duplicate?, division*, section*, former_ids?}`.

**Enrichment.** `bibliography.build_enrichment(tmi_motifs)` (bibliography.py) — SINGLE fetch of
folkmasa `motif_bib.htm`; produces a standalone `tmi_bibliography.json` (citation-key document,
join = citation head counted across motif `notes`), **not** an in-place attach.

**Output dict** (trilogy.py:1186-1211): `{label, long_label, attribution, homepage, chapters,
culture_legend, motifs, divisions, subdivisions, subdivisions3, sections, aliases}` → `tmi.json`.

### 2.2 ATU — Aarne-Thompson-Uther tale types (`_build_atu`, `build_motifs.py`)

**Fetch (three single CSVs).** `atu_df.csv` (the types), `atu_seq.csv` (ordered TMI-motif sequence
per type), `atu_combos.csv` (type combinations) — all via `_read_csv`.

**Parse — `trilogy.build_atu` (trilogy.py:1214).**
- `_parse_atu_seq` (trilogy.py:388) → `{atu_id: [ordered TMI motif codes]}` (codes healed by
  `_fix_motif_codes`).
- `_parse_atu_combos` (trilogy.py:420) → `{atu_id: [combo ids]}`.
- `_parse_atu` (trilogy.py:809) — per type: `id`, `num`, `chapter` (derived from the number range,
  not the CSV), `division`/`sub_division` (+`_range`), `name`+`summary` (rejoined via `_repair_atu_name`),
  `defining_motifs` (adjacent `[code]`), `former_name`/`former_ids` (apparatus), `references`,
  `attestations` + `attestations_grouped` (`atu_regions.group_by_region`), `remarks`; then
  `motifs`←`seq[id]`, `combos`←`combos[id]`.
- Post: drop See/Cf stubs (recorded as redirects), fill divisions from canonical tables, set
  `parent`/`subtypes`, sort. `_atu_aliases` → `{old_id: current_id}`.

**Record shape** (trilogy.py:826-857): `{id, num, chapter, division*, name, summary, defining_motifs,
former_name, former_ids, references, attestations, attestations_grouped, remarks, motifs, combos,
parent?, subtypes?}`.

**Enrichment (both mutate `atu_index["types"]` in place, before `atu.json` is written).**
- `atu_wikidata.build_enrichment` (atu_wikidata.py) — SINGLE SPARQL GET to Wikidata → `atu.json`
  raw cache `raw/wikidata/atu.json`. Join key = canonical ATU id (`parse_bindings` keeps only ids
  already in the index). Adds `names` (multilingual), `wikipedia`, `wikisource`, `concordances`
  (AaTh/KHM/Perry/Aesop/Child), `wikidata` (Q-id).
- `ashliman.build_enrichment` (ashliman.py) — CRAWL-DISCOVERED (see §2.4). Adds `tales` (list of
  `{title, url}` example-tale variants) to each covered type. Join = canonical ATU id, off-catalogue
  site types attaching to a hierarchical relative (`attach_target`), not equivalence.

**Output dict** (trilogy.py:1223-1237): `{label, …, divisions, subdivisions, culture_legend,
aliases, types, atu_seq}` → `atu.json`. `atu_seq` is the one field that MUST be persisted for the
crosswalk. Also writes `.discovered.ashliman.json`.

### 2.3 Berezkin — areal catalogue (`_build_berezkin`, `build_motifs.py`)

**Order note:** `mapsofmyths.build_enrichment` runs FIRST (writes three `mapsofmyths_*.json`
sidecars), THEN `berezkin.build` reads them to attach English/nodes/traditions.

**Fetch.** `index-left.html` (single index page, windows-1251) + **per-motif detail pages**
(discovered: one page per motif keyed by `motif["page"]`, fetched concurrently, gated on
`fetch_details`). `fetchables()` = `walk_fetchables("berezkin", …)` = index + every pinned detail
page.

**Parse — `berezkin.build` (berezkin.py:513).**
1. `parse_index(html)` (berezkin.py:367) — the **whole motif set from one page**. Chapters from
   `<p>/<b>` vs `_CHAPTER_RE`; motifs from `li a[href$=.html]`. Per motif, `parse_motif_entry`
   (berezkin.py:230) extracts `code`, `atu_refs` (title cites), `areas` (trailing dotted list →
   integer areal ids), `name` (residue after stripping id/ATU/see-also tokens).
   **Record shape** (berezkin.py:281-289): `{id, chapter, name, areas, see_also:[], atu_refs, page}`.
2. `_fetch_details` (berezkin.py:557) — per motif, fetch `motif["page"]`, `parse_definition` →
   attach `definition` (join key = `motif["page"]`; empty string on miss/error, never aborts).
3. `_attach_see_also` (berezkin.py:542) — parse "см. мотив X" in the Russian `definition` →
   `see_also` (kept only if the id resolves to a real motif). Runs **before** the English swap.
4. `_attach_english` (berezkin.py:441) from `mapsofmyths_en.json`, join `id.upper()` — moves
   `name`→`name_rus`, `definition`→`definition_rus`, sets English `name`/`definition`.
5. `_attach_nodes` (berezkin.py:467) from `mapsofmyths_nodes.json`, join `id.upper()` — adds
   `motif_type`, `motif_group`, `motif_group_num`, `tmi_refs`, `atu_refs` (unioned), `traditions`
   (areal ids).

**Output dict** (berezkin.py:530-539): `{label, …, chapters, areas (canonical macro-area legend),
traditions (areal_id → name/path/language), motifs}` → `berezkin.json`. Also `berezkin_bibliography`
(single `biblio.html` fetch + reuse of pinned detail pages) → standalone `berezkin_bibliography.json`.

### 2.4 How the enrichment sets are discovered (the refresh gap)

The base sets above are single files. The **enrichment** page/node sets on ashliman and mapsofmyths
are discovered by crawling/parsing an index, and that discovery lives only in `build`:

| source | build discovery | refresh (`fetchables`) enumeration |
|---|---|---|
| **ashliman** | LIVE: `discover_site_types` (ashliman.py:280) fetches `folktexts.html`/`folktexts2.html`, harvests `type\d+.html` slugs + walks themed pages reading `types NNN` declarations, UNION the frozen `_TYPE_PAGES` constant. `_page` uses `.absent` markers to skip known-404 derived names. | `walk_fetchables("ashliman", …)` — **pinned files only**; no index fetch, no themed walk. |
| **mapsofmyths** | Parse-discovered: `parse_motifs_full(get("/motifs_full"))` → node hrefs; `/traditions_full` → node ids → POST `gmap-markers-tradition` (`_post_markers`, honours `MYTHO_OFFLINE`). Credential-gated. | node set = parse of **pinned** `motifs_full.html`; markers = **pinned** `markers_*.json`. |

So on refresh the enumerated set = the pinned set, never a freshly-crawled index → a newly-added
site page/node is invisible until a `build` (or forced re-scrape) re-crawls. The motif itself is
unaffected (it comes from the base index); only the secondary annotation lags. See
[`../known-issues.md`](../known-issues.md) and the `expand`-descriptor fix in the atomisation doc.

---

## 3. Crosswalk — linking the three catalogues (movement B)

### 3.1 `derive.py` — re-project the stored JSONs

`load_indexes()` → `derived_from_indexes(berezkin, tmi, atu)` (derive.py:17-47) reloads the three
catalogues and extracts the join inputs (a `None`/absent source degrades to `{}`, never crashes):
- from **tmi**: `tmi_ids`, `tmi_aliases` (old→current), `tmi_notes` (`id → atu_inline` "Type N" cites).
- from **atu**: `atu_ids`, `atu_defining` (`id → defining_motifs`), `atu_aliases`, `atu_summaries`,
  `atu_seq` (ordered TMI codes per type), and `aath_to_atu` — inverts each type's `concordances.AaTh`
  → `{AaTh code: [atu_id]}` so old AaTh cites in TMI notes resolve to current ATU ids.
- from **berezkin**: the motif list (each with `atu_refs`, `tmi_refs`, `page`).

### 3.2 `crosswalk.build` — directed maps + inference (crosswalk.py:100-304)

Every link is stored in **both directions** (so edges appear on both pages). Resolvers apply
aliases and normalise ids before matching. Direct links:

- **ATU→TMI constituent** = `atu_seq` values (alias-resolved, deduped); inverse `tmi_to_atu`.
- **ATU→TMI defining** = `atu_defining` filtered to real TMI ids; kept separate from constituent.
- **TMI→ATU note** = each `tmi_notes` ref → `[ref]` if a real ATU id else `aath_to_atu[ref]`.
- **ATU→TMI summary** = motif tokens + ranges parsed out of each type's `summary` prose, expanded
  to every index member in range, filtered to TMI ids.
- **Berezkin→ATU** = each motif's `atu_refs` (title cites), alias-resolved; exact inverses.
- **Berezkin→TMI direct** = each motif's curated `tmi_refs` (from mapsofmyths), kept if a real TMI
  id — the one direct Berezkin↔TMI bridge, present only if mapsofmyths ran.

**Inferred** (crosswalk.py:226-284) — transitive closure completing a triangle only through a pivot
whose fan-out ≤ `INFER_FANOUT_CAP=2` (never a broad tale type): A (ATU↔TMI via a narrow Berezkin
motif), D (Berezkin↔ATU via a ≤cap TMI motif), C (Berezkin↔TMI via an ATU defining motif). Each
inferred edge records `{index, id, via_index, via_id}` on both endpoints, kept apart from direct
concordances.

**Output** `crosswalk.json` (crosswalk.py:288-304): the twelve directed maps + `inferred`
(`{berezkin,tmi,atu}` by id) + `inferred_count` + `linked_tmi_count`.

---

## 4. Parallels — unlinked look-alike suggestions (movement C)

Three suggestion layers, each kept apart from the curated crosswalk and each **subtracting
already-linked pairs** so it surfaces only *unlinked* look-alikes:

- **Lexical — `parallels.py`** (built live in `motifs:parallels`). Two TF-IDF spaces (title gate +
  title×3+desc recall), cosine k-NN, tiered A/B thresholds; subtracts existing crosswalk edges.
  Emits `adjacency` (`index→id→[{index,id,tier,title_sim,doc_sim,shared,score}]`), `triangles`,
  `counts` → `parallels.json`. Requires scikit-learn + TMI+ATU present, else no file and the fp is
  **not** stamped (the ParallelsStage guard).
- **Semantic — `semantic_parallels.py`** (PRECOMPUTED OFFLINE). `scripts/build_semantic_parallels.py`
  runs BGE-M3 (~2 GB) over TMI+ATU+Berezkin titles/text and commits
  `src/motifs/data/semantic_parallels.json`; the `motifs:semantic` stage just **copies it in** — the
  model never runs during `mytho build`. Same adjacency shape + `also_lexical` flag.
- **Reasoned — `reasoned_parallels.py`** (hand-authored, static). A literal `GROUPS` list of curated
  cross-index concept groups; no fetch, no build stage, no output file — compiled-in Python data,
  counted at report time.

---

## 5. Meta — summary + degradation watch (`_build_meta`, build_motifs.py:371-406)

Reads everything from disk (no in-memory handoff) and writes `meta.json`: `built_at`, per-index
`counts`, `enrichment` (merged from the three `.enrichment.json` sidecars), `crosswalk` link
tallies, `parallels` counts, `sources` provenance, plus the degradation machinery — per-metric
all-time `highwater`, durable self-clearing `yield-drop` `flags` (advance only on a trusted build),
and `discovery-shrank` flags when a parse-root (berezkin / mapsofmyths / ashliman) drops
previously-listed links (union in `.discovery.json`). The final cross-index rollup is logged by
`_log_summary` (build_motifs.py:414-467).

---

## 6. Fingerprints & incrementality

Each stage gates on `outputs/motifs/.fp.<name>` (`fingerprint.py`):
- **source fp** = blake2b of that source's raw slice + `config/motifs.json` + `MOTIFS_ALGO_VERSION`
  (empty `{}` when the source is config-disabled).
- **crosswalk fp** = `combine_fingerprints("crosswalk", <3 source fps>)`.
- **parallels fp** = `combine_fingerprints("parallels", crosswalk_fp)` — stamped only if the file was
  written.
- **semantic fp** = hash of the committed `data/semantic_parallels.json` (empty when absent).
- **meta fp** = fold of every upstream stage's desired fp.

So editing one source's raw re-runs exactly that source → crosswalk → parallels/semantic → meta, and
nothing else.

---

## 7. The served structure

The frontend/service reads (per-process cached, `store.py:90-133`): the three per-index catalogues
(`motifs`/`types` arrays + legends), the one `crosswalk.json` map, the two suggestion maps
(`parallels.json`, `semantic_parallels.json`), and the `meta.json` manifest. A motif/type record is
joined at read time to its cross-index links and suggestion adjacency **by `id`**. `is_built()` =
`meta.json` exists.

---

## 8. Worked example — one Berezkin motif, end to end

1. **Discovered** as a `<li><a href="M123.html">` in `index-left.html` → base record
   `{id:"M123", page:"M123.html", areas:[…], atu_refs:["ATU 300"], name:"…", chapter:"M"}`.
2. **Definition** fetched from the detail page `raw/berezkin/M123.html` and attached.
3. **Enriched** from `mapsofmyths_nodes.json` (join `M123`): gains `tmi_refs:["B11.2"]`, `motif_type`,
   `traditions:[…]`, and English `name`/`definition` (Russian moved to `*_rus`).
4. **Written** into `berezkin.json` under `motifs`.
5. **Crosswalk** turns its `atu_refs` into `berezkin_to_atu["M123"]=["300"]` (+ inverse), its curated
   `tmi_refs` into `berezkin_to_tmi["M123"]=["B11.2"]` (+ inverse), and may add an **inferred** edge
   (e.g. Berezkin↔TMI via an ATU-300 defining motif).
6. **Parallels** may suggest an *unlinked* TMI/ATU/Berezkin look-alike for `M123` (lexical or
   semantic), excluded if already in the crosswalk.
7. **Served**: the frontend renders `M123` from `berezkin.json` and, by `id`, hangs its crosswalk
   links and parallel suggestions off it.
