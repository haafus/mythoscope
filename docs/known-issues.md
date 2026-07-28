# Known issues & caveats

Register of known issues, caveats and design tensions across the project (motifs,
embeddings, …): what's wrong or by-design, why, where it bites, and the options.
Append new entries at the top.

---

## Deactivating an embedding model does not protect its collection from `clean`

**Status:** by design — GC reachability is keyed on live (active) stages, not on config presence.

Moving a model from `models.json` `models` to `inactive` drops its pipeline stage, but its Chroma
collection stays on disk. `mytho build` never touches it (build only builds active stages, and
never reaps). But it is now a **level-2 orphan** — no live stage claims it — so:

- `mytho clean` (unscoped) or `mytho clean embeddings` (whole family) **will delete it** on `--apply`.
- `mytho clean embeddings:<other-active>` (single member) will **not** — level-2 is family-granular
  (`driver.clean`; `pipeline-and-incrementality.md` §2.7).
- `mytho status` / `mytho clean` (dry-run) surface it as an orphan first.

Where it bites: parking a model by deactivating it, then running a family/full `clean --apply`,
silently discards its (expensive) embeddings. (This differs from the pre-Part-3 inspector, which
spared inactive collections via `include_inactive=True`.)

Handling: to **park** a model, deactivate it and simply don't run a family/full `clean` — build
ignores it, and re-activating it reuses the collection (the fp gate skips unchanged docs). Run a
family/full `clean --apply` only when you actually want the disk back.

---

## Enrichment discovery: `refresh` self-sufficiency + two narrow residuals

**Status:** flagged — much narrower than first written; verified against the source. Full audit:
[`proposals/motifs-atomisation.md`](proposals/motifs-atomisation.md) ("Guarantees & gaps"); the
`expand` design in the same doc (§8).

**The alarm ("new motifs / enrichments are invisible without `--force`") is essentially false.**
The set-revealing index of *every* source is a pinned file that `refresh` re-checks, and after
`refresh --apply` a normal `build` re-parses it and fetches the new children on cache-miss:

- **Base motifs** live in one file each — TMI `tmi.csv`, ATU trilogy `atu_*` CSVs (+ the one
  Wikidata `atu.json`), Berezkin its index page. A new motif = a changed pinned file → `refresh
  --apply` + `build`. No `--force`.
- **mapsofmyths** — both listing pages (`motifs_full.html`, `traditions_full.html`) are **explicit
  `fetchables()`** (`mapsofmyths.py:237-238`). A new node/marker changes a listing → `refresh`
  flags it → `build` re-parses the adopted listing and fetches the new `node_*.html` / POST markers
  on cache-miss. No gap.
- **ashliman** — the index pages (`folktexts.html`/`folktexts2.html`) and themed pages are pinned,
  and `fetchables()=walk_fetchables("ashliman",…)` enumerates them, so `refresh` re-checks them too.
  A newly **linked** type page (referenced from an index or declared on a themed page) flows through
  `refresh --apply` + `build`.

Two genuine but narrow residuals remain:

1. **ashliman numbered pages behind a frozen probe constant.** `discover_site_types` takes its
   `numbered` set from the hardcoded `_TYPE_PAGES` frozenset (`ashliman.py:326`), regenerated only
   by a manual brute-force run (`probe=True`). A type page that *exists but is not linked* from any
   index/themed page — findable only by probing the `typeNNNN.html` numbering — is invisible until
   the probe is re-run. (Only the secondary "example tales" annotation on an already-present ATU
   type; never a missing motif.)
2. **No orphan detection for a de-linked-but-live page.** A page dropped from an enrichment index
   yet still returning 200 is re-checked as `not changed`; nothing notices it left the index.

Fix (designed, optional): the recursive `expand: bytes -> [Fetchable]` descriptor (§8) would make
`refresh` **self-sufficient** (discover children itself, without needing a following `build`) and,
with a scope-diff, add the orphan detection of (2). It does **not** address (1) — that needs a
periodic re-probe of the numbering, not index parsing.

---

## Raw write path has no `fsync` — atomic but not power-loss durable

**Status:** flagged — accepted trade-off, documented; no `fsync` in the write path.

