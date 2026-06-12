import logging
import sys

import click

logger = logging.getLogger(__name__)


class _LazyEmbeddingGroup(click.Group):
    """Defers import of embedding.cli until a subcommand is actually invoked."""

    _loaded = False

    def _load(self):
        if not self._loaded:
            from embedding.cli import clear_cache, compare, generate, query, show_config, test, validate_cache

            for cmd in [generate, query, test, compare, clear_cache, validate_cache, show_config]:
                self.add_command(cmd)
            self._loaded = True

    def list_commands(self, ctx):
        self._load()
        return super().list_commands(ctx)

    def get_command(self, ctx, cmd_name):
        self._load()
        return super().get_command(ctx, cmd_name)


@click.group()
@click.version_option(package_name="mythosemantic")
def mytho():
    """MythoSemantic — computational framework for comparative mythology."""


# ---------------------------------------------------------------------------
# corpus
# ---------------------------------------------------------------------------
@mytho.command()
@click.option(
    "--type",
    "text_type",
    type=click.Choice(["translation", "original", "all"]),
    default="all",
    help="Filter by text type.",
)
@click.option("--force", is_flag=True, help="Overwrite existing files.")
def corpus(text_type: str, force: bool):
    """Download and build the text corpus (Gutenberg cleanup is automatic)."""
    from settings import setup_logging

    setup_logging(log_filename="corpus.log", clear_handlers=True)
    from corpus.builder import build_corpus

    filter_type = {"translation", "original"} if text_type == "all" else {text_type}
    build_corpus(filter_type=filter_type, force=force)
    click.echo(click.style("Corpus build completed.", fg="green"))


# ---------------------------------------------------------------------------
# embeddings — delegate to the existing click group
# ---------------------------------------------------------------------------
@mytho.group(cls=_LazyEmbeddingGroup)
@click.option("--config", "-c", default="config/embedding.yaml", help="Path to config file.")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output.")
@click.pass_context
def embeddings(ctx, config: str, verbose: bool):
    """Generate, query, and manage embeddings."""
    from embedding.config_manager import ConfigManager

    ctx.ensure_object(dict)
    ctx.obj["config_manager"] = ConfigManager(config)
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


# ---------------------------------------------------------------------------
# projection
# ---------------------------------------------------------------------------
@mytho.command()
@click.option("--model", "-m", default=None, help="Embedding model name (all models if omitted).")
@click.option("--no-plots", is_flag=True, help="Skip plot generation, only compute stats.")
def projection(model: str | None, no_plots: bool):
    """Generate dimensionality-reduction projections (PCA, t-SNE, UMAP)."""
    from settings import setup_logging

    setup_logging(log_filename="analyzer.log")
    from projection.visualization import analyze_embeddings

    analyzer = analyze_embeddings(model_name=model, generate_all_plots=not no_plots)
    if analyzer is None:
        click.echo(click.style("No data found — check that embeddings exist.", fg="red"), err=True)
        sys.exit(1)
    click.echo(click.style("Projection analysis completed.", fg="green"))


# ---------------------------------------------------------------------------
# clustering
# ---------------------------------------------------------------------------
@mytho.command()
@click.option("--model", "-m", default=None, help="Embedding model name.")
@click.option(
    "--algorithm", "-a", "clustering_model", default="kmeans",
    help="Clustering algorithm (kmeans, spectral, birch, gmm).",
)
@click.option("--single-model", is_flag=True, help="Run only the selected algorithm.")
@click.option("--no-viz", is_flag=True, help="Skip visualization generation.")
@click.option("--output-dir", default="outputs/analysis", help="Output base directory.")
@click.option("--models-list", multiple=True, help="Explicit list of algorithms to run.")
def cluster(model, clustering_model, single_model, no_viz, output_dir, models_list):
    """Run clustering analysis on embeddings."""
    from datetime import datetime

    from settings import setup_logging

    setup_logging(log_filename=f"clustering_run_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")

    from clustering.run_clustering import run_all_clustering_models, run_clustering_analysis
    from projection.analyzer import EmbeddingAnalyzer

    analyzer = EmbeddingAnalyzer()
    if not analyzer.available_models:
        click.echo(click.style("No available embedding models in the database.", fg="red"), err=True)
        sys.exit(1)

    models_to_process = [model] if model else analyzer.available_models

    for current_model in models_to_process:
        click.echo(f"Clustering: {current_model}")
        if single_model:
            run_clustering_analysis(
                model_name=current_model,
                clustering_model=clustering_model,
                generate_visualizations=not no_viz,
                output_base_dir=output_dir,
                _analyzer=analyzer,
            )
        else:
            run_all_clustering_models(
                model_name=current_model,
                models_to_run=list(models_list) or None,
                output_base_dir=output_dir,
                _analyzer=analyzer,
            )

    click.echo(click.style("Clustering completed.", fg="green"))


