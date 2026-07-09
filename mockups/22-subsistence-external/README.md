# 22 · Subsistence from D-PLACE + theme test

Wires the one external dataset the model needs and answers a question the proposal
asserted but never checked.

`macro-area-facets.md` gives `tradition` four facets — `area`, `family`, `subsistence`,
`theme_profile` — but **`subsistence` has no in-corpus source**; the proposal says it is
"derivable from D-PLACE". This mockup does that, then tests the asserted correlation
*foragers are cosmology-heavy, farmers tale-heavy*.

## Pipeline

1. **D-PLACE → subsistence buckets.** Each Ethnographic-Atlas society is mapped to one of
   the 4 buckets from `EA042` (dominant activity) with `EA028` (agriculture intensity)
   disambiguating the mixed/unknown cases: gathering/fishing/hunting → **forager**,
   pastoralism → **pastoralist**, casual/extensive agriculture → **horticulturalist**,
   intensive → **agrarian-state**. 1203 societies with a bucket + coordinates, cached in
   `dplace_subsistence.json`.
2. **Join.** Each Berezkin tradition is placed at its `tradition-coords.json` point and
   matched to its nearest D-PLACE society by great-circle distance; 820 land within 250 km
   (median 120 km).
3. **Test `subsistence × theme`.** For each matched tradition (≥20 motifs) compute the
   Category-A (cosmology/etiology) share of its motifs, averaged per subsistence bucket.

## What it shows

- **The predicted split holds:** the extractive/low-intensity economies are
  cosmology-heavy — **foragers 54.7%**, **horticulturalists 57.6%** Category A — while the
  intensive/mobile ones are tale-heavy — **agrarian-states 39.5%**, **pastoralists 36.2%**.
  Cosmology gives way to adventure/tale as production intensifies, exactly as the proposal
  argued (foragers etiology-heavy, farmers märchen-heavy).
- **Pastoralists are the sharpest tale-heavy case (36.2%):** the epic/heroic narrative
  traditions of Central-Asian and Near-Eastern herders.
- The `subsistence × area` cross-tab passes the sanity check: Australia 100% forager,
  Europe all agrarian-state, the Near East mostly pastoralist, Sub-Saharan mostly
  horticulturalist.

## Honest caveat — the area confound

Subsistence correlates with area (pastoralists ≈ Central Asia, foragers ≈
Australia/N-America/Siberia), so part of the `subsistence × theme` gradient is really
`area × theme`. **Now tested (mockup 25):** the gradient *survives* restricted permutation
within area (p=0.003) and within language family (p=0.006), so subsistence carries its own
contribution — it attenuates to marginal only when both are controlled at once (low power).
The confound is real but does not explain the signal away.

*(Coordinates are per-tradition from the committed `tradition-coords.json` snapshot, so the
join is at real tradition locations, not subregion centroids.)*

## Data

D-PLACE (Kirby et al. 2016, *PLoS ONE*), Ethnographic Atlas (Murdock 1967), **CC-BY-4.0**.
`dplace_subsistence.json` is a compact derivative (society, glottocode, coords, bucket)
committed for reproducibility; regenerate it from the EA `societies.csv` + `data.csv`.

## Run

```bash
python mockups/22-subsistence-external/build_data.py   # writes data.js
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/22-subsistence-external/
```

`data.js` is git-ignored; `dplace_subsistence.json` is committed.
