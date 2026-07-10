# 43 · Narrative tradition profiles

Mockup **16** re-run on the data-driven facet. Each tradition becomes a **16-dim narrative-cluster
profile** (the proportion of its motifs in each of mockup 41's narrative clusters) instead of the
13 hand themes; traditions with ≥ 30 motifs (840 of them) are clustered by that profile alone
(k-means, k=8, no geography/language) and plotted on the world map.

Justified by mockup 42: the narrative profile is a strictly better tradition descriptor (it
subsumes the theme profile on the Jaccard-ΔR² test). The question here: does the *better*
descriptor give a sharper / more cross-continental grouping of cultures?

## What it shows

- **Even more geography-orthogonal.** Macro-area explains only **31 %** of the narrative-profile
  variance vs **38 %** for the 13-theme profile — the narrative profile carries *more* information
  that isn't reducible to "where the tradition is."
- **Cross-continental worldview clusters** (each spans 9–13 macro-areas): a celestial/cosmology
  profile that groups Cherokee + Ancient Italy + SE-Australia + Netsilik; a cosmology cluster tying
  Mesoamerica–Andes to Tibet / East Asia; a Eurasian märchen profile (magic-wife + magic-flight +
  ogre-escape). These are **worldview** affinities pure geography or language would miss — the same
  phenomenon mockup 16 found, on a sharper descriptor.

## Caveat

Same as mockup 16: raw proportions are confounded by **attestation intensity** (a densely
catalogued corpus reflects what was recorded); the raw profile is enough to show the signal exists.

## Run

```bash
python mockups/43-narrative-tradition-profiles/build_data.py   # writes data.js
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/43-narrative-tradition-profiles/
```

`data.js` is git-ignored. Reads `outputs/motifs/berezkin.json`, mockup 41's committed
`narrative_taxonomy.json`, `mockups/_geo.py` coordinates, and the committed `land.js`.
