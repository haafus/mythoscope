import numpy as np
from typing import Dict, List, Optional
from sklearn.metrics import (
    silhouette_score,
    davies_bouldin_score,
    calinski_harabasz_score,
    adjusted_rand_score,
    normalized_mutual_info_score,
    homogeneity_score,
    completeness_score,
    v_measure_score,
    adjusted_mutual_info_score
)


def calculate_clustering_metrics(
        embeddings: np.ndarray,
        predicted_labels: np.ndarray,
        true_labels: Optional[np.ndarray] = None
) -> Dict[str, float]:
    metrics = {}

    if len(embeddings) == 0:
        return {'error': 'Empty embeddings array'}

    n_clusters = len(set(predicted_labels)) - (1 if -1 in predicted_labels else 0)
    n_noise = np.sum(predicted_labels == -1)

    metrics['n_clusters_found'] = n_clusters
    metrics['n_noise_points'] = n_noise
    metrics['noise_ratio'] = n_noise / len(predicted_labels) if len(predicted_labels) > 0 else 0

    if n_clusters >= 2:
        mask = predicted_labels != -1
        n_points = np.sum(mask)

        if n_points > n_clusters and n_points >= 2:
            clean_embeddings = embeddings[mask]
            clean_labels = predicted_labels[mask]

            try:
                if n_points >= 3:
                    metrics['silhouette_score'] = silhouette_score(clean_embeddings, clean_labels)
                else:
                    metrics['silhouette_score'] = None
            except Exception as e:
                metrics['silhouette_score'] = None

            try:
                metrics['davies_bouldin_score'] = davies_bouldin_score(clean_embeddings, clean_labels)
            except Exception:
                metrics['davies_bouldin_score'] = None

            try:
                metrics['calinski_harabasz_score'] = calinski_harabasz_score(clean_embeddings, clean_labels)
            except Exception:
                metrics['calinski_harabasz_score'] = None

    unique_labels = [l for l in set(predicted_labels) if l != -1]
    intra_distances = []

    for label in unique_labels:
        cluster_points = embeddings[predicted_labels == label]
        if len(cluster_points) > 1:
            centroid = cluster_points.mean(axis=0)
            intra_distances.append(np.mean(np.linalg.norm(cluster_points - centroid, axis=1)))

    metrics['avg_intra_distance'] = np.mean(intra_distances) if intra_distances else 0.0

    if len(unique_labels) > 1:
        centroids = []
        for label in unique_labels:
            cluster_points = embeddings[predicted_labels == label]
            if len(cluster_points) > 0:
                centroids.append(cluster_points.mean(axis=0))

        if len(centroids) > 1:
            centroids = np.array(centroids)
            from sklearn.metrics.pairwise import euclidean_distances
            dist_matrix = euclidean_distances(centroids)
            inter_distances = dist_matrix[np.triu_indices_from(dist_matrix, k=1)]
            metrics['avg_inter_distance'] = np.mean(inter_distances)

            if metrics['avg_intra_distance'] > 0:
                metrics['separation_ratio'] = metrics['avg_inter_distance'] / metrics['avg_intra_distance']
            else:
                metrics['separation_ratio'] = 0.0
        else:
            metrics['avg_inter_distance'] = 0.0
            metrics['separation_ratio'] = 0.0
    else:
        metrics['avg_inter_distance'] = 0.0
        metrics['separation_ratio'] = 0.0

    if true_labels is not None and n_clusters >= 2:
        mask = predicted_labels != -1
        if np.sum(mask) > 0:
            clean_pred = predicted_labels[mask]
            clean_true = true_labels[mask]

            unique_pred = np.unique(clean_pred)
            pred_mapping = {old: new for new, old in enumerate(unique_pred)}
            clean_pred_mapped = np.array([pred_mapping[l] for l in clean_pred])

            unique_true = np.unique(clean_true)
            true_mapping = {old: new for new, old in enumerate(unique_true)}
            clean_true_mapped = np.array([true_mapping[l] for l in clean_true])

            try:
                metrics['adjusted_rand_score'] = adjusted_rand_score(clean_true_mapped, clean_pred_mapped)
            except Exception:
                metrics['adjusted_rand_score'] = None

            try:
                metrics['normalized_mutual_info'] = normalized_mutual_info_score(clean_true_mapped, clean_pred_mapped)
            except Exception:
                metrics['normalized_mutual_info'] = None

            try:
                metrics['adjusted_mutual_info'] = adjusted_mutual_info_score(clean_true_mapped, clean_pred_mapped)
            except Exception:
                metrics['adjusted_mutual_info'] = None

            try:
                metrics['homogeneity'] = homogeneity_score(clean_true_mapped, clean_pred_mapped)
            except Exception:
                metrics['homogeneity'] = None

            try:
                metrics['completeness'] = completeness_score(clean_true_mapped, clean_pred_mapped)
            except Exception:
                metrics['completeness'] = None

            try:
                metrics['v_measure'] = v_measure_score(clean_true_mapped, clean_pred_mapped)
            except Exception:
                metrics['v_measure'] = None

    if n_clusters >= 2 and metrics.get('avg_intra_distance', 0) > 0:
        metrics['cluster_compactness'] = 1 / (1 + metrics['avg_intra_distance'])
    else:
        metrics['cluster_compactness'] = 0.0

    return metrics


def evaluate_all_models(
        embeddings: np.ndarray,
        true_labels: np.ndarray,
        models_to_test: List[str] = None
) -> Dict[str, Dict]:
    from .models import get_clustering_model, list_available_models

    if models_to_test is None:
        models_to_test = list_available_models()

    results = {}

    if len(embeddings) == 0:
        return {'error': 'Empty embeddings array'}

    for model_name in models_to_test:
        try:
            n_true_clusters = len(np.unique(true_labels))

            if model_name in ['kmeans', 'agglomerative', 'spectral']:
                model = get_clustering_model(model_name, n_clusters=n_true_clusters)
            elif model_name == 'gmm':
                model = get_clustering_model(model_name, n_components=n_true_clusters)
            else:
                model = get_clustering_model(model_name)

            predicted = model.fit_predict(embeddings)
            metrics = calculate_clustering_metrics(embeddings, predicted, true_labels)
            results[model_name] = metrics

        except Exception as e:
            print(f"Ошибка при тестировании модели {model_name}: {e}")
            results[model_name] = {'error': str(e)}

    return results