`commit_bytes` (`src/fetch_cache.py`) stages to a unique `.partial` then `os.replace` — atomic, so
a crash never leaves a torn/half-written live file. But it calls no `fsync` on the file or its
parent directory. `os.replace` guarantees *atomicity* (which of the two versions you see), not
*durability* (that the new version survived to disk).

Where it bites: a power cut or kernel panic between the write and the OS's physical flush can lose
a just-adopted byte-set, falling back to the old pinned copy. No corruption — you never get a
half-file — but a fresh `refresh --apply` adoption is not guaranteed to have landed.

Options: accept (current — rare, and the fallback is the last-good copy, not garbage); or `fsync`
the temp file + parent dir in `commit_bytes` before/after `os.replace` for true durability, at a
per-write I/O cost.

---

## Lenient validators can adopt a structured 200-error over good pinned data

**Status:** flagged — deferred; needs a per-source semantic parser.

The adopt gate validators (`src/motifs/sources/fetch.py`: `valid_html`/`valid_csv`/`valid_json`)
are deliberately lenient — non-empty + carries markup / parses as CSV/JSON — so a genuine payload
is never falsely kept-pinned. But a **well-formed HTML error page served with 200**, or a
plausibly-structured-but-wrong payload, passes the check and *can* be adopted over a good pinned
copy on `refresh --apply`.

Where it bites: an anti-bot interstitial or a "service unavailable" page rendered as valid HTML
with a 200 status overwrites the last-good raw when the user applies a refresh.

Options: accept (current — the common empty/wrong-content-type failures are already caught); or add
a per-source **semantic** validator (does the parse yield the expected records?) as the adopt gate,
beyond the structural check.

---

## LLM concurrency is one global constant, but the right value is per-provider

**Status:** flagged — single hand-tuned constant; per-provider derivation not implemented.

`max_concurrent` (in-flight LLM chunks) is a single number per stage —
`settings.GraphsSettings.max_concurrent` (8) and `settings.ProjectionsSettings.max_concurrent`
(5) — but the value that keeps the pipe full without over-driving the provider depends on the
**provider's rate limits and the typical call size**, which change when you switch `graphs.llm`
(or `embeddings`/`projections` model) to a different entry in `config/models.json`.

Two regimes pull the right number in opposite directions:

- **TPM-bound tier (e.g. `gpt4o-mini`: 200k TPM).** Graph calls are ~13k tokens each
  (50k-char chunks × 4 prompts/chunk), so only ~15 fit in a minute. TPM is the bind; the rate
  limiter (`src/llm/rate_limiter.py`) paces admissions regardless, so concurrency above ~8 just
  leaves threads idle-waiting in `acquire()`. Hence the 8 default.
- **No configured limit (e.g. `gpt4o`, `gemini25-flash` — no `rpm`/`tpm` in `config/models.json`).**
  The governor reports "concurrency only": in-flight concurrency is the *only* throttle, so a
  low number needlessly serializes a provider that could take far more.

Where it bites:

- **Silent mis-tune on model switch.** Point `graphs.llm` at an unlimited or higher-TPM provider
  and the run stays capped at a concurrency picked for `gpt-4o-mini` — leaving throughput on the
  table. Point it at a *tighter* tier and 8 could be too high.
- The number encodes an assumption about the *current* model's limits that nothing re-derives.

Options:

- **Accept (current).** One hand-tuned constant per stage; retune by hand when you change model.
- **Derive it from the provider.** Compute an effective concurrency from the model's
  `rpm`/`tpm` (in `config/models.json`) and a typical call-token estimate — e.g.
  `min(rpm-derived, tpm / typical_call_tokens)` — falling back to a plain concurrency cap when no
  limits are configured. The rate limiter already knows the limits; this would just size the pool
  to match instead of relying on a separate constant.
- **Per-provider override.** Add an optional `max_concurrent` to each `config/models.json` entry,
  so the value travels with the model it was tuned for rather than living in stage settings.

---

## Motifs page names/colours regions with two non-aligned vocabularies

**Status:** flagged — motif-index side, fix deferred with the cross-index review below; not started.

