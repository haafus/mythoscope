import logging

from model_registry import embedding_config

from . import PROJECTION_METHODS
from .analyzer import ModelData, load_model_data
from .visualization import CHART_GENERATORS, SCATTER_TRANSFORMS

logger = logging.getLogger(__name__)


def build_projections(
    model_name: str | None = None,
    generate_all_plots: bool = True,
    force: bool = False,
) -> ModelData | None:
    from embeddings import chroma_manager

    available = chroma_manager.get_available_models()

    if not available:
        logger.error("ERROR: No available collections in the Chroma database!")
        return None

    keys = [embedding_config(model_name)["key"]] if model_name else available
    logger.info(f"Variants queued for analysis: {keys}")

    result: ModelData | None = None
    for key in keys:
        logger.info(f"Starting analysis: {key}")

        model_data = load_model_data(key)

        if model_data is None:
            logger.warning(f"No data found for variant {key}, skipping...")
            continue

        result = model_data
        if generate_all_plots:
            _generate_plots(model_data, force=force)

    logger.info("Projection analysis complete.")
    return result


def _generate_plots(model_data: ModelData, force: bool = False) -> None:
    for method in PROJECTION_METHODS:
        key = method["key"]
        chart_type = method["chart_type"]
        label = method["label"]
        output_path = model_data.output_dir / f"{key}.json"

        if not force and output_path.exists():
            logger.info("Skipping %s (already exists)", label)
            continue

        logger.info("Generating %s...", label)
        generator = CHART_GENERATORS[chart_type]
        try:
            kwargs = {}
            if chart_type == "scatter":
                kwargs["transform"] = SCATTER_TRANSFORMS[key]
            generator(model_data.data, model_data.embeddings, output_path, model_name=model_data.model_name, **kwargs)
        except Exception:
            logger.exception("Error creating %s", label)

    logger.info("Visualizations for %s: %s", model_data.model_name, model_data.output_dir)
