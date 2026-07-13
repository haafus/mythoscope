"""Shared logic for `mytho status` and `mytho clean`."""

import json
import logging
from pathlib import Path
from typing import Any

from graphs.completion import is_book_complete
from projections import PROJECTION_KEYS

logger = logging.getLogger(__name__)

GRAPHS_CACHE = "extraction_cache.jsonl"
SUMMARIES_CACHE = "summaries.jsonl"


# ---------------------------------------------------------------------------
# Size helpers
# ---------------------------------------------------------------------------

def dir_size(path: Path, exclude_names: tuple[str, ...] = ()) -> int:
    if not path.exists():
        return 0
    return sum(
        f.stat().st_size
        for f in path.rglob("*")
        if f.is_file() and f.name not in exclude_names
    )


def file_size(path: Path) -> int:
    return path.stat().st_size if path.exists() else 0


def format_size(nbytes: int) -> str:
    if nbytes < 1024:
        return f"{nbytes} B"
    for unit in ("KB", "MB", "GB"):
        nbytes /= 1024
        if nbytes < 1024:
            return f"{nbytes:.1f} {unit}"
    return f"{nbytes:.1f} GB"


# ---------------------------------------------------------------------------
# Corpus inspection
# ---------------------------------------------------------------------------

def _read_corpus_config(settings) -> int:
    config_path = settings.config_dir / "corpus.json"
    if not config_path.exists():
        return 0
    return len(json.loads(config_path.read_text(encoding="utf-8")))


def _read_corpus_metadata(settings) -> list[dict]:
    meta_path = settings.corpus_dir / "corpus.json"
    if not meta_path.exists():
        return []
    return json.loads(meta_path.read_text(encoding="utf-8"))


def corpus_status(settings) -> dict[str, Any]:
    config_count = _read_corpus_config(settings)
    meta_entries = _read_corpus_metadata(settings)

    known_paths: set[str] = set()
    corpus_dir = Path(settings.corpus_dir)
    for entry in meta_entries:
        rel = entry.get("path")
        if rel:
            known_paths.add(str((corpus_dir / rel).resolve()))

    total_size = dir_size(corpus_dir)

    return {
        "config_count": config_count,
        "built_count": len(meta_entries),
        "missing_count": max(0, config_count - len(meta_entries)),
        "known_paths": known_paths,
        "corpus_dir": corpus_dir,
        "total_size": total_size,
    }


def corpus_orphans(settings) -> list[tuple[Path, int]]:
    if not (settings.corpus_dir / "corpus.json").exists():
        return []

    info = corpus_status(settings)
    corpus_dir: Path = info["corpus_dir"]
    known: set[str] = info["known_paths"]

    orphans = []
    for txt in corpus_dir.rglob("*.txt"):
        if str(txt.resolve()) not in known:
            orphans.append((txt, file_size(txt)))
    return orphans


# ---------------------------------------------------------------------------
# Embeddings inspection
# ---------------------------------------------------------------------------

def embeddings_status(settings) -> dict[str, Any]:
    chroma_path = Path(settings.embeddings_dir)
    result: dict[str, Any] = {
        "exists": chroma_path.exists(),
        "total_size": dir_size(chroma_path),
        "collections": [],
    }
    if not chroma_path.exists():
        return result

    try:
        from embeddings import chroma_manager

        for col in chroma_manager.list_collections():
            result["collections"].append({
                "name": col.name,
                "model": (col.metadata or {}).get("model", col.name),
                "count": col.count(),
            })
    except Exception as e:
        result["error"] = str(e)

    return result


def embeddings_orphan_collections(settings) -> list[dict[str, Any]]:
    from model_registry import embedding_variants

    info = embeddings_status(settings)
    if not info["exists"]:
        return []

    known_keys = set(embedding_variants(include_inactive=True))

    return [c for c in info["collections"] if c["name"] not in known_keys]


def embeddings_orphan_chunks(settings, *, skip_collections: set[str] | None = None) -> list[dict[str, Any]]:
    from corpus.utils import normalize_catalog_id

    chroma_path = Path(settings.embeddings_dir)
    if not chroma_path.exists():
        return []

    if skip_collections is None:
        skip_collections = {c["name"] for c in embeddings_orphan_collections(settings)}

    meta_entries = _read_corpus_metadata(settings)
    if not meta_entries:
        return []

    known_text_ids = {normalize_catalog_id(e["title"]) for e in meta_entries if e.get("title")}
    results = []
    try:
        from embeddings import chroma_manager

        for col in chroma_manager.list_collections():
            if col.name in skip_collections:
                continue
            all_meta = col.get(include=["metadatas"])
            orphan_ids = []
            for doc_id, meta in zip(all_meta["ids"], all_meta["metadatas"], strict=True):
                text_id = (meta or {}).get("text_id")
                if text_id and text_id not in known_text_ids:
                    orphan_ids.append(doc_id)
            if orphan_ids:
                model = (col.metadata or {}).get("model", col.name)
                results.append({
                    "collection": col.name,
                    "model": model,
                    "orphan_ids": orphan_ids,
                    "total_count": col.count(),
                })
    except Exception:
        logger.exception("Failed to scan chroma for orphan chunks")

    return results


