from fastapi import APIRouter

from ui_server.services.corpus import get_traditions_info

router = APIRouter(prefix="/api/geography", tags=["geography"])


@router.get("/traditions")
def traditions():
    data = get_traditions_info()
    return {"traditions": data, "total": len(data)}

