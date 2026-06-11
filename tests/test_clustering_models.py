import importlib.util
import os

import numpy as np
import pytest

_spec = importlib.util.spec_from_file_location(
    "embeddings_clustering_models",
    os.path.join(os.path.dirname(__file__), "..", "src", "embeddings_clustering", "models.py"),
)
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

BaseClusteringModel = _mod.BaseClusteringModel
KMeansClustering = _mod.KMeansClustering
HDBSCANClustering = _mod.HDBSCANClustering
SpectralClusteringModel = _mod.SpectralClusteringModel
BirchClustering = _mod.BirchClustering
GMMClustering = _mod.GMMClustering
get_clustering_model = _mod.get_clustering_model
list_available_models = _mod.list_available_models


class TestGetClusteringModel:
    def test_returns_kmeans(self):
        model = get_clustering_model("kmeans")
        assert isinstance(model, KMeansClustering)

    def test_returns_hdbscan(self):
        model = get_clustering_model("hdbscan")
        assert isinstance(model, HDBSCANClustering)

    def test_returns_spectral(self):
        model = get_clustering_model("spectral")
        assert isinstance(model, SpectralClusteringModel)

    def test_returns_birch(self):
        model = get_clustering_model("birch")
        assert isinstance(model, BirchClustering)

    def test_returns_gmm(self):
        model = get_clustering_model("gmm")
        assert isinstance(model, GMMClustering)

    def test_unknown_model_raises(self):
        with pytest.raises(ValueError, match="Unknown model"):
            get_clustering_model("nonexistent")

    def test_passes_params(self):
        model = get_clustering_model("kmeans", n_clusters=5)
        assert model.n_clusters == 5


class TestListAvailableModels:
    def test_returns_list(self):
        models = list_available_models()
        assert isinstance(models, list)
        assert len(models) >= 5

    def test_contains_expected_models(self):
        models = list_available_models()
        for expected in ["kmeans", "hdbscan", "spectral", "birch", "gmm"]:
            assert expected in models


class TestKMeansClustering:
    def test_fit_predict(self):
        data = np.random.rand(50, 10)
        model = KMeansClustering(n_clusters=3)
        labels = model.fit_predict(data)
        assert len(labels) == 50
        assert len(set(labels)) <= 3

    def test_small_sample_returns_zeros(self):
        data = np.random.rand(1, 10)
        model = KMeansClustering(n_clusters=2)
        labels = model.fit_predict(data)
        assert len(labels) == 1
        assert labels[0] == 0


class TestBirchClustering:
    def test_fit_predict(self):
        data = np.random.rand(50, 10)
        model = BirchClustering(n_clusters=2)
        labels = model.fit_predict(data)
        assert len(labels) == 50


class TestBaseClusteringModel:
    def test_get_description(self):
        model = KMeansClustering(n_clusters=2)
        desc = model.get_description()
        assert "kmeans" in desc

    def test_get_params_info(self):
        model = KMeansClustering(n_clusters=2)
        info = model.get_params_info()
        assert isinstance(info, dict)