# ---------------------------------------------------------------------------
# graphs
# ---------------------------------------------------------------------------
@mytho.command()
@click.option("--force", is_flag=True, help="Overwrite existing graph outputs.")
def graphs(force: bool):
    """Extract knowledge graphs from corpus texts using an LLM."""
    from datetime import datetime

    from settings import setup_logging

    setup_logging(
        log_filename=f"generation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
        log_dir="logs",
    )
    from graphs.run_graph_generation import run_generate_graphs

    run_generate_graphs(force=force)
    click.echo(click.style("Graph generation completed.", fg="green"))


# ---------------------------------------------------------------------------
# server
# ---------------------------------------------------------------------------
@mytho.command()
@click.option("--host", "-h", default=None, help="Bind address (default from config).")
@click.option("--port", "-p", default=None, type=int, help="Port (default from config).")
def server(host: str | None, port: int | None):
    """Start the web UI server."""
    import uvicorn

    from server.config import server_config

    uvicorn.run(
        "main:app",
        host=host or server_config.host,
        port=port or server_config.port,
        reload=False,
    )


# ---------------------------------------------------------------------------
# pipeline — run everything end-to-end
# ---------------------------------------------------------------------------
@mytho.command()
@click.option("--model", "-m", default=None, help="Embedding model (default from config).")
@click.option(
    "--text-type", "-t",
    type=click.Choice(["translation", "original", "all"]),
    default="all",
    help="Corpus text type filter.",
)
@click.option("--skip-corpus", is_flag=True, help="Skip corpus download.")
@click.option("--skip-embeddings", is_flag=True, help="Skip embedding generation.")
@click.option("--skip-projection", is_flag=True, help="Skip projection generation.")
@click.option("--skip-clustering", is_flag=True, help="Skip clustering analysis.")
@click.option("--skip-graphs", is_flag=True, help="Skip graph extraction.")
def pipeline(model, text_type, skip_corpus, skip_embeddings, skip_projection, skip_clustering, skip_graphs):
    """Run the full analysis pipeline end-to-end."""
    from settings import setup_logging

    setup_logging(log_filename="pipeline.log", clear_handlers=True)

    steps = [
        ("Corpus", skip_corpus, _pipeline_corpus, {"text_type": text_type}),
        ("Embeddings", skip_embeddings, _pipeline_embeddings, {"model": model, "text_type": text_type}),
        ("Projection", skip_projection, _pipeline_projection, {"model": model}),
        ("Clustering", skip_clustering, _pipeline_clustering, {"model": model}),
        ("Graphs", skip_graphs, _pipeline_graphs, {}),
    ]

    for name, skip, fn, kwargs in steps:
        if skip:
            click.echo(click.style(f"[skip] {name}", fg="yellow"))
            continue
        click.echo(click.style(f"[start] {name}", fg="cyan", bold=True))
        try:
            fn(**kwargs)
            click.echo(click.style(f"[done]  {name}", fg="green"))
        except Exception as e:
            click.echo(click.style(f"[fail]  {name}: {e}", fg="red"), err=True)
            sys.exit(1)

    click.echo(click.style("\nPipeline finished.", fg="green", bold=True))


def _pipeline_corpus(text_type: str):
    from corpus.builder import build_corpus

    filter_type = {"translation", "original"} if text_type == "all" else {text_type}
    build_corpus(filter_type=filter_type)


def _pipeline_embeddings(model: str | None, text_type: str):
    from embedding.build_embeddings import build_embeddings, normalize_text_type

    build_embeddings(model_name=model, text_type=normalize_text_type(text_type))


def _pipeline_projection(model: str | None):
    from projection.visualization import analyze_embeddings

    analyze_embeddings(model_name=model)


def _pipeline_clustering(model: str | None):
    from clustering.run_clustering import run_all_clustering_models
    from projection.analyzer import EmbeddingAnalyzer

    analyzer = EmbeddingAnalyzer(model_name=model)
    if analyzer.available_models:
        models = [model] if model else analyzer.available_models
        for m in models:
            run_all_clustering_models(model_name=m, _analyzer=analyzer)


def _pipeline_graphs():
    from graphs.run_graph_generation import run_generate_graphs

    run_generate_graphs()


if __name__ == "__main__":
    mytho()
