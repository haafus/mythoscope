import logging

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from embedding_analyzer.utils import reduce_dimensions  # noqa: F401 — re-exported

logger = logging.getLogger(__name__)


def plot_clustering_results_2d(
    embeddings_2d: np.ndarray,
    predicted_labels: np.ndarray,
    true_labels: np.ndarray | None = None,
    title: str = "Clustering results",
    output_path: str = None,
) -> go.Figure | None:
    if len(embeddings_2d) == 0:
        logger.warning("No data for visualization")
        return None

    if embeddings_2d.shape[1] < 2:
        logger.warning(f"Not enough dimensions for visualization: {embeddings_2d.shape[1]}")
        return None

    df = pd.DataFrame({"x": embeddings_2d[:, 0], "y": embeddings_2d[:, 1], "cluster": predicted_labels.astype(str)})

    if true_labels is not None:
        df["tradition"] = true_labels

    unique_clusters = sorted(set(predicted_labels))
    colors = px.colors.qualitative.Set3 + px.colors.qualitative.Dark24
    color_map = {str(c): colors[i % len(colors)] for i, c in enumerate(unique_clusters)}

    fig = go.Figure()

    for cluster in unique_clusters:
        cluster_data = df[df["cluster"] == str(cluster)]
        if len(cluster_data) == 0:
            continue

        fig.add_trace(
            go.Scatter(
                x=cluster_data["x"],
                y=cluster_data["y"],
                mode="markers",
                name=f"Cluster {cluster}" if cluster != -1 else "Noise",
                marker=dict(
                    size=6, opacity=0.7, color=color_map[str(cluster)], symbol="circle" if cluster != -1 else "x"
                ),
                text=[str(cluster)] * len(cluster_data) if true_labels is not None else None,
                hovertemplate="<b>Cluster:</b> %{text}<br><b>Tradition:</b> %{customdata}<extra></extra>"
                if true_labels is not None
                else None,
                customdata=cluster_data["tradition"] if true_labels is not None else None,
            )
        )

    fig.update_layout(
        title=dict(text=title, font=dict(size=18)),
        width=1000,
        height=800,
        legend=dict(title="Clusters", orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
    )

    if output_path:
        try:
            fig.write_html(output_path)
            logger.info(f"Visualization saved: {output_path}")
        except Exception:
            logger.exception("Error saving visualization")

    return fig


def plot_confusion_matrix_heatmap(
    true_labels: np.ndarray, predicted_labels: np.ndarray, output_path: str = None
) -> go.Figure | None:
    mask = predicted_labels != -1
    if np.sum(mask) == 0:
        logger.warning("No data for matrix (all points are noise)")
        return None

    clean_true = true_labels[mask]
    clean_pred = predicted_labels[mask]

    cm_df = pd.crosstab(pd.Series(clean_true, name="Traditions"), pd.Series(clean_pred, name="Clusters"))

    fig = px.imshow(
        cm_df.values,
        x=[f"Cluster {c}" for c in cm_df.columns],
        y=cm_df.index,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="Blues",
        title="Tradition-cluster correspondence matrix",
    )

    fig.update_layout(xaxis_title="Clusters", yaxis_title="Traditions", width=800, height=600)

    if output_path:
        try:
            fig.write_html(output_path)
            logger.info(f"Confusion matrix saved: {output_path}")
        except Exception:
            logger.exception("Error saving confusion matrix")

    return fig


def plot_metrics_dashboard(metrics: dict[str, dict], output_path: str = None) -> go.Figure | None:
    score_types = ["silhouette_score", "adjusted_rand_score", "normalized_mutual_info", "v_measure"]
    plot_data = []

    for model_name, model_metrics in metrics.items():
        if "error" not in model_metrics and model_metrics:
            for score_type in score_types:
                value = model_metrics.get(score_type)
                if value is not None:
                    plot_data.append({"Model": model_name, "Metric": score_type, "Value": float(value)})

    if not plot_data:
        logger.warning("No data for dashboard")
        return None

    fig = px.bar(
        pd.DataFrame(plot_data),
        x="Model",
        y="Value",
        color="Metric",
        barmode="group",
        title="Clustering quality metrics comparison",
        text="Value",
    )

    fig.update_layout(height=500, width=1000, yaxis_range=[0, 1.1])

    if output_path:
        try:
            fig.write_html(output_path)
            logger.info(f"Metrics dashboard saved: {output_path}")
        except Exception:
            logger.exception("Error saving metrics dashboard")

    return fig
