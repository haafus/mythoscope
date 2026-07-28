#!/usr/bin/env python3
"""Validate the integrity of the embeddings (Chroma) collections.

Diagnoses the class of bug where a scatter click on one chunk surfaced a *different*
chunk (e.g. "Popol Vuh #76" showed "Ramayan #1709"): that happens when a Chroma row's
**id disagrees with its own metadata**, so `collection.get(ids=["<doc>::76"])` returns
another document's row. This script checks every collection for:

  * **id <-> metadata** — every id must equal ``chunk_id(meta.document_id, meta.chunk_index)``.
    A mismatch is the smoking gun for the click-shows-wrong-chunk bug.
  * **orphans** — a chunk whose ``document_id`` is not in the corpus catalog (a removed/
    renamed book left behind; surfaces in search with an unresolvable id).
  * **n_chunks / contiguity** — per document, the stored ``n_chunks`` matches the real
    chunk count and the chunk indices are a contiguous 0..N-1 (no holes/dupes).
  * **self-query** (optional, ``--self-query N``) — a chunk's own embedding must rank the
    chunk itself first. If not, the stored id/vector are out of sync (an HNSW-vs-store
    drift), which is what made the click return a neighbour instead of the point.

Focused mode reproduces one report directly:
    python scripts/validate_chroma.py bge-m3 --title "The Popol Vuh" --chunk 76

Full sweep (all collections), non-zero exit if any inconsistency is found:
    python scripts/validate_chroma.py

Run from the repo root; needs a built Chroma DB under ``outputs/embeddings/``.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import json  # noqa: E402

from corpus.utils import chunk_id  # noqa: E402
from embeddings import chroma_manager  # noqa: E402
from settings import settings  # noqa: E402


def _load_catalog() -> dict[str, dict]:
    """{document_id -> {title, tradition}} from the built corpus catalog (for orphan + title lookup)."""
    path = Path(settings.corpus_dir) / "corpus.json"
    if not path.exists():
        return {}
    out: dict[str, dict] = {}
    for row in json.loads(path.read_text(encoding="utf-8")):
        did = row.get("document_id")
        if did:
            out[did] = {"title": row.get("title", ""), "tradition": row.get("tradition", "")}
    return out


def _doc_id_for_title(catalog: dict[str, dict], title: str) -> str | None:
    for did, row in catalog.items():
        if row.get("title") == title:
            return did
    return None


def _label(catalog: dict[str, dict], document_id: str) -> str:
    row = catalog.get(document_id)
    return f"{row['title']} ({row['tradition']})" if row else f"<not in corpus: {document_id}>"


# --------------------------------------------------------------------------- full sweep


def validate_collection(coll, catalog: dict[str, dict], *, self_query: int, limit: int) -> int:
    """Check one collection; print findings; return the number of problems found."""
    name = coll.name
    got = coll.get(include=["metadatas", "documents"])
    ids = got.get("ids") or []
    metas = got.get("metadatas") or []
    print(f"\n=== {name}: {len(ids)} chunks ===")

    id_mismatch: list[tuple[str, str]] = []   # (stored id, id its metadata implies)
    orphans: list[str] = []                   # ids whose document_id is not in the corpus
    by_doc: dict[str, list[dict]] = defaultdict(list)

    for cid, meta in zip(ids, metas, strict=False):
        meta = meta or {}
        did = meta.get("document_id")
        cidx = meta.get("chunk_index")
        if did is None or cidx is None:
            id_mismatch.append((cid, "<missing document_id/chunk_index in metadata>"))
            continue
        expected = chunk_id(did, cidx)
        if expected != cid:
            id_mismatch.append((cid, expected))
        if did not in catalog:
            orphans.append(cid)
        by_doc[did].append(meta)

    # n_chunks + contiguity per document
    chunk_gaps: list[str] = []
    n_chunks_bad: list[str] = []
    for did, ms in by_doc.items():
        idxs = sorted(m.get("chunk_index") for m in ms if m.get("chunk_index") is not None)
        if idxs and idxs != list(range(len(idxs))):
            chunk_gaps.append(f"{_label(catalog, did)}: indices {idxs[:8]}{'…' if len(idxs) > 8 else ''} "
                              f"(count {len(idxs)}, not a contiguous 0..{len(idxs) - 1})")
        stored = {m.get("n_chunks") for m in ms if m.get("n_chunks") is not None}
        if stored and stored != {len(ms)}:
            n_chunks_bad.append(f"{_label(catalog, did)}: stored n_chunks {sorted(stored)} != actual {len(ms)}")

    def _report(title: str, items, fmt) -> int:
        if not items:
            print(f"  OK   {title}")
            return 0
        print(f"  FAIL {title}: {len(items)}")
        for it in items[:limit]:
            print(f"        - {fmt(it)}")
        if len(items) > limit:
            print(f"        … and {len(items) - limit} more")
        return len(items)

    problems = 0
    problems += _report("id <-> metadata consistent", id_mismatch,
                        lambda t: f"id {t[0]!r} but metadata implies {t[1]!r}")
    problems += _report("no orphan document_ids", orphans,
                        lambda cid: f"{cid!r} -> document not in corpus catalog")
    problems += _report("chunk indices contiguous", chunk_gaps, lambda s: s)
    problems += _report("stored n_chunks matches actual", n_chunks_bad, lambda s: s)

    if self_query:
        problems += _self_query_check(coll, ids, min(self_query, len(ids)))
    return problems


def _self_query_check(coll, ids: list[str], sample: int) -> int:
    """For a sample of chunks: the chunk's own embedding must rank the chunk itself first."""
    import random  # local: not needed for the main sweep

    picks = ids if sample >= len(ids) else random.sample(ids, sample)
    bad = []
    for cid in picks:
        one = coll.get(ids=[cid], include=["embeddings"])
        embs = one.get("embeddings")
        if embs is None or len(embs) == 0:
            continue
        res = coll.query(query_embeddings=[embs[0]], n_results=1, include=["metadatas"])
        top = (res.get("ids") or [[None]])[0][0]
        if top != cid:
            bad.append((cid, top))
    if not bad:
        print(f"  OK   self-query returns self first ({len(picks)} sampled)")
        return 0
    print(f"  FAIL self-query returns a different chunk first ({len(picks)} sampled): {len(bad)}")
    for cid, top in bad[:10]:
        print(f"        - {cid!r} -> nearest is {top!r} (not itself)")
    return len(bad)


