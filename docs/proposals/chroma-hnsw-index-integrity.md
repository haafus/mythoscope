# Chroma HNSW index integrity — desync between the store and the search graph

Status: **analysis + recommendations** (some items shipped, most proposed). Register entry:
[`known-issues.md`](../known-issues.md) → "HNSW index integrity". Roadmap hook:
[`implementation-roadmap.md`](implementation-roadmap.md) OPEN FOLLOW-UPS.

## Symptom

Clicking a scatter point on Similarity (e.g. *The Popol Vuh* #76) surfaced a **different** book's
fragment (*The Ramayan of Valmiki* #1709). Diagnosis via `scripts/validate_chroma.py`:

- id ↔ metadata ↔ text ↔ **stored vector** are all correct (`get(ids=[cid])` returns the right row).
- But a **self-query** with the row's own stored vector does **not** retrieve the row within top-k —
  it returns another book's chunk. So the *record store is right; the HNSW search graph is wrong*.
- Scope on `bge-m3`: ~6 cross-book desyncs out of 22 711 chunks (~0.03%), stable across runs. A
  separate, benign class — same-book overlapping chunks tying for first — flaps between runs and is
  **not** corruption (it is `chunk_overlap` near-duplicates).

## Root cause (two documented mechanisms, both from mutating the live graph)

Chroma keeps a vector/record store and a separate HNSW navigation graph. Our **positional ids**
(`doc::index`) + the fingerprint gate mean the same labels are repeatedly **updated in place**
(`upsert` over an existing id = hnswlib `updatePoint`/`repairConnectionsForUpdate`) and, on a shrink,
**deleted**. That churn is exactly where the store and the graph drift apart:

1. **HNSW degradation under update/delete — "unreachable points."** Delete+reinsert cycles create
   nodes with outgoing but no incoming edges → unfindable in search even by their own vector. Recall
   drops; ~3–4% unreachable after 3000 cycles.
   — [arXiv:2407.07871](https://arxiv.org/html/2407.07871v2) (MN-RU); confirmed almost verbatim by
   [MemPalace #521 — "updatePoint … on modified-file re-mine"](https://github.com/MemPalace/mempalace/issues/521).
2. **Chroma segment/compaction desync.** Historically the "delete → re-add same id before persist"
   bug ([chroma #2062](https://github.com/chroma-core/chroma/issues/2062) → fixed
   [PR #2512](https://github.com/chroma-core/chroma/pull/2512), mid-2024). In our **1.5.9** the 1.x
   log-structured rewrite is better, but "interrupted/concurrent compaction can leave the HNSW segment's
   element count out of sync with `max_seq_id`" still applies ([MemPalace #1238](https://github.com/MemPalace/mempalace/issues/1238),
   [#1843](https://github.com/MemPalace/mempalace/issues/1843)).

The delete-then-re-add-**same-id** path (#2062) is rare for us (needs a doc to shrink then grow back),
and is patched in 1.5.9 anyway. Our real exposure is (1): plain in-place `upsert` of a changed chunk
is already the fragile update. **This is a property of HNSW, not of Chroma** — every HNSW store
(Qdrant/Weaviate/Milvus/pgvector) has it and hides it behind automatic segment compaction / scheduled
reindex; industry norm is to reindex when the deletion ratio exceeds ~10–15%.

## Already shipped

- **`scripts/validate_chroma.py`** — full integrity check: id↔metadata, orphans, n_chunks/contiguity,
  and **self-query** (on by default). Self-query passes on **top-k membership** (not rank 1), so real
  desync is separated from benign overlap ties; both are reported **separately**; chunk ids are decoded
  to book titles; a **desync pattern** aggregation shows FROM/TO books (attractors = large, trimmed books).
- **Tail-reap bug fixed** (`build_embeddings.py`): the rebuild step nulled a rebuild-doc's stored fp but
  now **keeps the chunk-id key**, so `embed_plan`'s tail-`stale` detection can still delete the shrunk
  tail. This was the "1035 rows but n_chunks=986" inconsistency. Regression test added
  (`tests/test_build_embeddings_gate.py`) exercising the real `embed_plan`.
- **Similarity click head from `get`-by-id** (`services/similarity.py::get_point`): the head is now
  always the clicked chunk fetched by id, never `query[0]`; `_query` is used only for neighbours (the
  clicked chunk is dropped from them by id, not by rank). This closes the *Popol Vuh → Ramayan* symptom
  at the app layer regardless of graph health, at zero extra cost (the `get`-by-id call already happened).

## Recommendations (prioritized)

### Immediate — low risk, direct effect
1. ✅ **Similarity click: head from `get`-by-id, not the ANN query** — **shipped** (see "Already shipped").
   The head is always the clicked chunk fetched by id; `_query` supplies only neighbours. Closes the
   foreign-fragment symptom at the app layer regardless of graph health, at zero extra cost.
   (Graph node hover was never affected — it reads `node.data` from the already-loaded graph JSON.)
2. **One-time clean rebuild** of the affected collection: `mytho build embeddings:bge-m3 --force`
   (drop + re-encode into a fresh graph), then `validate_chroma bge-m3 --self-query 22711` to confirm
   `desync = 0` (only `WARN` ties remain). Use `--force` (re-encode) for the *first* cleanup rather than
   trusting possibly-degraded cached vectors.

### Structural — deliberate (see "Refactor assessment")
4. **Rebuild-on-structural-change** — a controlled reindex instead of in-place update/delete:
   read the current vectors, re-encode **only** the changed docs, build a **fresh** collection with pure
   inserts, and **atomically swap**. This is the Chroma-native path ("recreate the collection") and what
   mature DBs do automatically. Gate it (only when the build deletes / churn exceeds a threshold), not every build.

### Guardrail / hygiene
5. **Wire a sampled `self-query` into the embeddings build / CI** — this class is invisible to
   id↔metadata checks, so it must be caught actively, not by a user clicking a point.
6. **Schedule periodic reindex** (industry norm; when deletion ratio > ~10–15%).

### Version
7. Stay on **1.5.9** (latest stable; don't ship 1.5.10.dev). Upgrade is **not** the lever: #2062 is
   already fixed here, and the HNSW-degradation + compaction-sync issues are version-independent.
8. Watch for **1.5.10 stable** (compaction-sync fixes); upgrade within `<2` when it lands.
9. **Do not** add `chromadb-ops` (`chops hnsw rebuild`) to the pipeline — it relies on internal Chroma
   APIs ("may require maintenance as ChromaDB evolves"). There is **no native** Chroma rebuild/reindex API:
   `collection.modify()` only tweaks runtime params (`ef_search`, `num_threads`, `batch_size`,
   `sync_threshold`, `resize_factor`); `space`/`ef_construction`/`max_neighbors` are immutable → the only
   supported "recompute the graph" is recreating the collection.

### Rejected
- **Raising `hnsw:search_ef` (≈100).** *Declined.* It costs **2–3× query latency** and treats the wrong
  problem: search_ef only widens the beam to recover *approximate misses* and *ties* — it does not repair
  a **degraded graph**, and truly unreachable nodes (no incoming edges) are not found at any `ef`. The root
  cause here is **graph degradation from in-place update/delete churn**, not query instability, so the fix
  belongs at build time (rebuild-on-structural-change), not at query time. The click-head fix already makes
  the clicked fragment deterministic without touching recall.

## Refactor assessment (item 4)

- **Complexity: moderate, localized** to `build_embeddings._save_corpus_to_chroma`. New data flow:
  (a) `collection.get(include=["embeddings","metadatas","documents"])` to pull already-computed vectors;
  (b) re-encode only the `rebuild` set (existing loop); (c) create a temp collection and `upsert` the
  union (unchanged cached + newly encoded) as **pure inserts**; (d) swap (`delete_collection` + rename via
  `collection.modify(name=…)`). Building into a temp name preserves atomicity on crash.
- **Fit:** good — we already use `delete_collection`, `get_or_create_collection`, `upsert`, and
  `get(embeddings)`. The genuinely new parts are the union-accumulation and the swap.
- **Healing property:** rebuilding the graph from the (correct) stored vectors **fixes existing desync**
  without re-encoding — because the corruption is graph-level, not vector-level.
- **Slowdown:** the dominant new cost is a **full HNSW index build** (all ~22 711 vectors) on every
  structural change, vs the incremental path that only touches changed docs. Reading all vectors out of
  Chroma is also non-trivial (seconds). Encode cost stays delta-only. Rough order: a full index rebuild is
  tens of seconds to a couple of minutes of CPU (no GPU/LLM) for the current corpus — needs a real bench.
- **On every build?** No. A clean build already short-circuits (nothing to do). A build with any change
  would pay a full index rebuild — wasteful during iterative dev with small edits. **Gate it:** reindex
  only when the build performs deletes (structural shrink/removal) or churn exceeds a threshold; keep
  pure same-count re-embeds incremental (they degrade the graph slower) + rely on the guardrail (#5) and
  periodic reindex (#6). Deletes are rare (structural), so gated reindex is cheap in aggregate.

## Sources

- HNSW is approximate / recall & determinism: [OpenSource Connections](https://opensourceconnections.com/blog/2025/02/27/vector-search-navigating-recall-and-performance/),
  [Marqo — Understanding Recall in HNSW](https://www.marqo.ai/blog/understanding-recall-in-hnsw-search).
- Exact-embedding not returned: [chroma #3113](https://github.com/chroma-core/chroma/issues/3113);
  non-deterministic results: [#2675](https://github.com/chroma-core/chroma/issues/2675),
  [#860](https://github.com/chroma-core/chroma/issues/860).
- Deletes don't compact the graph: [#2594](https://github.com/chroma-core/chroma/issues/2594),
  [#2963](https://github.com/chroma-core/chroma/issues/2963).
- Cross-DB practice / compaction: [aimultiple benchmark](https://aimultiple.com/open-source-vector-databases),
  [InfraSketch — Vector DB System Design](https://infrasketch.net/blog/vector-database-system-design).
- Chroma 1.x architecture: [DeepWiki](https://deepwiki.com/chroma-core/chroma).
- Maintenance / no native rebuild: [Cookbook — Maintenance](https://cookbook.chromadb.dev/running/maintenance/),
  [Performance Tips](https://cookbook.chromadb.dev/running/performance-tips/),
  [chromadb-ops](https://github.com/amikos-tech/chromadb-ops).
