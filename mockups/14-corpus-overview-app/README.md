# 14 · Corpus overview, in the app's design

The corpus overview from [`13-corpus-overview`](../13-corpus-overview/), **re-skinned
in MythoScope's own design system** to show how it would look as the real **Sources**
page — the one reached by clicking *Sources* in the main nav.

Same data and blocks as #13 (headline stats, composition by macro-area, per-text size
bars, TF-IDF text-similarity heatmap with seriation, sortable catalogue); the change
is purely presentational:

- the app **navbar** (MythoScope wordmark + uppercase nav links, *Sources* active),
- the app **tokens** — beige `#faf9f5` page, `.card` surfaces, `.stat-card` tiles,
  muted uppercase section headers, the `#4f7096` hover / `#e2edf0` active accents,
- the toggle restyled as the app's tab control, the table as the app's table style.

Design tokens mirror `src/server/web/assets/app.css` inline (the mock stays
self-contained — the logo is a text wordmark since `/assets` isn't served here).

## Run

```bash
python mockups/14-corpus-overview-app/build_data.py   # downloads (cached) + writes data.js
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/14-corpus-overview-app/
```

## If this graduates to the app

It replaces (or fronts) the current `#/corpus` reader page. Wire it to real data:
`get_catalog_documents()` already yields per-text `word_count` / `sentence_count` /
`tradition` / `major_tradition`; the heatmap should use mean-pooled BGE-M3 document
vectors instead of the TF-IDF stand-in. The reader (library tree + text) becomes a
drill-down from the catalogue row.
