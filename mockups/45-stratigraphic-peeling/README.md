# 45 · Stratigraphic peeling

An interactive realisation of [`stratigraphic-peeling.md`](../../docs/proposals/stratigraphic-peeling.md):
**recursive, coverage-corrected peeling** of the Berezkin attestation matrix into nested **layers**, shown
by layer, geography and motif composition — with a **dating proxy**, **bootstrap stability**, and a parallel
**soft-factor (NMF)** view.

## The idea

Let the statistics (not a priori Laurasia/Gondwana labels) define the top split; each large block's shared
**core** is a candidate layer; peel it and recurse. **Coverage correction is step 0** — without it the first
seam is just the most-catalogued zone (Western Europe). With it, the top seam is **New World ↔ Old World**,
and recursion recovers a recognisable genetic-geographic stratigraphy.

The honest caveat is built into the page: mythological similarity is a **clinal** geographic gradient, not a
hierarchy of crisp modules (silhouettes are weak at *every* level, including the root; a permutation null
floors at significance everywhere). So the tree is a **discretisation of a continuum**, not discrete strata —
which is why the **soft factors** are shown alongside as the mathematically honest layer model (a tradition
loads on several at once).

## What it shows

- **Map** — all 948 traditions (≥15 motifs each) placed by coordinate, coloured by their leaf layer
  (hard mode) or dominant soft factor (factor mode). Selecting a layer highlights its traditions.
- **Layer tree** — the nested peel: `Old World → {Eurasian märchen → SW&C-Asia/India, Tibet/SE-Asia},
  Sub-Saharan Africa` and `New World → {Beringian bridge → N-American, Siberia–Mongolia}, American cosmology
  → {Amazonian, Mesoamerican/Andean}`.
- **Detail panel** — for the selected layer: continent + macro-area composition, the **theme-group profile**
  of its core, the **core motifs** (top by lift, with theme group and cross-continental breadth), a
  breadth-based **dating proxy** (broad + disjunct = deep — the root's core is the pan-global celestial
  substrate; peeled leaves are regional/shallow), and **bootstrap stability** (how reproducibly the block
  recovers under resampling — 0.54–0.83 here; the Beringian bridge is the least stable, as expected).
