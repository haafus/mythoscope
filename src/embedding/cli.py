import click

from settings import settings

from .build_embeddings import build_embeddings
from .builder import EmbeddingBuilder
from .chroma_manager import collection_name_for_model, delete_collection, ensure_chroma_writable
from .performance_metrics import PerformanceMetrics


def _create_builder(*, model: str | None = None, chunking: str | None = None) -> EmbeddingBuilder:
    emb = settings.embedding
    return EmbeddingBuilder(
        corpus_dir=settings.corpus_dir,
        out_dir=settings.analysis_dir,
        chroma_path=settings.chroma_dir,
        embedding_model=model or emb.models[0],
        chunking=chunking or emb.default_chunking,
        batch_size=emb.batch_size,
    )


@click.command()
@click.option("--model", "-m", default=None, help="Embedding model to use")
@click.option("--chunking", "-ch", default=None, help="Chunking strategy")
@click.option("--batch-size", "-b", default=None, type=int, help="Batch size for encoding")
@click.pass_context
def generate(ctx, model: str | None, chunking: str | None, batch_size: int | None):
    metrics = PerformanceMetrics(settings.embedding.metrics_file)
    metrics.start_operation("generate_embeddings")

    try:
        build_embeddings(
            model_name=model,
            chunking=chunking,
            batch_size=batch_size,
        )
        click.echo(click.style("Embeddings generated successfully", fg="green"))
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        raise
    finally:
        metrics.end_operation("generate_embeddings")
        metrics.save()


@click.command()
@click.argument("query")
@click.option("--top-k", "-k", default=5, type=int, help="Number of results to return")
@click.option("--model", "-m", default=None, help="Model to use for query encoding")
@click.pass_context
def query(ctx, query: str, top_k: int, model: str | None):
    builder = _create_builder(model=model)

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
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)


@click.command()
@click.option("--model", "-m", default=None, help="Model name")
@click.option("--strategy", "-s", default=None, help="Chunking strategy")
@click.argument("text_file", type=click.Path(exists=True))
@click.pass_context
def test(ctx, text_file: str, model: str | None, strategy: str | None):
    with open(text_file, encoding="utf-8") as f:
        text = f.read()

    builder = _create_builder(model=model, chunking=strategy)

    metrics = PerformanceMetrics()
    metrics.start_operation("test_embedding")

    try:
        result = builder.build_embeddings(text)
        metrics.end_operation("test_embedding")

        click.echo(click.style("\nTest completed successfully", fg="green"))
        click.echo(f"  Model: {result['model']}")
        click.echo(f"  Chunking: {result['chunking']}")
        click.echo(f"  Number of chunks: {result['num_chunks']}")
        click.echo(f"  Batch size used: {result['batch_size_used']}")

        if metrics.metrics:
            click.echo("\n  Performance:")
            click.echo(f"    Duration: {metrics.metrics.get('duration', 0):.2f}s")
            if "memory_usage_mb" in metrics.metrics:
                click.echo(f"    Memory usage: {metrics.metrics['memory_usage_mb']:.1f} MB")
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)


@click.command()
@click.option("--model", "-m", multiple=True, help="Models to compare")
@click.option("--strategy", "-s", multiple=True, help="Strategies to compare")
@click.argument("text_file", type=click.Path(exists=True))
@click.pass_context
def compare(ctx, text_file: str, model: tuple, strategy: tuple):
    with open(text_file, encoding="utf-8") as f:
        text = f.read()

    models = list(model) if model else None
    strategies = list(strategy) if strategy else None

    builder = _create_builder()

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
        click.echo()


@click.command()
@click.option("--model", "-m", default=None, help="Model whose collection should be deleted")
@click.option("--yes", is_flag=True, help="Skip confirmation")
@click.pass_context
def clear_cache(ctx, model: str | None, yes: bool):
    model_name = model or settings.embedding.models[0]
    collection = collection_name_for_model(model_name)

    if not yes:
        click.confirm(f"Delete collection '{collection}' for model '{model_name}'?", abort=True)

    import chromadb

    chroma_path = ensure_chroma_writable(str(settings.chroma_dir))
    client = chromadb.PersistentClient(path=str(chroma_path))

    try:
        deleted = delete_collection(client, collection)
        if deleted:
            click.echo(click.style(f"Collection '{collection}' deleted", fg="green"))
        else:
            click.echo(click.style(f"Collection '{collection}' does not exist", fg="yellow"))
    except Exception as e:
        click.echo(click.style(f"Error deleting collection: {e}", fg="red"))


