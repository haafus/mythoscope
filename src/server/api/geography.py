from fastapi import APIRouter

from server.schemas import TraditionsResponse
from server.services.corpus import get_traditions_info

router = APIRouter(prefix="/api/geography", tags=["geography"])


@router.get("/traditions", response_model=TraditionsResponse)
def traditions():
    data = get_traditions_info()
    return {"traditions": data, "total": len(data)}
