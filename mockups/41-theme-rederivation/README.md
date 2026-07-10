# 41 · Theme re-derivation (UMAP)

Instead of taking Berezkin's **13 hand-assigned theme groups** as given, this asks what themes
the catalogue proposes *by itself*: cluster the motifs **by meaning** (BGE-M3 embeddings), name
the natural clusters, sub-cluster them, and compare the two-level data structure against the
hand taxonomy.

## Pipeline

1. **Embeddings** — the Berezkin block of the cached BGE-M3 matrix (`outputs/motifs/raw/bge_m3.npy`).
   The embedded text is **name + definition** (`"{name}. {definition}"`), ~96 % English
   (mapsofmyths) with a ~4 % Russian tail; BGE-M3 is multilingual, so both share one space.
2. **UMAP** to 2-D (the scatter you look at) and to **10-D** for clustering. UMAP-10 beats PCA-64
   and the raw 1024-d space on **both** cluster purity (0.51 vs 0.48 vs 0.46) and agreement with
   the hand themes (ARI 0.12 vs 0.08 vs 0.07) — reducing first genuinely helps.
3. **Level-1** KMeans → **16** natural clusters, each hand-named (keyed to a signature motif so
   the label follows content, not the KMeans index).
4. **Level-2** KMeans inside each cluster → ~55 sub-categories, each **hand-named** (keyed to its
   signature motif). Click a cluster card to enter the level-2 view: the scatter recolours that
   cluster's points by sub-cluster and a panel lists the named sub-categories.
5. **Comparison** to the 13 hand themes — contingency, purity, adjusted Rand, and a per-theme
   verdict (how concentrated each theme is in one data cluster).

**Coverage & fitness.** KMeans is a hard partition, so all 3488 motifs are assigned — nothing is
left uncovered. The scheme in fact *increases* coverage over the hand taxonomy: the **141** motifs
Berezkin left un-grouped ("?") each receive a data-theme. A third scatter mode, **"по пригодности"**,
colours each motif by how loosely it sits in its cluster, with a **L1-centre ↔ L2-sub-centre**
toggle: flip it and the peripheral knots (rainbow, girl-from-fruit) go from red (far from the big
L1 centroid) to green (dead-centre of their own sub-theme). The KPI states it — **outliers > p98:
70 from L1 → 1 from L2**: the "2 % outliers" are not noise but *under-resolved* micro-themes that
level 2 already names. The **"хуже всего вписаны"** panel lists the loosest-at-L2 motifs; only the
single row flagged **"оба уровня"** (loose at both levels) is the genuine residue.

## What it shows

- **The celestial / cosmogonic / formulaic block is real.** Sun-Moon (88 % of the theme lands in
  one cluster), Stars (67 %), Cosmogony, and Names are **recovered**; and the data even carves out
  tiny *pure* islands the hand scheme buries inside bigger groups — **Formulae** (100 % pure),
  the **death-messenger** complex (100 %), the trickster **casting** ("who is the trickster",
  "who is the dupe") split cleanly from trickster *plots*.
- **The two catch-alls dissolve.** **Adventures** (concentration 0.20) and **Flora/fauna** have no
  natural cluster of their own; the data reorganises them into **narrative complexes** — magic-wife,
  ogre-escape, animal-fable, ogre-dupe, revenge, miraculous-birth — that cut straight **across** the
  Adventures/Tricks line. The low ARI (0.12) is the headline: content structure agrees with the hand
  taxonomy only partly, and precisely where the hand groups are coherent (the celestial axis).

Toggle the scatter between **theme** and **cluster** colouring; hover a point for its motif;
click a cluster card (or legend entry) to highlight its points.

## Honest limits

Embeddings are name+definition, so the clustering reflects **catalogue phrasing**, not the raw
tale texts; UMAP geometry depends on `n_neighbors` / `min_dist` (fixed at 15 / 0.1–0.0) and its
`random_state`; KMeans K1 = 16 is a choice (silhouette is uninformative at ~0.02, as usual for
1024-d text embeddings — cluster *purity* against the hand themes is the selector used here). This
is a **content**-derived taxonomy; it is deliberately blind to distribution/depth (mockups 17, 40).

## Run

```bash
pip install umap-learn                                 # build-time dependency
python mockups/41-theme-rederivation/build_data.py     # writes data.js (~330 KB, ~1 min: UMAP + numba JIT)
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/41-theme-rederivation/
```

`data.js` is git-ignored. Reads `outputs/motifs/berezkin.json` and the cached BGE-M3 matrix.
