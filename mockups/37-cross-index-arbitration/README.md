# 37 · Cross-index arbitration (roadmap M37)

Uses the **BZ ↔ TMI ↔ ATU crosswalk as replication**: a Berezkin motif corroborated by an
*independent* cataloguer (Thompson's Motif-Index, Uther's ATU tale types) is trustworthy; a
Berezkin-only motif is coding-dependent. Emits a **per-motif confidence weight** — the observation
multiplier the joint capstone (M38) can use — and answers the honest worry: **are our findings
(cosmology, breadth) artifacts of Berezkin's idiosyncratic coding, or cross-corroborated?**

Confidence levels: **triple** (in TMI *and* ATU, ×1.0) · **strong** (TMI tier-A, or ATU, ×0.85) ·
**moderate** (TMI tier-B, ×0.7) · **berezkin-only** (neither, ×0.5).

## What it shows

- **48 % of the 3488 motifs are cross-index corroborated** (TMI 1311, ATU 535, all-three 14);
  mean confidence weight 0.65. A per-motif weight is now available.
- **Confidence is NOT skewed by theme.** Corroboration is uniform (~40–57 % across the 13 groups),
  and **Category A (cosmology) = Category B (tales) at 49 %** — so the cosmology findings are **not**
  a Berezkin-specific coding artifact; independent indexes corroborate them as much as the tales.
- **Broad motifs are corroborated *more* than narrow ones** (broad > 15 traditions: 54 %; narrow
  ≤ 3: 20 %) — our breadth/depth findings lean on the **replicated core**, not the coding-dependent
  narrow tail (mostly fine sub-variants). This hardens the whole project.

## Honest limit — the crosswalk is automated

The crosswalk is a computed **title/description-similarity** match, so "berezkin-only" carries
**false negatives**: e.g. **K25 swan-maiden** (513 traditions — the broadest motif) is flagged
berezkin-only, yet it plainly has the well-known **ATU 400** parallel the automated match missed.
So the *true* corroborated share is **higher than 48 %**, and "berezkin-only" is an **upper bound**
on coding-dependence — which only strengthens the "not an artifact" conclusion. The BZ↔ATU arm is
thin (ATU indexes European tale types only), so ATU corroboration is weaker than TMI.

## Verdict

The findings are **not artifacts of Berezkin's coding**: corroboration is theme-blind and
concentrated in the broad motifs the analysis relies on. For **M38**: use the confidence weight
(triple 1.0 … berezkin-only 0.5) as an observation multiplier; flag broad berezkin-only motifs for
caution (and re-check them by hand — many are automated-crosswalk false negatives).

## Run

```bash
python mockups/37-cross-index-arbitration/build_data.py   # writes data.js (~2 s)
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/37-cross-index-arbitration/
```

`data.js` is git-ignored. Reads `outputs/motifs/berezkin.json` + the committed crosswalk CSVs in
`docs/motifs/crosswalk/`.