On one screen (`src/server/web/assets/page-motifs.js`) two region vocabularies coexist and don't line up:

- **The data.** `services/motifs.py::_berezkin_region` groups Berezkin area codes 10–74 into **11 names**:
  `Africa · Europe · Near East · Central Asia · Oceania · Asia · Siberia · Arctic · North America ·
  Mesoamerica & Caribbean · South America`.
- **The palette.** `page-motifs.js::REGION_COLORS` has **17 keys**: the 11 above **plus** `South Asia`,
  `East Asia`, `Southeast Asia`, `Mesoamerica`, `Caribbean` (and `—`).

Concrete conflicts:

- **`Asia`** — the data lumps codes 21–26 into a single `Asia` bucket, while the palette also carries
  `South Asia`/`East Asia`/`Southeast Asia`: colours for a split the data never emits.
- **`Mesoamerica` / `Mesoamerica & Caribbean` / `Caribbean`** — the data emits only `Mesoamerica & Caribbean`;
  the palette holds all three, so two keys are dead.
- So `South Asia`, `East Asia`, `Southeast Asia`, `Mesoamerica`, `Caribbean` in the palette **never match** a
  data name — dead entries — and `Asia` is named at two granularities on the same page.

Resolution: fold into the cross-index review below (align the palette to the actual `_berezkin_region`
output, or vice versa, and drop the dead keys). Untouched by the tradition `region` work
(`docs/proposals/region-implementation.md` §2.7).

---

## Cross-index reference/inference system between motif indexes is noisy and redundant

**Status:** flagged — needs a dedicated review to compress; not started.

The web of **cross-references and inferred parallels** linking the motif indexes to one another
(TMI ↔ ATU ↔ Berezkin, plus reasoned/derived links and unresolved citations — see
`docs/motifs/crosswalk/` and `src/motifs/sources/`) has grown **noisy and redundant**: overlapping links,
low-signal or speculative parallels, and duplicated assumptions that add volume without adding
information.

Where it bites:

- **Signal-to-noise.** Weak/duplicate links dilute the genuine cross-index parallels; downstream
  analysis inherits the noise.
- **Maintenance surface.** More links and assumptions than are load-bearing means more to keep correct
  and reconcile on every source update.

Resolution:

- **Do a review and compress it.** Audit the cross-reference/inference layer end to end, drop the
  redundant and low-confidence links, and keep a tighter, higher-confidence set. Scope and criteria to
  be defined by that review. *(This is separate from the tradition `region` work — it is the motif-index
  side; see the "do not touch the motif-index region system" decision in
  `docs/proposals/region-implementation.md` §2.7.)*

---

## Chunk text and metadata are duplicated across every collection

**Status:** by design — inherent to the per-variant collection layout; Option A adds one more copy.

Each embedding variant (a model, or a model × preprocessing mode) is its **own Chroma
collection**, and every collection stores a full copy of what it embeds:

- the chunk text goes into Chroma's `document` field, and
- per-chunk metadata (`text_id`, `chunk_index`, `tradition`, `major_tradition`, `url`)
  is attached to every point.

So the **same chunks are copied into every collection**, once per variant — including
**raw variants**, not only preprocessing ones: a raw variant's `document` is itself a
per-model copy of the source. With M active models the corpus text exists as M separate
copies (one `document` set per model).

Preprocessing variants (the "Option A" plan) add a **further** copy: their `document`
holds the *processed* text, so to also reveal the original in the UI we would store the
source chunk in metadata (`source_text`) — an extra copy on top of the per-model baseline.

Where it bites:

- **Storage scales with variant count × corpus size.** Adding a model or a preprocess
  mode re-copies the whole corpus's chunks; a preprocess variant stores the chunk twice
  (processed `document` + `source_text` metadata).
- **Snapshot drift.** Every copy is frozen at build time; re-cleaning the corpus or
  changing chunk params leaves stale copies until each collection is rebuilt.

Options:

- **Accept (current).** One collection per variant is Chroma's native model, and each
  collection carries everything it shows — no lookup against another store at view time.
