import logging
import sys
import time
from datetime import datetime, timedelta

import click

from log_setup import setup_logging
from pipeline.caches import format_size

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
@click.argument("scope", nargs=-1)
@click.option("--model", "-m", default=None, help="Embedding model (default from config).")
@click.option("--force", "-f", is_flag=True, help="Force regeneration of all steps.")
@click.option("--sample", "-s", is_flag=False, flag_value=str(SAMPLE_MAX_TEXTS), default=None,
              type=int, metavar="N",
              help=f"Quick run: first embedding model, limited to N texts "
                   f"(default {SAMPLE_MAX_TEXTS} when given bare, e.g. -s 50 for more).")
def build(scope, model, force, sample):
    """Run the pipeline: build everything missing or stale (``--force`` rebuilds all).

    SCOPE (optional, repeatable) restricts the build to exactly the named stages (name/prefix,
    e.g. ``graphs`` or ``embeddings:bge-m3``) — built when stale/missing (a param/algo change
    invalidates them via the fingerprint, no ``--force`` needed); ``--force`` rebuilds them
    regardless. Upstream is not rebuilt, and the downstream cascade is left for a plain
    ``mytho build``."""
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

    stages, targets = _scoped_pipeline(scope)
    if model:
        stages = _scope_to_model(stages, model)

    start = time.monotonic()
    try:
        # Scope restricts WHICH stages build; --force (separate) decides whether to ignore the
        # fingerprint gate. A param/algo change invalidates a stage via its fp, so a scoped
        # build rebuilds it without --force.
        plans = run_pipeline(stages, force=force, targets=targets)
    except Exception as e:
        _fail("Build", e)
    for p in plans:
        n = len(p.stage.desired()) if force else len(p.to_build)
        if n:
            click.echo(f"  {p.stage.name}: {n} built")
    click.echo(click.style("\nBuild finished.", fg="green", bold=True) + f" ({_fmt_elapsed(time.monotonic() - start)})")


def _scoped_pipeline(scope):
    """Return ``(stages, targets)``. Without a scope: the full pipeline, ``targets=None`` (act on
    all). With a scope: the matched stages (name/prefix) PLUS their upstream dependencies — the
    deps are in the list only to wire and topologically order the targets, not to be acted on —
    and ``targets`` = just the matched stage names, so the scope is literal (``build X`` does X,
    not its stale upstream; a full ``build`` is how you cascade)."""
    from pipeline import build_pipeline

    stages = build_pipeline()
    if not scope:
        return stages, None
    matched = [s for s in stages if any(s.name == o or s.name.startswith(o) for o in scope)]
    if not matched:
        _fail("Scope", ValueError(f"no stage matches {list(scope)} — see `mytho status`"))
    targets = {s.name for s in matched}
    keep = {id(s): s for s in matched}
    frontier = list(matched)
    while frontier:
        for inp in frontier.pop().inputs():
            if id(inp) not in keep:
                keep[id(inp)] = inp
                frontier.append(inp)
    order = {id(s): i for i, s in enumerate(stages)}
    return sorted(keep.values(), key=lambda s: order[id(s)]), targets


def _scope_to_model(stages, model):
    """Keep the whole pipeline but only the given model's embeddings/projections (corpus,
    graphs and motifs always run) — the ``--model`` convenience atop ``--only``."""
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


_REFRESHABLE = {"documents": "corpus", "corpus": "corpus", "motifs": "motifs"}


