# 14 · Corpus overview, in the app's design

The corpus overview from [`13-corpus-overview`](../13-corpus-overview/), **re-skinned
in MythoScope's own design system** to show how it would look as the real **Sources**
page — the one reached by clicking *Sources* in the main nav.

It follows the app's **index-section pattern** — a persistent left sidebar, an
overview page, and a per-item detail page — exactly like Motifs (overview + motif
detail). Here the sidebar is the corpus library tree (macro-area → tradition → texts),
the overview is the dashboard, and clicking a text opens its **detail page**.

- **Navbar** — the real MythoScope logo (`logo.png`) + uppercase nav links, *Sources* active.
- **Sidebar** — the app's `library-tree`: collapsible macro-area sections, tradition
  groups with colour dots, and the texts under each. A "Corpus overview" item sits on top.
- **Overview** (default) — the #13 dashboard: headline stats, composition by macro-area,
  per-text size bars, the TF-IDF similarity heatmap (with seriation), and a catalogue.
  Rows, size bars, and sidebar texts all drill into detail.
- **Detail** (per text) — colour dot + title, macro-area · tradition, word/sentence/char
  tiles, the description, and an "Opening" excerpt (public-domain preview) — the stub
  where the app's full reader (text + structure) would open.

App tokens mirror `src/server/web/assets/app.css` inline so the mock stays self-contained.

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
