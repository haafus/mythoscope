# 29 · Content vs theme / depth (roadmap M29)

Crosses the BGE-M3 semantic embeddings (built in the morphology stage, cached in
`outputs/motifs/raw/bge_m3.npy`) with the two motif axes: does a motif's **content** predict
its **theme** (what it is about) and its **depth** (how old its distribution is)? The embedding
order is TMI · ATU · Berezkin, so the Berezkin block is the last `len(motifs)` rows —
alignment verified (A3 → sun/moon motifs, K25 → swan/crane/goose-wife, M182 → sticky-trap).

## What it shows

- **Content is theme, but not depth.** Nearest-by-meaning motifs share the theme group **58%**
  of the time vs **20%** by chance (×2.9) — the embeddings are validated and content is almost
  exactly the theme axis. But content barely predicts distribution: `content → breadth`
  correlation **0.28**, `content → prevalence` **0.18**. Meaning tells you *what* a motif is
  about, not *how old* it is — a direct confirmation that **`stratum` must be computed from
  distribution, not read off content.**
- **Content-redundancy is not banality (honest negative).** Mean cosine to nearest neighbours
  flags **near-duplicate motif families** (the M29* trickster-is-a-X variants), not
  reinvention-proneness; its correlation with mockup 20's short-definition proxy is ≈ **0**.
  So embedding density measures catalogue granularity, not homoplasy — a real content-based
  banality would need a different construction (distance to a "generic" centroid), not
  neighbour density.

## Takeaway

The independent content signal corroborates the program's split: theme is a content/given axis
(embeddings recover it), stratum is a distributional/computed axis (embeddings can't see it).
The attempt to get a *content* banality for free did not pan out — recorded as a negative
result rather than a claimed win.

## Run

```bash
python mockups/29-content-stratum/build_data.py   # writes data.js (<1 s)
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/29-content-stratum/
```

`data.js` is git-ignored. Reads `outputs/motifs/berezkin.json` + the cached `bge_m3.npy`.
