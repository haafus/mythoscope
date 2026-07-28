import sys
import time
from datetime import datetime, timedelta

import click

from log_setup import setup_logging
from pipeline.caches import format_size

COMMAND_SECTIONS = [
    ("Pipeline", ["build", "status", "clean", "refresh", "export"]),
    ("Server", ["server"]),
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
@click.version_option(package_name="mythoscope", prog_name="Mythoscope")
def mytho():
    """Mythoscope — computational framework for comparative mythology."""
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
@click.option("--host", "-h", default=None, help="Bind address (default from config).")
@click.option("--port", "-p", default=None, type=int, help="Port (default from config).")
def server(host: str | None, port: int | None):
    """Start the web UI server."""
    from server.run_server import run_server

    run_server(host, port)


@mytho.command()
@click.argument("scope", nargs=-1)
@click.option("--force", "-f", is_flag=True, help="Force regeneration of all steps.")
@click.option("--sample", "-s", is_flag=False, flag_value=str(SAMPLE_MAX_TEXTS), default=None,
              type=int, metavar="N",
              help=f"Quick smoke run: cap EVERY stage's build to at most N elements (default "
                   f"{SAMPLE_MAX_TEXTS} when given bare, e.g. -s 50 for more).")
def build(scope, force, sample):
    """Run the pipeline: build everything missing or stale (``--force`` rebuilds all).

    SCOPE (optional, repeatable) restricts the build to exactly the named stages (name/prefix,
    e.g. ``graphs`` or ``embeddings:bge-m3``) — built when stale/missing (a param/algo change
    invalidates them via the fingerprint, no ``--force`` needed); ``--force`` rebuilds them
    regardless. Upstream is not rebuilt, and the downstream cascade is left for a plain
    ``mytho build``.

    ``--sample N`` caps every stage's per-run build to at most N elements (quick smoke run;
    non-destructive)."""
    from pipeline import build as run_pipeline

    stages, targets = _scoped_pipeline(scope)
    if sample is not None:
        click.echo(click.style(f"[sample] at most {sample} element(s) per stage", fg="yellow"))

    start = time.monotonic()
    try:
        plans = run_pipeline(stages, force=force, targets=targets, sample=sample)
    except Exception as e:
        _fail("Build", e)
    for p in plans:
        if p.built:   # what was actually built (a silently-failed key is excluded — honest count)
            click.echo(f"  {p.stage.name}: {len(p.built)}/{p.desired_count} built")
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


_MOTIF_SOURCES = ("berezkin", "tmi", "atu")


@mytho.command()
@click.argument("scope", nargs=-1)
@click.option("--apply", is_flag=True, help="Adopt upstream changes (default previews and keeps the pinned copy).")
def refresh(scope, apply: bool):
    """Re-fetch upstream into the pinned raw archive (networked; preview then --apply).

    Unlike `build` (which never re-fetches present raw) and `--force` (which rebuilds derived
    from that raw), `refresh` is the deliberate, human-gated re-check of upstream. SCOPE picks the
    targets: ``corpus``, ``motifs`` (all three sources), or a single ``motifs:source:<berezkin|tmi|
    atu>``; with no SCOPE it refreshes everything. Each motif source is re-checked independently
    (diff vs the pinned copy → keep-pinned by default → adopt on --apply)."""
    try:
        corpus, sources = _resolve_refresh(scope)
        if corpus:
            _refresh_documents(apply)
        if sources:
            _refresh_motifs(apply, sources)
    except Exception as e:
        _fail("Refresh", e)


def _resolve_refresh(scope) -> tuple[bool, list[str] | None]:
    """Parse SCOPE → ``(refresh_corpus, motif_sources)``. ``motif_sources`` is ``None`` when motifs
    were not selected, else the ordered source list. No scope → corpus + all sources."""
    if not scope:
        return True, list(_MOTIF_SOURCES)
    corpus, motifs, sel = False, False, set()
    for tok in scope:
        if tok == "corpus":
            corpus = True
        elif tok in ("motifs", "motifs:source"):
            motifs = True
            sel.update(_MOTIF_SOURCES)
        elif tok.startswith("motifs:source:"):
            name = tok.split(":", 2)[2]
            if name not in _MOTIF_SOURCES:
                raise ValueError(f"unknown motif source {name!r} — choose {', '.join(_MOTIF_SOURCES)}")
            motifs = True
            sel.add(name)
        else:
            raise ValueError(f"not a refreshable target: {tok!r} — choose "
                             f"corpus | motifs | motifs:source:<{'|'.join(_MOTIF_SOURCES)}>")
    return corpus, ([s for s in _MOTIF_SOURCES if s in sel] if motifs else None)


def _refresh_motifs(apply: bool, sources: list[str]) -> None:
    """Fan out to each selected source stage's own ``refresh`` — a source is re-checked, kept
    pinned, and adopted entirely on its own; nothing central knows its resources."""
    from pipeline.stages.motifs import AtuSource, BerezkinSource, TmiSource

    stages = {"berezkin": BerezkinSource, "tmi": TmiSource, "atu": AtuSource}
    for name in sources:
        click.echo(click.style(f"[start] Refresh motifs:source:{name}"
                               f" ({'apply' if apply else 'preview'})", fg="cyan", bold=True))
        _render_refresh_table(stages[name]().refresh(apply=apply), apply)


def _render_refresh_table(result, apply: bool) -> None:
    """The §9 three-column table (resource · status · action), plain text. Only actionable rows are
    listed (a full re-check is thousands of resources); ``not changed`` collapses into the footer
    tally, then the kept-pinned count (never 'all clear' while a source is unhealthy), then apply."""
    from motifs.refresh import CHANGED, NEW, NOT_CHANGED

    rows = sorted((o for o in result.outcomes if o.status != NOT_CHANGED), key=lambda o: (o.status, o.title))
    if rows:
        click.echo(f"  {'resource':<48} {'status':<12} action")
        for o in rows:
            click.echo(f"  {o.title:<48} {o.status:<12} {o.action}")
    tally = result.tally()
    click.echo(f"  {len(result.outcomes)} checked: "
               + (", ".join(f"{tally[k]} {k}" for k in sorted(tally)) or "nothing pinned"))
    if result.kept_pinned:
        click.echo(f"  {result.kept_pinned} kept pinned (degraded/gone — see above)")
    pending = sum(1 for o in result.outcomes if o.status in (CHANGED, NEW))
    if apply:
        click.echo(f"  adopted {len(result.adopted)} — run `mytho build` to re-derive.")
    elif pending:
        click.echo(f"  preview only — re-run with --apply to adopt {pending}.")


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


@mytho.command()
@click.argument("scope", nargs=-1)
def status(scope):
    """Show what each stage would build, rebuild, or reap — the driver's desired/actual diff.

    SCOPE (optional) restricts to stages matching a name/prefix plus their upstream."""
    from pipeline import status as pipeline_status

    try:
        stages, targets = _scoped_pipeline(scope)
        plans = pipeline_status(stages)   # topo_order can raise on a cycle / malformed pipeline
    except Exception as e:
        _fail("Status", e)                # no bare traceback, like build/clean/refresh
    dirty = 0
    for p in plans:
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
        if caches and scope:
            # The caches are global (graph extraction / chunk preprocess / motif raw), not
            # per-stage — a scoped clean must not silently reap another stage's cache.
            click.echo(click.style("  --caches is global — run `mytho clean --caches` without a SCOPE to remove", fg="yellow"))
        elif caches:
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
