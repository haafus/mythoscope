import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

from settings import Settings, setup_logging

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


try:
    from embedding_analyzer.analyzer import EmbeddingAnalyzer
except ImportError:
    logger.error("Error: embedding_analyzer was not found. Make sure it is installed or available in the project.")
    sys.exit(1)

if __package__:
    from .metrics import calculate_clustering_metrics
    from .models import get_clustering_model, list_available_models
    from .visualization import (
        plot_clustering_results_2d,
        plot_confusion_matrix_heatmap,
        plot_metrics_dashboard,
        reduce_dimensions,
    )
else:
    from embeddings_clustering.metrics import calculate_clustering_metrics
    from embeddings_clustering.models import get_clustering_model, list_available_models
    from embeddings_clustering.visualization import (
        plot_clustering_results_2d,
        plot_confusion_matrix_heatmap,
        plot_metrics_dashboard,
        reduce_dimensions,
    )


class NumpyEncoder(json.JSONEncoder):
    """Custom encoder for converting numpy types to native Python types for JSON."""

    def default(self, obj):
        if isinstance(obj, (np.integer, np.int32, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def _get_num_clusters(true_labels) -> int:
    labels = np.array([label for label in true_labels if str(label) and str(label) != "unknown"])
    n_samples = len(true_labels)
    if n_samples == 0:
        return 0

    n_labels = len(np.unique(labels)) if len(labels) else len(np.unique(true_labels))
    if n_samples == 1:
        return 1
    return max(2, min(n_labels, n_samples))


def _process_single_model(
    embeddings: np.ndarray,
    true_labels: np.ndarray,
    model_name: str,
    cl_model_name: str,
    clustering_params: dict,
    base_dir: Path,
    generate_visualizations: bool = True,
    embeddings_2d: np.ndarray = None,
) -> dict:
    """Universal function for running one clustering model and saving results."""
    base_dir.mkdir(parents=True, exist_ok=True)

    try:
        clusterer = get_clustering_model(cl_model_name, **clustering_params)
        predicted_labels = clusterer.fit_predict(embeddings)
        n_clusters_found = len(set(predicted_labels)) - (1 if -1 in predicted_labels else 0)
        logger.info(f"  • Clusters actually found ({cl_model_name}): {n_clusters_found}")
    except Exception:
        logger.exception(f"Clustering error ({cl_model_name})")
        return {"error": f"Error while running {cl_model_name}"}

    eval_embeddings = getattr(clusterer, "processed_embeddings", embeddings)

    metrics = calculate_clustering_metrics(eval_embeddings, predicted_labels, true_labels)

    unique, counts = np.unique(predicted_labels, return_counts=True)
    cluster_counts = dict(zip(unique.tolist(), counts.tolist(), strict=False))

    tradition_cluster_map = {}
    for tradition in np.unique(true_labels):
        mask = true_labels == tradition
        trad_labels = predicted_labels[mask]
        unique_trad, counts_trad = np.unique(trad_labels, return_counts=True)
        tradition_cluster_map[str(tradition)] = dict(zip(unique_trad.tolist(), counts_trad.tolist(), strict=False))

    results = {
        "metrics": metrics,
        "cluster_counts": cluster_counts,
        "tradition_cluster_map": tradition_cluster_map,
        "all_labels": predicted_labels.tolist(),
        "true_labels": true_labels.tolist(),
    }

    metrics_path = base_dir / "clustering_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, cls=NumpyEncoder, ensure_ascii=False, indent=2)

    np.save(base_dir / "cluster_labels.npy", predicted_labels)

    if generate_visualizations:
        try:
            if embeddings_2d is None:
                embeddings_2d = reduce_dimensions(
                    embeddings, method="umap", n_components=2, normalize=True, fallback_on_error=True
                )

            if embeddings_2d is not None and len(embeddings_2d) > 0:
                clusters_path = base_dir / f"clusters_{cl_model_name}.html"
                plot_clustering_results_2d(
                    embeddings_2d,
                    predicted_labels,
                    true_labels,
                    title=f"Embedding clustering ({cl_model_name})",
                    output_path=str(clusters_path),
                )

                confusion_path = base_dir / f"confusion_matrix_{cl_model_name}.html"
                plot_confusion_matrix_heatmap(true_labels, predicted_labels, output_path=str(confusion_path))
        except Exception:
            logger.exception(f"Error creating visualizations ({cl_model_name})")

    return results


def run_clustering_analysis(
    model_name: str = None,
    clustering_model: str = "kmeans",
    clustering_params: dict = None,
    generate_visualizations: bool = True,
    output_base_dir: str = "analysis",
):
    logger.info("STARTING CLUSTERING ANALYSIS")

    analyzer = EmbeddingAnalyzer(model_name=model_name)

    if not analyzer.available_models:
        logger.error("Error: no available embedding models!")
        return None

    if model_name is None:
        model_name = analyzer.available_models[0]
        analyzer.set_model(model_name)

    safe_model_name = Settings.safe_model_name(model_name)
    logger.info(f"Analysis for embedding model: {model_name}")

    data = analyzer.filter_by_model()
    if not data:
        logger.error(f"Error: no data for model '{model_name}'")
        return None

    embeddings = np.stack([item["embedding"] for item in data])
    true_labels = np.array([item["tradition"] for item in data])

    logger.info(f"  • Points loaded: {len(embeddings)}")
    logger.info(f"  • Dimension: {embeddings.shape[1]}")

    base_analysis_dir = Path(project_root) / output_base_dir / safe_model_name / "clustering" / clustering_model

    clustering_params = {} if clustering_params is None else dict(clustering_params)

    num_clusters = _get_num_clusters(true_labels)
    if clustering_model in ["kmeans", "spectral", "birch"]:
        clustering_params["n_clusters"] = num_clusters
    elif clustering_model == "gmm":
        clustering_params["n_components"] = num_clusters

    results = _process_single_model(
        embeddings=embeddings,
        true_labels=true_labels,
        model_name=model_name,
        cl_model_name=clustering_model,
        clustering_params=clustering_params,
        base_dir=base_analysis_dir,
        generate_visualizations=generate_visualizations,
    )

    logger.info("ANALYSIS COMPLETE")
    return results


def run_all_clustering_models(model_name: str = None, models_to_run: list = None, output_base_dir: str = "analysis"):
    if models_to_run is None:
        models_to_run = list_available_models()

    analyzer = EmbeddingAnalyzer(model_name=model_name)
    if not analyzer.available_models:
        logger.error("Error: no available embedding models!")
        return None

    if model_name is None and analyzer.available_models:
        model_name = analyzer.available_models[0]
        analyzer.set_model(model_name)

    safe_model_name = Settings.safe_model_name(model_name)
    data = analyzer.filter_by_model()

    if not data:
        return None

    embeddings = np.stack([item["embedding"] for item in data])
    true_labels = np.array([item["tradition"] for item in data])
    num_clusters = _get_num_clusters(true_labels)

    all_results = {}

    embeddings_2d = reduce_dimensions(embeddings, method="umap", n_components=2, normalize=True, fallback_on_error=True)

    for cl_model in models_to_run:
        base_dir = Path(project_root) / output_base_dir / safe_model_name / "clustering" / cl_model

        clustering_params = {}
        if cl_model in ["kmeans", "spectral", "birch"]:
            clustering_params["n_clusters"] = num_clusters
        elif cl_model == "gmm":
            clustering_params["n_components"] = num_clusters

        results = _process_single_model(
            embeddings=embeddings,
            true_labels=true_labels,
            model_name=model_name,
            cl_model_name=cl_model,
            clustering_params=clustering_params,
            base_dir=base_dir,
            generate_visualizations=True,
            embeddings_2d=embeddings_2d,
        )

        all_results[cl_model] = results.get("metrics", results)

    comparison_dir = Path(project_root) / output_base_dir / safe_model_name / "clustering" / "comparison"
    comparison_dir.mkdir(parents=True, exist_ok=True)

    plot_metrics_dashboard(all_results, output_path=str(comparison_dir / "metrics_dashboard.html"))

    with open(comparison_dir.parent / "all_models_comparison.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, cls=NumpyEncoder, ensure_ascii=False, indent=2)

    return all_results


def build_clusters():
    parser = argparse.ArgumentParser(description="Embedding clustering analysis")
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--clustering", type=str, default="kmeans", choices=list_available_models())
    parser.add_argument("--single-model", action="store_true")
    parser.add_argument("--no-viz", action="store_true")
    parser.add_argument("--output-dir", type=str, default="analysis")
    parser.add_argument("--models-list", type=str, nargs="+", default=None)
    args = parser.parse_args()
    setup_logging(log_filename=f"clustering_run_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")

    from embedding_analyzer.analyzer import EmbeddingAnalyzer

    analyzer = EmbeddingAnalyzer()
    available_models = analyzer.available_models

    if not available_models:
        logger.error("ERROR: No available embedding models in the database!")
        return

    models_to_process = [args.model] if args.model else available_models

    logger.info(f"Queued for clustering: {models_to_process}")

    for current_model in models_to_process:
        logger.info(f"Clustering embeddings for: {current_model}")

        if args.single_model:
            run_clustering_analysis(
                model_name=current_model,
                clustering_model=args.clustering,
                generate_visualizations=not args.no_viz,
                output_base_dir=args.output_dir,
            )
        else:
            run_all_clustering_models(
                model_name=current_model, models_to_run=args.models_list, output_base_dir=args.output_dir
            )
