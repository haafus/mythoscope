# Motif browser UI — three views in one surface (design)

A design proposal — **partially implemented** — for organising the three ways of
looking at a motif catalogue — **(1) hierarchy/tree exploration, (2) flat
filtered & sorted lists, (3) full-text search** — plus the two reading intents
(**browsing lists** vs **reading a card**) inside the existing Motifs page. The
flat-list/sort lens and search are live (`flatList` / `mState.sort` in
`page-motifs.js`); the full unified-navigator layout is prototyped in
`mockups/09-motifs-navigator/` but not yet the production surface. This doc is the
target model and the map onto today's identifiers.

Implementation lives in `src/server/web/assets/page-motifs.js` (vanilla ES
module SPA) and `src/server/services/motifs.py` (read service). This doc maps the
target model onto the identifiers that exist today and lays out an incremental
path; it deliberately does not change behaviour by itself.

---

## 1. Where we are today

The page is a master–detail split (`renderMotifs`):

```
.workspace
├── aside.motifs-sidebar
│   ├── #motifsTabs        index switch (TMI / Berezkin / ATU)
│   ├── #motifsOverview    "Overview" button
│   ├── #motifsSearch      text input  → loadList() (debounced 250ms)
│   ├── #motifsChapter      <select> of chapters → loadList()
│   └── #motifsList         the FLAT list  (loadList → renderList)
└── article.motifs-detail (#motifsDetail)   the "reader"
    ├── renderOverview()        dashboards (default)
    ├── openMotif → renderDetail()   a motif card + inline tree lineage
    └── browseRoot / browseChapterLevel0   TREE exploration (drill-down)
```

The three approaches already exist, but they are split across **two surfaces**,
which is the core problem:

