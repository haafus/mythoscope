# Dated raw-snapshot — a reproducible, citable dataset-of-record

**Status: PROPOSAL, NOT STARTED.**

Companion to [`fetch-and-refresh.md`](fetch-and-refresh.md) (how raw is acquired) and
[`pipeline-and-incrementality.md`](pipeline-and-incrementality.md) (how builds are gated). The
motif data feeds the public site's flagship crosswalk (see the citability step in
[`public-docs-plan.md`](public-docs-plan.md) §15); this proposal makes that dataset
**reproducible and citable**.

## 1. The problem (scoped precisely)

The motif indexes are built by scraping **live** external sources (areasofmyths / mapsofmyths
HTML, the folkmasa bibliography, Wikidata SPARQL). The scraped bytes are cached under
`outputs/motifs/raw/**` at `sha1(url)` (`fetch_cache.py`).

Two facts bound the problem:

- **The build is deterministic given a fixed cache.** `mytho build motifs` re-parses the
  existing cache and never touches the network; `MYTHO_OFFLINE` even makes a rebuild "a pure
  function of the pinned cache" (`fetch_cache.py`). So the non-determinism is **only** in the
  fetch step (`refresh --apply` re-scrapes).
- **The cache is sticky, not fresh.** `build` reuses whatever was last scraped; re-fetching is
  human-gated. So in practice you are pinned to your last scrape — but the cache is **not
  labelled, versioned, or archived**.

What that costs:

1. **Non-reproducibility.** After a `refresh --apply`, nobody can reproduce an earlier build —
   different day / machine ⇒ different motifs, counts, crosswalk edges. No canonical version.
