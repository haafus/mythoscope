# 44 · Narrative stratum — the depth the catch-alls hid

Theme × depth, but on the **narrative taxonomy** (mockup 41) instead of Berezkin's 13 hand themes.
This was the original motivation for re-deriving themes: the giant catch-alls **"Adventures" (1243)**
and **"Tricks" (620)** average over motifs of very different antiquity, so a theme×depth analysis on
the hand scheme is blunt.

Depth proxy = **cross-continental reach** — the mega-set span (0–3: does the motif touch the
New-World / Old-World / Sahul continental sets?), the disjunction proxy that best tracks deep time
(widespread *across oceans* ≈ old), reported alongside mean breadth.

## What it shows

- **A clean depth gradient the flat catch-alls averaged away:** narrative clusters run from mega-set
  span **1.00** (Formulae — a recent, purely-Eurasian rhetorical layer) up to **2.10** (the
  death-messenger complex).
- **Deep = etiological, shallow = märchen.** The deep clusters draw 0–32 % of their motifs from the
  catch-alls (cosmogony, luminaries, anthropogony); the shallow ones draw **82–90 %** (ogre-dupe,
  revenge, magic-wife). The narrative split recovers the etiology↔märchen depth axis.
- **The find the catch-alls hid:** the **swallowing-monster / vulnerable-body** cluster is deep
  (span **1.80**) yet **53 %** built from motifs Berezkin filed under Adventures/Tricks/Flora. The
  flat catch-all averaged this deep complex together with shallow tales; the facet pulls it out.
- **Decomposition:** old "Adventures" (flat span 1.59) now fans across clusters **1.43–1.96**; old
  "Tricks" (flat 1.40) fans **1.26–1.67**.

## Honest limit

Depth here is a **breadth/span proxy** (widespread ≈ old) that conflates deep descent with wide
diffusion, exactly as in mockups 17 and 39; the tiny pure clusters at the top (death-messenger,
victim-casting) score high partly on diffusion, not age. On the calibrated node ages of the datable
minority (mockups 30/31) the test could be sharpened.

## Run

```bash
python mockups/44-narrative-stratum/build_data.py   # writes data.js
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/44-narrative-stratum/
```

`data.js` is git-ignored. Reads `outputs/motifs/berezkin.json`, mockup 41's committed
`narrative_taxonomy.json`, and mockup 21's `area_of`.
