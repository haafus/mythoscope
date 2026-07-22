import pytest
from pydantic import ValidationError

from server.schemas import (
    CorpusDocument,
    DocumentsResponse,
    ModelListResponse,
    ModelSummary,
    SearchRequest,
    SearchResult,
    TraditionsResponse,
)


class TestSearchRequest:
    def test_valid(self):
        req = SearchRequest(query="test query", model="model_a")
        assert req.top_k == 20

    def test_custom_top_k(self):
        req = SearchRequest(query="q", model="m", top_k=50)
        assert req.top_k == 50

    def test_empty_query_rejected(self):
        with pytest.raises(ValidationError):
            SearchRequest(query="", model="m")

    def test_top_k_too_large(self):
        with pytest.raises(ValidationError):
            SearchRequest(query="q", model="m", top_k=200)

    def test_top_k_zero(self):
        with pytest.raises(ValidationError):
            SearchRequest(query="q", model="m", top_k=0)


class TestSearchResult:
    def test_defaults(self):
        # B1: a hit carries the document reference + chunk data only.
        r = SearchResult(similarity_score=0.95)
        assert r.document_id == ""
        assert r.chunk_index == 0
        assert r.text == ""

    def test_carries_document_reference(self):
        r = SearchResult(document_id="d1", chunk_index=3, similarity_score=0.9, text="t")
        assert r.document_id == "d1" and r.chunk_index == 3

    def test_no_tradition_or_colour_on_hit(self):
        # tradition/region/url/colour are resolved on the front, never on the hit.
        r = SearchResult(document_id="d1", tradition="Greek", color="#f00", similarity_score=0.5)
        assert not hasattr(r, "tradition") or getattr(r, "tradition", None) is None
        assert not hasattr(r, "color") or getattr(r, "color", None) is None


class TestCorpusDocument:
    def test_defaults(self):
        doc = CorpusDocument(title="test")
        assert doc.document_id == ""
        assert doc.word_count == 0
        assert not hasattr(doc, "major_tradition") or doc.major_tradition == ""

    def test_reference_fields(self):
        doc = CorpusDocument(document_id="d1", title="Iliad", tradition="Greek",
                             dating="~8th c. BCE", word_count=12000)
        assert doc.tradition == "Greek" and doc.dating == "~8th c. BCE"

    def test_no_colour_field(self):
        doc = CorpusDocument(title="x", color="#f00")  # color ignored (resolved on front)
        assert not hasattr(doc, "color") or getattr(doc, "color", None) is None


class TestDocumentsResponse:
    def test_empty(self):
        resp = DocumentsResponse(documents=[], total=0)
        assert resp.total == 0

    def test_with_documents(self):
        resp = DocumentsResponse(
            documents=[CorpusDocument(title="d1"), CorpusDocument(title="d2")],
            total=2,
        )
        assert len(resp.documents) == 2


class TestTraditionsResponse:
    def test_structure(self):
        resp = TraditionsResponse(traditions={"Greek": {"color": "#red"}}, total=1)
        assert resp.total == 1


class TestModelSummary:
    def test_fields(self):
        m = ModelSummary(name="BAAI/bge-m3", key="BAAI_bge-m3")
        assert m.name == "BAAI/bge-m3"


class TestModelListResponse:
    def test_structure(self):
        resp = ModelListResponse(
            models=[ModelSummary(name="m1", key="k1")]
        )
        assert len(resp.models) == 1
