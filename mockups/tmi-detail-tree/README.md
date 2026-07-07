# TMI detail — filter + hierarchy tree (mock)

The **filter + category tree** that used to sit at the bottom of a Thompson (TMI)
motif's detail page. It was removed from the main app (`renderTmiTree` in
`src/server/web/assets/page-motifs.js`, plus the `.motif-hierarchy` rule in
`app.css`) and preserved here, working, as an isolated mock.

Open `index.html` directly (`file://…`) — no API, no build step, no framework.
Everything (CSS lifted from `app.css`, JS reproducing `renderTmiTree` and its
helpers, and a real data slice) is inlined.

## What it shows

The lineage tree for one motif: `/ All motifs → A Myths → A100 Deity → A102`
(current, highlighted) → its direct sub-motifs, with the **tier filter** above it.

- **Filter** — Full index / With definitions / Substantive only / With ATU types.
  Picking a tier hides the child rows that don't match and swaps every badge count
  (root, chapter, ancestors, and the recursive descendant counts) to that tier —
  exactly as in the app, driven by the same `filter-*` CSS classes.
- **Click a row** to re-root: a sub-motif opens its own tree, `/` lists the
  chapters, a chapter lists its level-0 motifs.

## Data

A real connected slice of **chapter A** of the built TMI index (≈47 motif nodes +
the 23 chapter summaries + the index tier totals), embedded in `index.html`. Rows
outside that slice (other chapters, leaves not fetched) show a small inline note
instead of navigating.
