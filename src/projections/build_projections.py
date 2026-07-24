import logging

from corpus.utils import content_fingerprint
from model_registry import embedding_config

from . import PROJECTION_METHODS
from .analyzer import ModelData, load_model_data
from .visualization import CHART_GENERATORS, SCATTER_TRANSFORMS

logger = logging.getLogger(__name__)


def _fingerprint_from_metas(metas: list[dict]) -> str:
    """Identity of the projection input, from chunk metadata alone (no vectors) — folds in
    each chunk's embeddings fingerprint (the upstream per-chunk fp: hash(doc_fp, model,
    transform_v)). Added/removed texts (id set) and edits (fp) both change it."""
    parts = sorted(
        f"{(m or {}).get('document_id', '')}:{(m or {}).get('chunk_index', '')}:{(m or {}).get('fingerprint', '')}"
        for m in metas
    )
    return content_fingerprint("\n".join(parts).encode("utf-8"))


def _up_to_date(output_dir, current_fp: str) -> bool:
    fp_path = output_dir / ".input-fp"
    return (fp_path.exists()
            and fp_path.read_text(encoding="utf-8").strip() == current_fp
            and all((output_dir / f"{m['key']}.json").exists() for m in PROJECTION_METHODS))


def build_projections(
    model_name: str | None = None,
    generate_all_plots: bool = True,
    force: bool = False,
) -> ModelData | None:
    from embeddings import chroma_manager
    from settings import settings

    available = chroma_manager.get_available_models()

    if not available:
        logger.error("ERROR: No available collections in the Chroma database!")
        return None

    keys = [embedding_config(model_name)["key"]] if model_name else available
    logger.info(f"Variants queued for analysis: {keys}")

    result: ModelData | None = None
    for key in keys:
        logger.info(f"Starting analysis: {key}")

        # Fingerprint the input from metadata only (cheap) and skip before loading the large
        # embedding vectors when the projections are already current.
        metas = chroma_manager.get_collection(key).get(include=["metadatas"]).get("metadatas") or []
        if not metas:
            logger.warning(f"No data found for variant {key}, skipping...")
            continue
        current_fp = _fingerprint_from_metas(metas)
        if not force and _up_to_date(settings.projections_dir / key, current_fp):
            logger.info("%s already up to date — skipping (no vector load)", key)
            continue

        model_data = load_model_data(key)  # loads the vectors — only when there is work
        if model_data is None:
            logger.warning(f"No data found for variant {key}, skipping...")
            continue

        result = model_data
        if generate_all_plots:
            _generate_plots(model_data, current_fp)

    logger.info("Projection analysis complete.")
    return result


def _generate_plots(model_data: ModelData, current_fp: str) -> None:
    # Reached only for a stale (or forced) variant, so (re)generate every method.
    ok = True
    for method in PROJECTION_METHODS:
        key = method["key"]
        chart_type = method["chart_type"]
        label = method["label"]
        output_path = model_data.output_dir / f"{key}.json"

        logger.info("Generating %s...", label)
        generator = CHART_GENERATORS[chart_type]
        try:
            kwargs = {}
            if chart_type == "scatter":
                kwargs["transform"] = SCATTER_TRANSFORMS[key]
            generator(model_data.data, model_data.embeddings, output_path, model_name=model_data.model_name, **kwargs)
        except Exception:
            ok = False
            logger.exception("Error creating %s", label)

    if ok:
        (model_data.output_dir / ".input-fp").write_text(current_fp, encoding="utf-8")  # stamp so a rerun skips
    logger.info("Visualizations for %s: %s", model_data.model_name, model_data.output_dir)
