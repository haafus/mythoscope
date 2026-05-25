import os
import logging
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Optional


logger = logging.getLogger(__name__)


try:
    from sklearn.metrics import confusion_matrix
    from sklearn.preprocessing import Normalizer
    from sklearn.decomposition import PCA
    from sklearn.manifold import TSNE
    from sklearn.preprocessing import LabelEncoder
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("sklearn is not installed. Some functionality (PCA, TSNE, confusion matrices) will be unavailable.")

try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False
    logger.warning("umap-learn is not installed. PCA will be used instead of UMAP if sklearn is available.")


def reduce_dimensions(embeddings: np.ndarray, method: str = 'umap', n_components: int = 2) -> np.ndarray:
    if len(embeddings) == 0:
        return np.array([])

    if len(embeddings) < 3:
        logger.warning(f"Too few points ({len(embeddings)}) for dimensionality reduction")
        return np.zeros((len(embeddings), n_components))

    
    if SKLEARN_AVAILABLE:
        scaler = Normalizer(norm='l2')
        embeddings_scaled = scaler.fit_transform(embeddings)
    else:
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        embeddings_scaled = np.divide(embeddings, norms, out=np.zeros_like(embeddings), where=norms!=0)

    if method == 'umap' and UMAP_AVAILABLE:
        try:
            n_neighbors = max(2, min(15, len(embeddings) - 1))
            reducer = umap.UMAP(n_components=n_components, random_state=42, n_neighbors=n_neighbors, metric='cosine')
            return reducer.fit_transform(embeddings_scaled)
        except Exception:
            logger.exception("Error using UMAP, trying PCA")
            method = 'pca'

    if method == 'pca' and SKLEARN_AVAILABLE:
        try:
            reducer = PCA(n_components=n_components, random_state=42)
            return reducer.fit_transform(embeddings_scaled)
        except Exception:
            logger.exception("Error using PCA")
            return np.zeros((len(embeddings), n_components))

    if method == 'tsne' and SKLEARN_AVAILABLE:
        try:
            perplexity = max(1, min(30, len(embeddings) - 1))
            reducer = TSNE(n_components=n_components, random_state=42, perplexity=perplexity, metric='cosine')
            return reducer.fit_transform(embeddings_scaled)
        except Exception:
            logger.exception("Error using t-SNE, trying PCA")
            if SKLEARN_AVAILABLE:
                reducer = PCA(n_components=n_components, random_state=42)
                return reducer.fit_transform(embeddings_scaled)

    logger.error("Could not reduce dimensionality (required libraries are not installed)")
    return np.zeros((len(embeddings), n_components))


def plot_clustering_results_2d(
        embeddings_2d: np.ndarray,
        predicted_labels: np.ndarray,
        true_labels: Optional[np.ndarray] = None,
        title: str = "Clustering results",
        output_path: str = None
) -> Optional[go.Figure]:
    if len(embeddings_2d) == 0:
        logger.warning("No data for visualization")
        return None

    if embeddings_2d.shape[1] < 2:
        logger.warning(f"Not enough dimensions for visualization: {embeddings_2d.shape[1]}")
        return None

    df = pd.DataFrame({
        'x': embeddings_2d[:, 0],
        'y': embeddings_2d[:, 1],
        'cluster': predicted_labels.astype(str)
    })

    if true_labels is not None:
        df['tradition'] = true_labels

    unique_clusters = sorted(set(predicted_labels))
    colors = px.colors.qualitative.Set3 + px.colors.qualitative.Dark24
    color_map = {str(c): colors[i % len(colors)] for i, c in enumerate(unique_clusters)}

    fig = go.Figure()

    for cluster in unique_clusters:
        cluster_data = df[df['cluster'] == str(cluster)]
        if len(cluster_data) == 0:
            continue

        fig.add_trace(go.Scatter(
            x=cluster_data['x'],
            y=cluster_data['y'],
            mode='markers',
            name=f"Cluster {cluster}" if cluster != -1 else "Noise",
            marker=dict(
                size=6,
                opacity=0.7,
                color=color_map[str(cluster)],
                symbol='circle' if cluster != -1 else 'x'
            ),
            text=[str(cluster)] * len(cluster_data) if true_labels is not None else None,
            hovertemplate="<b>Cluster:</b> %{text}<br><b>Tradition:</b> %{customdata}<extra></extra>" if true_labels is not None else None,
            customdata=cluster_data['tradition'] if true_labels is not None else None
        ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=18)),
        width=1000, height=800,
        legend=dict(title="Clusters", orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )

    if output_path:
        try:
            fig.write_html(output_path)
            logger.info(f"Visualization saved: {output_path}")
        except Exception:
            logger.exception("Error saving visualization")

    return fig


def plot_confusion_matrix_heatmap(
        true_labels: np.ndarray,
        predicted_labels: np.ndarray,
        output_path: str = None
) -> Optional[go.Figure]:
    mask = predicted_labels != -1
    if np.sum(mask) == 0:
        logger.warning("No data for matrix (all points are noise)")
        return None

    clean_true = true_labels[mask]
    clean_pred = predicted_labels[mask]

    
    
    cm_df = pd.crosstab(
        pd.Series(clean_true, name="Traditions"),
        pd.Series(clean_pred, name="Clusters")
    )

    fig = px.imshow(
        cm_df.values,
        x=[f"Cluster {c}" for c in cm_df.columns],
        y=cm_df.index,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="Blues",
        title="Tradition-cluster correspondence matrix"
    )

    fig.update_layout(xaxis_title="Clusters", yaxis_title="Traditions", width=800, height=600)

    if output_path:
        try:
            fig.write_html(output_path)
            logger.info(f"Confusion matrix saved: {output_path}")
        except Exception:
            logger.exception("Error saving confusion matrix")

    return fig


def plot_metrics_dashboard(
        metrics: Dict[str, Dict],
        output_path: str = None
) -> Optional[go.Figure]:
    score_types = ['silhouette_score', 'adjusted_rand_score', 'normalized_mutual_info', 'v_measure']
    plot_data = []

    for model_name, model_metrics in metrics.items():
        if 'error' not in model_metrics and model_metrics:
            for score_type in score_types:
                value = model_metrics.get(score_type)
                if value is not None:
                    plot_data.append({
                        'Model': model_name,
                        'Metric': score_type,
                        'Value': float(value)
                    })

    if not plot_data:
        logger.warning("No data for dashboard")
        return None

    fig = px.bar(
        pd.DataFrame(plot_data),
        x='Model',
        y='Value',
        color='Metric',
        barmode='group',
        title="Clustering quality metrics comparison",
        text='Value'
    )

    fig.update_layout(height=500, width=1000, yaxis_range=[0, 1.1])

    if output_path:
        try:
            fig.write_html(output_path)
            logger.info(f"Metrics dashboard saved: {output_path}")
        except Exception:
            logger.exception("Error saving metrics dashboard")

    return fig