- **Flat list (#2)** lives in the **sidebar** (`loadList` → `/api/motifs/{index}/motifs?chapter&q&limit` → `renderList`). It honours `chapter` + `q` but **not** the tier filter and **not** any sort.
- **Tree (#1)** lives in the **detail panel** (`browseRoot`, `browseChapterLevel0`, `renderTmiTree`). It has its own controls (`controls()` → `filterSelect()` tier dropdown + a `Flat list` checkbox) and its own drill-down with subtree-relevance.
- **Search (#3)** is the sidebar input; it only drives the sidebar list. It has no effect on the tree in the detail panel.

So a tier filter chosen in the tree does not touch the sidebar list; a search in
the sidebar does not touch the tree; and the `Flat list` checkbox in the tree
duplicates the idea of the sidebar list. Two mental models for one catalogue.

State today (`mState`):

```js
{ indexes, index, chapter, query, selectedId,
  motifFilter: "all"|"def"|"sub"|"atu",   // tier, only read by the tree
  flatList: false,                          // tree-only flat toggle
  browseChapter, browseView }               // "root"|"chapter"|null
```

---

## 2. Target model: one navigator + composable lenses

Treat the three approaches not as three screens but as **one result surface with
composable lenses**. Tree vs list is a *layout*; filter and search are
*predicates*; sort is an *ordering*. They combine; they don't exclude.

The navigator is the **left pane**. The right pane stays the reader. The left
pane gets a persistent **toolbar** on top and a single **result region** below
that renders either the tree or the list:

```
┌── Catalog navigator (left pane) ────┐ ┌── Reader (right pane) ─────┐
│ [TMI][Berezkin][ATU]   (Overview)   │ │  A1.2  Creator Has Two…    │
│ ┌─────────────────────────────────┐ │ │  ───────────────────────  │
│ │ 🔍 search id or text…           │ │ │  Definition · Cultures…    │
│ └─────────────────────────────────┘ │ │  References · Raw notes    │
│  ⊟ Tree  ☰ List      Chapter:[A ▾]  │ │                            │
│  Filter:[Substantive ▾]  Sort:[—▾]  │ │                            │
│ ─────────────────────────────────── │ │                            │
│  ▸ A0–A99  Creator           ✓·12   │ │                            │
│    ▾ A1   The creator               │ │                            │
│        A1.1 …                       │ │                            │
└──────────────────────────────────────┘ └────────────────────────────┘
```

This merges the sidebar list and the detail-panel tree into one surface, so the
filter/search/sort always act on what you see.

### The lens matrix

| Control | Role | In **Tree** view | In **List** view |
|---|---|---|---|
| **Search** (`mState.query`) | predicate on id+name (optionally notes/definition) | highlight matches, auto-expand their ancestors | filter + rank to top |
| **Filter** (`mState.motifFilter`: all/def/sub/atu) | predicate | subtree-relevance (already built) | direct row filter (`tier=` param) |
| **Sort** (`mState.sort`, new) | ordering | disabled (tree has intrinsic order) | id / notes size / cultures / breadth |
| **View** (`mState.view`, new) | layout only | — | — |
| **Chapter** (`mState.chapter`) | scope | roots / one chapter | prefix scope |

**Binding rule that keeps it coherent:** search and sort never switch the view —
they re-render whatever view is active. Empty query + Tree = pure hierarchy
exploration (#1). Filter/sort + List = flat filtered/sorted list (#2). Typing in
search = lens #3, working *in both* views.

---

## 3. State changes

```js
const mState = {
  // unchanged
  indexes, index, chapter, query, selectedId, motifFilter,
  // changed / new
  view:  "tree" | "list",   // replaces `flatList` (checkbox → segmented control)
  sort:  "id" | "notes" | "cultures" | "breadth",  // new, applies in list view
  focus: "browse" | "read", // new, see §6
  // browseChapter stays as the tree's drill-down position
};
```

`flatList` is removed: "flat" is simply `view === "list"`. `browseView` can fold
into `view` + `browseChapter` (root vs a specific chapter is just whether
`chapter` is set).

A single dispatcher replaces the scattered renderers:

```js
function renderNavigator() {
  if (mState.view === "list") return renderListView();   // tier+q+sort, flat
  return renderTreeView();                                // drill-down + q highlight
}
```

`renderTreeView` is today's `browseRoot` / `browseChapterLevel0` logic;
`renderListView` is today's `loadList` / `renderList`, extended with `tier` and
`sort`. The toolbar's change handlers all call `renderNavigator` (search through
the existing 250 ms debounce on `searchTimer`).

---

## 4. Toolbar: build it once, above the result region

Replace the three loose sidebar controls (`#motifsSearch`, `#motifsChapter`, the
`Overview` button) and the tree-embedded `controls()` with one toolbar component
rendered at the top of the navigator pane:

```
[ search ]                       ← #motifsSearch (kept, same debounce)
[⊟ Tree] [☰ List]   Chapter:[ ▾] ← view segmented control + #motifsChapter
Filter:[ ▾]   Sort:[ ▾]          ← filterSelect() + new sortSelect()
```

- The view segmented control writes `mState.view` and calls `renderNavigator`.
- `filterSelect()` already exists; move it from inside the tree to the toolbar so
  it governs both views (its tier counts come from `list_indexes`, already
  subtree-relevant).
- `sortSelect()` is new; disabled (greyed, tooltip "sort applies to the list
  view") when `view === "tree"`.
- The `Overview` button stays — Overview is a third destination of the **reader**
  pane, independent of the navigator (see §6); it does not need a toolbar slot.

Because the toolbar is one component over one result region, the current bug-class
"filter set in tree doesn't affect the sidebar list" disappears by construction.

---

## 5. Search as a cross-cutting lens

Search should narrow whatever view is active, not force a mode.

- **List view:** unchanged in spirit — `q=` is sent to the API; matches fill the
  list. (Optionally add server-side ranking so exact id / name-prefix hits sort
  first; today it's just a filter.)
- **Tree view:** the query becomes a *highlight + reveal*. Matching motifs get a
  highlighted row, and every ancestor on the path to a match is auto-expanded so
  the hit is visible in context. Non-matching siblings stay collapsed. This is the
  natural tree analogue of "filter to matches" and preserves hierarchy (#1) while
  searching (#3).
  - Mechanics: reuse the existing subtree-relevance machinery. The service already
    computes subtree flags for tiers (`_tier_relevant`, `*_subtree`); add an
    equivalent "query-subtree" pass (ids whose subtree contains a `q` match) so the
    tree can decide which branches to open and which rows to mark. Falls back to
    the flat list if the match set is large.
- **Soft nudge, not a forced switch:** when a query is non-empty in Tree view,
  show a small affordance next to the toolbar — `N matches — show as list` — that
  flips `view` to `list`. The user keeps their place if they ignore it.

---

## 6. Two reading intents: a focus toggle on the same split

Browsing lists and reading a card are two intents on the same master–detail
layout, not two screens. Add one flag, `mState.focus`, that rebalances the split
and the navigator's density. Nothing about the navigator's lenses changes.

**`focus: "browse"` — lists are primary:**

```
┌── navigator (wide) ─────────┐ ┌─ reader (narrow, preview) ─┐
│ full rows: id · name · ✓·12 │ │ short definition + key     │
│ A1.2 ← selected             │ │ fields, "open to read →"   │
└─────────────────────────────┘ └────────────────────────────┘
```

Navigator takes the larger share; the reader shows a compact preview (definition
+ key fields). Clicking a row updates the preview; focus stays in the list.

**`focus: "read"` — the card is primary:**

```
┌─ rail ─┐ ┌── reader (wide, full card) ──────────────┐
│ A1   · │ │ A1.2 Creator Has Two Sons                │
│ A1.2 ◄ │ │ Definition · Cultures · References · …    │
│ A2   · │ │ full text, raw notes, cross-links         │
└────────┘ └───────────────────────────────────────────┘
```

The navigator collapses to a thin **rail** (id/code only, current highlighted) —
it does not disappear, it becomes a card-stepper. The reader expands to full
width.

What makes the two intents flow into one another:

1. **One toggle, shared selection.** An expand control on the card (or
   double-click / Enter on a row) does browse→read; "back to list" / Esc does
   read→browse. `selectedId` is shared, so nothing is lost.
2. **The list stays a live navigator while reading.** In `read`, `↑/↓` (or `j/k`)
   step through the rail rows and load the next/prev card immediately — flipping
   through the catalogue without leaving the reader. This is the bridge between
   intent #1 and #2.
3. **Context persists.** Collapsing the navigator keeps scroll position, the
   expanded tree branch, and all lens settings; expanding returns you in place.
4. **Deep links choose the start state.** `#/motifs?index=tmi` opens `browse`;
   `#/motifs?index=tmi&id=A1.2` opens `read` (rail + full card) — the URL already
   carries the intent (`renderMotifs` reads `params.get("id")` today).
5. **Overview** is just the reader showing the dashboard (`renderOverview`); it is
   orthogonal to `focus` and to the navigator's lenses.

Implementation is mostly CSS: `focus` sets a class on `.workspace` that drives the
two pane-width ratios and whether `.motifs-list` renders full rows or rail rows.
On narrow screens the two states degrade to "full list" ↔ "full card with a back
button" — same model.

---

## 7. Per-index degradation

A real hierarchy exists only for TMI (place-value codes). For Berezkin (flat list
+ chapters) and ATU (chapters/divisions), the Tree/List control means
**"group by chapter" vs "flat"**:

- **Tree** → one-level grouping by chapter (chapter row → its motifs).
- **List** → flat, exactly today's `renderList`.

So the segmented control stays meaningful everywhere; only TMI gets multi-level
drill-down. Tier filter + sort apply identically across indexes.

---

## 8. Backend touch-points

Most of this is frontend. The service (`motifs.py`) needs:

- **Sort.** `list_motifs(..., sort=...)` ordering by `id` (default), `notes_size`,
  culture count, or areal breadth. The fields already exist on records
  (`notes_size`, cultures, `areas`); this is a sort key + a new `sort` query param
  on `/api/motifs/{index}/motifs`.
- **Query-subtree flags (optional, for tree highlight).** A `q`-scoped analogue of
  `_tier_relevant` so the tree knows which branches to auto-open for a search.
  Can be deferred — v1 can fall back to switching to list view on search.
- No schema change for tiers/search (already wired); keep
  `ConfigDict(extra="allow")` on the list/summary models so enrichment fields keep
  flowing.

---

## 9. CSS touch-points (`app.css`, bump `?v=`)

- `.workspace.focus-browse` / `.workspace.focus-read` — the two pane-width ratios.
- `.motifs-list.rail` — compact id-only rows for read mode.
- `.motif-toolbar` — the unified toolbar (search, segmented view control, chapter,
  filter, sort) above the result region.
- `.seg-control` — Tree/List segmented buttons.
- `.tree-row.match` / `.tree-row.ancestor-of-match` — search highlight in tree.
- Keep the existing tier badge content-swap classes (`tier-badge`, `f-def`/`f-sub`/`f-atu`).

---

## 10. Incremental rollout

Each phase ships on its own and leaves the page working:

1. **Unify the surface.** Move `filterSelect()` and the view control into one
   toolbar; make `renderNavigator` dispatch list vs tree; delete the `Flat list`
   checkbox and `flatList` (→ `view`). Sidebar list and tree now share lenses.
2. **Search everywhere.** Make `query` drive `renderNavigator`; in tree view add
   highlight + auto-expand (or, as a stopgap, the "show as list" nudge).
3. **Sort.** Add `sortSelect()` + the `sort` API param; enable it in list view.
4. **Focus modes.** Add `mState.focus`, the browse/read CSS states, the card
   expand/back control, keyboard stepping, and deep-link start-state.

---

## 11. Open questions

- Should search default to id+name only, or also scan `definition` / `notes`? The
  latter is more powerful but needs server-side text indexing to stay fast.
- In tree view with a large match set, where is the cutoff to auto-fall-back to
  list rather than auto-expanding hundreds of branches?
- Should `sort` persist per index, or reset on index switch (like `query` does in
  `switchIndex`)?
- Rail width and whether the rail shows the badge or just the id.
