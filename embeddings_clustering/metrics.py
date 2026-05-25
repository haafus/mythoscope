import numpy as np
import logging
from typing import Dict, Optional
from sklearn.metrics import (
    silhouette_score,
    davies_bouldin_score,
    calinski_harabasz_score,
    adjusted_rand_score,
    normalized_mutual_info_score,
    homogeneity_score,
    completeness_score,
    v_measure_score,
    adjusted_mutual_info_score,
    pairwise_distances
)

logger = logging.getLogger(__name__)


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
    metrics['noise_ratio'] = float(n_noise / len(predicted_labels)) if len(predicted_labels) > 0 else 0.0

    mask = predicted_labels != -1

    if n_clusters >= 2:
        
        clean_embeddings = embeddings[mask]
        clean_labels = predicted_labels[mask]

        unique_labels = np.unique(clean_labels)
        centroids = []
        intra_dists = []

        for label in unique_labels:
            cluster_points = clean_embeddings[clean_labels == label]
            raw_centroid = np.mean(cluster_points, axis=0)

            
            centroids.append(raw_centroid)

            if len(cluster_points) > 1:
                dist_to_centroid = np.mean(pairwise_distances(cluster_points, [raw_centroid]))
            else:
                dist_to_centroid = 0.0
            intra_dists.append(dist_to_centroid)

        metrics['avg_intra_distance'] = float(np.mean(intra_dists))

        if len(centroids) > 1:
            centroid_matrix = np.array(centroids)
            centroid_dists = pairwise_distances(centroid_matrix)
            upper_tri_indices = np.triu_indices(len(centroids), k=1)
            avg_inter_distance = np.mean(centroid_dists[upper_tri_indices])
            metrics['avg_inter_distance'] = float(avg_inter_distance)
        else:
            metrics['avg_inter_distance'] = 0.0

        if metrics['avg_intra_distance'] > 0:
            metrics['separation_ratio'] = float(metrics['avg_inter_distance'] / metrics['avg_intra_distance'])
        else:
            metrics['separation_ratio'] = float('inf') if metrics['avg_inter_distance'] > 0 else 0.0

        if len(set(clean_labels)) >= 2:
            try:
                metrics['silhouette_score'] = float(silhouette_score(clean_embeddings, clean_labels))
                metrics['davies_bouldin_score'] = float(davies_bouldin_score(clean_embeddings, clean_labels))
                metrics['calinski_harabasz_score'] = float(calinski_harabasz_score(clean_embeddings, clean_labels))
            except Exception:
                logger.exception("Error calculating internal metrics")

        if true_labels is not None and np.sum(mask) > 0:
            clean_pred = predicted_labels[mask]
            clean_true = true_labels[mask]

            external_metrics = {
                'adjusted_rand_score': adjusted_rand_score,
                'normalized_mutual_info': normalized_mutual_info_score,
                'adjusted_mutual_info': adjusted_mutual_info_score,
                'homogeneity': homogeneity_score,
                'completeness': completeness_score,
                'v_measure': v_measure_score
            }

            for metric_name, metric_func in external_metrics.items():
                try:
                    metrics[metric_name] = float(metric_func(clean_true, clean_pred))
                except Exception:
                    logger.exception(f"Error {metric_name}")
                    metrics[metric_name] = None

    if n_clusters >= 2 and metrics.get('avg_intra_distance', 0) > 0:
        metrics['cluster_compactness'] = float(1 / (1 + metrics['avg_intra_distance']))
    else:
        metrics['cluster_compactness'] = 0.0

    return metrics