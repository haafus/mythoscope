from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ui_server.schemas import SearchRequest
from ui_server.services.embedding_index import embedding_index_service
from ui_server.services.projections import get_projection_data, get_saved_html_plot

router = APIRouter(prefix="/api/similarity", tags=["similarity"])


@router.get("/projections/{model_key}/{method}")
def projection(model_key: str, method: str):
    data = get_projection_data(model_key, method)
    if not data:
        saved_html_plot = get_saved_html_plot(model_key, method)
        raise HTTPException(
            status_code=404,
            detail={
                "message": "Projection JSON not found",
                "saved_html_plot": saved_html_plot,
            },
        )
    return data


@router.get("/saved-html/{model_key}/{method}")
def saved_html_plot(model_key: str, method: str):
    return get_saved_html_plot(model_key, method)


@router.get("/points/{model_key}/{point_id}")
def point_info(model_key: str, point_id: str, chunk_index: Optional[int] = Query(None)):
    try:
        return embedding_index_service.get_point(model_key, point_id, chunk_index)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Point not found") from exc


@router.get("/points/{model_key}/{point_id}/neighbors")
def point_neighbors(
    model_key: str,
    point_id: str,
    n: int = Query(10, ge=1, le=100),
    chunk_index: Optional[int] = Query(None),
):
    try:
        neighbors = embedding_index_service.get_neighbors(model_key, point_id, n, chunk_index)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Point not found") from exc
    return {"point_id": point_id, "neighbors": neighbors}


@router.post("/search")
def search(request: SearchRequest):
    results = embedding_index_service.search(request.model, request.query, request.top_k)
    return {
        "query": request.query,
        "model": request.model,
        "results": results,
        "total": len(results),
    }
