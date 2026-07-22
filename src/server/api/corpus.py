from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from server.schemas import DocumentsResponse, TraditionsResponse
from server.services.corpus import get_document_text, get_documents, get_traditions_tree

router = APIRouter(prefix="/api/corpus", tags=["corpus"])


# Plural = the collection; singular + ?id= = one item (aligns with /api/motifs/{index}/motif).
@router.get("/documents", response_model=DocumentsResponse)
def documents():
    docs = get_documents()
    return {"documents": docs, "total": len(docs)}


@router.get("/document", response_class=PlainTextResponse)
def document(id: str = Query(..., description="document_id = hash(locator), D1")):
    text = get_document_text(id)
    if text is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return text


@router.get("/traditions", response_model=TraditionsResponse)
def traditions() -> dict:
    tree = get_traditions_tree()
    return {"traditions": tree, "total": len(tree)}
