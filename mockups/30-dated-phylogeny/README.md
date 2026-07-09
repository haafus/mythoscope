# 30 · Dated phylogeny (roadmap M30)

The Tier-3 capability step: turn a descent motif's **ordinal** clade depth (mockups 18/19)
into an approximate **calendar age**. Two external ingredients wired in:

1. **Glottolog** (CC-BY) — each Berezkin tradition joined to its nearest Glottolog language
   (median 53 km) so every tradition carries a standard **family** name + **glottocode**
   (the glottocode is what a full node-level dated ASR, M31, will need). Cached in
   `glottolog_join.json`. Sign-language / bookkeeping pseudo-families are excluded from the
   join.
2. A curated table of published **family expansion / time-depth** estimates (`FAMILY_DATES`,
   23 families) — Bouckaert, Gray, Grollemund, Heggarty, Bowern, Kitchen… — as point
   estimates with wide ranges.

**Dating rule.** A motif that is phylogenetically **clustered** (phylo-signal ≥ 0.4 —
inherited, not areal) *and* **concentrated in one family** (≥ 55% of its attesting
traditions) is dated to that family's expansion: if it rode the family's spread, that is
roughly its age.

## What it shows

- **451 of 3036 motifs get a calendar age** — the ordinal→absolute payoff. They spread from
  ~9000 BP (Afro-Asiatic) to ~1500 BP (Quechuan), **concentrated at Indo-European ~5500 BP
  (~300 motifs)** — the Eurasian märchen belt, now dated, recovering the phylomemetics picture.
- **B4 (fished-out earth) → ~5200 BP** (Austronesian expansion): mockup 18's "Austronesian
  clade" is now a date.
- **The areal majority is correctly excluded** — A3 (sun & moon) and K25 (swan-maiden) have
  low phylo-signal (0.15–0.17) and spread across families, so they get **no** family date;
  their age is a geographic question (mockup 19), as it should be.

## Honest limits

- **Family resolution, not node-level.** These are family-expansion dates, not Bayesian node
  ages on a dated tree — that is M31 (which needs the glottocodes this mockup provides).
- **Descent-only.** Only the inherited, family-concentrated minority is datable this way; the
  bulk is areal.
- **Wide uncertainty.** The dates are literature point-estimates with ranges (Indo-European
  alone spans the Steppe-vs-Anatolian debate, ~4500–8000 BP); the join can still jump a family
  boundary. **Ages are ranges, not claims.**
- **`FAMILY_DATES` is 45 families of *coarse* estimates.** The 22 beyond the well-established
  core (Salishan, Siouan, Tungusic, Japonic, Nakh-Daghestanian…) are deliberately conservative
  ceilings with wide ranges; they raise coverage but add few *motifs* (small families rarely hold
  a ≥55%-concentrated motif). Dated-family coverage is ~85% of traditions; the ~5% isolates are
  an irreducible floor (an isolate has no clade to date).

## Data

Glottolog (Hammarström et al., CC-BY-4.0). `build_join.py` builds the committed
`glottolog_join.json` (tradition → glottocode / family / distance) **name-first** — matching the
tradition's declared language by name and only falling back to nearest-coordinate — which fixes
the wrong-neighbour matches a pure coordinate join makes (Biloxi → Siouan, not the nearest French
creole; name-agreement 14% → 29%). Pseudo-languoids (Sign Language, Bookkeeping, …) are excluded.
It downloads a git-ignored snapshot of glottolog-cldf `languages.csv`. Expansion dates are from
the comparative-phylolinguistics literature (cited inline in `FAMILY_DATES`).

## Run

```bash
python mockups/30-dated-phylogeny/build_join.py   # (re)build glottolog_join.json (downloads glottolog-cldf)
python mockups/30-dated-phylogeny/build_data.py   # writes data.js (~8 s)
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/30-dated-phylogeny/
```

`data.js` and `glottolog_languages.csv` are git-ignored; `glottolog_join.json` is committed.
