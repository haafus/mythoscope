import json
import logging

import click

from .build_embeddings import build_embeddings, normalize_text_type
from .builder import EmbeddingBuilder
from .cache_validator import CacheValidator
from .chroma_manager import collection_name_for_model, delete_collection, ensure_chroma_writable
from .config_manager import ConfigManager
from .performance_metrics import PerformanceMetrics


@click.group()
@click.option("--config", "-c", default="config/embeddings_builder.yaml", help="Path to config file")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx, config: str, verbose: bool):
    ctx.ensure_object(dict)
    ctx.obj["config_manager"] = ConfigManager(config)
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


@cli.command()
@click.option("--model", "-m", default=None, help="Embedding model to use")
@click.option("--chunking", "-ch", default=None, help="Chunking strategy")
@click.option(
    "--text-type", "-t", default=None, type=click.Choice(["original", "translate", "translation", "all", "both"])
)
@click.option("--batch-size", "-b", default=None, type=int, help="Batch size for encoding")
@click.pass_context
def generate(ctx, model: str | None, chunking: str | None, text_type: str | None, batch_size: int | None):
    config_mgr = ctx.obj["config_manager"]

    if model:
        config_mgr.set("embedding.default_model", model)
    if chunking:
        config_mgr.set("embedding.default_chunking", chunking)
    if text_type:
        config_mgr.set("embedding.text_type", normalize_text_type(text_type))
    if batch_size:
        config_mgr.set("embedding.batch_size", batch_size)
    metrics = PerformanceMetrics(config_mgr.get("performance.metrics_file"))
    metrics.start_operation("generate_embeddings")

    try:
        build_embeddings(
            batch_size=config_mgr.get("embedding.batch_size"),
            config_path=str(config_mgr.config_path),
            model_name=model,
            chunking=chunking,
            text_type=normalize_text_type(text_type) if text_type else None,
        )
        click.echo(click.style("✓ Embeddings generated successfully", fg="green"))
    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)
        raise
    finally:
        metrics.end_operation("generate_embeddings")
        metrics.save()


@cli.command()
@click.argument("query")
@click.option("--top-k", "-k", default=5, type=int, help="Number of results to return")
@click.option("--model", "-m", default=None, help="Model to use for query encoding")
@click.pass_context
def query(ctx, query: str, top_k: int, model: str | None):
    config_mgr = ctx.obj["config_manager"]

    builder = EmbeddingBuilder(
        corpus_dir=config_mgr.get("paths.corpus_dir"),
        out_dir=config_mgr.get("paths.out_dir"),
        chroma_path=config_mgr.get("paths.chroma_path"),
        cache_dir=config_mgr.get("paths.cache_dir"),
        embedding_model=model or config_mgr.get("embedding.default_model"),
        chunking=config_mgr.get("embedding.default_chunking"),
        text_type=config_mgr.get("embedding.text_type"),
        batch_size=config_mgr.get("embedding.batch_size"),
    )

    try:
        results = builder.query_chroma(query, top_k=top_k)
        click.echo(f"\n{'=' * 60}")
        click.echo(click.style(f"Query: {query}", fg="cyan", bold=True))
        click.echo(f"{'=' * 60}\n")

        for i, result in enumerate(results, 1):
            click.echo(click.style(f"[{i}] Score: {1 - result['distance']:.3f}", fg="yellow"))
            click.echo(f"    File: {result['metadata'].get('filename', 'unknown')}")
            click.echo(f"    Tradition: {result['metadata'].get('tradition', 'unknown')}")
            click.echo(f"    Text: {result['document'][:200]}...")
            click.echo()
    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)


@cli.command()
@click.option("--model", "-m", default=None, help="Model name")
@click.option("--strategy", "-s", default=None, help="Chunking strategy")
@click.argument("text_file", type=click.Path(exists=True))
@click.pass_context
def test(ctx, text_file: str, model: str | None, strategy: str | None):
    config_mgr = ctx.obj["config_manager"]

    with open(text_file, encoding="utf-8") as f:
        text = f.read()

    builder = EmbeddingBuilder(
        corpus_dir=config_mgr.get("paths.corpus_dir"),
        out_dir=config_mgr.get("paths.out_dir"),
        chroma_path=config_mgr.get("paths.chroma_path"),
        cache_dir=config_mgr.get("paths.cache_dir"),
        embedding_model=model or config_mgr.get("embedding.default_model"),
        chunking=strategy or config_mgr.get("embedding.default_chunking"),
        text_type=config_mgr.get("embedding.text_type"),
        batch_size=config_mgr.get("embedding.batch_size"),
    )

    metrics = PerformanceMetrics()
    metrics.start_operation("test_embedding")

    try:
        result = builder.build_embeddings(text)
        metrics.end_operation("test_embedding")

        click.echo(click.style("\n✓ Test completed successfully", fg="green"))
        click.echo(f"  Model: {result['model']}")
        click.echo(f"  Chunking: {result['chunking']}")
        click.echo(f"  Number of chunks: {result['num_chunks']}")
        click.echo(f"  Embedding dimension: {result['embedding_dim']}")
        click.echo(f"  Batch size used: {result['batch_size_used']}")

        if metrics.metrics:
            click.echo("\n  Performance:")
            click.echo(f"    Duration: {metrics.metrics.get('duration', 0):.2f}s")
            if "memory_usage_mb" in metrics.metrics:
                click.echo(f"    Memory usage: {metrics.metrics['memory_usage_mb']:.1f} MB")
    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"), err=True)


