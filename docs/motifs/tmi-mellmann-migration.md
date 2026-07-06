# Migration plan: TMI source Trilogy → Mellmann

Status: **proposed, not implemented.** This document is the plan only.

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

## 3. Source facts

| | Trilogy TMI (current) | Mellmann (target) |
|---|---|---|
| URL | `raw.githubusercontent.com/j-hagedorn/trilogy/master/data/tmi.csv` | `raw.githubusercontent.com/KatjaMellmann/TMI_as_CSV/main/tmi.csv` |
| license | CC-BY-SA-4.0 | **CC-BY-4.0** |
| rows / codes | 46 230 / 46 222 | 46 302 / 46 237 (incl. 60 blank ghost rows) |
| columns | `id, chapter_name, motif_name, notes, level, level_0..level_6, chapter_id` | `code, [sorting field], 1st ed., chapter, division1, division2, division3, section ("tens"), MOTIF, bibliographies` |
| encoding | UTF-8 | UTF-8, `,` sep, `"` quote |

Note the licence change (SA → plain BY): update attribution text; BY-4.0 is
strictly more permissive, no downstream-share-alike obligation.

## 4. Field mapping

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

## 5. Structural changes to the pipeline

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

## 6. Cross-walk reconciliation (the real risk area)

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

## 7. Capabilities unlocked (follow-on, not required for parity)

- A real **Classification / hierarchy** section for TMI in the UI, driven by
  `division1-3` + `section` (the long-discussed missing heading layer).
- **First-edition provenance** surfaced per motif; "added in revised edition"
  filter.
- Cleaner **definition** field for embeddings/semantic-parallels (already
  separated at source → less parser noise).

## 8. Migration steps (ordered)

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
8. Update docs: `motif-index-data-sources.md`, `tmi-reference.md` (hierarchy
   + `.0` sections now obsolete), `cross-walk.md`; add a `1st ed.` note.
9. Bump asset versions if the motif API shape changes (new fields) — UI,
   `page-motifs.js`, `app.css` `?v=` query.
10. Tests: update fixtures/expected counts; add tests for the renumber map,
    ghost-row harvesting, malformed-split repair, dup normalization.

## 9. Validation checklist (compare pre/post)

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

## 10. Risks & rollback

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

## 11. Open decisions

- Duplicate notation: normalize Mellmann's `[b]`/`[.1]`/`.2.2` to our `~N`,
  or adopt brackets? (Recommend `~N` for uniformity with existing UI.)
- Keep Trilogy TMI as a **secondary** source purely to graft `†` dagger
  typography? (Recommend no — cosmetic, no informational gain.)
- Where the renumber map lives (a generated data file vs computed at build).
- Whether to expose `division1-3`/`section` in the API now or defer to the
  Classification-section work.
