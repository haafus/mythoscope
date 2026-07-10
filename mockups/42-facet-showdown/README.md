# 42 · Facet showdown — 13 hand themes vs the narrative facet

Empirical head-to-head: is the data-driven **narrative** classification (16 clusters / 61
sub-themes, from mockup 41) a better **tradition facet** than Berezkin's **13 hand themes**?
Two established metrics on one working set (910 traditions with ≥ 15 motifs).

Faithful replication: the hand-theme ΔR² comes out at **0.125** — exactly mockup 32's published
value — so the comparison is on equal footing.

## Test A — facet adequacy (mockup 32's metric)

Predict pairwise tradition motif-set **Jaccard** from `{area, family, subsistence}` ± a theme
facet; ΔR² = the variance *only* that facet adds.

| facet | ΔR² (unique) | residual (1 − full R²) |
|---|---|---|
| 13 hand themes | 0.125 | 0.636 |
| 16 narrative clusters | **0.191** | **0.570** |
| 61 narrative sub-themes | **0.321** | **0.440** |

- The narrative facet **shrinks mockup 32's 64 % residual** to 57 % (16) / 44 % (61).
- **Subsumption:** with both facets in the model, the hand theme's unique Δ collapses to **0.003**
  (nearly redundant) while the narrative facet keeps **0.069** on top of theme. The narrative facet
  almost entirely **subsumes** the hand-theme facet as a tradition descriptor; not the reverse.

## Test B — areal signal (mockup 23's metric)

Theme × area over motif attestations. **Mixed:**

| facet | Cramér's V | mean top-area share |
|---|---|---|
| 13 hand themes | **0.125** | 0.264 |
| 16 narrative clusters | 0.102 | 0.288 |
| 61 narrative sub-themes | **0.142** | 0.313 |

By Cramér's V the **16 clusters dilute** the areal signal (the hand scheme carries it through the
etiological celestial themes; the big märchen clusters are pan-Eurasian). It recovers and beats the
old scheme **only at the 61-sub level**. By top-area concentration both new levels are sharper.

## Verdict

As a **tradition descriptor** (A) the narrative facet clearly wins and nearly replaces the theme
facet. As an **areal marker** (B) it only pays off at fine granularity; the coarse 16 clusters are
slightly worse than the hand themes. **Recommendation:** *add* the narrative facet (it earns its
keep in mockup 32) but *keep* the 13 etiological themes (they carry the areal signal the coarse
narrative clusters dilute). The two schemes are orthogonal — "how the tale is built" vs "what the
myth explains."

## Run

```bash
python mockups/42-facet-showdown/build_data.py   # writes data.js (~1 s)
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/42-facet-showdown/
```

`data.js` is git-ignored. Reads `outputs/motifs/berezkin.json`, mockup 41's committed
`narrative_taxonomy.json`, mockup 21's `area_of`/`family_of`, and mockup 22's subsistence join.