@cli.command()
@click.option("--model", "-m", multiple=True, help="Models to compare")
@click.option("--strategy", "-s", multiple=True, help="Strategies to compare")
@click.argument("text_file", type=click.Path(exists=True))
@click.pass_context
def compare(ctx, text_file: str, model: tuple, strategy: tuple):
    config_mgr = ctx.obj["config_manager"]

    with open(text_file, encoding="utf-8") as f:
        text = f.read()

    models = list(model) if model else None
    strategies = list(strategy) if strategy else None

    builder = EmbeddingBuilder(
        corpus_dir=config_mgr.get("paths.corpus_dir"),
        out_dir=config_mgr.get("paths.out_dir"),
        chroma_path=config_mgr.get("paths.chroma_path"),
        cache_dir=config_mgr.get("paths.cache_dir"),
        embedding_model=config_mgr.get("embedding.default_model"),
        chunking=config_mgr.get("embedding.default_chunking"),
        text_type=config_mgr.get("embedding.text_type"),
        batch_size=config_mgr.get("embedding.batch_size"),
    )

    click.echo("Running comparison... This may take a while.\n")

    results = builder.compare_models_and_strategies(text, list(models) if models else None, list(strategies) if strategies else None)

    click.echo(f"{'=' * 80}")
    click.echo(click.style("Comparison Results", fg="cyan", bold=True))
    click.echo(f"{'=' * 80}\n")

    for key, result in results.items():
        model_name, strategy_name = key.split("____")
        click.echo(click.style(f"Model: {model_name}", fg="yellow"))
        click.echo(f"  Strategy: {strategy_name}")
        click.echo(f"  Chunks: {result['num_chunks']}")
        click.echo(f"  Embedding dim: {result['embedding_dim']}")
        click.echo()


@cli.command()
@click.option("--model", "-m", default=None, help="Model whose collection should be deleted")
@click.option("--yes", is_flag=True, help="Skip confirmation")
@click.pass_context
def clear_cache(ctx, model: str | None, yes: bool):
    config_mgr = ctx.obj["config_manager"]
    model_name = model or config_mgr.get("embedding.default_model")
    collection = collection_name_for_model(model_name)

    if not yes:
        click.confirm(f"Delete collection '{collection}' for model '{model_name}'?", abort=True)

    import chromadb

    chroma_path = ensure_chroma_writable(config_mgr.get("paths.chroma_path"))
    client = chromadb.PersistentClient(path=str(chroma_path))

    try:
        deleted = delete_collection(client, collection)
        if deleted:
            click.echo(click.style(f"Collection '{collection}' deleted", fg="green"))
        else:
            click.echo(click.style(f"Collection '{collection}' does not exist", fg="yellow"))
    except Exception as e:
        click.echo(click.style(f"✗ Error deleting collection: {e}", fg="red"))


@cli.command()
@click.pass_context
def validate_cache(ctx):
    config_mgr = ctx.obj["config_manager"]
    validator = CacheValidator(config_mgr.get("paths.cache_dir"))

    click.echo("Validating cache...")
    results = validator.validate_all()

    click.echo(f"\n{'=' * 60}")
    click.echo(click.style("Cache Validation Results", fg="cyan", bold=True))
    click.echo(f"{'=' * 60}")
    click.echo(f"Total files: {results['total']}")
    click.echo(f"Valid: {click.style(str(results['valid']), fg='green')}")
    click.echo(f"Corrupted: {click.style(str(results['corrupted']), fg='red')}")
    click.echo(f"Size: {results['size_mb']:.2f} MB")

    if results["corrupted"] > 0:
        click.echo("\nCorrupted files:")
        for file in results["corrupted_files"]:
            click.echo(f"  - {file}")


@cli.command()
@click.pass_context
def show_config(ctx):
    config_mgr = ctx.obj["config_manager"]
    config_dict = config_mgr.get_all()
    click.echo(json.dumps(config_dict, indent=2, default=str))


if __name__ == "__main__":
    cli(obj={})
