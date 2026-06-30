# The Berezkin Areal Motif Catalogue in MythoScope

How the Berezkin & Duvakin catalogue (*Тематическая классификация и
распределение фольклорно-мифологических мотивов по ареалам*) is sourced, parsed,
and decoded in this project. Companion file: [`tmi-reference.md`](tmi-reference.md).

---

## 1. Source

Scraped from **[areasofmyths.com](http://areasofmyths.com)** (windows-1251). The
site is a frameset; the whole inventory lives in one navigation page,
`index-left.html` — each `<li>` is a motif (code, name, optional internal
see-also codes, and a trailing list of areal indices). Per-motif detail pages
(`a1.html`, `k84.html`, …) add a short definition and the ordered macro-area
headers used to decode the area legend (§6).

Parsing is in `src/motifs/sources/berezkin.py`; fetching is split from parsing so
it can be unit-tested on static fixtures.

---

## 2. Structure

- **Codes** — a latin letter + a digit + optional sub-suffixes (`A1`, `A2a1`,
  `B12`). The **leading letter is the chapter**; finer structure (`A2 → A2A →
  A2a1`) is only latent in the code string — the source is a flat list, with no
  parsed parent/level (unlike TMI). See `tmi-reference.md` §2 for the contrast.
- **Chapters** — 14 thematic sections `A`–`N`, named in Russian (all-caps in the
  source; sentence-cased at serve time, Roman numerals preserved):

  | | | | |
  |---|---|---|---|
  | A Солнце и луна | D Огонь и смех | H Потерянный рай | L Приключения II: чудовища |
  | B Происхождение особенностей мира | E Происхождение людей и культуры | I Сверхъестественные объекты | M Приключения III: проделки |
  | C Катастрофы | F Пол и секс | J Герои-мстители: америндейский цикл | N Сказочные и эпические формулы |
  | | G Плодородие, земледелие | K Приключения I: деяния героев | |

- **Areal indices** — the dotted numbers after a motif (`… .19.21.`) are
  **region codes**: the geographic areas where the motif is attested (§6). The
  catalogue's primary axis is geography, not a motif hierarchy.

---

## 3. Composition

| | |
|---|---|
| Motifs | 3,488 |
| Chapters | 14 (`A`–`N`) |
| With a definition | 3,447 |
| With areal indices | 3,458 |
| With internal see-also refs | 184 |
| With ATU cross-references | 485 |
| Decoded macro-areas | 65 (codes 10–74) |

---

## 4. Record fields

Each stored motif (`outputs/motifs/berezkin.json → motifs[]`):

| field | meaning |
|---|---|
| `id` | motif code (`B12`) |
| `chapter` | leading letter |
| `name` | motif name (Russian), cleaned of codes / refs / Thompson notation |
| `definition` | short definition from the detail page |
| `areas` | sorted unique region codes (§6) |
| `see_also` | internal cross-references to other Berezkin motifs |
| `atu_refs` | ATU tale-type references parsed from the title |
| `page` | source detail-page filename (for the back-link) |

Index-level keys: `label, long_label, attribution, homepage, chapters, areas`
(the region legend).

---

## 5. Parsing decisions

All in `berezkin.py`.

- **Entry split.** Layout is `CODE. Name. [see-also codes] .area.area.`. The
  areal list is introduced by a space-dot before the first number, which splits
  it off without eating the digits of a see-also code.
- **Areal sequence.** `_parse_area_seq` reads the dotted list into ordered
  `(index, parenthetical)` pairs: a `-` is an inclusive range; **parentheses
  mark a comparative entry** (the motif is *not* counted in the correlation for
  that area) and are flagged so they can be excluded. Implausible numbers (a
  digit that leaked out of a name) above 150 are dropped.
- **Area legend (the decoding).** In a clean detail page the bold macro-area
  headers appear in the same ascending order as the motif's numeric area list,
  so for a motif whose count of non-parenthetical indices equals its count of
  non-comparative headers, index *i* aligns 1:1 with header *i*. Voting these
  alignments across the whole catalogue, and keeping a name only when ≥2 motifs
  agree, yields the global `index → macro-area` legend (§6).
- **ATU / see-also.** ATU clauses (`ATU 311, 312`) and bare tale-type refs
  (`804A`) are pulled from the title into `atu_refs`; uppercase-initial codes are
  internal `see_also`; leftover Thompson notation (`Th …`) is stripped.
- **Homoglyph repair.** The source occasionally types a latin letter inside a
  Cyrillic word (`Cупруг` for `Супруг`); a latin glyph adjacent to Cyrillic is
  swapped for its Cyrillic twin.

---

## 6. Areal region codes (the key)

The dotted numbers are Berezkin's **areal region codes**. Per the official
intro, numbering **starts at 10**, and numbers **in parentheses** mark a motif
*excluded* from the correlation for that area.

No clean canonical "number → name" table is published on the reachable pages
(the numbering is embedded in the catalogue's correlation tables and in the maps
at [mapsofmyths.com](http://mapsofmyths.com)). So the legend here is **decoded
empirically** from the site's own detail-page headers (§5) — **65 macro-areas,
codes 10–74**, stored in `berezkin.json → areas` and served at
`GET /api/motifs/berezkin/...`:

| codes | region group |
|---|---|
| 10–14 | Africa — SW, Bantu, West, Sudan–East, North |
| 15–17 | South / West Europe, Near East |
| 18–26 | Australia, Melanesia, Micronesia–Polynesia, Tibet/NE India, Burma–Indochina, South Asia, Malaysia–Indonesia, Taiwan–Philippines, China–Korea |
| 27–40 | Balkans, Caucasus–Asia Minor, Iran–Central Asia, North Europe, Volga–Perm, Turkestan, S. Siberia–Mongolia, W./E. Siberia, Amur–Sakhalin, Japan, NE Asia, Arctic |
| 41–53 | North America — Subarctic, NW Coast, Coast–Plateau, Northeast, Plains, SE US, California, Great Basin, Greater SW, NW Mexico, Mesoamerica, Honduras–Panama |
| 54–74 | Caribbean, Andes, Amazonia, Brazil, Chaco, Southern Cone |

(The full 10→74 list with Russian names is in `berezkin.json`.)

---

## 7. Cross-walks

Geography is the catalogue's own axis, but motif **equivalence** runs through
ATU: `berezkin → atu` (from `atu_refs`, 485 motifs) and `atu → tmi`. A Berezkin
motif page shows its ATU tale types and, through them, the Thompson motifs.

A direct geographic alignment of **Berezkin areas ↔ TMI cultures** (via a shared
region taxonomy) is possible but not built — it would be a coarse region-level
overlay, not motif-to-motif links.

---

## 8. Known limitations

- **Codes 1–9.** Used by ~15 motifs as the leading index (`K84 .1.11.13…`) but
  below the official start-of-10. Header-voting could not decode them and their
  alignment is ambiguous — likely parse noise or a few anomalous entries; no
  online key was found to resolve them.
- **Voted-legend drift.** A few adjacent codes share a decoded name (`27/28
  Балканы`, `43/44 Побережье–Плато`, `58/59 Гвиана`) — sub-area splits or
  off-by-one voting drift; would need manual checking against the maps.
- **Decoding ≈ 65 of the used codes**; a handful covered by too few clean
  alignments keep an empty name but are still counted.
- The areal legend is an inference from the source, not a published canonical
  table; the raw codes are always retained in `areas`.
