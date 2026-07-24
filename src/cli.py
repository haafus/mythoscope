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
    ("Management", ["build", "refresh", "status", "clean", "export", "server"]),
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
    """Run the full pipeline: build everything missing or stale (``--force`` rebuilds all)."""
    if sample is not None:
        # Quick dev run — the pre-driver per-stage path: first model, first N texts
        # (corpus + graphs). Sampling by doc count doesn't fit the incremental driver.
        from model_registry import embedding_variants
        model = model or embedding_variants()[0]
        click.echo(click.style(f"[sample] model={model}, max_texts={sample}", fg="yellow"))
        steps = [
            ("Corpus", _build_corpus, {"force": force, "max_texts": sample}),
            ("Embeddings", _build_embeddings, {"model": model, "force": force}),
            ("Projections", _build_projections, {"model": model, "force": force}),
            ("Graphs", _build_graphs, {"force": force, "max_texts": sample}),
            ("Motifs", _build_motifs, {"force": force}),
        ]
        start = time.monotonic()
        for name, fn, kwargs in steps:
            _run(name, fn, **kwargs)
        click.echo(click.style("\nBuild finished.", fg="green", bold=True) + f" ({_fmt_elapsed(time.monotonic() - start)})")
        return

    from pipeline import build as run_pipeline
    from pipeline import build_pipeline

    stages = build_pipeline()
    if model:
        stages = _scope_to_model(stages, model)

    start = time.monotonic()
    try:
        plans = run_pipeline(stages, force=force)
    except Exception as e:
        _fail("Build", e)
    for p in plans:
        n = len(p.stage.desired()) if force else len(p.to_build)
        if n:
            click.echo(f"  {p.stage.name}: {n} built")
    click.echo(click.style("\nBuild finished.", fg="green", bold=True) + f" ({_fmt_elapsed(time.monotonic() - start)})")


def _scope_to_model(stages, model):
    """Keep the whole pipeline but only the given model's embeddings/projections (corpus,
    graphs and motifs always run) — the ``--model`` scope, pre-item-4."""
    from model_registry import embedding_config

    key = embedding_config(model)["key"]
    return [
        s for s in stages
        if not (s.name.startswith(("embeddings:", "projections:")) and s.name.split(":", 1)[1] != key)
    ]


def _build_corpus(force: bool = False, max_texts: int | None = None):
    from corpus.builder import build_corpus

    build_corpus(force=force, max_texts=max_texts)


def _build_embeddings(model: str | None, force: bool = False):
    # torch/sentence-transformers now load lazily inside the build — and only when a variant
    # actually has chunks to encode — so nothing heavy loads here. The model load, when it
    # happens, is announced by model_manager.
    from embeddings.build_embeddings import build_embeddings

    build_embeddings(model_name=model, force=force)


def _build_projections(model: str | None, force: bool = False):
    # umap is imported lazily, only when a projection is actually regenerated, so an
    # up-to-date run never loads it; this import pulls only chromadb (to read the collections).
    logger.info("Loading chromadb...")
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
@click.argument("target", type=click.Choice(["documents", "motifs"]), default="documents")
@click.option("--apply", is_flag=True, help="Adopt upstream changes (default previews and keeps the pinned copy).")
def refresh(target: str, apply: bool):
    """Re-fetch upstream into the pinned raw archive (networked; preview then --apply).

    Unlike `build` (which never re-fetches present raw) and `--force` (which rebuilds
    derived from that raw), `refresh` is the deliberate, human-gated re-check of upstream.
    """
    try:
        if target == "documents":
            _refresh_documents(apply)
        else:
            _refresh_motifs(apply)
    except Exception as e:
        _fail("Refresh", e)


def _refresh_documents(apply: bool):
    from corpus.refresh import refresh_corpus

    click.echo(click.style("[start] Refresh documents", fg="cyan", bold=True))
    r = refresh_corpus(apply=apply)

    for title, reason in r.unreachable:
        click.echo(click.style(f"  unreachable  {title} ({reason}) — kept pinned", fg="yellow"))
    for title, reason in r.degraded:
        click.echo(click.style(f"  degraded     {title} ({reason}) — kept pinned", fg="yellow"))
    for title in r.new:
        verb = "acquired" if apply else "would acquire"
        click.echo(f"  new          {title} ({verb})")
    for title in r.changed:
        verb = "adopted" if apply else "changed — rerun with --apply to adopt"
        color = "green" if apply else "yellow"
        click.echo(click.style(f"  {'adopted' if apply else 'changed':<12} {title} ({verb})", fg=color))

    click.echo(f"  {r.unchanged} unchanged, {r.skipped_local} local (checked on build)")
    problems = len(r.unreachable) + len(r.degraded)
    if apply and r.adopted:
        click.echo(click.style(f"[done]  adopted {len(r.adopted)} — run `mytho build` to re-derive.", fg="green"))
    elif r.changed or r.new:
        click.echo(click.style("Preview only. Re-run with --apply to adopt.", fg="yellow"))
    elif problems:
        # Nothing to adopt, but some sources were kept pinned — don't claim all-clear.
        click.echo(click.style(f"[done]  Refresh — {problems} source(s) kept pinned (see above).", fg="yellow"))
    else:
        click.echo(click.style("[done]  Refresh — everything current.", fg="green"))


def _refresh_motifs(apply: bool):
    # Motif sources re-scrape wholesale (no cheap per-source diff yet — the per-source
    # staged refresh is the Part 3 source-unit work); --apply re-fetches, else previews.
    if not apply:
        click.echo("Would re-scrape all motif sources (Berezkin, TMI, ATU + enrichment).")
        click.echo(click.style("Preview only. Re-run with --apply to re-fetch.", fg="yellow"))
        return
    _run("Refresh motifs", _build_motifs, force=True)


@mytho.command()
def status():
    """Show what each stage would build, rebuild, or reap — the driver's desired/actual diff."""
    from pipeline import build_pipeline
    from pipeline import status as pipeline_status

    dirty = 0
    for p in pipeline_status(build_pipeline()):
        if p.clean:
            click.echo(click.style(f"  {p.stage.name:<28} up to date", fg="green"))
            continue
        dirty += 1
        bits = []
        if p.missing:
            bits.append(f"{len(p.missing)} to build")
        if p.stale:
            bits.append(f"{len(p.stale)} stale")
        if p.orphans:
            bits.append(f"{len(p.orphans)} orphan")
        click.echo(click.style(f"  {p.stage.name:<28} " + ", ".join(bits), fg="yellow"))

    click.echo()
    click.echo("Everything up to date."
               if not dirty
               else f"{dirty} stage(s) need work — run `mytho build` (or `mytho clean` for orphans).")


def _header(name: str, size: int):  # used by _clean (retired with it in a later step)
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