# --------------------------------------------------------------------------- focused mode


def focus(coll, catalog: dict[str, dict], document_id: str, chunk_index: int) -> int:
    """Reproduce a single report: fetch <document_id>::<chunk_index> and show what Chroma stores."""
    cid = chunk_id(document_id, chunk_index)
    print(f"\n=== {coll.name}: get(ids=[{cid!r}]) ===")
    print(f"  requested: {_label(catalog, document_id)}  chunk {chunk_index}")
    got = coll.get(ids=[cid], include=["metadatas", "documents", "embeddings"])
    if not (got.get("ids") or []):
        print("  RESULT: id NOT FOUND in the collection (nothing would render).")
        return 1
    meta = (got["metadatas"] or [{}])[0] or {}
    doc = (got.get("documents") or [""])[0] or ""
    stored_did = meta.get("document_id")
    stored_idx = meta.get("chunk_index")
    print(f"  stored metadata: document_id={stored_did!r} chunk_index={stored_idx!r} "
          f"-> {_label(catalog, stored_did)}")
    print(f"  text[:160]: {doc[:160]!r}")

    problems = 0
    if chunk_id(stored_did, stored_idx) != cid:
        print("  ✗ MISMATCH: the id does not match its own metadata — this id resolves to the WRONG chunk.")
        problems += 1
    else:
        print("  ✓ id matches its metadata.")

    embs = got.get("embeddings")
    if embs is not None and len(embs):
        res = coll.query(query_embeddings=[embs[0]], n_results=3, include=["metadatas"])
        print("  self-query (this chunk's own embedding), nearest 3:")
        for rid, rmeta in zip((res.get("ids") or [[]])[0], (res.get("metadatas") or [[]])[0], strict=False):
            rmeta = rmeta or {}
            print(f"        {rid!r}  -> {_label(catalog, rmeta.get('document_id'))} chunk {rmeta.get('chunk_index')}")
        top = (res.get("ids") or [[None]])[0][0]
        if top != cid:
            print("  ✗ self-query does NOT return this chunk first — stored id/vector are out of sync.")
            problems += 1
        else:
            print("  ✓ self-query returns this chunk first.")
    return problems


# --------------------------------------------------------------------------- entry point


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("collection", nargs="?", help="Model/variant key (a Chroma collection). Default: all.")
    ap.add_argument("--title", help="Focused mode: resolve this book title to a document_id (needs the catalog).")
    ap.add_argument("--doc", help="Focused mode: check this document_id directly.")
    ap.add_argument("--chunk", type=int, help="Focused mode: the chunk_index to inspect (with --title/--doc).")
    ap.add_argument("--self-query", type=int, default=0, metavar="N",
                    help="Also self-query N random chunks per collection (0 = skip; heavier, loads embeddings).")
    ap.add_argument("--limit", type=int, default=10, help="Max example issues to print per check.")
    args = ap.parse_args()

    catalog = _load_catalog()
    if not catalog:
        print("[warn] no corpus catalog (outputs/corpus/corpus.json) — orphan/title checks limited.")

    try:
        colls = ([chroma_manager.get_collection(args.collection)] if args.collection
                 else chroma_manager.list_collections())
    except Exception as e:
        print(f"[fail] could not open collection(s): {e}")
        return 2
    if not colls:
        print("[fail] no Chroma collections found (is the DB built under outputs/embeddings/?).")
        return 2

    # Focused mode
    if args.chunk is not None or args.title or args.doc:
        document_id = args.doc or (_doc_id_for_title(catalog, args.title) if args.title else None)
        if not document_id:
            print(f"[fail] could not resolve a document_id (title={args.title!r}, doc={args.doc!r}).")
            return 2
        if args.chunk is None:
            print("[fail] focused mode needs --chunk N.")
            return 2
        problems = sum(focus(c, catalog, document_id, args.chunk) for c in colls)
        print(f"\n{'PROBLEMS FOUND' if problems else 'OK'} ({problems}).")
        return 1 if problems else 0

    # Full sweep
    total = sum(validate_collection(c, catalog, self_query=args.self_query, limit=args.limit) for c in colls)
    print(f"\n{'=' * 40}\n{'PROBLEMS FOUND: ' + str(total) if total else 'ALL CHECKS PASSED'}")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
