# 39 · Tradition stratigraphy (roadmap M39)

Turns `stratum` around: instead of classifying each *motif* by depth (mockups 17–20), profile each
*tradition* as its **stack of strata** — the share of its motifs that are deep/broad vs areal vs
local/endemic — a **geological-column** view of a corpus. Then the strong **falsification test**:
deep-substrate-rich traditions should cluster in **early-peopled regions / refugia** (Africa,
Australia), not the late-peopled ones (the Americas).

Motif depth proxy = **breadth** (# attesting traditions, mockup 17): deep/broad ≥ 85th percentile
(≥ 60 traditions), areal 50–85th, local < 50th (< 18). A tradition's depth = the share of its
motifs in the deep tier.

## The falsification test PASSES — and honestly

- **corr(deep-share, region peopling age) = +0.43 raw; +0.48 controlling for coverage.** Tradition
  depth **rises with how early its region was peopled**. Deep-substrate-rich traditions really do
  sit in the early-peopled regions — strong support for the whole stratum logic.
- **The gradient is clean:** **Sub-Saharan Africa 63 %** (~65 ky) → early Old World 56–59 %
  (SE-Asia, S-Asia, Near East, Europe) → **the Americas 48–49 %** (~14–15 ky).
- **The coverage confound *masked* the signal, it did not fake it.** deep-share correlates
  **negatively** with coverage a(t) (−0.30): a thickly-catalogued corpus (Europe, a(t) 328) records
  more rare motifs and looks artificially shallow. So controlling for coverage **strengthens** the
  result (0.43 → 0.48) — the opposite of an artifact.
- Deepest traditions: African + South-Asian tribal groups (Herero, Iraku, Bobo, Kannikaran);
  shallowest: Amazonian (Pirahã, Urarina, Cariri) and recent/well-catalogued (Prussians, Chamorro).

## Honest limit

"Depth" here is a **breadth proxy** (widespread ≈ old), and breadth conflates deep descent with wide
diffusion — so a tradition rich in *broadly-diffused* (not necessarily ancient) motifs also scores
deep. On the calibrated node ages of the dated descent minority (M30 / M31) the test could be
sharpened; Austronesia/Oceania (deep New Guinea + recent Polynesia) also averages over two very
different peopling ages.

## Run

```bash
python mockups/39-tradition-stratigraphy/build_data.py   # writes data.js (~3 s)
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/39-tradition-stratigraphy/
```

`data.js` is git-ignored. Reads `outputs/motifs/` + mockup 21's `area_of`.
