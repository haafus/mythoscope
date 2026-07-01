# Motif indexes — troubleshooting & known issues

Running log of cross-cutting problems in the motif subsystem: what's wrong, why,
where it bites, and the options for fixing it. Append new entries at the top.

---

## Four competing macro-area schemes

**Status:** open — needs a decision before touching `_berezkin_region`.

There are **four independent "macro-region" vocabularies** in play at once, none
of which agree with the others. Three of them are geographic and overlap in the
same UI; the fourth is a different axis entirely. This makes "region" ambiguous:
the same Berezkin motif page labels regions one way in the overview chart and
another way in its Traditions section.

### The four schemes

| # | Scheme | Buckets | Where it lives | Authored by | Used for |
|---|---|---|---|---|---|
| 1 | Berezkin broad regions | **11** | `_berezkin_region()` in `src/server/services/motifs.py` | us (ad-hoc) | Berezkin overview "Motifs by region" chart |
| 2 | TMI culture regions | **12** | `_REGION` in `src/motifs/sources/culture_dict.py` | us (ad-hoc) | TMI overview "Motifs by region" + per-motif "Attestations by culture" grouping |
| 3 | Berezkin areal hierarchy (major traditions) | **16** | `areal_path[0]` in `outputs/motifs/mapsofmyths_traditions.json` | Berezkin (authoritative) | Berezkin per-motif "Traditions" distribution grouping |
| 4 | Corpus tradition families | **12** | `config/traditions.json` | us (hand-authored) | Geography map + corpus grouping — **different dataset (our texts), not motifs** |

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

### Note

TMI (#2) is intrinsically its own scheme — it sits over Thompson's culture
labels, a different source with no areal codes — so it will never fully match a
Berezkin-derived vocabulary regardless of the choice above.
