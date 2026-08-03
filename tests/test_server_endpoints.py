import json

import pytest
from fastapi.testclient import TestClient

from server.run_server import create_app
from server.services.projections import _build
from settings import settings

client = TestClient(create_app())


@pytest.fixture
def projection_file(tmp_path, monkeypatch):
    """A real projection on disk, with the payload cache cleared around it.

    The route serves cached bytes, so these tests point settings at a temp dir
    and drop the cache rather than mocking the service out — the cache and the
    gzip passthrough are the parts worth covering.
    """
    model_dir = tmp_path / "m"
    model_dir.mkdir()
    path = model_dir / "umap.json"
    path.write_text(json.dumps({"points": [{"x": 1, "y": 2}], "labels": ["a"]}))

    monkeypatch.setattr(settings, "projections_dir", tmp_path)
    _build.cache_clear()
    yield path
    _build.cache_clear()


class TestSPA:
    def test_spa_serves_index(self):
        response = client.get("/")
        assert response.status_code == 200


class TestModelsEndpoint:
    def test_list_models(self):
        from unittest.mock import patch

        with patch("server.api.similarity.chroma_manager") as mock_cm, \
                patch("server.api.similarity._text_search_available", return_value=True):
            mock_cm.get_available_models.return_value = []
            response = client.get("/api/similarity/models")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert isinstance(data["models"], list)
        # text_search capability rides on this existing response.
        assert data["text_search"] is True

    def test_list_models_hides_text_search_without_embedding_stack(self):
        from unittest.mock import patch

        with patch("server.api.similarity.chroma_manager") as mock_cm, \
                patch("server.api.similarity._text_search_available", return_value=False):
            mock_cm.get_available_models.return_value = []
            response = client.get("/api/similarity/models")
        assert response.status_code == 200
        assert response.json()["text_search"] is False

    def test_settings_flag_gates_text_search_and_warmup(self):
        from unittest.mock import patch

        from settings import settings

        with patch.object(settings.server, "text_search", False):
            with patch("server.api.similarity.chroma_manager") as mock_cm:
                mock_cm.get_available_models.return_value = []
                assert client.get("/api/similarity/models").json()["text_search"] is False
            r = client.post("/api/similarity/warmup", json={"model": "any"})
            assert r.status_code == 200 and r.json()["status"] == "skipped"


class TestCorpusCatalog:
    def test_documents_returns_list(self):
        response = client.get("/api/corpus/documents")
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "total" in data
        assert isinstance(data["documents"], list)
        assert data["total"] == len(data["documents"])

    def test_documents_ignores_unknown_params(self):
        response = client.get("/api/corpus/documents?source=anything")
        assert response.status_code == 200


class TestTraditionsEndpoint:
    def test_traditions(self):
        response = client.get("/api/corpus/traditions")
        assert response.status_code == 200
        data = response.json()
        assert "traditions" in data
        assert "total" in data


class TestCorpusDocumentEndpoint:
    def test_missing_id(self):
        response = client.get("/api/corpus/document")
        assert response.status_code == 422

    def test_nonexistent_document(self):
        response = client.get("/api/corpus/document", params={"id": "nonexistent_xyz"})
        assert response.status_code == 404


class TestSimilarityEndpoints:
    def test_search_validation(self):
        response = client.post("/api/similarity/search", json={"query": "", "model": "m"})
        assert response.status_code == 422

    def test_projection_not_found(self):
        response = client.get("/api/similarity/projections/fake_model/umap")
        assert response.status_code == 404

    def test_methods_match_schema(self):
        response = client.get("/api/similarity/methods")
        assert response.status_code == 200
        methods = response.json()
        assert methods and all({"key", "label", "chart_type"} <= set(m) for m in methods)

    def test_projection_response_keeps_chart_specific_fields(self, projection_file):
        # The ProjectionData schema is extra="allow"; the chart-specific payload
        # (here `points`) must survive, not be dropped. The route now returns
        # pre-encoded bytes, so this goes through the real cache rather than a
        # mocked service.
        response = client.get("/api/similarity/projections/m/umap")
        assert response.status_code == 200
        data = response.json()
        assert data["method"] == "umap"
        assert data["points"] == [{"x": 1, "y": 2}]
        assert data["labels"] == ["a"]

    def test_projection_serves_gzip_without_double_compressing(self, projection_file):
        # The body is cached pre-compressed; GZipMiddleware must pass it through
        # rather than gzip it a second time (which httpx would fail to decode).
        response = client.get(
            "/api/similarity/projections/m/umap", headers={"accept-encoding": "gzip"}
        )
        assert response.status_code == 200
        assert response.headers["content-encoding"] == "gzip"
        assert response.json()["points"] == [{"x": 1, "y": 2}]

    def test_projection_revalidates_with_etag(self, projection_file):
        first = client.get("/api/similarity/projections/m/umap")
        etag = first.headers["etag"]
        assert etag

        again = client.get(
            "/api/similarity/projections/m/umap", headers={"if-none-match": etag}
        )
        assert again.status_code == 304
        assert not again.content

    def test_projection_cache_follows_the_file(self, projection_file):
        before = client.get("/api/similarity/projections/m/umap").json()
        assert before["labels"] == ["a"]

        # A `push-outputs` swap replaces the file; the cache key is mtime+size,
        # so the next request must reflect the new contents.
        projection_file.write_text(
            json.dumps({"points": [{"x": 1, "y": 2}], "labels": ["a", "b"]})
        )
        after = client.get("/api/similarity/projections/m/umap").json()
        assert after["labels"] == ["a", "b"]

    def test_search_without_embedding_models_returns_503(self):
        # collection exists, but text encoding (torch) is missing -> 503, not 500.
        from unittest.mock import patch

        with patch("server.api.similarity._available_models", return_value=["m"]), \
             patch(
                 "server.api.similarity.similarity_service.search",
                 side_effect=ModuleNotFoundError("No module named 'torch'"),
             ):
            response = client.post("/api/similarity/search", json={"query": "hero", "model": "m"})
        assert response.status_code == 503

    def test_warmup_without_embedding_models_returns_503(self):
        # Same contract as search: missing torch -> 503, not 500.
        from unittest.mock import patch

        # Force past the text-search-available gate and the collection check so we
        # exercise the warmup ImportError -> 503 path itself (not the graceful skip).
        with patch("server.api.similarity._text_search_available", return_value=True), \
             patch("server.api.similarity._available_models", return_value=["m"]), \
             patch(
                 "server.api.similarity.similarity_service.warmup",
                 side_effect=ModuleNotFoundError("No module named 'torch'"),
             ):
            response = client.post("/api/similarity/warmup", json={"model": "m"})
        assert response.status_code == 503
