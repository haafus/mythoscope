import numpy as np
import pytest

from embedding_analyzer.utils import _check_umap, reduce_dimensions


@pytest.fixture
def random_embeddings():
    rng = np.random.default_rng(42)
    return rng.standard_normal((50, 128))


@pytest.fixture
def small_embeddings():
    rng = np.random.default_rng(42)
    return rng.standard_normal((10, 32))


class TestReduceDimensionsPCA:
    def test_basic_2d(self, random_embeddings):
        result = reduce_dimensions(random_embeddings, method="pca", n_components=2)
        assert result.shape == (50, 2)

    def test_basic_3d(self, random_embeddings):
        result = reduce_dimensions(random_embeddings, method="pca", n_components=3)
        assert result.shape == (50, 3)

    def test_no_nans(self, random_embeddings):
        result = reduce_dimensions(random_embeddings, method="pca", n_components=2)
        assert not np.isnan(result).any()

    def test_small_dataset(self, small_embeddings):
        result = reduce_dimensions(small_embeddings, method="pca", n_components=2)
        assert result.shape == (10, 2)

    def test_n_components_clamped_to_features(self):
        data = np.random.default_rng(42).standard_normal((20, 3))
        result = reduce_dimensions(data, method="pca", n_components=10)
        assert result.shape[0] == 20
        assert result.shape[1] <= 3

    def test_with_normalization(self, random_embeddings):
        result = reduce_dimensions(random_embeddings, method="pca", n_components=2, normalize=True)
        assert result.shape == (50, 2)


class TestReduceDimensionsTSNE:
    def test_basic_2d(self, small_embeddings):
        result = reduce_dimensions(small_embeddings, method="tsne", n_components=2)
        assert result.shape == (10, 2)

    def test_no_nans(self, small_embeddings):
        result = reduce_dimensions(small_embeddings, method="tsne", n_components=2)
        assert not np.isnan(result).any()

    def test_custom_perplexity(self, small_embeddings):
        result = reduce_dimensions(small_embeddings, method="tsne", n_components=2, perplexity=3)
        assert result.shape == (10, 2)


class TestReduceDimensionsUMAP:
    @pytest.fixture(autouse=True)
    def _skip_if_no_umap(self):
        if not _check_umap():
            pytest.skip("umap-learn not installed")

    def test_basic_2d(self, random_embeddings):
        result = reduce_dimensions(random_embeddings, method="umap", n_components=2)
        assert result.shape == (50, 2)

    def test_custom_params(self, random_embeddings):
        result = reduce_dimensions(random_embeddings, method="umap", n_components=2, n_neighbors=5, min_dist=0.5)
        assert result.shape == (50, 2)


class TestEdgeCases:
    def test_empty_array(self):
        result = reduce_dimensions(np.array([]).reshape(0, 10), method="pca")
        assert len(result) == 0

    def test_two_points_returns_zeros(self):
        data = np.random.default_rng(42).standard_normal((2, 10))
        result = reduce_dimensions(data, method="pca", n_components=2)
        assert result.shape == (2, 2)
        assert np.allclose(result, 0)

    def test_one_point_returns_zeros(self):
        data = np.random.default_rng(42).standard_normal((1, 10))
        result = reduce_dimensions(data, method="pca", n_components=2)
        assert result.shape == (1, 2)
        assert np.allclose(result, 0)

    def test_unknown_method_raises(self, random_embeddings):
        with pytest.raises(ValueError, match="Unknown method"):
            reduce_dimensions(random_embeddings, method="nonexistent")

    def test_fallback_on_error_to_pca(self, random_embeddings):
        result = reduce_dimensions(random_embeddings, method="umap", n_components=2, fallback_on_error=True)
        assert result.shape == (50, 2)

    def test_normalize_does_not_change_shape(self, random_embeddings):
        result_norm = reduce_dimensions(random_embeddings, method="pca", n_components=2, normalize=True)
        result_raw = reduce_dimensions(random_embeddings, method="pca", n_components=2, normalize=False)
        assert result_norm.shape == result_raw.shape
