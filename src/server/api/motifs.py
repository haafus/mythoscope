from fastapi import APIRouter, HTTPException, Query

from motifs import INDEX_LABELS
from server.schemas import MotifDetail, MotifIndexesResponse, MotifListResponse
from server.services import motifs as svc

router = APIRouter(prefix="/api/motifs", tags=["motifs"])


def _require_built() -> None:
    if not svc.is_built():
        raise HTTPException(status_code=503, detail="Motif database not built. Run `mytho motifs`.")


def _require_index(index: str) -> None:
    if index not in INDEX_LABELS:
        raise HTTPException(status_code=404, detail=f"Unknown motif index: {index}")


@router.get("/indexes", response_model=MotifIndexesResponse)
def indexes():
    _require_built()
    return {"indexes": svc.list_indexes()}


@router.get("/{index}/motifs", response_model=MotifListResponse)
def list_motifs(
    index: str,
    chapter: str = Query(""),
    division: str = Query(""),
    q: str = Query(""),
    level: int | None = Query(None, ge=0),
    tier: str = Query(""),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    _require_built()
    _require_index(index)
    return svc.list_motifs(index, chapter=chapter, division=division, q=q,
                           level=level, tier=tier, limit=limit, offset=offset)


@router.get("/{index}/cultures")
def cultures(index: str) -> dict:
    _require_built()
    _require_index(index)
    return {"index": index, "cultures": svc.culture_legend(index)}


@router.get("/{index}/stats")
def stats(index: str) -> dict:
    _require_built()
    _require_index(index)
    return svc.stats(index)


@router.get("/{index}/motif", response_model=MotifDetail)
def motif(index: str, id: str = Query(..., min_length=1)) -> dict:
    _require_built()
    _require_index(index)
    detail = svc.get_motif(index, id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Motif not found: {index}/{id}")
    return detail
