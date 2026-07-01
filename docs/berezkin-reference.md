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
(`a1.html`, `k84.html`, …) add a short definition. The introduction page
([`intro.html`](http://areasofmyths.com/intro.html)) carries the licence and the
authoritative region-code key (§6).

**Licence.** The catalogue's data "can be freely used for non-commercial
purposes" under **CC BY-NC-SA 4.0**, with mandatory attribution to the source.
We attribute *Ю.Е. Березкин, Е.Н. Дувакин* and link the homepage; the catalogue
is "in perpetual progress", so citations should quote a motif's definition or
name alongside its code.

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
| `name` | motif name — **English** where available (§9), else the cleaned Russian name |
| `name_rus` | the Russian original name (only when English replaced it) |
| `definition` | short definition — **English** where available (§9), else the Russian one |
| `definition_rus` | the Russian original definition (only when English replaced it) |
| `areas` | sorted unique region codes (§6) |
| `see_also` | internal cross-references to other Berezkin motifs |
| `atu_refs` | ATU tale-type references parsed from the title |
| `page` | source detail-page filename (for the back-link) |

Index-level keys: `label, long_label, attribution, homepage, chapters, areas`
(the region legend).

---

## 9. English names & definitions (mapsofmyths.com)

The sister site **[mapsofmyths.com](http://mapsofmyths.com)** (same authors, same
motif ids, CC BY-NC-SA 4.0) carries an **English name and English definition** for
almost every motif. Its `/motifs_full` page lists them as Drupal nodes.

**Pipeline step.** `motifs.sources.mapsofmyths.refresh()` runs as part of
`mytho motifs`: it fetches the pages into the resumable raw cache
(`outputs/motifs/raw/mapsofmyths/`) and writes the parsed files next to the index
JSONs (`outputs/motifs/mapsofmyths_*.json`). **Neither the cache nor the parsed
files are committed** — only the code is. The step is **credential-gated** (HTTP
basic auth via `MYTHO_MOTIFS__MAPSOFMYTHS_USER` / `_PASS`); without credentials it
logs a warning and the catalogue is built without the enrichment. `mytho status`
reports the per-source enrichment counts. `scripts/fetch_mapsofmyths.py` is a thin
wrapper around the same step for a standalone refresh.

`mapsofmyths_en.json` is `{ID_UPPER: {name_eng, definition_eng}}` (~3,400 entries).
At build time `berezkin.py` matches by case-insensitive id (`A7B == a7b`) and
**prefers the English text**: it becomes the motif's `name` / `definition`, and the
Russian originals move to `name_rus` / `definition_rus` (shown as sub-titles on the
motif page). ~96 % of motifs get an English name, ~95 % an English definition;
motifs with no English match keep their Russian text.

### Node-level enrichment

The same step also scrapes every motif's `/node/N` page and the `/traditions_full`
list into two more files under `outputs/motifs/`, which `berezkin.py` attaches by
case-insensitive id:

- `mapsofmyths_nodes.json` → per motif:
  - `motif_type` / `motif_group` — the **2-level thematic taxonomy** (2 types → 13
    groups), a second axis distinct from the letter-chapters;
  - `tmi_refs` — **direct Thompson (TMI) motif ids** (~226 motifs); this is new — we
    had no direct Berezkin→TMI link, only an indirect ATU hop. On the motif page
    they become cross-index links into our TMI catalogue;
  - `atu_refs` — the ATU id from the node, **merged** with the ids already parsed
    from the Russian title (largely overlapping — used as corroboration);
  - `traditions` — the areal ids of every **tradition attesting the motif** (avg ~35,
    up to 555): the fine, tradition-level distribution behind the maps.
- `mapsofmyths_traditions.json` → the **1,046 traditions**, each with its English +
  Russian name, a **named 4-level areal hierarchy** (16 mega-regions → 59 regions →
  228 areas → 1,046 traditions, decoding each `areal_id` like `5.1.3.2`), and its
  **language family**. Stored index-level in `berezkin.json` as `traditions`.

The motif page renders the classification, the tradition distribution grouped by
macro-region (each region expandable to the named traditions), and the TMI links.
Still **not** ingested: the per-motif correlation (co-occurrence) network and the
distribution maps.

---

## 5. Parsing decisions

All in `berezkin.py`.

- **Entry split.** Layout is `CODE. Name. [see-also codes] .area.area.`. The
  areal list is introduced by a space-dot before the first number, which splits
  it off without eating the digits of a see-also code.
- **Areal sequence.** `_parse_area_seq` reads the dotted list into ordered
  `(index, parenthetical)` pairs: a `-` is an inclusive range; **parentheses
  mark a comparative entry** (the motif is *not* counted in the correlation for
  that area). Implausible numbers (a digit that leaked out of a name) above 150
  are dropped. Only the numeric codes are kept on the record (`areas`); names
  come from the published key, not from the page.
- **Area legend (the decoding).** Taken **verbatim from the published key** in
  `intro.html` ("Цифры соответствуют следующим регионам"), hard-coded as
  `_CANONICAL_AREAS` / `canonical_area_legend()` (§6). No inference: detail-page
  fetching now serves only the definitions.
- **ATU / see-also.** ATU clauses (`ATU 311, 312`) and bare tale-type refs
  (`804A`) are pulled from the title into `atu_refs`; uppercase-initial codes are
  internal `see_also`; leftover Thompson notation (`Th …`) is stripped.
- **Homoglyph repair.** The source occasionally types a latin letter inside a
  Cyrillic word (`Cупруг` for `Супруг`); a latin glyph adjacent to Cyrillic is
  swapped for its Cyrillic twin.

---

## 6. Areal region codes (the key)

The dotted numbers are Berezkin's **areal region codes**. The catalogue
[publishes the key in its introduction](http://areasofmyths.com/intro.html)
("Цифры соответствуют следующим регионам"); numbering **starts at 10** and runs
to **74**, and numbers **in parentheses** mark a motif *excluded* from the
correlation for that area.

We copy that key verbatim into `_CANONICAL_AREAS` (`berezkin.py`); it is stored
in `berezkin.json → areas` and served at `GET /api/motifs/berezkin/...`. **65
macro-areas, codes 10–74** (code 58, *Дельта Ориноко*, is defunct — folded into
59, *Гвиана* — but still tags older entries, so it is kept):

| codes | region group |
|---|---|
| 10–14 | Africa — SW, Bantu, West, Sudan–East, North |
| 15–17 | South / West Europe, Near East |
| 18–26 | Australia, Melanesia, Polynesia–Micronesia, Tibet/NE India, Burma–Indochina, South Asia, Malaysia–Indonesia, Taiwan–Philippines, China–Korea |
| 27–40 | Balkans, **Central Europe**, Caucasus–Asia Minor, Iran–Central Asia, North Europe, Volga–Perm, Turkestan, S. Siberia–Mongolia, W./E. Siberia, Amur–Sakhalin, Japan, NE Asia, Arctic |
| 41–53 | North America — Subarctic, NW Coast, Coast–Plateau, Midwest, Northeast, Plains, SE US, California, Great Basin, Greater SW, NW Mexico, Mesoamerica, Honduras–Panama |
| 54–74 | Antilles, Andes, Amazonia, Brazil, Chaco, Southern Cone |

(The full 10→74 list with Russian names is `_CANONICAL_AREAS` / `berezkin.json`.)

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
  below the official start-of-10 in the published key, so they have no name and
  show as the bare number — likely parse noise or a few anomalous entries.
- **Code 58 (*Дельта Ориноко*)** is officially defunct (folded into 59,
  *Гвиана*) yet still tags ~180 older entries; it is kept in the key so those
  motifs decode rather than show a bare number.
- The areal legend is the catalogue's own published key, copied verbatim; the
  raw codes are always retained in `areas` as well.
