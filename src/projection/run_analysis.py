import logging
from pathlib import Path

from settings import settings

from .analyzer import EmbeddingAnalyzer
from .utils import _check_umap
from .visualization import (
    DEFAULT_SAMPLE_SIZE,
    add_click_handler_to_html,
    plot_comparison_dashboard,
    plot_distance_heatmap,
    plot_hyperparameter_tuning_dashboard,
    plot_interactive_2d,
    plot_tradition_distribution,
)

logger = logging.getLogger(__name__)


def generate_clickable_plots(output_dir: Path, model_name: str) -> None:
    html_files = list(output_dir.glob("*.html"))

    if not html_files:
        logger.warning(f"No HTML files found in {output_dir} to make clickable.")
        return

    for filepath in html_files:
        add_click_handler_to_html(str(filepath))


def analyze_embeddings(model_name: str | None = None, generate_all_plots: bool = True) -> EmbeddingAnalyzer | None:
    try:
        base_analyzer = EmbeddingAnalyzer()
        available_models = base_analyzer.available_models

        if not available_models:
            logger.error("ERROR: No available models in the Chroma database!")
            return None

        models_to_analyze = [model_name] if model_name else available_models
        logger.info(f"Models queued for analysis: {models_to_analyze}")

        analyzer: EmbeddingAnalyzer | None = None
        for current_model in models_to_analyze:
            logger.info(f"Starting model analysis: {current_model}")

            analyzer = EmbeddingAnalyzer(model_name=current_model)

            if not analyzer.data:
                logger.warning(f"No data found for model {current_model}, skipping...")
                continue

            analyzer.print_statistics()
            analyzer.save_summary()
            analyzer.save_models_list()

            if generate_all_plots and analyzer.data:
                _generate_all_plots(analyzer)

        return analyzer

    except Exception:
        logger.exception("Critical error during embedding analysis")
        return None


def _generate_all_plots(analyzer: EmbeddingAnalyzer) -> None:
    data = analyzer.filter_by_model()
    logger.info("Generating visualizations with hyperparameter variations...")

    config = settings.projection
    umap_configs = config.umap_configs
    tsne_configs = config.tsne_configs
    pca_configs = config.pca_configs
    baseline_configs = config.baseline_configs

    configs_map = {"umap": umap_configs, "tsne": tsne_configs, "pca": pca_configs}

    for method, configs in configs_map.items():
        if method == "umap" and not _check_umap():
            continue

        logger.info(f"  - Generating individual {method.upper()} plots...")
        for cfg in configs:
            try:
                plot_interactive_2d(
                    data,
                    sample_size=DEFAULT_SAMPLE_SIZE,
                    output_dir=analyzer.output_dir,
                    model_name=analyzer.model_name,
                    method=method,
                    reducer_kwargs=cfg,
                )
            except Exception:
                logger.exception("Error creating %s with %s", method.upper(), cfg)

    logger.info("  - Generating hyperparameter tuning dashboards...")
    try:
        if _check_umap():
            plot_hyperparameter_tuning_dashboard(
                data, method="umap", param_configs=umap_configs,
                output_dir=analyzer.output_dir, model_name=analyzer.model_name,
            )
        plot_hyperparameter_tuning_dashboard(
            data, method="tsne", param_configs=tsne_configs,
            output_dir=analyzer.output_dir, model_name=analyzer.model_name,
        )
    except Exception:
        logger.exception("Error creating hyperparameter dashboards")

    logger.info("  - Generating cross-method comparison dashboard...")
    try:
        plot_comparison_dashboard(
            data, output_dir=analyzer.output_dir,
            model_name=analyzer.model_name, baseline_configs=baseline_configs,
        )
    except Exception:
        logger.exception("Error creating comparison dashboard")

    logger.info("  - Distance heatmap...")
    try:
        plot_distance_heatmap(data, output_dir=analyzer.output_dir, model_name=analyzer.model_name)
    except Exception:
        logger.exception("Error creating heatmap")

    logger.info("  - Tradition distribution chart...")
    try:
        plot_tradition_distribution(data, output_dir=analyzer.output_dir, model_name=analyzer.model_name)
    except Exception:
        logger.exception("Error creating distribution chart")

    logger.info("  - Adding click handlers...")
    try:
        if analyzer.model_name:
            generate_clickable_plots(analyzer.output_dir, analyzer.model_name)
    except Exception:
        logger.exception("Error adding click handlers")

    logger.info(f"\nAll visualizations for {analyzer.model_name} saved to: {analyzer.output_dir}")
