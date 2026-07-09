# 33 · Alternative-tree test (roadmap M33)

Tests **alt-hypothesis #3** — "the descent signal is an artifact of the *wrong* (language)
tree." Re-runs the descent detector (chance-corrected Fitch phylo-signal, mockups 18 / 28) on a
**human genetic tree** instead of the language tree, and compares per-motif signal on the 2991
motifs (≥ 6 traditions) over the 972 traditions present on both trees.

## The genetic tree

A **curated consensus topology at continental resolution** — the uncontroversial
population-genetics backbone: Africa outgroup → out-of-Africa → **West Eurasian** (European,
Near-Eastern, South-Asian) vs **East Eurasian** (East-Asian, Siberian, Austronesian) with
**Native Americans nested inside East Eurasia** via Beringia and **Australo-Papuans** deep in the
East branch. Traditions are joined to a population by **geography** (Berezkin macro-area), *not*
by language — using language would be circular.

Why it is a real test, not a relabelling: the **language** tree unites families that cross
genetic/continental lines (Altaic runs Anatolia → Yakutia; Indo-European spans West-Eurasian +
South-Asian), while the **genetic** tree splits them by continent. So comparing signals asks
whether a motif's inheritance follows *language* or *genes / geography*.

## What it shows

- **corr(language, genetic) = 0.43; robustness = 89 %.** Of the **1019** motifs that are descent
  on the language tree, **905 (89 %)** stay descent on the genetic tree → the descent signal is
  **not** an artifact of the language tree. alt-#3 is largely refuted.
- **Three modes** (the scatter's quadrants):
  - **both (905)** — genes + language + area agree: the deepest, most robust inheritance
    (e.g. **B4** fished-earth, Austronesian, sig 0.61 / 0.62).
  - **language-only (114)** — follow language but not genes; dominated by exactly the
    **cross-continental families** — **Indo-European (68), Altaic (23)**. This is the signature of
    genuine *linguistic* transmission across genetic boundaries (e.g. **Cinderella K57**,
    0.49 / 0.31).
  - **genetic-only (1219)** — continentally clustered but language-crossing = areal-within-a-
    continent, which the coarse genetic (≈ continental) tree doubles as a detector for (e.g.
    **Jonah K8aa**, an African-substrate motif, 0.13 / 0.48).

## Honest limit

Continental resolution + geographic join means **genetic-only overlaps with "areal"**, and the
tree cannot resolve within-continent structure (North vs South Indian, Anatolian vs Central-Asian
Turk). A fine **SNP-based population tree** (HGDP / 1000G) is the full version and needs the actual
genetic data — future work. The tradition → population join built here is what **M36** (admixture
graph with back-migration edges) will extend.

## Run

```bash
python mockups/33-alt-tree/build_data.py   # writes data.js (~7 s)
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/33-alt-tree/
```

`data.js` is git-ignored. Reuses mockup 21's `area_of` and the same Fitch machinery as mockups
18 / 28.
