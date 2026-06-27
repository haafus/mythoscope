from fastapi import APIRouter, HTTPException, Query

from embeddings import chroma_manager
from projections import PROJECTION_METHODS
from server.schemas import ModelListResponse, SearchRequest, SearchResult, WarmupRequest
from server.services.projections import get_projection_data
from server.services.similarity import similarity_service

router = APIRouter(prefix="/api/similarity", tags=["similarity"])


def _available_models() -> list[str]:
    """Available embedding collections, mapping store failures to HTTP 503."""
    try:
        return chroma_manager.get_available_models()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Embedding store unavailable: {e}") from e


def _require_collection(model: str) -> None:
    """404 if the model has no embedding collection, 503 if the store is unreachable."""
    if model not in _available_models():
        raise HTTPException(status_code=404, detail=f"Model '{model}' not found")


@router.get("/models", response_model=ModelListResponse)
def list_models() -> dict:
    models = [{"name": key, "key": key} for key in _available_models()]
    return {"models": models}


@router.post("/search", response_model=list[SearchResult])
def search(request: SearchRequest):
    _require_collection(request.model)
    try:
        return similarity_service.search(request.model, request.query, request.top_k)
    except ImportError as e:
        # viewer build has no embedding models; text-query encoding needs them.
        raise HTTPException(
            status_code=503,
            detail="Text-query search is unavailable in this build (embedding models not installed)",
        ) from e


@router.post("/warmup")
def warmup(request: WarmupRequest) -> dict:
    """Best-effort preload so the first text search isn't a cold start.

    Called fire-and-forget from the UI on model change; the client ignores the
    outcome. Mirrors search()'s ImportError -> 503 so the viewer build (no
    embedding deps) responds cleanly instead of 500.
    """
    _require_collection(request.model)
    try:
        similarity_service.warmup(request.model)
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail="Warmup is unavailable in this build (embedding models not installed)",
        ) from e
    return {"status": "warmed", "model": request.model}


@router.get("/points/{model}/{text_id}", response_model=list[SearchResult])
def point_info(
    model: str,
    text_id: str,
    chunk_index: int = Query(...),
    top_k: int = Query(1, ge=1, le=100),
):
    _require_collection(model)
    return similarity_service.get_point(
        model, text_id, chunk_index, top_k=top_k,
    )


@router.get("/methods")
def methods() -> list[dict]:
    return PROJECTION_METHODS


@router.get("/projections/{model}/{method}")
def projection(model: str, method: str) -> dict:
    data = get_projection_data(model, method)
    if not data:
        raise HTTPException(status_code=404, detail="Projection data not found")
    return data