2. **Non-citability / non-archivability** (the one that matters for an academic project). You
   cannot hand a reviewer *exactly* the data behind a published number (e.g. "7,297 cross-index
   edges") — they re-scrape and get their own.
3. **Drift indistinguishable from regression.** A smaller fresh scrape could be legitimate
   upstream change *or* a fetch/parse bug; with no pinned baseline you cannot tell. (Partly
   mitigated by validate-before-commit + `.discovered` shrink flags in
   `motifs-fetch-stabilization.md`, but that is a guard, not a baseline.)
4. **Durability / data-loss risk.** The cache is gitignored and regenerated. If upstream edits
   or dies and the local cache is cleared, that version is **unrecoverable** — the only copy of
   "the data as it was" is an ephemeral, untracked directory.

**Root cause:** the raw inputs are not versioned. Some sources have *no* upstream version to pin
(live HTML, SPARQL), so the only achievable pin is **archiving the fetched bytes** — the bytes
*are* the version.

## 2. Current state (what already helps)

- `MYTHO_OFFLINE` ⇒ deterministic rebuild from a frozen cache (the reproducibility engine
  already exists — it just needs a dated, durable cache to point at).
- `mytho export --caches` ⇒ ships the `raw/**` snapshot (excluded by default).
- `.discovered` sidecars ⇒ shrink detection per parse-root (`build_motifs.py`).
- `raw_fetched_at` in `outputs/motifs/meta.json` (2026-07) ⇒ an **approximate** "data last
  refreshed" stamp: the newest filesystem mtime across the raw cache. Cheap and visible, but
  mtime is reset by an export→restore, so it is not the durable, content-addressed provenance
  §3.1 provides — it closes the "when roughly?" gap, not the reproducibility one.
- Missing: any **content hash, snapshot manifest, snapshot id, or durable archive**.

> **Operational caveat (until this lands).** The raw cache is a point-in-time snapshot, not a
> versioned dataset — a `refresh --apply` can return different counts, and two machines scraping
> on different days may disagree. So **every motif / type / tradition count in the docs is an
> approximate snapshot of one build**; re-verify against a fresh build before quoting it. Only
> code is committed — the built indexes and the raw cache are regenerated, not tracked (ship a
> working dataset with `mytho export`, adding `--caches` for the raw scrape). This is *by design*,
> not a bug: it is the gap this proposal closes.

## 3. Design — five pieces

Cheap-to-add provenance (1–3), then the load-bearing durability (4), plus an optional baseline
(5).

### 3.1 Capture provenance (per source, at fetch time)
On each successful `commit_bytes` / fetch, record `{url, fetched_at (UTC ISO-8601),
content_sha256, http_etag, http_last_modified}`. Store as a small sidecar next to each cache
file (`<sha1(url)>.meta.json`) or accumulate into the manifest below. Today the cache stores
only bytes; nothing is dated.

### 3.2 Snapshot manifest + id
On `refresh --apply` (or an explicit `mytho snapshot` command), aggregate all sources'
provenance into one dated manifest, e.g. `outputs/motifs/raw/_snapshot.json`:
```json
{ "snapshot_id": "2026-07-28.ab12cd34",
  "created_at": "2026-07-28T09:00:00Z",
  "sources": { "<url>": {"fetched_at": "...", "sha256": "...", "bytes": 12345}, ... } }
```
`snapshot_id = <date>.<short aggregate hash over the per-source sha256s>` — stable, orderable,
content-addressed.

### 3.3 Stamp the built indexes
Write `raw_snapshot: <snapshot_id>` into `outputs/motifs/meta.json`, so every built index (and
the crosswalk) is **attributable** to a snapshot and any quoted count reads "as of snapshot X".

### 3.4 Durable archival (the crux)
The snapshot must survive a cache-clear and upstream change, so persist it immutably. Options:

| Option | Pros | Cons |
|---|---|---|
| **git-LFS** in-repo | one repo, versioned with code, simple | LFS quota/bandwidth; repo bloat over snapshots |
| **GitHub Release asset** (zipped snapshot per version) | out of git history, big-file friendly, tagged | manual-ish; not content-addressed by default |
| **Zenodo deposit + DOI** | **citable (DOI)**, archival guarantee, fits §15 | external step; per-version DOI curation |

**Recommendation:** Zenodo deposit **for tagged releases** (each gets a DOI — directly powers
the citability step in `public-docs-plan.md` §15), with a GitHub Release asset as the working
mirror; git-LFS only if an in-repo copy is wanted. Day-to-day snapshots stay in `outputs/`
(gitignored); a *release* snapshot is the archived dataset-of-record.

### 3.5 (Optional) previous-snapshot diff
Retain the prior `_snapshot.json` and emit a structured diff on `refresh` (added / removed /
changed sources + count deltas) — turns "drift vs regression" from a judgement call into a
reviewable report. Extends, not replaces, the existing shrink flags.

## 4. Reproduce-a-build flow (the payoff)
```
mytho snapshot fetch     # refresh --apply + write _snapshot.json (dated, hashed)
mytho snapshot archive   # zip raw/** + _snapshot.json → release asset / Zenodo (DOI)
# anyone, later:
mytho snapshot restore <id|doi>   # download + unzip into outputs/motifs/raw
MYTHO_OFFLINE=1 mytho build motifs # deterministic rebuild == the archived dataset
```

## 5. Scope, non-goals, effort
- **In:** provenance capture, manifest+id, meta stamp, an archive/restore path, optional diff.
- **Non-goals:** pinning upstream *source* versions (impossible for live HTML/SPARQL — we pin
  bytes); changing the fetch/refresh atomicity model (that stays as in `fetch-and-refresh.md`);
  the corpus raw (Gutenberg is already stable/versioned — this is motif-scrape-specific,
  though the same manifest shape could later cover corpus raw).
- **Effort:** 3.1–3.3 are small and additive (metadata only, no fp change → no rebuild). 3.4 is
  the real work (an archive/restore command + a hosting choice). 3.5 is optional.
- **Migration:** additive; existing caches simply lack `_snapshot.json` until the next
  `refresh` writes one. No rebuild forced.

## 6. Checklist (when we return)
- [ ] `fetch_cache.commit_bytes`: write a per-file `.meta.json` (url, fetched_at, sha256, etag).
- [ ] `mytho snapshot` command: `fetch` / `archive` / `restore` (+ manifest + id).
- [ ] Stamp `raw_snapshot` into `outputs/motifs/meta.json` at build.
- [ ] Pick + wire the archive target (Zenodo/Release/LFS); document the DOI flow (§15).
- [ ] (opt) `refresh` prints a snapshot diff vs the previous manifest.
- [ ] Tests: manifest id is content-addressed & stable; `restore` + `MYTHO_OFFLINE` build is
      byte-identical to the archived build; missing manifest → no rebuild (fallback).
