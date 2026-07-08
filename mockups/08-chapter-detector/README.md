# 08 · Chapter / section detector

A prototype that probes **how well chapters / sections / a table of contents can be
extracted automatically** from the downloaded corpus texts. Fully isolated from the
main pipeline.

## What it does

`build_data.py`:

1. Reads only the source list in `../../config/corpus.json` (28 Project Gutenberg URLs).
2. Downloads each raw `.txt` via `curl` into a gitignored `cache/` (re-runs are cached).
3. Strips the Gutenberg header/footer and runs a **layered heading detector on the raw
   text** — deliberately *before* the main pipeline's cleaner, which collapses the
   blank-line gaps and deletes the divider lines that headings rely on.
4. Emits a compact `data.js`: per book, the winning strategy, per-strategy candidate
   counts, and each detected heading's title + char offset + a short context preview
   (not the full body, so `data.js` stays ~400 KB).

`index.html` is a self-contained viewer: the book list (winning method + chapter
count) on the left; on the right, the book's stats, the first 45 lines (to spot the
Contents block / heading style), per-strategy candidate counts, and the detected
headings with previews.

## Detection strategies (priority order)

| Strategy   | Fires on                                                        |
|------------|-----------------------------------------------------------------|
| `keyword`  | isolated line starting `CHAPTER / BOOK / PART / CANTO / SURA / PSALM / HYMN …` |
| `contents` | a `Contents` block near the top, each entry re-located in the body |
| `roman`    | isolated standalone Roman-numeral lines (`I.`, `IV`, …)          |
| `allcaps`  | short, isolated, all-uppercase title lines                      |
| `numbered` | isolated standalone number lines (verse/section numbers)        |

The winning method is the highest-priority strategy that clears a small minimum count.
The viewer shows *all* candidate counts, so under/over-detection (e.g. keyword winning
with 2 hits while `numbered` found 81) is visible at a glance.

## Run

```bash
# from the repo root
python mockups/08-chapter-detector/build_data.py     # downloads (cached) + writes data.js
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/08-chapter-detector/
```

## Current coverage (28 books)

`keyword` 14 · `contents` 5 · `allcaps` 5 · `roman` 2 · `none` 2.

The two misses are honest: the **KJV Bible** (Gutenberg marks verses as `1:1`, not
`CHAPTER`) and one Australian folktale collection. This is the intended output of a
probe — it shows where a heuristic detector is strong (epics, Gutenberg books with a
Contents block) and where a source needs its own rule.

## Notes on offsets

Offsets here are char indices into the **raw** stripped body. If this graduated into
the pipeline, detection should run on the **served (cleaned)** text so the offsets
match what the reader receives — see the discussion in the main design notes.
