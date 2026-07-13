import logging
import sys
import time
from datetime import datetime, timedelta

import click

from log_setup import setup_logging
from pipeline_inspect import format_size

logger = logging.getLogger(__name__)

COMMAND_SECTIONS = [
    ("Pipeline", ["corpus", "embeddings", "projections", "graphs", "motifs"]),
    ("Management", ["build", "status", "clean", "export", "server"]),
]

# Number of texts processed by `build --sample` (quick smoke run).
SAMPLE_MAX_TEXTS = 2


class OrderedGroup(click.Group):
    def format_help(self, ctx, formatter):
        super().format_help(ctx, formatter)
        formatter.write("\nRun 'mytho COMMAND --help' for details on a specific command.\n")

    def format_commands(self, ctx, formatter):
        for label, names in COMMAND_SECTIONS:
            rows = []
            for name in names:
                if name in self.commands:
                    help_text = self.commands[name].get_short_help_str(limit=formatter.width)
                    rows.append((name, help_text or ""))
            if rows:
                with formatter.section(label):
                    formatter.write_dl(rows)


@click.group(cls=OrderedGroup)
@click.version_option(package_name="mythoscope", prog_name="MythoScope")
def mytho():
    """MythoScope — computational framework for comparative mythology."""
    setup_logging()