# ---------------------------------------------------------------------------
# Projections inspection
# ---------------------------------------------------------------------------

PROJECTION_PLOTS = [f"{m}.json" for m in sorted(PROJECTION_KEYS)]


def projections_status(settings) -> dict[str, Any]:
    proj_dir = Path(settings.projections_dir)
    result: dict[str, Any] = {
        "exists": proj_dir.exists(),
        "total_size": dir_size(proj_dir, exclude_names=(SUMMARIES_CACHE,)),
        "models": [],
    }
    if not proj_dir.exists():
        return result

    for model_dir in sorted(d for d in proj_dir.iterdir() if d.is_dir()):
        existing = [p for p in PROJECTION_PLOTS if (model_dir / p).exists()]
        result["models"].append({
            "name": model_dir.name,
            "path": model_dir,
            "plots_done": len(existing),
            "plots_total": len(PROJECTION_PLOTS),
            "size": dir_size(model_dir, exclude_names=(SUMMARIES_CACHE,)),
        })

    return result


def projections_orphans(settings) -> list[dict[str, Any]]:
    info = projections_status(settings)
    if not info["exists"] or not info["models"]:
        return []

    emb_info = embeddings_status(settings)
    if "error" in emb_info:
        return []

    known_dirs = {c["name"] for c in emb_info["collections"]}

    return [m for m in info["models"] if m["name"] not in known_dirs]


# ---------------------------------------------------------------------------
# Graphs inspection
# ---------------------------------------------------------------------------

def graphs_status(settings) -> dict[str, Any]:
    graphs_dir = Path(settings.graphs_dir)
    result: dict[str, Any] = {
        "exists": graphs_dir.exists(),
        "total_size": dir_size(graphs_dir, exclude_names=(GRAPHS_CACHE,)),
        "count": 0,
    }
    if not graphs_dir.exists():
        return result

    complete = [d for d in graphs_dir.iterdir() if d.is_dir() and is_book_complete(d)]
    html_files = list(graphs_dir.glob("*.html"))
    result["count"] = len(complete) + len(html_files)
    return result


def graphs_orphans(settings) -> list[tuple[Path, int]]:
    """Find orphan graph directories in graphs_dir.

    Matches subdirectory names against normalized text_ids from corpus.
    If corpus metadata is missing, returns [] (can't determine orphans).
    """
    from corpus.utils import normalize_catalog_id

    graphs_dir = Path(settings.graphs_dir)
    if not graphs_dir.exists():
        return []

    meta_entries = _read_corpus_metadata(settings)
    if not meta_entries:
        return []

    known_text_ids = {normalize_catalog_id(e["title"]) for e in meta_entries if e.get("title")}

    subdirs = [d for d in graphs_dir.iterdir() if d.is_dir()]

    orphans = []
    for item in subdirs:
        if item.name not in known_text_ids:
            orphans.append((item, dir_size(item)))

    return orphans


# ---------------------------------------------------------------------------
# Motifs inspection
# ---------------------------------------------------------------------------

def motifs_status(settings) -> dict[str, Any]:
    motifs_dir = Path(settings.motifs_dir)
    meta_path = motifs_dir / "meta.json"
    # Built artifacts are the top-level JSON files; the raw scrape cache is
    # reported separately (and only removed via `clean --caches`).
    built_size = sum(file_size(p) for p in motifs_dir.glob("*.json")) if motifs_dir.exists() else 0
    result: dict[str, Any] = {
        "exists": motifs_dir.exists(),
        "built": meta_path.exists(),
        "total_size": built_size,
        "counts": {},
    }
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        result["counts"] = meta.get("counts", {})
        result["built_at"] = meta.get("built_at", "")
        result["enrichment"] = meta.get("enrichment", {})
    return result


def motifs_raw_cache(settings) -> tuple[Path, int] | None:
    """The Berezkin/Trilogy raw scrape cache as a single (dir, size), or None."""
    raw = Path(settings.motifs_dir) / "raw"
    if not raw.exists():
        return None
    return (raw, dir_size(raw))


# ---------------------------------------------------------------------------
# Resumable caches (graphs extraction + chunk preprocessing)
# ---------------------------------------------------------------------------

def cache_files(settings) -> list[tuple[Path, int]]:
    """All resumable cache files (graphs extraction + chunk preprocessing), with sizes.
    Also sweeps the pre-redesign ``summaries.jsonl`` files if any remain."""
    result: list[tuple[Path, int]] = []
    for base, pattern in (
        (Path(settings.graphs_dir), GRAPHS_CACHE),
        (Path(settings.preprocessed_dir), "*.jsonl"),
        (Path(settings.projections_dir), SUMMARIES_CACHE),
    ):
        if base.exists():
            result.extend((p, file_size(p)) for p in base.rglob(pattern))
    return result
