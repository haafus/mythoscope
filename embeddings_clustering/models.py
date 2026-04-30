import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from sklearn.cluster import (
    KMeans,
    AgglomerativeClustering,
    DBSCAN,
    Birch,
    SpectralClustering,
    MeanShift,
    OPTICS
)
from sklearn.preprocessing import StandardScaler


class BaseClusteringModel:

    def __init__(self, name: str, **params):
        self.name = name
        self.params = params
        self.model = None
        self.scaler = StandardScaler()

    def fit_predict(self, embeddings: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def get_params_info(self) -> Dict:
        return self.params

    def get_description(self) -> str:
        return f"{self.name}: {self.params}"


class KMeansClustering(BaseClusteringModel):
    def __init__(self, n_clusters: int = None, max_clusters: int = 1000, **kwargs):
        super().__init__("kmeans", **kwargs)
        self.n_clusters = n_clusters
        self.max_clusters = max_clusters

    def fit_predict(self, embeddings: np.ndarray) -> np.ndarray:
        if len(embeddings) < 2:
            return np.zeros(len(embeddings), dtype=int)

        embeddings_scaled = self.scaler.fit_transform(embeddings)

        if self.n_clusters is None:
            max_k = min(self.max_clusters, len(embeddings) - 1)
            if max_k < 2:
                self.n_clusters = 1
            else:
                best_k = 2
                best_score = -1

                for k in range(2, min(max_k + 1, 11)):
                    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                    labels = kmeans.fit_predict(embeddings_scaled)

                    if len(set(labels)) > 1:
                        from sklearn.metrics import silhouette_score
                        score = silhouette_score(embeddings_scaled, labels)
                        if score > best_score:
                            best_score = score
                            best_k = k

                self.n_clusters = best_k
                print(f"  • Автоматически выбрано {self.n_clusters} кластеров (silhouette={best_score:.3f})")

        self.n_clusters = max(1, min(self.n_clusters, len(embeddings)))
        self.model = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        return self.model.fit_predict(embeddings_scaled)


class AgglomerativeClusteringModel(BaseClusteringModel):

    def __init__(self, n_clusters: int = None, distance_threshold: float = None, **kwargs):
        super().__init__("agglomerative", **kwargs)
        self.n_clusters = n_clusters
        self.distance_threshold = distance_threshold

    def fit_predict(self, embeddings: np.ndarray) -> np.ndarray:
        if len(embeddings) < 2:
            return np.zeros(len(embeddings), dtype=int)

        embeddings_scaled = self.scaler.fit_transform(embeddings)

        if self.n_clusters is None and self.distance_threshold is None:
            self.distance_threshold = 1.5

        self.model = AgglomerativeClustering(
            n_clusters=self.n_clusters,
            distance_threshold=self.distance_threshold,
            metric='euclidean',
            linkage='ward'
        )
        return self.model.fit_predict(embeddings_scaled)


class DBSCANClustering(BaseClusteringModel):

    def __init__(self, eps: float = 0.5, min_samples: int = 5, auto_eps: bool = True, **kwargs):
        super().__init__("dbscan", **kwargs)
        self.eps = eps
        self.min_samples = min_samples
        self.auto_eps = auto_eps

    def fit_predict(self, embeddings: np.ndarray) -> np.ndarray:
        if len(embeddings) < 2:
            return np.zeros(len(embeddings), dtype=int)

        embeddings_scaled = self.scaler.fit_transform(embeddings)

        if self.auto_eps:
            from sklearn.neighbors import NearestNeighbors
            n_neighbors = min(20, len(embeddings) - 1)
            if n_neighbors > 1:
                nn = NearestNeighbors(n_neighbors=n_neighbors)
                nn.fit(embeddings_scaled)
                distances, _ = nn.kneighbors(embeddings_scaled)
                avg_distances = np.mean(distances, axis=1)
                self.eps = np.percentile(avg_distances, 90)
            else:
                self.eps = 0.5

        self.model = DBSCAN(eps=self.eps, min_samples=self.min_samples)
        return self.model.fit_predict(embeddings_scaled)


class SpectralClusteringModel(BaseClusteringModel):

    def __init__(self, n_clusters: int = None, max_clusters: int = 1000, **kwargs):
        super().__init__("spectral", **kwargs)
        self.n_clusters = n_clusters
        self.max_clusters = max_clusters

    def fit_predict(self, embeddings: np.ndarray) -> np.ndarray:
        if len(embeddings) < 3:
            return np.zeros(len(embeddings), dtype=int)

        embeddings_scaled = self.scaler.fit_transform(embeddings)

        if self.n_clusters is None:
            best_score = -1
            best_n = 2
            max_n = min(self.max_clusters, len(embeddings) - 1)

            for n in range(2, max_n + 1):
                try:
                    spectral = SpectralClustering(n_clusters=n, random_state=42, affinity='nearest_neighbors')
                    labels = spectral.fit_predict(embeddings_scaled)
                    if len(set(labels)) > 1:
                        from sklearn.metrics import silhouette_score
                        score = silhouette_score(embeddings_scaled, labels)
                        if score > best_score:
                            best_score = score
                            best_n = n
                except Exception:
                    continue

            self.n_clusters = best_n

        self.model = SpectralClustering(n_clusters=self.n_clusters, random_state=42, affinity='nearest_neighbors')
        return self.model.fit_predict(embeddings_scaled)


class BirchClustering(BaseClusteringModel):

    def __init__(self, n_clusters: int = None, threshold: float = 0.5, **kwargs):
        super().__init__("birch", **kwargs)
        self.n_clusters = n_clusters
        self.threshold = threshold

    def fit_predict(self, embeddings: np.ndarray) -> np.ndarray:
        if len(embeddings) < 2:
            return np.zeros(len(embeddings), dtype=int)

        embeddings_scaled = self.scaler.fit_transform(embeddings)

        self.model = Birch(n_clusters=self.n_clusters, threshold=self.threshold)
        return self.model.fit_predict(embeddings_scaled)


def get_clustering_model(model_name: str, **params) -> BaseClusteringModel:
    models = {
        'kmeans': KMeansClustering,
        'agglomerative': AgglomerativeClusteringModel,
        'dbscan': DBSCANClustering,
        'spectral': SpectralClusteringModel,
        'birch': BirchClustering,
    }

    if model_name not in models:
        available = list(models.keys())
        raise ValueError(f"Unknown model: {model_name}. Available: {available}")

    return models[model_name](**params)


def list_available_models() -> List[str]:
    return ['kmeans', 'agglomerative', 'dbscan']