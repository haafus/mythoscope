from fastapi.testclient import TestClient

from server.run_server import create_app

client = TestClient(create_app())


class TestHealthEndpoint:
    def test_returns_ok(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestSPAFallback:
    def test_spa_serves_index(self):
        response = client.get("/nonexistent/page")
        assert response.status_code == 200

    def test_missing_index_returns_404(self, tmp_path, monkeypatch):
        from server import run_server as run_mod
        from server.config import ProjectPaths

        fake_paths = ProjectPaths(
            project_root=tmp_path,
            ui_root=tmp_path,
            web_root=tmp_path,
            assets_dir=tmp_path / "a",
            analysis_dir=tmp_path / "b",
            template_dir=tmp_path / "c",
            corpus_dir=tmp_path / "d",
            corpus_chunked_dir=tmp_path / "e",
        )
        monkeypatch.setattr(run_mod, "paths", fake_paths)
        test_client = TestClient(create_app())
        response = test_client.get("/nonexistent/page")
        assert response.status_code == 404


class TestModelsEndpoint:
    def test_list_models(self):
        response = client.get("/api/models")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert isinstance(data["models"], list)


class TestCorpusCatalog:
    def test_catalog_returns_list(self):
        response = client.get("/api/corpus/catalog")
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "total" in data
        assert isinstance(data["documents"], list)
        assert data["total"] == len(data["documents"])

    def test_catalog_source_validation(self):
        response = client.get("/api/corpus/catalog?source=invalid")
        assert response.status_code == 422

    def test_catalog_chunked_source(self):
        response = client.get("/api/corpus/catalog?source=chunked")
        assert response.status_code == 200


class TestGeographyEndpoint:
    def test_traditions(self):
        response = client.get("/api/geography/traditions")
        assert response.status_code == 200
        data = response.json()
        assert "traditions" in data
        assert "total" in data


class TestCorpusDocumentEndpoint:
    def test_missing_params(self):
        response = client.get("/api/corpus/documents")
        assert response.status_code == 422

    def test_nonexistent_document(self):
        response = client.get(
            "/api/corpus/documents",
            params={
                "id": "nonexistent_xyz",
                "major_tradition": "none",
                "tradition": "none",
            },
        )
        assert response.status_code in (403, 404)


class TestSimilarityEndpoints:
    def test_search_validation(self):
        response = client.post("/api/similarity/search", json={"query": "", "model": "m"})
        assert response.status_code == 422

    def test_search_job_not_found(self):
        response = client.get("/api/similarity/search/jobs/nonexistent_id")
        assert response.status_code == 404

    def test_projection_not_found(self):
        response = client.get("/api/similarity/projections/fake_model/pca")
        assert response.status_code == 404


class TestClusteringEndpoints:
    def test_algorithms_empty(self):
        response = client.get("/api/clustering/fake_model/algorithms")
        assert response.status_code == 200
        data = response.json()
        assert data["algorithms"] == []
