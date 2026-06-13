import numpy as np
import pytest

from clustering.metrics import calculate_clustering_metrics


class TestCalculateClusteringMetrics:
    def test_empty_embeddings(self):
        with pytest.raises(ValueError, match="Empty embeddings"):
            calculate_clustering_metrics(np.array([]), np.array([]))

    def test_single_cluster(self):
        embeddings = np.random.rand(10, 5)
        labels = np.zeros(10, dtype=int)
        result = calculate_clustering_metrics(embeddings, labels)
        assert result["n_clusters_found"] == 1
        assert result["n_noise_points"] == 0

    def test_two_clusters(self):
        embeddings = np.vstack([
            np.random.rand(10, 5) + 0,
            np.random.rand(10, 5) + 5,
        ])
        labels = np.array([0] * 10 + [1] * 10)
        result = calculate_clustering_metrics(embeddings, labels)
        assert result["n_clusters_found"] == 2
        assert "silhouette_score" in result
        assert "davies_bouldin_score" in result
        assert "calinski_harabasz_score" in result

    def test_noise_points(self):
        embeddings = np.random.rand(15, 5)
        labels = np.array([0] * 5 + [1] * 5 + [-1] * 5)
        result = calculate_clustering_metrics(embeddings, labels)
        assert result["n_noise_points"] == 5
        assert result["noise_ratio"] > 0

    def test_with_true_labels(self):
        embeddings = np.random.rand(20, 5)
        predicted = np.array([0] * 10 + [1] * 10)
        true = np.array([0] * 10 + [1] * 10)
        result = calculate_clustering_metrics(embeddings, predicted, true)
        assert "adjusted_rand_score" in result
        assert "normalized_mutual_info" in result
        assert "v_measure" in result

    def test_separation_ratio(self):
        embeddings = np.vstack([
            np.random.rand(10, 5) * 0.1,
            np.random.rand(10, 5) * 0.1 + 10,
        ])
        labels = np.array([0] * 10 + [1] * 10)
        result = calculate_clustering_metrics(embeddings, labels)
        assert "separation_ratio" in result
        assert result["separation_ratio"] > 0

    def test_cluster_compactness(self):
        embeddings = np.random.rand(20, 5)
        labels = np.array([0] * 10 + [1] * 10)
        result = calculate_clustering_metrics(embeddings, labels)
        assert "cluster_compactness" in result
        assert 0 <= result["cluster_compactness"] <= 1
