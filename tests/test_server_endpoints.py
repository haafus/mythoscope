from fastapi.testclient import TestClient

from server.run_server import create_app

client = TestClient(create_app())


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

    def test_projection_response_keeps_chart_specific_fields(self):
        # The ProjectionData schema is extra="allow"; the chart-specific payload
        # (here `points`) must survive response_model serialization, not be dropped.
        from unittest.mock import patch

        payload = {"method": "umap", "points": [{"x": 1, "y": 2}], "labels": ["a"]}
        with patch("server.api.similarity.get_projection_data", return_value=payload):
            response = client.get("/api/similarity/projections/m/umap")
        assert response.status_code == 200
        data = response.json()
        assert data["method"] == "umap"
        assert data["points"] == [{"x": 1, "y": 2}]
        assert data["labels"] == ["a"]

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

        with patch("server.api.similarity._available_models", return_value=["m"]), \
             patch(
                 "server.api.similarity.similarity_service.warmup",
                 side_effect=ModuleNotFoundError("No module named 'torch'"),
             ):
            response = client.post("/api/similarity/warmup", json={"model": "m"})
        assert response.status_code == 503
