from fastapi import APIRouter, HTTPException

from server.services.models import get_model_info, list_model_summaries

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("")
def list_models():
    return {"models": list_model_summaries()}


@router.get("/{model_key}/stats")
def model_stats(model_key: str):
    info = get_model_info(model_key)
    if not info:
        raise HTTPException(status_code=404, detail="Model info not found")
    return info