- **Soft factors — two models, toggled** (the honest layer model for clinal data). Both factor the
  coverage-corrected matrix into six **overlapping** latent layers, each **dated** by the M17 disjunction
  depth score of its motifs (a **dated stratigraphy**, deep→shallow). The two differ in one instructive way:
  - **NMF** (Euclidean) — isolates a **clean Austronesian/Oceanic layer** (F3: Eurasia 77 · Oceania 36),
    but is not corrected for cataloguing effort by construction.
  - **M38 Poisson** — `P[t,m] ~ Poisson(a(t)·(WH)[t,m])` with the attestation-intensity offset `a(t)`,
    **coverage-corrected by construction**; it **distributes** Oceania across factors (F1 + F3) rather than
    isolating it. Switching models shows exactly how effort-correction reshapes the layers.

  The M38 Poisson stratigraphy (soft layers where the hard tree could not build them — but a *re-presentation*
  of M17 depth + existing factor components, not a new result; see the proposal's Conclusions):

  | Layer | depth | geography | core motifs |
  |---|--:|---|---|
  | F1 | 81 | Americas | Sun & Moon, Theft of fire, Magic wife, Stars-are-people |
  | F2 | 72 | Americas + Eurasia | Earth-grows-big, Primeval waters, thunderbirds |
  | F3 | 63 | Eurasia + Africa | Magic wife, primeval sky, trickster-hare |
  | F4 | 62 | Eurasia | Man-in-the-Moon, Cosmic hunt, lunar-disc figure |
  | F5 | 33 | Eurasia + Africa | trickster-fox, external soul, nestlings |
  | F6 | 30 | Eurasia + Africa | dragon-slayer, kind-and-unkind, personified Death |

  Deep layers are cosmogonic/celestial (+ New-World-endemic); shallow layers are the young Eurasian/African
  **märchen** (ATU dragon-slayer, kind-and-unkind). Each hard leaf is matched to its dominant factor so the
  two views cross-read.

## Data

`build_data.py` builds the binary motif × tradition matrix from `outputs/motifs/berezkin.json`,
coverage-corrects it (per-tradition L1 normalisation + idf), peels it with Ward + outlier-routing to depth 3,
computes each node's core / themes / dating proxy / bootstrap stability, fits a `k=6` NMF for the soft
factors, and resolves coordinates via the shared `berezkin_coords()` (mockups/`_geo`). Deterministic; writes
`data.js`.

## Run

```bash
python mockups/45-stratigraphic-peeling/build_data.py     # writes data.js
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/45-stratigraphic-peeling/
```

## Two spaces — Geography and Worldview (three toggled tabs)

The same recursive peel runs in **two kinds of space**, toggled and grouped in the toolbar:

- **Geography** (motif-attestation, the modes above) — recovers areal structure, but is **clinal**
  (isolation-by-distance; top-split silhouette ≈ 0.03), so its layers discretise a gradient.
- **Worldview** — clusters traditions by *what kind of stories* they tell (CLR genre profile). Shown in
  **two independent derivations** as separate tabs, to check the finding isn't an artefact of one labelling:
  - **Theme (13)** — Berezkin's **13 etiological theme-groups** (the mockup 16 / 23 axis). Top split is a
    young **märchen/trickster** block (cosmology-share A ≈ 28 %, M17 depth ≈ 6) vs a deep **cosmology-rich**
    block (A ≈ 58 %, depth ≈ 53–87).
  - **Narrative (16)** — the **data-driven 16-dim narrative-form** clusters from mockup 41 (BGE-M3
    embeddings of motif name+definition → KMeans; *no* Berezkin theme labels). A fully bottom-up axis; its
    columns are narrative forms (Magic wife, Magic flight, Cosmogony, Sun & Moon, …). It recovers the **same
    young-tale → deep-cosmogony gradient** the theme axis does.

  Both worldview peels are far more **modular** than geography (top-split silhouette ≈ 0.16, up to 0.45
  deeper) and both **cross continents** — on the map the worldview colours are intermixed across regions,
  where the geography colours cluster by region. Each worldview layer carries its cosmology-share, M17 depth,
  genre profile and core motifs.

**The finding:** the two kinds of axis differ in *topology* — **geography is a continuum, worldview has
discrete layers** — so a worldview space is the one where a recursive *dated* stratigraphy actually finds
strata (young märchen → deep cosmology) rather than discretising a gradient. That both the hand-labelled
(13-dim) and the bottom-up embedding (16-dim) derivations recover it is the robustness check.

### Which worldview tab worked better — confirmatory (13) vs exploratory (16)

Measured head-to-head over the two 8-leaf partitions:

| | Theme (13) | Narrative (16) |
|---|--:|--:|
| Global 8-leaf silhouette | +0.059 | +0.065 |
| Split silhouette, top / mean | 0.139 / 0.166 | 0.145 / **0.196** |
| Top-split cosmology-share gap | **0.30** | 0.19 |
| Top-split M17 gap | **47** | 28 |
| Leaf M17 range (depth ladder) | **82** (to M17 87) | 74 |
| r(leaf a-share, leaf M17) | **+0.88** | +0.77 |
| Agreement of the two trees | ARI **0.06** · V 0.17 | — |

- **Theme (13) — better *confirmatory* ladder:** sharpest young/deep cut, widest monotone depth range
  (down to the anthropogonic *primeval-tree* leaf at M17 = 87), tightest cosmology↔depth coupling. But it
  *wins on the axis it was designed for* (Berezkin's themes = the cosmology-vs-tale distinction), so it's
  partly circular.
- **Narrative (16) — better *exploratory* stratigraphy:** steadier modularity at depth, more balanced
  leaves, and it surfaces structure the theme axis can't represent — off-diagonal leaves (*Sun & Moon myths*:
  a-share 0.33 yet M17 = 57) and a **form-based trickster/dupe stratum** crossing the New/Old-World line.
- **The real result is their agreement on the coarse polarity at ARI = 0.06** — a bottom-up axis with *no*
  cosmology labels reproduces the same young→deep top split as the hand-labelled one, so the polarity is a
  property of the data, not of Berezkin's design. Complementary, not redundant.

## Agreement with Berezkin's own partition

The hard-layer map is the only prototype that shows a single coverage-corrected **nested** areal partition
of all ~950 traditions on one map (mockup 15 = flat biclusters; 16 / 43 = k-means theme clusters). Measured
against Berezkin's 16 macro-areas it is a **consistent coarsening**: V = 0.68, completeness = 0.81; the top
New/Old-World split matches his 3-way megaset at ARI = 0.73. Purest leaves — Sub-Saharan Africa 98%,
Mesoamerica/Andes 98%, N-America 73%, Amazonia 76%. Two principled departures: the "Eurasian märchen" leaf
merges his Europe + Near East + Central Asia into one belt, and the "Siberia" leaf is a **Beringian bridge**
crossing his Old/New-World line. A distinctive, faithful *visualisation* of the known areal structure — not
a new scientific finding (see the proposal's Conclusions).

## Notes / honest limits

- Coverage is controlled by L1+idf here, **not** the full bias weights (mockup 24) — the qualitative result
  (effort artefact gone, Americas the distinct pole) is stable, but production dating should use M24 + M17.
- The dating is a **breadth proxy**, not a calibrated age; the stability is the internal check, clade
  correspondence is the external one still to wire in.
- Depth is a **discretisation choice** (fixed at 3), not a discovered bottom — there is none, because the
  structure is clinal. Treat the tree as a *naming / discovery* tool; the soft factors are the layer model to
  date and count.
