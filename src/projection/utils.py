import logging
from typing import Any

import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import Normalizer

logger = logging.getLogger(__name__)

_UMAP_AVAILABLE = None


def _check_umap() -> bool:
    global _UMAP_AVAILABLE
    if _UMAP_AVAILABLE is None:
        try:
            import umap  # noqa: F401

            _UMAP_AVAILABLE = True
        except ImportError:
            _UMAP_AVAILABLE = False
    return _UMAP_AVAILABLE


def reduce_dimensions(
    embeddings: np.ndarray,
    method: str = "umap",
    n_components: int = 2,
    normalize: bool = False,
    fallback_on_error: bool = False,
    **kwargs: Any,
) -> np.ndarray:
    if len(embeddings) == 0:
        return np.array([])

    if len(embeddings) < 3:
        logger.warning(f"Too few points ({len(embeddings)}) for dimensionality reduction")
        return np.zeros((len(embeddings), n_components))

    data = Normalizer(norm="l2").fit_transform(embeddings) if normalize else embeddings

    try:
        return _run_reducer(data, method, n_components, **kwargs)
    except Exception:
        if not fallback_on_error or method == "pca":
            raise
        logger.exception(f"{method.upper()} failed, falling back to PCA")
        return _run_reducer(data, "pca", n_components, **kwargs)


def _run_reducer(data: np.ndarray, method: str, n_components: int, **kwargs: Any) -> np.ndarray:
    random_state = kwargs.get("random_state", 42)

    if method == "umap":
        if not _check_umap():
            raise ImportError("umap-learn is not installed")
        import umap

        n_neighbors = kwargs.get("n_neighbors", min(15, len(data) - 1))
        reducer = umap.UMAP(
            n_components=n_components,
            n_neighbors=max(2, n_neighbors),
            min_dist=kwargs.get("min_dist", 0.1),
            metric=kwargs.get("metric", "cosine"),
            random_state=random_state,
            n_jobs=-1,
        )
        result: np.ndarray = reducer.fit_transform(data)
        return result

    if method == "pca":
        from sklearn.preprocessing import StandardScaler

        actual_components = min(n_components, data.shape[1], len(data) - 1)
        scaled: np.ndarray = StandardScaler().fit_transform(data)
        reducer = PCA(n_components=max(1, actual_components), random_state=random_state)
        result = reducer.fit_transform(scaled)
        return result

    if method == "tsne":
        from sklearn.manifold import TSNE

        perplexity = kwargs.get("perplexity", min(30, len(data) - 1))
        reducer = TSNE(
            n_components=n_components,
            perplexity=max(1, perplexity),
            random_state=random_state,
            max_iter=kwargs.get("max_iter", kwargs.get("n_iter", 1000)),
            metric=kwargs.get("metric", "cosine"),
        )
        result = reducer.fit_transform(data)
        return result

    raise ValueError(f"Unknown method: {method}. Use 'umap', 'pca', or 'tsne'.")


def safe_numpy_array(emb: list | np.ndarray) -> np.ndarray:
    return np.array(emb) if isinstance(emb, list) else emb
