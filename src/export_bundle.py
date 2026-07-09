"""Bundle the built pipeline outputs into a portable zip for another machine.

The archive holds the ``outputs/`` products (corpus, embeddings, projections,
graphs, motifs) so a viewer-profile install elsewhere can serve them offline
(no GPU / internet / LLM needed), plus any local ``file:`` corpus sources under
``sources/`` (so the originals travel with the bundle and a rebuild on the
target can re-ingest them). Resumable caches and logs are excluded by default —
they are rebuild fuel, useless on the target — and added only with
``include_caches``. There is no separate import step: restore is just ``unzip``
from the project root.

The embeddings directory (ChromaDB) is copied file-for-file, so it carries
whatever the live store contains — including orphan collections of disabled
models and orphan chunks of removed texts. We don't prune inside the DB; instead
``orphan_summary`` reports them (reusing the same checks as ``mytho clean``) so
the caller can warn and suggest ``mytho clean --apply`` for a tidy bundle.
"""

from __future__ import annotations

import logging
import zipfile
from dataclasses import dataclass, field
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from pipeline_inspect import (
    GRAPHS_CACHE,
    SUMMARIES_CACHE,
    corpus_orphans,
    embeddings_orphan_chunks,
    embeddings_orphan_collections,
    graphs_orphans,
    projections_orphans,
)
from settings import settings

logger = logging.getLogger(__name__)

# Cache files that live among the products but are excluded unless --caches.
_CACHE_FILENAMES = {GRAPHS_CACHE, SUMMARIES_CACHE}
# The Berezkin/Trilogy raw scrape cache (a subdirectory of the motifs output).
_RAW_DIR_NAME = "raw"


def _components() -> list[tuple[str, Path, str]]:
    """(archive name, source dir, archive root) for each exportable component, in
    order. Most live under ``outputs/``; local ``file:`` corpus sources live under
    ``sources/`` and restore there, so they carry their own archive root."""
    return [
        ("corpus", Path(settings.corpus_dir), "outputs/corpus"),
        ("embeddings", Path(settings.embeddings_dir), "outputs/embeddings"),
        ("projections", Path(settings.projections_dir), "outputs/projections"),
        ("graphs", Path(settings.graphs_dir), "outputs/graphs"),
        ("motifs", Path(settings.motifs_dir), "outputs/motifs"),
        ("sources", Path(settings.sources_dir), "sources"),
    ]


def _is_cache(component: str, rel: Path) -> bool:
    # outputs/motifs/raw/** is the scrape cache; the jsonl files are resumable caches.
    in_raw_dir = component == "motifs" and bool(rel.parts) and rel.parts[0] == _RAW_DIR_NAME
    return rel.name in _CACHE_FILENAMES or in_raw_dir


@dataclass
class ExportResult:
    path: Path | None = None
    total_files: int = 0
    total_bytes: int = 0
    components: dict[str, int] = field(default_factory=dict)  # name -> bytes
    chromadb_version: str | None = None
    included_caches: bool = False


def chromadb_version() -> str | None:
    try:
        return version("chromadb")
    except PackageNotFoundError:
        return None


def orphan_summary() -> list[str]:
    """Human-readable lines describing orphans that an export would carry along.

    Mirrors the categories of ``mytho clean``. Each probe is guarded so a missing
    optional dependency (e.g. chromadb) or unreadable store never aborts export.
    """
    lines: list[str] = []

    def _safe(fn):
        try:
            return fn()
        except Exception as exc:  # never let orphan reporting break the export
            logger.debug("orphan probe failed: %s", exc)
            return []

    for path, _ in _safe(lambda: corpus_orphans(settings)):
        lines.append(f"corpus: orphan text {path.name}")
    for col in _safe(lambda: embeddings_orphan_collections(settings)):
        lines.append(f"embeddings: orphan collection {col['model']} ({col['count']} chunks)")
    for info in _safe(lambda: embeddings_orphan_chunks(settings)):
        lines.append(f"embeddings: orphan chunks in {info['model']} ({len(info['orphan_ids'])}/{info['total_count']})")
    for model in _safe(lambda: projections_orphans(settings)):
        lines.append(f"projections: orphan {model['name']}")
    for path, _ in _safe(lambda: graphs_orphans(settings)):
        lines.append(f"graphs: orphan directory {path.name}/")
    return lines


def export_outputs(*, include_caches: bool = False, out_dir: Path | None = None, timestamp: str = "") -> ExportResult:
    """Zip the built outputs into ``mythoscope-export-<timestamp>.zip``.

    Returns an :class:`ExportResult`; ``path`` is None when nothing is built (no
    archive is written). ``out_dir`` defaults to the current directory and
    ``timestamp`` is injected by the caller (kept out of the core for testability).
    """
    result = ExportResult(included_caches=include_caches)
    out_dir = out_dir or Path.cwd()
    archive = out_dir / f"mythoscope-export-{timestamp}.zip"

    # Gather files first so we can skip writing an empty archive.
    plan: list[tuple[Path, str, int]] = []  # (file, arcname, size)
    for name, src, arc_root in _components():
        if not src.exists():
            continue
        comp_bytes = comp_files = 0
        for file in sorted(src.rglob("*")):
            if not file.is_file():
                continue
            rel = file.relative_to(src)
            if not include_caches and _is_cache(name, rel):
                continue
            size = file.stat().st_size
            plan.append((file, (Path(arc_root) / rel).as_posix(), size))
            comp_bytes += size
            comp_files += 1
        if comp_files:
            result.components[name] = comp_bytes

    if not plan:
        return result

    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for file, arcname, _ in plan:
            zf.write(file, arcname=arcname)

    result.path = archive
    result.total_files = len(plan)
    result.total_bytes = sum(size for _, _, size in plan)
    result.chromadb_version = chromadb_version() if "embeddings" in result.components else None
    logger.info("Exported %d files (%d bytes) to %s", result.total_files, result.total_bytes, archive)
    return result