def _fmt_elapsed(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    return str(timedelta(seconds=round(seconds)))


def _fail(name: str, error: Exception) -> None:
    """Report a failed step on stderr and exit non-zero (no bare traceback)."""
    click.echo(click.style(f"[fail]  {name}: {error}", fg="red"), err=True)
    sys.exit(1)


def _run(name: str, fn, /, **kwargs) -> None:
    """Run a pipeline step with timing; on failure report cleanly and exit non-zero."""
    click.echo(click.style(f"[start] {name}", fg="cyan", bold=True))
    start = time.monotonic()
    try:
        fn(**kwargs)
    except Exception as e:
        _fail(name, e)
    click.echo(click.style(f"[done]  {name}", fg="green") + f" ({_fmt_elapsed(time.monotonic() - start)})")


@mytho.command()
@click.option("--force", "-f", is_flag=True, help="Overwrite existing files.")
def corpus(force: bool):
    """Download and build the text corpus."""
    _run("Corpus", _build_corpus, force=force)


@mytho.command()
@click.option("--model", "-m", default=None, help="Embedding model to use.")
@click.option("--force", "-f", is_flag=True, help="Regenerate even if collection exists.")
def embeddings(model: str | None, force: bool):
    """Generate embeddings for the corpus."""
    _run("Embeddings", _build_embeddings, model=model, force=force)


@mytho.command()
@click.option("--model", "-m", default=None, help="Embedding variant key (all variants if omitted).")
@click.option("--force", "-f", is_flag=True, help="Regenerate all plots even if they already exist.")
def projections(model: str | None, force: bool):
    """Generate UMAP projections and embedding visualizations."""
    _run("Projections", _build_projections, model=model, force=force)


@mytho.command()
@click.option("--force", "-f", is_flag=True, help="Re-extract from scratch (clear caches); default rebuilds from cache.")
def graphs(force: bool):
    """Extract knowledge graphs from corpus texts using an LLM."""
    _run("Graphs", _build_graphs, force=force)


@mytho.command()
@click.option("--force", "-f", is_flag=True, help="Re-fetch all sources before rebuilding (default reuses the cache).")
def motifs(force: bool):
    """Build the cross-referenced motif database (Berezkin, TMI, ATU)."""
    _run("Motifs", _build_motifs, force=force)


@mytho.command()
@click.option("--host", "-h", default=None, help="Bind address (default from config).")
@click.option("--port", "-p", default=None, type=int, help="Port (default from config).")
def server(host: str | None, port: int | None):
    """Start the web UI server."""
    from server.run_server import run_server

    run_server(host, port)


@mytho.command()
@click.option("--model", "-m", default=None, help="Embedding model (default from config).")
@click.option("--force", "-f", is_flag=True, help="Force regeneration of all steps.")
@click.option("--sample", "-s", is_flag=False, flag_value=str(SAMPLE_MAX_TEXTS), default=None,
              type=int, metavar="N",
              help=f"Quick run: first embedding model, limited to N texts "
                   f"(default {SAMPLE_MAX_TEXTS} when given bare, e.g. -s 50 for more).")
def build(model, force, sample):
    """Run the full analysis pipeline end-to-end."""
    if sample is not None:
        from model_registry import embedding_variants
        from settings import settings
        model = model or embedding_variants()[0]
        max_texts = sample
        # Keep the motif scrape light on a smoke run: only the sampled detail pages.
        settings.motifs.max_motifs = max_texts
        click.echo(click.style(f"[sample] model={model}, max_texts={max_texts}", fg="yellow"))
    else:
        max_texts = None

    steps = [
        ("Corpus", _build_corpus, {"force": force, "max_texts": max_texts}),
        ("Embeddings", _build_embeddings, {"model": model, "force": force}),
        ("Projections", _build_projections, {"model": model, "force": force}),
        ("Graphs", _build_graphs, {"force": force, "max_texts": max_texts}),
        ("Motifs", _build_motifs, {"force": force}),
    ]

    start_all = time.monotonic()
    for name, fn, kwargs in steps:
        _run(name, fn, **kwargs)

    total = time.monotonic() - start_all
    click.echo(click.style("\nBuild finished.", fg="green", bold=True) + f" ({_fmt_elapsed(total)})")


def _build_corpus(force: bool = False, max_texts: int | None = None):
    from corpus.builder import build_corpus

    build_corpus(force=force, max_texts=max_texts)


def _build_embeddings(model: str | None, force: bool = False):
    # Announce the heavy first-time import so the pause before model load isn't silent.
    logger.info("Loading ML libraries (torch, transformers, chromadb)...")
    from embeddings.build_embeddings import build_embeddings

    build_embeddings(model_name=model, force=force)


def _build_projections(model: str | None, force: bool = False):
    logger.info("Loading ML libraries (torch, umap, chromadb)...")
    from projections.build_projections import build_projections

    build_projections(model_name=model, force=force)


def _build_graphs(force: bool = False, max_texts: int | None = None):
    logger.info("Loading graph libraries...")
    from graphs.build_graphs import build_graphs

    build_graphs(force=force, max_texts=max_texts)


def _build_motifs(force: bool = False):
    from motifs.build_motifs import build_motifs

    build_motifs(force=force)


@mytho.command()
def status():
    """Show the current state of the data pipeline."""
    from pipeline_inspect import (
        corpus_status,
        embeddings_status,
        graphs_status,
        motifs_status,
        projections_status,
    )
    from settings import settings

    total = 0

    # Corpus
    info = corpus_status(settings)
    total += info["total_size"]
    _header("Corpus", info["total_size"])
    built, cfg, missing = info["built_count"], info["config_count"], info["missing_count"]
    click.echo(f"  {built} texts built (from {cfg} in config)")
    if missing:
        click.echo(click.style(f"  {missing} missing", fg="yellow"))
    click.echo()

    # Embeddings
    info = embeddings_status(settings)
    total += info["total_size"]
    _header("Embeddings", info["total_size"])
    if not info["exists"]:
        click.echo("  No embeddings found")
    elif "error" in info:
        click.echo(click.style(f"  Error: {info['error']}", fg="red"))
    elif not info["collections"]:
        click.echo("  No embedding collections")
    else:
        for col in sorted(info["collections"], key=lambda c: c["model"]):
            click.echo(f"  {col['model']:<40} {col['count']:>6} chunks")
    click.echo()

    # Projections
    info = projections_status(settings)
    total += info["total_size"]
    _header("Projections", info["total_size"])
    if not info["exists"]:
        click.echo("  No projections found")
    elif not info["models"]:
        click.echo("  No model results")
    else:
        for m in info["models"]:
            done, tot = m["plots_done"], m["plots_total"]
            color = "green" if done == tot else "yellow" if done > 0 else "red"
            mark = "ok" if done == tot else f"{done}/{tot}"
            click.echo(click.style(f"  {m['name']:<40} {mark:>5}  {format_size(m['size']):>8}", fg=color))
    click.echo()

    # Graphs
    info = graphs_status(settings)
    total += info["total_size"]
    _header("Graphs", info["total_size"])
    if not info["exists"]:
        click.echo("  No graphs directory")
    else:
        click.echo(f"  {info['count']} graph files")
    click.echo()

    # Motifs
    info = motifs_status(settings)
    total += info["total_size"]
    _header("Motifs", info["total_size"])
    if not info["built"]:
        click.echo("  No motif database")
    else:
        counts = info["counts"]
        if counts:
            click.echo("  " + ", ".join(f"{k}: {v}" for k, v in counts.items()))
        else:
            click.echo("  Built (no counts recorded)")
        enr = info.get("enrichment") or {}
        # Each enrichment is owned by an index; when that index is built but its
        # enrichment key is absent from meta, the meta is stale/partial — flag it
        # so "no data" (e.g. missing Wikipedia links) is diagnosable, not silent.
        expected = [("mapsofmyths", "berezkin"), ("berezkin_bibliography", "berezkin"),
                    ("bibliography", "tmi"), ("atu_wikidata", "atu"), ("ashliman", "atu")]
        seen = set()
        for source, owner in expected:
            e = enr.get(source)
            seen.add(source)
            if e is None:
                if owner in counts:
                    click.echo(f"  {source}: not recorded (stale meta — rebuild to refresh)")
            elif e.get("skipped"):
                click.echo(f"  {source}: skipped ({e['skipped']})")
            elif e:
                click.echo(f"  {source}: " + ", ".join(f"{k} {v}" for k, v in e.items()))
        for source, e in enr.items():  # any future enrichment not in the list above
            if source not in seen and e:
                click.echo(f"  {source}: " + ", ".join(f"{k} {v}" for k, v in e.items()))
    click.echo()

    click.echo(f"Total: {format_size(total)}")


def _header(name: str, size: int):
    click.echo(f"{name}:  {format_size(size)}")


@mytho.command()
@click.option("--apply", is_flag=True, help="Actually delete files (default is dry run).")
@click.option("--caches", is_flag=True, help="Also remove resumable caches (extraction/preprocessing); needs --apply to delete.")
def clean(apply: bool, caches: bool):
    """Find and remove orphan files (and, with --caches, resumable caches)."""
    try:
        _clean(apply, caches)
    except Exception as e:
        _fail("Clean", e)


def _clean(apply: bool, caches: bool):
    import shutil

    from pipeline_inspect import (
        cache_files,
        corpus_orphans,
        embeddings_orphan_chunks,
        embeddings_orphan_collections,
        graphs_orphans,
        motifs_raw_cache,
        projections_orphans,
    )
    from settings import settings

    total_bytes = 0
    total_items = 0

    # Corpus
    orphans = corpus_orphans(settings)
    if orphans:
        _header("Corpus", sum(s for _, s in orphans))
        for path, size in orphans:
            total_bytes += size
            total_items += 1
            rel = str(path.relative_to(settings.corpus_dir))
            click.echo(f"  {rel:<50} {format_size(size):>8}")
            if apply:
                path.unlink(missing_ok=True)
        click.echo()

    # Embeddings orphan collections + chunks
    orphan_cols = embeddings_orphan_collections(settings)
    skip_col_names = {c["name"] for c in orphan_cols}
    orphan_chunks = embeddings_orphan_chunks(settings, skip_collections=skip_col_names)
    if orphan_cols or orphan_chunks:
        click.echo("Embeddings:")
        for col in orphan_cols:
            total_items += 1
            click.echo(f"  orphan collection: {col['model']:<30} {col['count']:>6} chunks")
        for info in orphan_chunks:
            n = len(info["orphan_ids"])
            total_items += n
            click.echo(f"  orphan chunks in {info['model']:<30} {n:>6} / {info['total_count']}")
        if apply:
            from embeddings import chroma_manager
            for col in orphan_cols:
                chroma_manager.delete_collection(col["name"])
            for info in orphan_chunks:
                collection = chroma_manager.get_collection(info["collection"])
                collection.delete(ids=info["orphan_ids"])
        click.echo()

    # Projections
    orphans = projections_orphans(settings)
    if orphans:
        _header("Projections", sum(m["size"] for m in orphans))
        for m in orphans:
            total_bytes += m["size"]
            total_items += 1
            click.echo(f"  {m['name']:<50} {format_size(m['size']):>8}")
            if apply:
                shutil.rmtree(m["path"])
        click.echo()

    # Graphs
    orphans = graphs_orphans(settings)
    if orphans:
        _header("Graphs", sum(s for _, s in orphans))
        for path, size in orphans:
            total_bytes += size
            total_items += 1
            name = path.name
            click.echo(f"  {name:<50} {format_size(size):>8}")
            if apply:
                shutil.rmtree(path)
        click.echo()

    # Caches (always shown; removed only with --caches --apply). The motif raw
    # scrape cache is a directory, removed wholesale rather than file-by-file.
    cache_list = cache_files(settings)
    motifs_cache = motifs_raw_cache(settings)
    if cache_list or motifs_cache:
        cache_bytes = sum(s for _, s in cache_list) + (motifs_cache[1] if motifs_cache else 0)
        _header("Caches", cache_bytes)
        outputs_root = settings.graphs_dir.parent
        for path, size in cache_list:
            try:
                label = str(path.relative_to(outputs_root))
            except ValueError:
                label = str(path)
            click.echo(f"  {label:<50} {format_size(size):>8}")
        if motifs_cache:
            try:
                label = str(motifs_cache[0].relative_to(outputs_root))
            except ValueError:
                label = str(motifs_cache[0])
            click.echo(f"  {label + '/':<50} {format_size(motifs_cache[1]):>8}")
        if caches:
            total_items += len(cache_list) + (1 if motifs_cache else 0)
            total_bytes += cache_bytes
            if apply:
                for path, _ in cache_list:
                    path.unlink(missing_ok=True)
                if motifs_cache:
                    shutil.rmtree(motifs_cache[0], ignore_errors=True)
        else:
            click.echo(click.style(f"  {format_size(cache_bytes)} reclaimable — add --caches to remove", fg="yellow"))
        click.echo()

    if total_items == 0:
        click.echo(click.style("Nothing to remove.", fg="green"))
        return

    summary = f"{total_items} items"
    if total_bytes:
        summary += f", {format_size(total_bytes)} on disk"

    if apply:
        click.echo(click.style(f"Removed: {summary}", fg="green"))
    else:
        click.echo(f"{summary}")
        click.echo(click.style("Dry run. Use --apply to delete.", fg="yellow"))


@mytho.command()
@click.option("--caches", is_flag=True, help="Also include resumable caches (extraction/preprocessing/motif raw scrape).")
def export(caches: bool):
    """Bundle built outputs into a portable zip for another machine."""
    from export_bundle import export_outputs, orphan_summary

    try:
        orphans = orphan_summary()
        if orphans:
            click.echo(click.style("[warn] orphans present and INCLUDED — run `mytho clean --apply` for a tidy bundle:", fg="yellow"))
            for line in orphans:
                click.echo(f"  {line}")

        result = export_outputs(include_caches=caches, timestamp=datetime.now().strftime("%Y%m%d-%H%M%S"))
    except Exception as e:
        _fail("Export", e)

    if result.path is None:
        click.echo("Nothing to export — build the pipeline first (mytho build).")
        return

    click.echo(click.style("[done]  Export", fg="green") + f" → {result.path.name} ({format_size(result.total_bytes)}, {result.total_files} files)")
    for name, size in result.components.items():
        click.echo(f"  {name:<12} {format_size(size):>10}")
    if result.chromadb_version:
        click.echo(f"\n  embeddings built with chromadb {result.chromadb_version} — install a compatible chromadb on the target.")
    click.echo(f"  Restore: unzip {result.path.name} from the project root, then `mytho server`.")


if __name__ == "__main__":
    mytho()
