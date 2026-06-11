import json

from .models import get_model_output_dir, key_to_model, model_to_key


def list_algorithms(model_key: str) -> list[str]:
    clustering_dir = get_model_output_dir(model_key) / "clustering"
    if not clustering_dir.exists():
        return []

    return sorted(item.name for item in clustering_dir.iterdir() if item.is_dir() and item.name != "comparison")


def get_metrics(model_key: str, algorithm: str) -> dict:
    metrics_path = get_model_output_dir(model_key) / "clustering" / algorithm / "clustering_metrics.json"
    if not metrics_path.exists():
        return {}

    with metrics_path.open("r", encoding="utf-8") as handle:
        result: dict = json.load(handle)
        return result


def get_saved_cluster_plots(model_key: str, algorithm: str) -> dict:
    model_name = key_to_model(model_key)
    safe_dir = model_to_key(model_name)
    base_dir = get_model_output_dir(model_key) / "clustering" / algorithm
    base_url = f"/analysis/{safe_dir}/clustering/{algorithm}"

    clusters_file = base_dir / f"clusters_{algorithm}.html"
    confusion_file = base_dir / f"confusion_matrix_{algorithm}.html"

    return {
        "clusters": {
            "exists": clusters_file.exists(),
            "url": f"{base_url}/clusters_{algorithm}.html" if clusters_file.exists() else None,
        },
        "confusion_matrix": {
            "exists": confusion_file.exists(),
            "url": f"{base_url}/confusion_matrix_{algorithm}.html" if confusion_file.exists() else None,
        },
    }
