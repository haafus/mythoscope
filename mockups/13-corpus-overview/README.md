# 13 · Corpus overview (dashboard)

A design prototype for a **corpus overview page** — the "what's in this corpus?"
dashboard. Isolated from the pipeline.

## What it shows

- **Headline stats** — texts, traditions, macro-areas, total words, total sentences.
- **Composition by macro-area** — total words per region (Abrahamic and Indian
  scripture dominate), bar colour = macro-area.
- **Size of each text** — every text on one linear scale, so the ~3-orders-of-magnitude
  length skew (KJV ~790k words vs a 38k-word Beowulf) is impossible to miss.
- **Text-similarity heatmap** — TF-IDF cosine between texts and between traditions,
  reordered by hierarchical clustering (**seriation**) so related rows sit together.
  Toggle traditions ↔ texts; hover any cell for the pair + score. Colour is a single
  sequential teal ramp normalised to the observed off-diagonal range.
- **Catalogue** — every text, sortable, with word/sentence counts.

The heatmap is a **lexical (TF-IDF)** stand-in for the pipeline's BGE-M3 *semantic*
distances — deterministic and model-free so the mock rebuilds anywhere. Even so the
seriation already recovers sensible groups: East-Asian (Confucian/Taoist/Buddhist),
Oceanic, the Germanic branch (Anglo-Saxon/Norse/Germanic), Christianity↔Islam, and
the classical epics (Greek/Roman/Hinduism).

## Data

`build_data.py` reads only `config/corpus.json` + `config/traditions.json`, downloads
the 28 raw Gutenberg texts into a gitignored `cache/` (following redirects), strips
the boilerplate, and computes word/sentence counts and both TF-IDF matrices. Traditions
carry no colour in config, so every text is coloured by its **macro-area**.

## Run

```bash
python mockups/13-corpus-overview/build_data.py     # downloads (cached) + writes data.js
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/13-corpus-overview/
```

## Notes / next steps

- Direction is an **analytical dashboard** (dense, for a researcher) rather than a
  friendly landing page.
- Swap the TF-IDF matrix for real document-level BGE-M3 vectors (mean-pooled over the
  chunk embeddings already produced by the pipeline) when wiring this into the app.
- A small world map (coordinates exist for all 23 traditions) and a "structure coverage"
  tile (from the mockup 08 chapter detector) are the natural second-tier additions.
