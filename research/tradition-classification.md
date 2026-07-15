# Tradition classification for the full-text corpus — criteria and candidates

Working design note for the single top-level classification of mythological and religious
traditions ("sections"/`разделы`) of mythoscope. Supersedes the ad-hoc facet discussion; records
the criteria, the corpus-first principle, and the candidate schemes.

## Guiding principle — corpus-first, not index-first

The catalogue is **not** built on Berezkin's motif index. We assemble a **full-text corpus** of
actual mythological/religious texts, and the classification is driven by what that corpus contains.

Consequences:

- **`areal_path` is not the final criterion.** It is Berezkin's own areal grouping — useful as a
  provisional geographic scaffold, but not authoritative for our sections.
- **"From data" now means significant differences between the *texts themselves*** (content,
  language, genre), not motif-attestation counts. Where a data-driven boundary is needed, it comes
  from the corpus, not from the index.
- **Re-annotation is allowed.** If the corpus needs a different partition than any off-the-shelf
  grouping, we re-annotate the traditions accordingly. The scheme serves the corpus, not vice versa.
- **Start from obtainability.** The first constraint is *what full text can actually be acquired*
  (open license, machine-readable, at scale). See the companion sourcing survey.

## The four criteria for judging a classification

Every candidate scheme is evaluated on these four, which routinely **conflict** (the whole design
tension is trading them off):

1. **Geography** — does each section map to a compact, unambiguous region on the map? Clean spatial
   boundaries help navigation and the map view.
2. **Cultural commonality** — are the traditions inside a section genuinely kin (shared language
   family, religion, descent, society type), not merely neighbours?
3. **Expressiveness & clarity** — are the section names recognizable and intuitive to a reader? Is
   the count sensible (not too many, not too few)? No artificial merges or index-artifact sections.
4. **Volume of traditions & material** — are sections balanced by content: both the number of
   traditions and the **actual full-text volume**? No empty sections, no overloaded heaps.
   *Measured against the full-text corpus we assemble, not the Berezkin index.*

Known conflicts: geography vs volume (Europe is small in area but huge in text); cultural
commonality vs volume (the literate Old World is few traditions / vast text; the oral world is many
traditions / little text); expressiveness vs volume (balance-driven merges read oddly as sections).

## Candidate schemes

### A — Volume-balanced (14), renamed for clarity

Balanced by documentation volume; heavy blocks split, thin ones pooled. Renamed from the
balance-artifact labels to clearer regional names (same membership):

1. Southern & Western Europe
2. Slavic & Balkan Europe
3. Northern Europe (Nordic, Baltic, Finno-Ugric)
4. Near East & North Africa
5. Caucasus & Anatolia
6. South Asia
7. East Asia & Mainland Southeast Asia
8. Island Southeast Asia & Oceania
9. Sub-Saharan Africa
10. Siberia & Mongolia
11. Arctic & Northwest North America
12. Native North America (Plains, Woodlands, Southwest, California)
13. Mesoamerica & the Andes
14. Lowland South America

*Strong on criterion 4 (balanced by Berezkin motif volume, no empty/heap sections, deterministic
from `areal_path`). Weak on 2–3 in a few seams (East Asia lumped with mainland SE Asia; Caucasus a
peer section). But criterion 4 must be re-measured against the full-text corpus, where it looks very
different — see below.*

### B — Cultural-areal (14, updated)

Balanced by cultural/geographic coherence, independent of volume; Australia merged into Oceania,
Europe split geographically, East + Southeast Asia merged, no Caucasus section.

1. Southern & Western Europe
2. Northern & Eastern Europe
3. Near East
4. Iran & Central Asia
5. Siberia & Circumpolar
6. South Asia
7. East & Southeast Asia
8. Oceania & Australia
9. West & Central Africa
10. East & Southern Africa
11. Arctic & Northwest America
12. North America
13. Mesoamerica & Andes
14. Amazonia & Lowland South America

*Strong on 1–3 (recognizable, culturally coherent). Weak on 4 by volume (East Asia and the two
African halves are thin; the African split is not even derivable from `areal_path`).*

### C — Encyclopedic / text-weighted (~22)

The organization real encyclopedias use (Larousse, Мифы народов мира, Bonnefoy): split the literate
Old World finely (each great textual tradition its own section), pool the oral world. This is the
scheme the **full-text criterion** actually points to — see the volume analysis.

Old World literate: Egyptian · Mesopotamian · Levantine & Anatolian · Greek & Roman · Celtic ·
Germanic-Norse · Slavic · Baltic & Finno-Ugric · Iranian-Zoroastrian · Abrahamic · South Asian
(Hindu/Buddhist/Jain) · Chinese · Japanese & Korean · Southeast Asian · Central Asian & Siberian.
Oral pools: Sub-Saharan Africa · Oceania & Australia · Native North America · Mesoamerica & Andes ·
Lowland South America.

## Why the corpus changes criterion 4

By **full-text volume** (not motif counts), the world is radically concentrated: ~29 traditions with
real written corpora, ~90% of the text in South Asia (Hindu + Buddhist canon) and the Near East
(Talmud + Christian corpus), and the entire oral world (Siberia, the Arctic, Native North America,
Amazonia, much of Africa, Oceania, Australia) contributes **near-zero text**. Under this measure both
A and B collapse to 4+ empty sections and 2 mega-sections; only a text-weighted scheme like **C** —
which splits South Asia and the Near East and pools the oral world — is balanced. This is why the
classification must start from the assembled corpus, and why the final scheme will likely resemble C
more than A or B once obtainability is settled.

## Companion documents

- `research/mythology-encyclopedias-survey.md` — how the major reference works carve the world.
- `research/corpus-sourcing-survey.md` — what full text is actually obtainable (in progress).
