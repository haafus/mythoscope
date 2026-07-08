# Migration plan: TMI source Trilogy → Mellmann

Status: **partially implemented — the additive-first phase shipped; the full
source swap was not done.** This document is kept as the plan and provenance.

What shipped (the recommended §3 "additive-first" path): Mellmann is wired in
as an *enrichment* source (`mellmann` in `config/motifs.json`, read once in
`trilogy.build_tmi`) — the printed classification headings (division1–3 +
section), the 10 recovered supplement motifs, and the `1st ed.` edition-history
redirects (`former_ids`/`aliases`, mirror-close). See `../tmi-reference.md`
§5–6. Trilogy remains the source of the motif text itself (it preserves the
`†` daggers and diacritics better), so the proposed *replacement* of the TMI
backbone (§1) was deliberately not carried out — the two layers below marked as
future work stay open.

## 1. Summary

Replace the **TMI motif-index source** — currently `tmi.csv` from the
`j-hagedorn/trilogy` dataset — with Katja Mellmann's
[`KatjaMellmann/TMI_as_CSV`](https://github.com/KatjaMellmann/TMI_as_CSV)
(OSF DOI `10.17605/OSF.IO/XEB67`, CC-BY-4.0, v1.1).

**Scope is narrow.** Trilogy stays the source for ATU (`atu_df.csv`,
`atu_seq.csv`, `atu_combos.csv`), and `atu_seq` keeps feeding the ATU↔TMI
cross-walk. Only the TMI *index* is swapped. There is no such thing as a
"Mellmann ATU" — this migration does not touch ATU or Berezkin.

## 2. Why (evidence)

A source-to-source comparison (Trilogy `tmi.csv` vs Mellmann `tmi.csv`,
both raw, both independent transcriptions of Thompson 1955–58) established:

- **Mellmann is the strictly fuller catalogue.**
  - Codes: Mellmann ⊇ Trilogy (**+14** codes; 0 the other way).
  - Citations on shared codes: **Trilogy-unique 0, Mellmann-unique 79**
    (the 79 are revised-edition supplements — `Irish myth: Cross`,
    `Jewish: Neuman`, `India: Thompson-Balys`).
  - Definitions: preserved in Mellmann's `MOTIF` field, **already split**
    from citations (`bibliographies`) — the split our `parse_notes` does by
    hand on Trilogy's conflated `notes` blob.
- **Mellmann carries non-derivable structure Trilogy lacks:** printed
  division headings (`division1–3`), the tens `section`, first-edition
  provenance (`1st ed.`, plus 60 dropped-motif "ghost" rows and ~1175
  old→new renumberings), and a canonical sort key.
- **The `.0` / `level=NA` corruption is Trilogy's, not Mellmann's.** It comes
  from Trilogy's home-built `level_0..level_6` ancestry columns; Mellmann
  never encodes a numeric level, so the defect (and our ~1418-code repair)
  does not exist there.
- **What Trilogy uniquely has is recoverable or cosmetic:** the recursive
  dot-tree is derivable from the codes (`_id_trim_parent`, which we already
  run); inline `(Cf. X)` cross-refs are in Mellmann's `MOTIF`; the `†`
  daggers (7024) are pure typography whose referenced code survives.

Conclusion: dropping Trilogy-as-TMI loses **nothing non-derivable**;
keeping Trilogy-as-TMI forgoes 79 citations, 14 codes, the heading scaffold,
provenance, and dangling-reference resolution.

## 3. Recommended shape: phased, additive-first

Do **not** treat this as one atomic swap. The valuable, non-derivable Mellmann
data (headings, `1st ed.` provenance) is *low-risk and additive*; the source
swap itself is the *risky* part (cross-walk join drift, embedding churn).
Decouple them:

- **Phase 0 — enrichment, no source change.** Harvest two things from Mellmann
  and join them onto the **existing Trilogy index by code**: (a) the
  `division1-3` + `section` heading scaffold, (b) the `1st ed.` old→new
  renumber map. Ship them as generated data files consumed as *optional
  overlays*. This delivers the Classification section and the dangling-ref
  resolution **before** touching the source, and is trivially reversible.
- **Phase 1 — source swap.** Only once Phase 0 has proven the heading/provenance
  data is sound, replace the TMI parser (sections 4–6). By then the risky part
  is isolated: coverage/citation/definition changes, nothing else.
- **Phase 2 — cleanup.** Retire the now-dead Trilogy TMI code paths (`.0`
  repair, `level_N` reader, definition-unmixing heuristics) and re-embed.

The migration can pause after any phase and still be net-positive.

## 4. Source facts

| | Trilogy TMI (current) | Mellmann (target) |
|---|---|---|
| URL | `raw.githubusercontent.com/j-hagedorn/trilogy/master/data/tmi.csv` | `raw.githubusercontent.com/KatjaMellmann/TMI_as_CSV/main/tmi.csv` |
| license | CC-BY-SA-4.0 | **CC-BY-4.0** |
| rows / codes | 46 230 / 46 222 | 46 302 / 46 237 (incl. 60 blank ghost rows) |
| columns | `id, chapter_name, motif_name, notes, level, level_0..level_6, chapter_id` | `code, [sorting field], 1st ed., chapter, division1, division2, division3, section ("tens"), MOTIF, bibliographies` |
| encoding | UTF-8 | UTF-8, `,` sep, `"` quote |

Note the licence change (SA → plain BY): update attribution text; BY-4.0 is
strictly more permissive, no downstream-share-alike obligation.

## 5. Field mapping

| internal motif field | from Mellmann | notes |
|---|---|---|
| `id` / `code` | `code` | strip editorial dup markers `[b]`, `[.1]`; keep for a raw column |
| `name` | title portion of `MOTIF` | `MOTIF` = `"CODE. Title. Optional definition…"` — split on first `". "` after the code |
| `definition` | definition portion of `MOTIF` | text after the title sentence; **replaces most of `parse_notes` definition-splitting** |
| `notes` (raw) | `bibliographies` | pure citations already — feed to citation/culture parser |
| `cultures`, `references`, `see_also`, `atu_inline` | parsed from `bibliographies` + `MOTIF` | keep existing extractors; `see_also.cf` now comes from `(Cf. X)` in `MOTIF` |
| `chapter` / `chapter_name` | `chapter` | `"A. Mythological motifs."` → split letter + name |
| `parent` | **derived** from `code` via `_id_trim_parent` | no `level_N` columns to read anymore |
| `level` (depth) | **derived** from parent chain | retire place-value + `.0` repair |
| `division1/2/3` | `division1/2/3` | **new** optional heading fields |
| `section` | `section ("tens")` | **new** flat tens-bucket label |
| `first_edition` | `1st ed.` | **new** provenance field |
| `sort_key` | `[sorting field]` | optional; validate against our `tmi_sort_key` |

## 6. Structural changes to the pipeline

All changes are confined to `src/motifs/sources/` and `config/motifs.json`;
downstream (crosswalk, store, API, UI) consumes the same normalized motif
dict, so those interfaces stay stable except where we *add* fields.

1. **New parser** `sources/mellmann.py` (or a `_parse_tmi_mellmann` path in a
   renamed module) reading the 10-column schema. `trilogy._parse_tmi` /
   `_finalize_tmi` for TMI are retired; `trilogy.build_atu` and the ATU
   parsing stay untouched.
2. **Hierarchy**: build the recursive dot-tree from codes only
   (`_id_trim_parent` already exists and is correct). Depth = distance to the
   chapter root. **Retire** `_is_zero_family`, the `.0` `level=NA` repair, and
   the `level_0..level_6` reader. The A1-under-A0 / `.0` questions dissolve:
   `A52.0.1`'s parent is `A52` by id-trim, exactly as today.
3. **Definition/citation split**: becomes trivial — Mellmann pre-separates.
   Keep the citation → cultures/references extractor; **drop** the fragile
   `_split_definition` / `FORCE_BIBLIOGRAPHY` / leading-citation heuristics
   (they existed only to unmix Trilogy's blob).
4. **Duplicates**: Mellmann already disambiguates Thompson's own dup codes
   with `[b]`/`[.1]`/`.2.2` (3 notations). Decide: (a) normalize them to our
   uniform `~N` + `duplicate` flag, or (b) adopt her bracket notation. Our
   dup set (8) and hers (6) only partly overlap — re-derive the dup set from
   Mellmann rather than porting the current list.
5. **Ingest cleanup** (Mellmann's own warts):
   - drop the 60 blank-`code` ghost rows from the catalogue, but **harvest**
     their `[First Edition: X.]` codes into the renumber/provenance map;
   - repair ~14 malformed `code`/`MOTIF` splits (missing `.`/space:
     `T317.0.1`, `X751.`, typo `Z56.1`→`Z356.1`, `detruction`);
   - normalize her three dup notations.
6. **Provenance & dangling resolution**: build an `old → new` map from
   `1st ed.` (≈1175 renumberings) + ghost codes. Expose `first_edition`
   on the motif; use the map in the cross-walk to resolve ATU references
   that cite pre-revision numbers (confirmed cases: `A14→A13.1.1`,
   `A35→A33.1.1`, `B478→B495.1`, `D21→D23.1`).

## 7. Cross-walk reconciliation (the real risk area)

`atu_seq` (Trilogy) lists TMI codes per tale type; the walk joins them to the
TMI index **by code string**. Swapping the index changes which codes exist.

- Re-run the ATU→TMI join against the Mellmann code set; **measure the new
  dangling count** (codes `atu_seq` cites but the index lacks) and compare to
  today's baseline.
- Apply the `1st ed.` renumber map before declaring a code dangling — this
  should *reduce* dangling vs today.
- Verify the `D16102.2 → D1610.2.2` fix (`_MOTIF_CODE_FIXES`) is still needed
  against Mellmann (it may already be correct there).
- The `~N` / bracket dup codes must resolve: `atu_seq` cites bare Thompson
  numbers, so the canonical (bare-code) survivor of each dup must remain the
  join target, exactly as now.
- `tmi_sort_key` (imported by `crosswalk.py`) is code-based and unaffected.

## 8. Side-by-side prototyping (no pipeline edits)

Two properties of the current code make a full A/B build possible **without
editing a single tracked file**:

- `settings` is pydantic with `env_prefix="MYTHO_"`, so `motifs_dir` is
  overridable via `MYTHO_MOTIFS_DIR`;
- `_read_csv` reads a **cache** at `{motifs_dir}/raw/trilogy/tmi.csv` and only
  downloads on a cache miss — so pre-seeding that path swaps the input.

Recommended harness (lives in `scripts/`, imports nothing into the pipeline):

1. `export MYTHO_MOTIFS_DIR=outputs/motifs_mellmann` — isolated output tree.
2. Copy the existing `atu_*.csv` into the parallel `raw/trilogy/` so ATU is
   byte-identical and **every diff is attributable to the TMI swap alone**.
3. A `mellmann_shim.py` writes a Trilogy-schema `tmi.csv` from Mellmann
   (reconstructing `level_N` via id-trim, `notes = bibliographies`). This runs
   the **real, unmodified pipeline** — `_finalize_tmi`, `parse_notes`,
   cross-walk — end to end on Mellmann data.
4. Run the normal build; it consumes the seeded cache (no download).
5. `diff` the two `outputs/motifs/*.json` trees.

Two depths, pick by goal:
- **Shim into Trilogy schema** (above): fastest, zero new modules, exercises
  the whole downstream incl. cross-walk — best for coverage/citation/dangling
  diffs. Cost: Mellmann's clean def/citation split and headings are flattened
  back into the Trilogy shape, so those advantages aren't visible this way.
- **Parallel builder** `sources/mellmann.py` (new file, unwired → existing
  behaviour unchanged) + a `scripts/compare_tmi.py` that builds both and diffs
  the normalized dicts — surfaces the new fields (`division`, `section`,
  `1st ed.`, clean `definition`). Wire `crosswalk.build(...)` in the harness if
  downstream comparison is wanted.

Keep the shim/harness even after migration: it becomes the regression oracle
for Phase 1 (section 9).

## 9. Reconciliation report as a committed artifact

Have the harness emit a `docs/motifs/tmi-mellmann-diff.md` (or a JSON under
`outputs/`) enumerating, deterministically: codes added/removed, per-motif
citation deltas, dangling ATU→TMI before/after, duplicate-set changes, and any
motif whose `parent`/depth moved. Commit it. This turns "trust me, it's fuller"
into an auditable diff a reviewer can read, and doubles as the sign-off gate
for each phase.

## 10. The renumber map is a reusable asset, not migration scaffolding

The `1st ed.` old→new map (~1175 renumberings + 54 dropped ghosts) has value
**independent of the source swap**: wired into the cross-walk it resolves ATU
references that cite pre-revision numbers (`A14→A13.1.1`, `B478→B495.1`, …).
Extract it as a standalone generated data file in Phase 0 and let the walk
consult it even while still on the Trilogy index. Ship it once, benefit before,
during, and after migration.

## 11. Capabilities unlocked (follow-on, not required for parity)

- A real **Classification / hierarchy** section for TMI in the UI, driven by
  `division1-3` + `section` (the long-discussed missing heading layer).
- **First-edition provenance** surfaced per motif; "added in revised edition"
  filter.
- Cleaner **definition** field for embeddings/semantic-parallels (already
  separated at source → less parser noise).

## 12. Migration steps (ordered)

1. `config/motifs.json`: add a `mellmann` source block (url, license,
   attribution, `files.tmi`); keep `trilogy` for ATU. Decide whether TMI
   `files.tmi` moves under `mellmann` or `trilogy` stays TMI-less.
2. Write `sources/mellmann.py`: parse, clean (step 5), build hierarchy from
   codes, emit the normalized motif dict + new fields.
3. Point `build_motifs.py` TMI step at the Mellmann builder; leave the ATU
   step on `trilogy.build_atu`.
4. Trim `parse_notes` to citation/culture extraction; delete the
   definition-unmixing heuristics and `.0` repair.
5. Reconcile the cross-walk (section 6); rebuild `crosswalk.json`.
6. Full rebuild; diff outputs vs baseline (section 9).
7. Recompute embeddings / semantic parallels **only if** definition/notes
   text materially changed the corpus (it will — the def text is now clean);
   plan a `bge_m3.npy` re-embed and `semantic_parallels.json` refresh.
8. Update docs: `../motif-index-data-sources.md`, `../tmi-reference.md` (hierarchy
   + `.0` sections now obsolete), `../crosswalk.md`; add a `1st ed.` note.
9. Bump asset versions if the motif API shape changes (new fields) — UI,
   `page-motifs.js`, `app.css` `?v=` query.
10. Tests: update fixtures/expected counts; add tests for the renumber map,
    ghost-row harvesting, malformed-split repair, dup normalization.

## 13. Validation checklist (compare pre/post)

- code count (expect ≈ +14 real, minus 60 ghosts filtered);
- 0 codes present before but missing after (except intentional dup-notation
  changes);
- citation coverage per motif ≥ baseline (expect +79 supplement citations);
- dangling ATU→TMI references **down** (renumber map);
- no `level=NA` / no `.0` repair warnings (code retired);
- hierarchy: every non-root has a resolvable `parent`; spot-check
  `A1`,`A52.0.1`,`A300.1`,`A661.0.1` land where they do today;
- duplicates: `S222`, `Z64`, `K561.1.1`, `E755.2.8` still handled;
- UI: motif page renders definition, citations, cultures, cross-refs, and
  (new) division/section + first-edition.

## 14. Test oracles worth adding

- **Sort-key oracle**: Mellmann's `[sorting field]` is an independent canonical
  ordering — assert our `tmi_sort_key` reproduces it (a free correctness check
  on our sort, regardless of migration outcome).
- **Golden snapshot**: freeze a fixture of ~50 representative motifs
  (roots, `.0`, dups, deep dotted, renumbered) pre-migration; assert post-swap
  parity except intended changes — the mechanical guard behind the section 9
  checklist.
- **Renumber round-trip**: for every `old→new` pair, assert `new` exists in the
  index and `old` does not (catches a stale or self-referential map).

## 15. Licensing composition

The product would then mix **CC-BY-4.0** (Mellmann TMI) with **CC-BY-SA-4.0**
(Trilogy ATU) and Berezkin's terms. These don't conflict, but attribution must
be **per-source**, and the SA obligation attaches only to Trilogy-derived
portions (the ATU index / `atu_seq`), not to the Mellmann-derived TMI. Update
the `attribution` blocks in `config/motifs.json` and any export/bundle notice
accordingly; do not let one blanket licence line imply SA over the whole set.

## 16. Upstream contribution (open-science hygiene)

Mellmann's repo is public, CC-BY, and actively versioned. The ~14 malformed
`code`/`MOTIF` rows and typos we found (`T317.0.1`, `X751.`, `Z56.1`→`Z356.1`,
`detruction`) are worth reporting/patching upstream — it benefits the shared
dataset and means our ingest cleanup (section 5) can eventually shrink. Track
which fixes are local workarounds vs upstreamed so the local list can be pruned
as upstream lands them.

## 17. Risks & rollback

- **Cross-walk drift**: the join is code-string based; any code-notation
  change (dups, brackets) can silently drop links. Mitigate with the
  pre/post dangling diff (section 9) as a gate.
- **Embedding churn**: cleaner definition text shifts the semantic-parallels
  corpus; treat the re-embed as part of the migration, not an afterthought.
- **Mellmann data warts**: her ghost rows / malformed splits / typos must be
  cleaned on ingest or they leak into the catalogue.
- **Rollback**: the change is source-local. Keeping the Trilogy TMI builder
  in-tree behind the config switch allows reverting `config/motifs.json` to
  fall back with no other code change.

## 18. Open decisions

- Duplicate notation: normalize Mellmann's `[b]`/`[.1]`/`.2.2` to our `~N`,
  or adopt brackets? (Recommend `~N` for uniformity with existing UI.)
- Keep Trilogy TMI as a **secondary** source purely to graft `†` dagger
  typography? (Recommend no — cosmetic, no informational gain.)
- Where the renumber map lives (a generated data file vs computed at build).
- Whether to expose `division1-3`/`section` in the API now or defer to the
  Classification-section work.
- Whether to keep a permanent `MYTHO_MOTIFS_DIR`-based A/B build in CI as a
  standing regression check, or tear the harness down after migration.
- Whether Phase 0 overlays (headings + renumber map) ship as committed
  generated data files or are recomputed at build time from a cached Mellmann
  copy.