@mytho.command()
@click.argument("scope", nargs=-1)
@click.option("--apply", is_flag=True, help="Adopt upstream changes (default previews and keeps the pinned copy).")
def refresh(scope, apply: bool):
    """Re-fetch upstream into the pinned raw archive (networked; preview then --apply).

    Unlike `build` (which never re-fetches present raw) and `--force` (which rebuilds derived
    from that raw), `refresh` is the deliberate, human-gated re-check of upstream. SCOPE selects
    which upstream-capable stages to re-check — ``corpus`` (aka ``documents``) and/or ``motifs``;
    with no SCOPE it refreshes all of them (stages with no network source are skipped).
    """
    unknown = [s for s in scope if s not in _REFRESHABLE]
    if unknown:
        _fail("Refresh", ValueError(f"not a refreshable stage: {unknown} — choose corpus|documents|motifs"))
    selected = {_REFRESHABLE[s] for s in scope} if scope else {"corpus", "motifs"}
    try:
        if "corpus" in selected:
            _refresh_documents(apply)
        if "motifs" in selected:
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
@click.argument("scope", nargs=-1)
def status(scope):
    """Show what each stage would build, rebuild, or reap — the driver's desired/actual diff.

    SCOPE (optional) restricts to stages matching a name/prefix plus their upstream."""
    from pipeline import status as pipeline_status

    stages, targets = _scoped_pipeline(scope)
    dirty = 0
    for p in pipeline_status(stages):
        if targets is not None and p.stage.name not in targets:
            continue  # upstream is present only to compute the targets' plans — don't list it
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


@mytho.command()
@click.argument("scope", nargs=-1)
@click.option("--apply", is_flag=True, help="Actually delete files (default is dry run).")
@click.option("--caches", is_flag=True, help="Also remove resumable caches (extraction/preprocessing); needs --apply to delete.")
def clean(scope, apply: bool, caches: bool):
    """Find and remove orphan files (and, with --caches, resumable caches).

    SCOPE (optional) restricts the orphan scan to stages matching a name/prefix plus upstream."""
    try:
        _clean(scope, apply, caches)
    except Exception as e:
        _fail("Clean", e)


def _clean(scope, apply: bool, caches: bool):
    import shutil

    from pipeline import clean as driver_clean
    from pipeline.caches import cache_files, format_size, motifs_raw_cache
    from settings import settings

    total_items = 0

    # Orphans — the driver's two-level reap: level-1 orphan keys inside a surviving stage (a
    # document removed from config → its .txt / chunks / graph), level-2 whole artifacts a
    # dropped stage left in a shared store (a removed model's collection or projection dir).
    # With --apply it deletes as it walks; otherwise it is a dry run.
    scoped_stages, targets = _scoped_pipeline(scope)
    report = driver_clean(scoped_stages, apply=apply, targets=targets)
    for stage, keys in report.level1.items():
        click.echo(f"{stage}: {len(keys)} orphan document(s)")
        for k in sorted(keys):
            click.echo(f"  {k}")
        total_items += len(keys)
    for store, ids in report.level2.items():
        click.echo(f"{store}: {len(ids)} orphan artifact(s)")
        for i in sorted(ids):
            click.echo(f"  {i}")
        total_items += len(ids)
    if not report.empty:
        click.echo()

    # Caches — internal resumable tiers (graph extraction, chunk preprocessing, the motif raw
    # scrape), not orphans: always shown, removed only with --caches --apply.
    cache_list = cache_files(settings)
    motifs_cache = motifs_raw_cache(settings)
    if cache_list or motifs_cache:
        cache_bytes = sum(s for _, s in cache_list) + (motifs_cache[1] if motifs_cache else 0)
        click.echo(f"Caches:  {format_size(cache_bytes)}")
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

    if apply:
        click.echo(click.style(f"Removed: {total_items} item(s).", fg="green"))
    else:
        click.echo(f"{total_items} item(s).")
        click.echo(click.style("Dry run. Use --apply to delete.", fg="yellow"))


@mytho.command()
@click.argument("scope", nargs=-1)
@click.option("--caches", is_flag=True, help="Also include resumable caches (extraction/preprocessing/motif raw scrape).")
def export(scope, caches: bool):
    """Bundle built outputs into a portable zip for another machine.

    SCOPE (optional) bundles only the named stage(s)' outputs (e.g. ``graphs``, ``motifs``)."""
    from export_bundle import export_outputs, orphan_summary

    try:
        orphans = orphan_summary(scope)
        if orphans:
            click.echo(click.style("[warn] orphans present and INCLUDED — run `mytho clean --apply` for a tidy bundle:", fg="yellow"))
            for line in orphans:
                click.echo(f"  {line}")

        result = export_outputs(scope=scope, include_caches=caches, timestamp=datetime.now().strftime("%Y%m%d-%H%M%S"))
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
