import numpy as np
import pytest

from clustering.models import (
    BirchClustering,
    GMMClustering,
    HDBSCANClustering,
    KMeansClustering,
    SpectralClusteringModel,
    get_clustering_model,
    list_available_models,
)


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
