from fastapi import APIRouter, HTTPException

from server.schemas import ModelListResponse
from server.services.models import get_model_info, list_model_summaries

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("", response_model=ModelListResponse)
def list_models() -> dict:
    return {"models": list_model_summaries()}


@router.get("/{model_key}/stats")
def model_stats(model_key: str) -> dict:
    info = get_model_info(model_key)
    if not info:
        raise HTTPException(status_code=404, detail="Model info not found")
    return info
