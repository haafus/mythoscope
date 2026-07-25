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

from pipeline.caches import GRAPHS_CACHE, SUMMARIES_CACHE
from settings import settings

logger = logging.getLogger(__name__)

# Cache files that live among the products but are excluded unless --caches.
_CACHE_FILENAMES = {GRAPHS_CACHE, SUMMARIES_CACHE}
# The Berezkin/Trilogy raw scrape cache (a subdirectory of the motifs output).
_RAW_DIR_NAME = "raw"


def _components(scope=None) -> list[tuple[str, Path, str]]:
    """(archive name, source dir, archive root) for each exportable component, in
    order. Most live under ``outputs/``; local ``file:`` corpus sources live under
    ``sources/`` and restore there, so they carry their own archive root.

    ``scope`` (stage names, e.g. ``graphs`` or ``embeddings:bge-m3``) keeps only the matching
    components by family (the part before ``:``) — bundle just the named stage(s)."""
    comps = [
        ("corpus", Path(settings.corpus_dir), "outputs/corpus"),
        ("embeddings", Path(settings.embeddings_dir), "outputs/embeddings"),
        ("projections", Path(settings.projections_dir), "outputs/projections"),
        ("graphs", Path(settings.graphs_dir), "outputs/graphs"),
        ("motifs", Path(settings.motifs_dir), "outputs/motifs"),
        ("sources", Path(settings.sources_dir), "sources"),
    ]
    if scope:
        valid = {c[0] for c in comps}
        families = {s.split(":", 1)[0] for s in scope}
        unknown = families - valid
        if unknown:   # a typo → error cleanly, like build/clean, not a silent empty bundle
            raise ValueError(f"not an exportable component: {sorted(unknown)} — choose {sorted(valid)}")
        comps = [c for c in comps if c[0] in families]
    return comps


def _is_staging(rel: Path) -> bool:
    """Validate-before-commit staging files (``.partial``/``.tmp``) — normally consumed by
    ``os.replace``, but a crash mid-write can leave one behind. Crash debris, never a product:
    excluded from EVERY bundle, including ``--caches`` (unlike the raw/cache tiers)."""
    return rel.suffix in (".partial", ".tmp")


def _is_cache(component: str, rel: Path) -> bool:
    # The pinned raw scrape caches — corpus web downloads (outputs/corpus/raw/**) and the motif
    # sources (outputs/motifs/raw/**) — plus the resumable jsonl caches, are the "raw/cache tier":
    # shipped only with --caches. (`sources/` local file: originals ship always — re-ingest needs
    # them; staging debris is handled by _is_staging.)
    in_raw_dir = component in ("corpus", "motifs") and bool(rel.parts) and rel.parts[0] == _RAW_DIR_NAME
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


def orphan_summary(scope=None) -> list[str]:
    """Human-readable lines describing orphans that an export would carry along — the driver's
    dry-run reap (same categories as ``mytho clean``). Guarded so a missing optional dependency
    (e.g. chromadb) or unreadable store never aborts the export. ``scope`` restricts the
    level-1 report to the named stage families (level-2 store orphans span stages, so they are
    reported only for an unscoped export)."""
    try:
        from pipeline import build_pipeline
        from pipeline import clean as driver_clean

        report = driver_clean(build_pipeline(), apply=False)
    except Exception as exc:  # never let orphan reporting break the export
        logger.debug("orphan probe failed: %s", exc)
        return []

    families = {s.split(":", 1)[0] for s in scope} if scope else None
    lines: list[str] = []
    for stage, keys in report.level1.items():
        if families is not None and stage.split(":", 1)[0] not in families:
            continue
        for key in sorted(keys):
            lines.append(f"{stage}: orphan document {key}")
    if families is None:
        for store, ids in report.level2.items():
            for artifact_id in sorted(ids):
                lines.append(f"{store}: orphan artifact {artifact_id}")
    return lines


def export_outputs(*, scope=None, include_caches: bool = False, out_dir: Path | None = None, timestamp: str = "") -> ExportResult:
    """Zip the built outputs into ``mythoscope-<timestamp>.zip`` (``mythoscope-caches-<timestamp>.zip``
    when ``include_caches`` — the ``-caches`` tag marks a bundle that carries the raw/cache tiers).

    Returns an :class:`ExportResult`; ``path`` is None when nothing is built (no
    archive is written). ``out_dir`` defaults to the current directory and
    ``timestamp`` is injected by the caller (kept out of the core for testability).
    """
    result = ExportResult(included_caches=include_caches)
    out_dir = out_dir or Path.cwd()
    tag = "-caches" if include_caches else ""
    archive = out_dir / f"mythoscope{tag}-{timestamp}.zip"

    # Gather files first so we can skip writing an empty archive.
    plan: list[tuple[Path, str, int]] = []  # (file, arcname, size)
    for name, src, arc_root in _components(scope):
        if not src.exists():
            continue
        comp_bytes = comp_files = 0
        for file in sorted(src.rglob("*")):
            if not file.is_file():
                continue
            rel = file.relative_to(src)
            if _is_staging(rel):
                continue   # crash debris — never ship, even with --caches
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