- **Intermediate chunk-text store (SQLite), the intended direction.** Keep the chunk
  texts — the source and each variant (summary, course of action, …) — in a store keyed
  by chunk id, with Chroma collections holding only vectors. The server resolves any view
  by id, so each text is stored once: the duplication disappears (both the `source_text`
  copy and the per-model `document` copies), and it generalizes to any number of views.
  Not planned yet.

---

## Raw scrape cache is a snapshot, not a reproducible dataset

**Status:** by design — treat all counts as version-dependent.

Every external download is cached under `outputs/motifs/raw/**` (areasofmyths /
mapsofmyths HTML, the folkmasa bibliography, Wikidata SPARQL responses). This
cache is **gitignored** and, by default, **not exported** (`mytho export` skips
`raw/**`; `mytho export --caches` deliberately includes it) because it isn't
reproducible:

- The upstream sites are live and change over time — pages get edited, motifs
  added or renumbered, a site can move or go down. A fresh `mytho refresh motifs
  --apply` (re-scrape) can therefore return **different counts** than a cache built
  earlier.
- The cache is a point-in-time snapshot, not a versioned dataset; two machines
  scraping on different days may disagree.

Consequences and handling:

- Every motif / type / tradition **count in these docs is an approximate
  snapshot** of one build — re-verify against a fresh build before quoting it.
- Only **code** is committed; the built indexes (`outputs/motifs/*.json`) and the
  raw cache are regenerated, not tracked. To hand a working dataset to someone
  without credentials or network, ship the built `*.json` via `mytho export`
  (raw excluded by default; add `--caches` to also ship the raw scrape).
- Refresh from upstream with `mytho refresh motifs --apply` (re-downloads); a plain
  `mytho build motifs` re-parses the existing cache without touching the network.

---

## Competing macro-area schemes (six vocabularies)

**Status:** open — needs a decision before touching `_berezkin_region`.

There are **six independent "macro-region" vocabularies** in play at once, none of
which fully agree. #1–#3 are geographic partitions of the **motif catalogue** and
overlap in the same UI; #4 is a different axis *and* a different dataset (our corpus
of texts); #5 is a frontend **colour layer** whose own key names form yet another
list; #6 is the **proposed unifying target** that would subsume the rest. This makes
"region" ambiguous: the same Berezkin motif page labels regions one way in the
overview chart and another way in its Traditions section.

### The schemes

