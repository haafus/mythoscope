---
title: "The Berezkin Areal Motif Catalogue"
description: "A rare English-language reference to Yuri Berezkin and Evgeny Duvakin's areal catalogue of folklore-mythological motifs — its structure, region codes, provenance, and integration into Mythoscope."
url: /indexes/berezkin
tier: B
---

# The Berezkin Areal Motif Catalogue

The **Berezkin & Duvakin catalogue** — *Тематическая классификация и
распределение фольклорно-мифологических мотивов по ареалам* ("Thematic
classification and areal distribution of folklore-mythological motifs") — is a
catalogue of narrative motifs organized above all by **geography**: for each
motif it records the world regions where the motif is attested. Compiled by Yuri
E. Berezkin and Evgeny N. Duvakin, it is the principal instrument for studying
the areal distribution of myth, and its cross-continental coverage — especially
of Siberian, Arctic, and New World traditions — reaches material the older
Western indexes barely distinguish.

The catalogue is primarily documented in Russian. This page is offered as an
English-language reference to its structure and codes, and to how Mythoscope
sources and decodes it. See also the [Thompson Motif-Index](tmi.md), the
[Aarne–Thompson–Uther index](atu.md), and [the crosswalk](../crosswalk.md)
linking all three.

---

## 1. Structure

Where TMI codes encode a full place-value hierarchy, the Berezkin catalogue is
organized on a different primary axis — geography — with a flat motif list:

- **Codes** — a latin letter, a digit, and optional sub-suffixes (`A1`, `A2a1`,
  `B12`). The leading letter is the chapter; any finer structure is only latent
  in the code string, since the source is a flat list with no parsed
  parent/level.
- **Chapters** — 14 thematic sections `A`–`N`, named in Russian. They run from
  celestial and cosmogonic themes through the origin of people and culture,
  fertility, the supernatural, and heroic-adventure cycles, to tale and epic
  formulae:

  | | | | |
  |---|---|---|---|
  | A Sun and moon | D Fire and laughter | H Lost paradise | L Adventures II: monsters |
  | B Origin of features of the world | E Origin of people and culture | I Supernatural objects | M Adventures III: tricks |
  | C Catastrophes | F Sex and gender | J Avenger heroes: Amerindian cycle | N Tale and epic formulae |
  | | G Fertility, agriculture | K Adventures I: deeds of heroes | |

- **Areal indices** — the dotted numbers following a motif are **region codes**:
  the geographic areas where it is attested (§4). Geography, not a motif
  hierarchy, is the catalogue's organizing principle.

---

## 2. Composition

| | |
|---|---|
| Motifs | 3,488 |
| Chapters | 14 (`A`–`N`) |
| With a definition | 3,447 |
| With areal indices | 3,458 |
| With internal see-also references | ~286 |
| With ATU cross-references | 485 |
| Decoded macro-areas | 65 (codes 10–74) |

---

## 3. What a motif record holds

Each stored motif carries its code and chapter; its **name** and short
**definition** (in English where available, §5, otherwise the original Russian,
with the Russian original retained alongside); its sorted **areal region codes**;
its internal **see-also** cross-references to other Berezkin motifs (read from
the definition text, kept only where they resolve); and its **ATU references**
parsed from the title.

---

## 4. Areal region codes

The dotted numbers are Berezkin's **areal region codes**, and their key is
published in the catalogue's own introduction. The numbering **starts at 10** and
runs to **74**, and a number in parentheses marks a motif *excluded* from the
correlation for that area. Mythoscope copies the key verbatim — **65 macro-areas,
codes 10–74** — and stores it as the catalogue's region legend:

| codes | region group |
|---|---|
| 10–14 | Africa — SW, Bantu, West, Sudan–East, North |
| 15–17 | South / West Europe, Near East |
| 18–26 | Australia, Melanesia, Polynesia–Micronesia, Tibet/NE India, Burma–Indochina, South Asia, Malaysia–Indonesia, Taiwan–Philippines, China–Korea |
| 27–40 | Balkans, Central Europe, Caucasus–Asia Minor, Iran–Central Asia, North Europe, Volga–Perm, Turkestan, S. Siberia–Mongolia, W./E. Siberia, Amur–Sakhalin, Japan, NE Asia, Arctic |
| 41–53 | North America — Subarctic, NW Coast, Coast–Plateau, Midwest, Northeast, Plains, SE US, California, Great Basin, Greater SW, NW Mexico, Mesoamerica, Honduras–Panama |
| 54–74 | Antilles, Andes, Amazonia, Brazil, Chaco, Southern Cone |

Code 58 (*Orinoco Delta*) is officially defunct — folded into 59 (*Guiana*) — but
is kept in the key because it still tags older entries, which would otherwise
decode to a bare number.

---

## 5. Provenance and English enrichment

The catalogue is scraped from **[areasofmyths.com](http://areasofmyths.com)**,
whose single navigation page holds the whole inventory (each entry giving a
motif's code, name, optional Thompson-id equivalences, and areal indices), with
per-motif detail pages supplying a short definition. The introduction page
carries the licence and the authoritative region-code key.

**Licence.** The catalogue's data may be freely used for non-commercial purposes
under **CC BY-NC-SA 4.0**, with mandatory attribution to the source. Mythoscope
attributes *Yu. E. Berezkin and E. N. Duvakin* and links the homepage. Because
the catalogue is a perpetual work in progress, a citation should quote a motif's
name or definition alongside its code.

**English text.** The sister site **[mapsofmyths.com](http://mapsofmyths.com)**
(same authors, same motif ids, same licence) carries an English name and
definition for almost every motif. Mythoscope matches these by id and prefers the
English text, moving the Russian original to a sub-title: about **96% of motifs
gain an English name and 95% an English definition**, with unmatched motifs
keeping their Russian text.

**Node-level enrichment.** The same source also supplies, per motif, a two-level
thematic taxonomy (a second axis distinct from the letter-chapters); **direct
Thompson (TMI) motif ids** (~226 motifs) — a direct Berezkin→TMI link that no
other route provides; corroborating ATU references; and the fine,
tradition-level attestation behind the areal maps. A separate table decodes the
**1,046 traditions**, each with its English and Russian name, a named four-level
areal hierarchy (16 mega-regions → 59 regions → 228 areas → 1,046 traditions),
and its language family. This enrichment is credential-gated and best-effort:
without it, the catalogue is built from the base source and the coarser areal
codes alone.

---

## 6. How Mythoscope integrates Berezkin

The catalogue is browsable by chapter and region, and each motif page renders its
definition, its thematic classification, its tradition distribution grouped and
expandable by macro-region, and its cross-index links. An overview dashboard
aggregates the catalogue into geographic, thematic, and diagnostic charts, with
the **tradition** as its organizing carrier where the enrichment is available and
the coarser **areal code** as a fallback.

Motif **equivalence** runs two ways. The **direct** Berezkin ↔ TMI link uses the
curated Thompson ids that mapsofmyths attaches to each motif — the exact,
hand-curated concordance, shown first on the motif page. The **via-ATU** link
reaches TMI through the tale-type references parsed from each title (~485
motifs): far more pairs are reachable this way, but a shared tale type is not the
same as a shared motif, so the two routes are kept distinct. A direct
**geographic** alignment of Berezkin areas to TMI cultures is deliberately not
built, because the catalogues use non-aligned macro-region schemes. The full
cross-catalogue machinery is documented in [the crosswalk](../crosswalk.md).

The catalogue's own **bibliography** (roughly 9,700 works) is linked to the areal
distribution, resolving the author-year citations in each motif's attestations
against it and attributing every citation to its macro-area.

---

## 7. Known limitations

- **Codes 1–9.** About 15 motifs use a leading index below the official
  start-of-10 in the published key, so they carry no region name and show as the
  bare number — likely parse noise or a few anomalous entries.
- **Code 58** (*Orinoco Delta*) is officially defunct but still tags roughly 180
  older entries; it is kept in the key so those motifs decode.
- The areal legend is the catalogue's own published key, copied verbatim, and the
  raw codes are always retained alongside the decoded regions.
