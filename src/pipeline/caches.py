"""Reclaimable caches + size formatting — the survivors of the retired ``pipeline_inspect``.

Resumable caches (graph extraction, chunk preprocessing) are internal tiers, not driver
artifacts, so ``mytho clean --caches`` enumerates them here rather than through the stage
diff. Orphan detection itself now lives in the driver (``pipeline.driver.clean``)."""

from __future__ import annotations

from pathlib import Path

GRAPHS_CACHE = "extraction_cache.jsonl"
SUMMARIES_CACHE = "summaries.jsonl"


def dir_size(path: Path, exclude_names: tuple[str, ...] = ()) -> int:
    if not path.exists():
        return 0
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file() and f.name not in exclude_names)


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


def motifs_raw_cache(settings) -> tuple[Path, int] | None:
    """The Berezkin/Trilogy raw scrape cache as a single (dir, size), or None."""
    raw = Path(settings.motifs_dir) / "raw"
    return (raw, dir_size(raw)) if raw.exists() else None


def cache_files(settings) -> list[tuple[Path, int]]:
    """All resumable cache files (graph extraction + chunk preprocessing), with sizes.
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