| # | Scheme | Buckets | Where it lives | Authored by | Used for |
|---|---|---|---|---|---|
| 1 | Berezkin broad regions | **11** | `_berezkin_region()` in `src/server/services/motifs.py` | us (ad-hoc) | Berezkin overview "Motifs by region" chart |
| 2 | TMI culture regions | **12** | `_REGION` in `src/motifs/sources/culture_dict.py` | us (ad-hoc) | TMI overview "Motifs by region" + per-motif "Attestations by culture" grouping |
| 3 | Berezkin areal hierarchy (major traditions) | **16** | `areal_path[0]` in `outputs/motifs/mapsofmyths_traditions.json` | Berezkin (authoritative) | Berezkin per-motif "Traditions" distribution grouping |
| 4 | Corpus tradition families (`major_tradition`) | **12** | `config/traditions.json` | us (hand-authored) | Geography map + corpus grouping — **different dataset (our texts), not motifs** |
| 5 | `REGION_COLORS` motif-region palette | **~16** | `REGION_COLORS` / `regionColor()` in `src/server/web/assets/page-motifs.js` | us (ad-hoc) | **Colour layer**, not a partition: maps region *names* → hex for the #1/#3 bars and attestation accordions. Its keys (`Central Asia`, `Southeast Asia`, `Caribbean`, `Asia`, `—`…) union #1+#2 names, so its vocabulary matches neither cleanly. See [`reviews/archive/color-system-review.md`](reviews/archive/color-system-review.md) §7 |
| 6 | Proposed `area` facet (**target**) | **12** | `docs/proposals/archive/macro-area-facets.md` → mockup 21; not yet in code (`region_facets.py` unwritten) | us (derived from #3's `areal_path`) | The converged geographic axis of a tradition in the entity model — the intended replacement that folds #1/#3/#5 into one deterministic 12-area vocabulary |

### Why they conflict

- **#1 vs #3 — the sharp one.** Both describe the *same* Berezkin 59-area system,
  but differently: #1 is our ad-hoc roll-up of the numeric area codes 10–74 into
  11 continents; #3 is Berezkin's own authoritative 16 macro-areas over the same
  areas. The two are **different partitions**, not a re-numbering — they diverge
  right after Africa (code 14 "North Africa" → our *Africa*, but Berezkin groups
  it with *Western Europe, North Africa*), differ in granularity (South America:
  20 codes vs 13 hierarchy areas), and carve differently (Beringia, Madagascar,
  Mexico–Central Andes, Plains-vs-North&West). So on **one Berezkin motif page**,
  the overview chart (#1) and the Traditions section (#3) speak different region
  languages.
- **#1 vs #2** disagree in three zones: Asia granularity (#1 lumps S/SE/E Asia as
  one "Asia" + a "Central Asia"; #2 splits into South/Southeast/East Asia with no
  Central Asia), Arctic (#1 keeps it; #2 folds it into North America), and
  Mesoamerica/Caribbean (#1 combined, #2 separate). They share 7 buckets exactly
  and disagree in *both* directions (neither refines the other).
- **#4** is orthogonal — grouped by cultural/religious family (Near Eastern,
  Indo-European, …), not geography, and it classifies our **corpus of texts**,
  not the motif catalogue's world coverage. It only shares a few incidental names
  ("Polynesian", "African").
- **#5** is not a competing *partition* but a colour map, so it can't be "wrong" the
  way #1–#3 can — yet its key list is a **fifth region naming** (it lists both #1 and
  #2 names so it can colour either), so it quietly hardcodes region names a third way
  and drifts from whatever #1/#2/#3 actually emit; an unlisted name silently falls to
  the fallback palette.
- **#6** doesn't conflict — it's the **target**: a deterministic 12-area collapse of
  #3's `areal_path`. It's listed so the enumeration is complete, but it lives only in
  the proposal + mockup 21, not yet in the running code.

### Impact

- Region vocabulary is inconsistent across the UI; you cannot cross-reference
  "motifs per macro-region" between the Berezkin and TMI overviews.
- The Berezkin motif page uses two different region schemes on the same screen
  (#1 in the chart, #3 in Traditions), so region names visibly disagree there.

### Resolution options (mutually tensioned)

- **Make Berezkin authoritative:** replace scheme #1 with scheme #3 (Berezkin's
  own 16 macro-areas). This requires a curated hardcoded `code → macro` map
  (no automated bridge exists — the two systems are different partitions; a
  positional/name/empirical match all fail), kept like `_CANONICAL_AREAS` so the
  chart still works without mapsofmyths credentials. **But** this pushes #1
  *further* from #2 (16 vs 12), not closer.
- **Unify #1 ↔ #2** into one shared geographic vocabulary. Requires reconciling
  four decisions: Asia granularity, keep/fold Arctic, keep/fold Central Asia,
  split/combine Mesoamerica+Caribbean. **But** the result is then *not* Berezkin's
  authoritative scheme.
- These two goals ("use the authoritative Berezkin scheme" and "align Berezkin
  with TMI") pull in **opposite directions** — pick one before editing
  `_berezkin_region`.
- **#4 stays separate** by design (different axis, different dataset).
- **Or model the entities instead of picking one list** — see
  [`proposals/archive/macro-area-facets.md`](proposals/archive/macro-area-facets.md): an entity model
  where a **tradition** carries `area` (12, derived from `areal_path` — this is scheme
  #6), `family` and `subsistence`, while time-depth (`stratum`) is a **motif** property,
  not a tradition one. Folds #1/#3 into `area` (#6), lets #5's palette re-key to those
  12 areas, recognises #4 as `family`, and gives the non-areal clusters (literary-epic
  Asia, Sun-&-Moon) a home as motif strata.

### Note

TMI (#2) is intrinsically its own scheme — it sits over Thompson's culture
labels, a different source with no areal codes — so it will never fully match a
Berezkin-derived vocabulary regardless of the choice above.
