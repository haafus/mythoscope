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

## What this actually tests (read this first)

At **continental resolution the genetic tree is built from `area`** (the tradition→population join
is geographic), so **genetic ≈ geography**, and both correlate with language family (M32:
V(area,family)=0.73). So this mockup is **not an independent genetic axis** — it is, honestly, the
**language-vs-geography** contrast (Method B vs Method A) with a continental *nesting* added on top
of flat area. Genuinely genetic information *beyond geography* only appears at fine resolution where
ancestry decouples from geography (admixture) — a **SNP tree (HGDP/1000G), future work**.

Because the three classifications are correlated, **the modes are separable only where they
disagree** (the off-diagonal). The correlated core (family = area) is *confounded and inseparable*
— that is the `both` bucket, and it is exactly the deep-vs-diffuse residual (A3 vs K25, mockup 27).
So the 89 % below is **largely tautological** (where language = area, both trees agree), **not**
an independent validation; the real evidence is in the two disagreement buckets.

## What it shows

- **corr(language, genetic) = 0.43.** The leverage is in the **disagreement**, not the agreement:
  - **language-only (114)** — a motif that tracks a family **across** areas is language-descent
    that geography *cannot* produce. That this bucket is non-empty and is exactly the
    cross-continental families (**Indo-European 68, Altaic 23**) is the real result: **linguistic
    transmission is real and not reducible to area.**
  - **genetic-only (1219)** — a motif that tracks an **area across** families is areal diffusion.
  - **both (905)** — family = area; descent and diffusion are **confounded**, not confirmed.
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

Restated from the top: continental resolution + geographic join means the "genetic" tree is
**area with a phylogenetic nesting**, so `genetic-only` overlaps with `areal` and the tree cannot
resolve within-continent structure (North vs South Indian, Anatolian vs Central-Asian Turk). The
truly independent third axis is what would decouple from *both* area and family — **fine SNP
genetics** (ancestry ≠ geography under admixture) and the **connectivity corridors (M34/M35)**,
which are neither flat area nor family. So M33 is strongest as "language-descent is real and
area-independent" and weakest as "genetics validates depth." The tradition → population join built
here is what **M36** (admixture graph with back-migration edges) will extend.

## Run

```bash
python mockups/33-alt-tree/build_data.py   # writes data.js (~7 s)
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/33-alt-tree/
```

`data.js` is git-ignored. Reuses mockup 21's `area_of` and the same Fitch machinery as mockups
18 / 28.
