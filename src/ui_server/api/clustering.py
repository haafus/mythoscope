from fastapi import APIRouter

from ui_server.services.clustering import get_metrics, get_saved_cluster_plots, list_algorithms

router = APIRouter(prefix="/api/clustering", tags=["clustering"])


@router.get("/{model_key}/algorithms")
def algorithms(model_key: str):
    items = list_algorithms(model_key)
    return {"algorithms": items, "total": len(items)}


@router.get("/{model_key}/{algorithm}/metrics")
def metrics(model_key: str, algorithm: str):
    return get_metrics(model_key, algorithm)


@router.get("/{model_key}/{algorithm}/plots")
def saved_plots(model_key: str, algorithm: str):
    return get_saved_cluster_plots(model_key, algorithm)
