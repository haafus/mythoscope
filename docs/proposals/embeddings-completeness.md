# Embeddings completeness — `EmbeddingsStage.actual()` reports partial documents as clean

**Status: DESIGNED, NOT IMPLEMENTED.** Reasoning captured; fix pending. See the marker in
[`implementation-roadmap.md`](implementation-roadmap.md) and the entry in
[`known-issues.md`](../known-issues.md).

The bug that started this: a HIGH data-integrity finding from the Stage IV code review —
`EmbeddingsStage.actual()` has no per-document completeness check, so a book that only got
*some* of its chunks embedded is reported as fully built ("clean"), and the driver never
re-embeds the missing chunks.

---

## 1. The chunk data model (what the fix hinges on)

Each chunk is a Chroma record: id `chunk_id(document_id, i)` (positional, `i = 0..N-1`) with
metadata (`build_embeddings.py`, `_build_chroma_entries`):

```python
{"document_id": ..., "chunk_index": i, "fingerprint": fp}   # (+ "source_text" for preprocess variants)
```

- **`chunk_index`** — the only genuinely per-chunk-unique field (position).
- **`fingerprint`** — **per-document, not per-chunk-content.** It is
  `chunk_fingerprint(doc_content_fp, transform_version)` (`transform.py`), computed **once per
  document** and copied **identically** onto every one of its chunks. Chunk metadata feeds into
  **no** fingerprint — the fp inputs are the whole-doc content hash + `transform_version` only.
- **Separately, on the collection** (`collection.modify`): `{key, model, chunk_size,
  total_chunks, transform_version}`. `total_chunks` is a corpus-wide sum — there is **no**
  per-document chunk count stored anywhere.

**Root cause:** `actual()` reads the fp off *any* chunk carrying `(document_id, fingerprint)`
and reports `out[did] = fp`. Since nothing records how many chunks a document *should* have, a
document with 1-of-N chunks is indistinguishable from a complete one.

---

## 2. Why `is_last` alone is not enough (preprocess breaks the prefix property)

First idea: mark the last chunk (`is_last`) as a "document fully processed" flag. This is
**correct for plain variants** and appealing because `actual()` stays a pure Chroma read.

Why it works for plain: chunks are upserted **in ascending index order, batched**
(`build_embeddings.py`), and any failure is caught **per-document** and aborts the rest — so
what gets written is always a **prefix** `0..k`, no mid-document holes. Hence *last chunk
present (with matching fp) ⟺ all chunks present*. The fp-match is essential: a stale last chunk
(old fp after a text edit whose re-embed didn't reach the tail) correctly fails the check.

**Why it fails for preprocess variants** (which *will* be active): a preprocess chunk whose LLM
transform comes back empty is dropped from `kept` (`build_embeddings.py`, the `if out.strip()`
filter) and **retried next run** — empty output is never cached (`preprocess.py`, `_store` only
writes `if out:`). So a not-yet-ready **middle** chunk is skipped while later chunks embed →
**real holes**, non-contiguous writes. The last chunk can be present while chunk 5 is a hole →
`is_last` would falsely report "complete." Once preprocess is in play, a **count** is required,
not just an end marker.

Note there is **no legitimate-permanent-empty** chunk: the preprocess model treats empty as
"not done yet, retry," so a fully-built preprocess document has **all N** chunks, exactly like
plain. That is what makes a single uniform completeness rule possible.

---

## 3. Chosen design — store `n_chunks` per chunk

Store `n_chunks` (the full non-empty raw chunk count `N = len([c for c in chunk_text(content,
chunk_size, chunk_overlap) if c.strip()])`, already computed at build time) in **every chunk's
metadata**. Then:

```
actual(): group chunks by document_id;
          a document is at fingerprint F  ⟺  it has n_chunks chunks all carrying (fp == F);
          report out[did] = F for that F, else omit the document (→ driver sees "missing" → rebuild).
```

- Uniform for plain **and** preprocess: a hole gives `count < n_chunks` → not reported →
  driver rebuilds → `build` fills the missing chunks (idempotent) → `count == n_chunks` → clean.
- `actual()` stays a **pure Chroma read** — no re-chunking the corpus on every `status`/diff
  (the reason to store `n_chunks` rather than recompute `N` from the corpus in `actual()`).
- Stored on **every** chunk (not just the last) so `N` is readable from **any** surviving chunk,
  regardless of which position is currently a hole. Redundancy is one int per chunk.

### Migration — no rebuild required

Adding `n_chunks` to metadata changes **no fingerprint** (metadata is not a fp input), so it
does **not** invalidate anything by itself. The only wrinkle is legacy chunks written before the
change (no `n_chunks` field): a strict `count == n_chunks` check would read `None`, report them
incomplete, and the driver would loop forever (build finds `to_embed == []` since fp already
matches → writes nothing → never adds `n_chunks`).

**Fix:** backward-compat fallback in `actual()` — **if `n_chunks` is absent, fall back to the
old behavior** (any chunk with fp ⟹ present). Legacy collections then behave as before (no
rebuild, no loop); only freshly-written chunks get the strict count check. The bug is fixed
going forward and legacy data is fixed opportunistically whenever it is next rebuilt.

---

## 4. `n_chunks` co-varies with `fingerprint` (why there is no torn state)

`N` is a function of `content`, `chunk_size`, `chunk_overlap`, and the `chunk_text` algorithm.
Everything that changes `N` also changes `fp`:

| what changes `N` | also changes `fp` via |
|---|---|
| document text (`content`) | `content_fingerprint` → doc fp → chunk fp |
| `chunk_size` | `transform_version` |
| `chunk_overlap` | `transform_version` |
| `chunk_text` logic | `EMBED_ALGO_VERSION` — **only if bumped** (else `--force`) |
| `if c.strip()` empty filter | not independent — derived from text/algorithm above |

So `n_chunks` and `fp` are written by the **same upsert**; there is never a state with the
correct (expected) fp but a stale `n_chunks`. Reading `n_chunks` off a matching-fp chunk always
yields the current `N`. The single gap — a `chunk_text` logic change **without** an
`EMBED_ALGO_VERSION` bump — is the **same** pre-existing hazard the fp gate already has (stale
vectors under an unchanged fp), covered by the "bump the algo version or `--force`" convention.
`n_chunks` introduces no new class of problem.

---

## 5. Implementation checklist (when we return)

- [ ] `_build_chroma_entries`: add `"n_chunks": len(chunks)` to each chunk's metadata.
- [ ] `EmbeddingsStage.actual()`: group by `document_id`; report a doc at fp `F` iff it has
      `n_chunks` chunks all at `F`; **fallback**: if a doc's chunks lack `n_chunks`, keep the
      old any-chunk-with-fp behavior.
- [ ] Tests:
  1. plain — a document with a written prefix but no tail chunk → **not** reported clean;
  2. preprocess — a hole in the middle with the last chunk present → **not** clean; after the
     hole fills → clean;
  3. legacy — chunks without `n_chunks` → reported clean (fallback, no rebuild).
- [ ] Sanity: adding the field triggers **no** re-embed on an existing collection.
