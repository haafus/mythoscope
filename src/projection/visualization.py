import glob
import json
import logging
import os
import textwrap
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.metrics.pairwise import cosine_distances

from settings import settings

from .utils import reduce_dimensions

MAX_TEXT_PREVIEW_LEN = 200
MAX_VIS_SAMPLES = None
DEFAULT_SAMPLE_SIZE = -1
RANDOM_SEED = 42
HEATMAP_WIDTH = 1000
HEATMAP_HEIGHT = 900
DASHBOARD_HEIGHT = 700
DISTRIBUTION_HEIGHT = 600
DISTRIBUTION_WIDTH = 900
GRID_COLOR = "rgba(190,200,210,0.45)"
ZERO_LINE_COLOR = "rgba(120,130,140,0.55)"
AXIS_LINE_COLOR = "rgba(120,130,140,0.65)"

logger = logging.getLogger(__name__)


def _resolve_sample_limit(sample_size: int | None) -> int | None:
    if sample_size is None or sample_size == DEFAULT_SAMPLE_SIZE:
        return None
    if sample_size <= 0:
        return None
    return sample_size


def _sample_for_visualization(data: list[dict], sample_size: int | None, reason: str) -> list[dict]:
    sample_limit = _resolve_sample_limit(sample_size)
    if sample_limit is None or len(data) <= sample_limit:
        return data

    logger.info(f"Sampling {sample_limit} of {len(data)} records for {reason}")
    indices = np.random.default_rng(RANDOM_SEED).choice(len(data), sample_limit, replace=False)
    return [data[i] for i in indices]


def _ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def _check_umap_available() -> bool:
    try:
        import umap  # noqa: F401

        return True
    except ImportError:
        logger.warning("UMAP not installed. Install with: pip install umap-learn")
        return False


def _traditions_of(data: list[dict]) -> list[str]:
    return [item.get("tradition", "unknown") for item in data]


def _add_tradition_scatter_traces(
    fig: go.Figure,
    coords: np.ndarray,
    traditions_array: np.ndarray,
    color_map: dict[str, str],
    *,
    row: int,
    col: int,
    show_legend: bool,
    marker_extra: dict[str, Any] | None = None,
    x_label: str = "X",
    y_label: str = "Y",
) -> None:
    """One scatter trace per tradition (shared by the dashboard plots)."""
    for tradition in sorted(set(traditions_array.tolist())):
        indices = np.where(traditions_array == tradition)[0]
        if len(indices) == 0:
            continue
        fig.add_trace(
            go.Scatter(
                x=coords[indices, 0],
                y=coords[indices, 1],
                mode="markers",
                name=tradition if show_legend else None,
                marker={"size": 5, "opacity": 0.7, "color": color_map[tradition], **(marker_extra or {})},
                legendgroup=tradition,
                showlegend=show_legend,
                hovertemplate=(
                    f"<b>{tradition}</b><br>{x_label}: %{{x:.3f}}<br>{y_label}: %{{y:.3f}}<extra></extra>"
                ),
            ),
            row=row,
            col=col,
        )


def _get_color_map(data: list[dict]) -> dict[str, str]:
    """
    Extract tradition colors directly from the data.
    If a color is missing, assign a default from the Plotly palette.
    """
    color_map = {}
    for item in data:
        tradition = item.get("tradition", "unknown")
        color = item.get("color")
        if tradition not in color_map and color:
            color_map[tradition] = color

    base_colors = px.colors.qualitative.Plotly
    unique_traditions = sorted(set(item.get("tradition", "unknown") for item in data))

    for i, trad in enumerate(unique_traditions):
        if trad not in color_map:
            color_map[trad] = base_colors[i % len(base_colors)]

    return color_map


def _reduce_dimensions_safe(
    embeddings: np.ndarray, method: str = "umap", n_components: int = 2, reducer_kwargs: dict[str, Any] | None = None
) -> np.ndarray | None:
    if reducer_kwargs is None:
        reducer_kwargs = {}

    try:
        return reduce_dimensions(embeddings, method=method, n_components=n_components, **reducer_kwargs)
    except Exception as e:
        logger.error(f"Dimension reduction failed for {method}: {e}")
        return None


def _cartesian_axis(title: str, tickangle: int = 0, showticklabels: bool = True) -> dict[str, Any]:
    return dict(
        title=dict(text=title, font=dict(size=12)),
        showgrid=True,
        gridcolor=GRID_COLOR,
        gridwidth=1,
        zeroline=True,
        zerolinecolor=ZERO_LINE_COLOR,
        zerolinewidth=1,
        showline=True,
        linecolor=AXIS_LINE_COLOR,
        mirror=True,
        ticks="outside",
        tickfont=dict(size=10),
        tickangle=tickangle,
        showticklabels=showticklabels,
    )


def _create_interactive_figure_2d(
    df_plot: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    color_map: dict,
    model_name: str | None = None,
    output_dir: str | None = None,
    filename: str | None = None,
) -> go.Figure:
    fig = go.Figure()

    for tradition, color in color_map.items():
        trad_data = df_plot[df_plot["tradition"] == tradition]
        if not trad_data.empty:
            customdata = []
            for _, row in trad_data.iterrows():
                text_preview = row["text"][:MAX_TEXT_PREVIEW_LEN]
                if len(row["text"]) > MAX_TEXT_PREVIEW_LEN:
                    text_preview += "..."
                text_preview = "<br>".join(textwrap.wrap(text_preview, width=60))
                customdata.append(
                    [row["id"], row["tradition"], row["chunk_index"], text_preview, row.get("doc_type", "unknown")]
                )

            fig.add_trace(
                go.Scatter(
                    x=trad_data[x_col],
                    y=trad_data[y_col],
                    mode="markers",
                    name=tradition,
                    marker=dict(size=8, opacity=0.7, color=color, line=dict(width=1, color="white")),
                    customdata=customdata,
                    hovertemplate="<b>%{customdata[1]}</b><br>"
                    "Type: %{customdata[4]}<br>"
                    "ID: %{customdata[0]}<br>"
                    "Chunk: %{customdata[2]}<br>"
                    "Text: %{customdata[3]}<extra></extra>",
                )
            )

    fig.update_layout(
        title=dict(text=title, font=dict(size=16, family="Arial, sans-serif"), x=0.5, xanchor="center"),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="rgba(0,0,0,0.2)",
            borderwidth=1,
            font=dict(size=11),
        ),
        hovermode="closest",
        margin=dict(l=50, r=50, t=80, b=100),
        plot_bgcolor="rgba(240,240,240,0.5)",
        paper_bgcolor="white",
        xaxis=_cartesian_axis(f"{x_col.split('_')[0].upper()} component 1"),
        yaxis=_cartesian_axis(f"{y_col.split('_')[0].upper()} component 2"),
    )

    if filename and output_dir:
        path = os.path.join(output_dir, filename)
        fig.write_html(path, include_plotlyjs="cdn", full_html=True)
        logger.info(f"Saved: {path}")

    return fig


def plot_interactive_2d(
    data: list[dict],
    sample_size: int | None = DEFAULT_SAMPLE_SIZE,
    save_html: bool = True,
    output_dir: str | None = None,
    model_name: str | None = None,
    method: str = "umap",
    reducer_kwargs: dict[str, Any] | None = None,
) -> go.Figure | None:
    if not data:
        logger.warning("No data for visualization.")
        return None

    if method == "umap" and not _check_umap_available():
        logger.warning("UMAP not available, falling back to PCA")
        method = "pca"

    if output_dir is None:
        output_dir = str(settings.analysis_dir)

    output_dir = _ensure_dir(output_dir)
    reducer_kwargs = reducer_kwargs or {}

    sample_limit = _resolve_sample_limit(sample_size)
    if method == "tsne":
        max_vis_limit = _resolve_sample_limit(MAX_VIS_SAMPLES)
        if max_vis_limit is not None and (sample_limit is None or sample_limit > max_vis_limit):
            sample_limit = max_vis_limit
            logger.info(f"t-SNE optimization: limiting sample size to {sample_limit}")

    sample = _sample_for_visualization(data, sample_limit, f"{method.upper()} visualization")

    try:
        embeddings = np.stack([item["embedding"] for item in sample])
    except Exception as e:
        logger.error(f"Failed to stack embeddings: {e}")
        return None

    embedding_2d = _reduce_dimensions_safe(embeddings, method=method, n_components=2, reducer_kwargs=reducer_kwargs)

    if embedding_2d is None:
        return None

    df_plot = pd.DataFrame(
        {
            f"{method}_x": embedding_2d[:, 0],
            f"{method}_y": embedding_2d[:, 1],
            "tradition": [item.get("tradition", "unknown") for item in sample],
            "id": [item.get("id", "unknown") for item in sample],
            "chunk_index": [item.get("chunk_index", 0) for item in sample],
            "text": [item.get("text", "") for item in sample],
            "doc_type": [item.get("doc_type", "unknown") for item in sample],
        }
    )

    color_map = _get_color_map(data)

    params_str = ", ".join([f"{k}={v}" for k, v in reducer_kwargs.items()])
    title_suffix = f" ({params_str})" if params_str else ""
    title = f"{method.upper()} visualization by tradition{title_suffix}"

    if model_name:
        title += f" - {model_name}"

    file_params = "_".join([f"{k}-{v}" for k, v in reducer_kwargs.items()])
    filename = f"{method}_2d_{file_params + '_' if file_params else ''}traditions.html" if save_html else None

    fig = _create_interactive_figure_2d(
        df_plot=df_plot,
        x_col=f"{method}_x",
        y_col=f"{method}_y",
        title=title,
        color_map=color_map,
        model_name=model_name,
        output_dir=output_dir if save_html else None,
        filename=filename,
    )

    return fig


def plot_hyperparameter_tuning_dashboard(
    data: list[dict],
    method: str = "umap",
    param_configs: list[dict[str, Any]] | None = None,
    output_dir: str | None = None,
    model_name: str | None = None,
    save_html: bool = True,
) -> go.Figure | None:
    if not data or not param_configs:
        return None

    if output_dir is None:
        output_dir = str(settings.analysis_dir)
    output_dir = _ensure_dir(output_dir)

    sample_data = _sample_for_visualization(data, MAX_VIS_SAMPLES, f"{method.upper()} hyperparameter tuning")

    embeddings = np.stack([item["embedding"] for item in sample_data])
    traditions = _traditions_of(sample_data)
    color_map = _get_color_map(data)

    cols = min(3, len(param_configs))
    rows = (len(param_configs) - 1) // cols + 1

    titles = [
        f"{method.upper()} ({', '.join(f'{k}={v}' for k, v in cfg.items()) or 'default'})" for cfg in param_configs
    ]

    fig = make_subplots(rows=rows, cols=cols, subplot_titles=titles, horizontal_spacing=0.08, vertical_spacing=0.1)
    traditions_array = np.array(traditions)

    for idx, cfg in enumerate(param_configs):
        r = idx // cols + 1
        c = idx % cols + 1

        logger.info(f"Computing {method.upper()} with params: {cfg}")
        coords = _reduce_dimensions_safe(embeddings, method=method, n_components=2, reducer_kwargs=cfg)

        if coords is None:
            continue

        _add_tradition_scatter_traces(
            fig, coords, traditions_array, color_map, row=r, col=c, show_legend=(idx == 0),
        )

        fig.update_xaxes(**_cartesian_axis(f"{method.upper()} component 1"), row=r, col=c)
        fig.update_yaxes(**_cartesian_axis(f"{method.upper()} component 2"), row=r, col=c)

    title = f"{method.upper()} Hyperparameter Tuning{' - ' + model_name if model_name else ''}"
    fig.update_layout(
        title=dict(text=title, font=dict(size=18), x=0.5, xanchor="center"),
        height=400 * rows + 100,
        width=400 * cols,
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5),
        plot_bgcolor="rgba(248,249,250,0.95)",
        paper_bgcolor="white",
        margin=dict(l=40, r=40, t=80, b=80),
    )

    if save_html and output_dir:
        output_path = os.path.join(output_dir, f"{method}_hyperparameters_dashboard.html")
        fig.write_html(output_path)
        logger.info(f"Tuning dashboard saved: {output_path}")

    return fig


def plot_distance_heatmap(
    data: list[dict], output_dir: str | None = None, model_name: str | None = None, save_html: bool = True
) -> go.Figure | None:
    if not data:
        logger.warning("No data for visualization.")
        return None

    if output_dir is None:
        output_dir = str(settings.analysis_dir)

    output_dir = _ensure_dir(output_dir)

    traditions_data: dict[str, list] = {}
    for item in data:
        trad = item.get("tradition", "unknown")
        if trad not in traditions_data:
            traditions_data[trad] = []
        traditions_data[trad].append(item["embedding"])

    centroids = {}
    for trad, embeddings in traditions_data.items():
        centroids[trad] = np.mean(embeddings, axis=0)

    trad_list = sorted(centroids.keys())
    centroid_matrix = np.array([centroids[trad] for trad in trad_list])
    distance_matrix = cosine_distances(centroid_matrix, centroid_matrix)

    fig = px.imshow(
        distance_matrix,
        x=trad_list,
        y=trad_list,
        text_auto=".3f",
        aspect="auto",
        color_continuous_scale="Viridis",
        title=f"Heatmap of distances between traditions{' - ' + model_name if model_name else ''}",
        labels=dict(x="Tradition", y="Tradition", color="Cosine distance"),
    )

    fig.update_layout(
        width=HEATMAP_WIDTH,
        height=HEATMAP_HEIGHT,
        title=dict(font=dict(size=16), x=0.5, xanchor="center"),
        xaxis=dict(
            title=dict(text="Tradition", font=dict(size=12)),
            tickangle=45,
            tickfont=dict(size=11),
            side="bottom",
            showgrid=False,
        ),
        yaxis=dict(tickfont=dict(size=11), title=dict(text="Tradition", font=dict(size=12)), showgrid=False),
        margin=dict(l=100, r=50, t=80, b=150),
    )

    fig.update_traces(
        textfont=dict(size=10, color="white" if distance_matrix.max() > 0.5 else "black"),
        hovertemplate="Distance between %{x} and %{y}: %{z:.4f}<extra></extra>",
    )

    if save_html and output_dir:
        output_path = os.path.join(output_dir, "distance_heatmap.html")
        fig.write_html(output_path)
        logger.info(f"Heatmap saved: {output_path}")

    return fig


def plot_comparison_dashboard(
    data: list[dict],
    output_dir: str | None = None,
    model_name: str | None = None,
    save_html: bool = True,
    baseline_configs: dict[str, Any] | None = None,
) -> go.Figure | None:
    if not data:
        logger.warning("No data for visualization.")
        return None

    if output_dir is None:
        output_dir = str(settings.analysis_dir)

    output_dir = _ensure_dir(output_dir)

    sample_data = _sample_for_visualization(data, MAX_VIS_SAMPLES, "cross-method comparison dashboard")

    try:
        embeddings = np.stack([item["embedding"] for item in sample_data])
    except Exception as e:
        logger.error(f"Failed to stack embeddings: {e}")
        return None

    methods_to_use = []
    if _check_umap_available():
        methods_to_use.append("umap")
    methods_to_use.extend(["pca", "tsne"])

    if baseline_configs is None:
        baseline_configs = settings.projection.baseline_configs

    coords_dict = {}
    for method in methods_to_use:
        logger.info(f"Computing {method.upper()} for comparison dashboard")

        kwargs = baseline_configs.get(method, {})

        coords = _reduce_dimensions_safe(embeddings, method=method, n_components=2, reducer_kwargs=kwargs)
        if coords is not None:
            coords_dict[method] = coords

    traditions = _traditions_of(sample_data)
    color_map = _get_color_map(data)

    fig = make_subplots(
        rows=1,
        cols=len(coords_dict),
        subplot_titles=[f"<b>{m.upper()}</b>" for m in coords_dict],
        horizontal_spacing=0.12,
    )

    traditions_array = np.array(traditions)

    for idx, (method, coords) in enumerate(coords_dict.items(), 1):
        _add_tradition_scatter_traces(
            fig, coords, traditions_array, color_map,
            row=1, col=idx, show_legend=(idx == 1),
            marker_extra={"size": 6, "line": dict(width=0.5, color="white")},
            x_label=f"{method.upper()} component 1",
            y_label=f"{method.upper()} component 2",
        )

        fig.update_xaxes(**_cartesian_axis(f"{method.upper()} component 1"), row=1, col=idx)
        fig.update_yaxes(**_cartesian_axis(f"{method.upper()} component 2"), row=1, col=idx)

    title = f"Comparison of visualization methods{' - ' + model_name if model_name else ''}"
    fig.update_layout(
        title=dict(text=title, font=dict(size=18), x=0.5, xanchor="center"),
        height=DASHBOARD_HEIGHT,
        width=550 * len(coords_dict),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="rgba(0,0,0,0.3)",
            borderwidth=1,
            font=dict(size=10),
            itemclick="toggle",
            itemdoubleclick="toggleothers",
        ),
        plot_bgcolor="rgba(248,249,250,0.95)",
        paper_bgcolor="white",
        hovermode="closest",
        margin=dict(l=60, r=60, t=80, b=120),
    )

    if save_html and output_dir:
        output_path = os.path.join(output_dir, "methods_comparison.html")
        fig.write_html(output_path)
        logger.info(f"Comparison dashboard saved: {output_path}")

    return fig


def plot_tradition_distribution(
    data: list[dict], output_dir: str | None = None, model_name: str | None = None, save_html: bool = True
) -> go.Figure | None:
    if not data:
        logger.warning("No data for visualization.")
        return None

    if output_dir is None:
        output_dir = str(settings.analysis_dir)

    output_dir = _ensure_dir(output_dir)

    tradition_counts: dict[str, int] = {}
    tradition_docs: dict[str, set] = {}
    for item in data:
        trad = item.get("tradition", "unknown")
        tradition_counts[trad] = tradition_counts.get(trad, 0) + 1
        tradition_docs.setdefault(trad, set()).add(item.get("id", "unknown"))

    sorted_traditions = sorted(tradition_counts.items(), key=lambda x: -x[1])
    traditions = [t[0] for t in sorted_traditions]
    counts = [t[1] for t in sorted_traditions]
    total_chunks = sum(counts)
    percentages = [(count / total_chunks * 100) if total_chunks else 0 for count in counts]
    doc_counts = [len(tradition_docs.get(trad, set())) for trad in traditions]

    color_map = _get_color_map(data)
    colors = [color_map[t] for t in traditions]

    fig = go.Figure(
        data=[
            go.Bar(
                x=counts,
                y=traditions,
                orientation="h",
                marker=dict(color=colors, line=dict(color="rgba(255,255,255,0.9)", width=1)),
                customdata=np.column_stack([percentages, doc_counts]),
                text=[f"{count:,} chunks ({pct:.1f}%)" for count, pct in zip(counts, percentages, strict=False)],
                textposition="outside",
                cliponaxis=False,
                hovertemplate="<b>%{y}</b><br>"
                "Chunks: %{x:,}<br>"
                "Share: %{customdata[0]:.2f}%<br>"
                "Source texts: %{customdata[1]}<extra></extra>",
            )
        ]
    )

    title = f"Distribution of chunks by tradition{' - ' + model_name if model_name else ''}"
    fig.update_layout(
        title=dict(text=title, font=dict(size=16), x=0.5, xanchor="center"),
        showlegend=False,
        height=max(DISTRIBUTION_HEIGHT, 28 * len(traditions) + 180),
        width=max(DISTRIBUTION_WIDTH, 1050),
        margin=dict(l=180, r=160, t=90, b=80),
        plot_bgcolor="rgba(248,249,250,0.95)",
        paper_bgcolor="white",
        xaxis=_cartesian_axis("Number of chunks"),
        yaxis=dict(
            title=dict(text="Tradition", font=dict(size=12)),
            autorange="reversed",
            showgrid=False,
            showline=True,
            linecolor=AXIS_LINE_COLOR,
            ticks="outside",
            tickfont=dict(size=11),
        ),
    )

    if save_html and output_dir:
        output_path = os.path.join(output_dir, "tradition_distribution.html")
        fig.write_html(output_path)
        logger.info(f"Distribution chart saved: {output_path}")

    return fig


def save_summary_to_files(data: list[dict], stats: dict, output_dir: str | None = None):
    if output_dir is None:
        output_dir = str(settings.analysis_dir)

    output_dir = _ensure_dir(output_dir)

    data_without_embeddings = []
    for item in data:
        item_copy = {k: v for k, v in item.items() if k != "embedding"}
        data_without_embeddings.append(item_copy)

    df_summary = pd.DataFrame(data_without_embeddings)
    csv_path = os.path.join(output_dir, "embeddings_data.csv")
    df_summary.to_csv(csv_path, index=False, encoding="utf-8")
    logger.info(f"CSV saved: {csv_path}")

    txt_path = os.path.join(output_dir, "analysis_summary.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("Embedding Analysis Summary\n")
        if stats.get("model"):
            f.write(f"Model: {stats['model']}\n")
        f.write(f"Total chunks in DB: {stats.get('total_chunks_in_db', stats['n_samples'])}\n")
        f.write(f"Chunks of selected model: {stats['n_samples']}\n")
        f.write(f"Embedding dimension: {stats['embedding_dim']}\n")
        f.write(f"Number of traditions: {stats['traditions']}\n")

        f.write("\n")
        f.write("DISTRIBUTION BY TRADITIONS\n")
        for trad, count in sorted(stats["tradition_counts"].items(), key=lambda x: -x[1]):
            percentage = count / stats["n_samples"] * 100
            f.write(f"  {trad:<30}: {count:>4} ({percentage:>5.1f}%)\n")

    logger.info(f"Text summary saved: {txt_path}")


def save_models_list(models: list[str], output_dir: str | None = None):
    if output_dir is None:
        output_dir = str(settings.analysis_dir)

    output_dir = _ensure_dir(output_dir)

    list_path = os.path.join(output_dir, "models.json")

    existing_models = []
    if os.path.exists(list_path):
        try:
            with open(list_path, encoding="utf-8") as f:
                existing_models = json.load(f)
        except Exception:
            pass

    all_models = list(set(existing_models + models))
    all_models.sort()

    with open(list_path, "w", encoding="utf-8") as f:
        json.dump(all_models, f, ensure_ascii=False, indent=2)

    logger.info(f"Models list saved: {list_path}")
    return list_path


def add_click_handler_to_html(html_path: str):
    try:
        with open(html_path, encoding="utf-8") as f:
            content = f.read()

        if "pointClickHandler" in content:
            return

        click_handler_js = """
        <script>
        (function() {
            function getUrlParameter(name) {
                const urlParams = new URLSearchParams(window.location.search);
                return urlParams.get(name);
            }

            function sendPointClick(pointId) {
                if (window.parent !== window) {
                    window.parent.postMessage({
                        type: 'pointClicked',
                        pointId: pointId
                    }, '*');
                }
            }

            function addClickHandler() {
                setTimeout(function() {
                    const plotDiv = document.querySelector('.plotly-graph-div') || document.getElementById('plotly-graph');
                    if (plotDiv && plotDiv.on) {
                        plotDiv.on('plotly_click', function(data) {
                            if (data.points && data.points[0] && data.points[0].customdata) {
                                let pointId = data.points[0].customdata[0];
                                if (pointId) {
                                    sendPointClick(pointId);
                                }
                            }
                        });
                        console.log('Click handler added to plot');
                    } else {
                        setTimeout(addClickHandler, 500);
                    }
                }, 1000);
            }

            addClickHandler();
        })();
        </script>
        </body>
        """

        if "</body>" in content:
            content = content.replace("</body>", click_handler_js)
        else:
            content += click_handler_js

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Added click handler to {html_path}")
    except Exception as e:
        logger.warning(f"Failed to add click handler to {html_path}: {e}")


def generate_clickable_plots(output_dir: str, model_name: str):

    html_files = glob.glob(os.path.join(output_dir, "*.html"))

    if not html_files:
        logger.warning(f"No HTML files found in {output_dir} to make clickable.")
        return

    for filepath in html_files:
        add_click_handler_to_html(filepath)


def analyze_embeddings(model_name: str | None = None, generate_all_plots: bool = True):
    from .analyzer import EmbeddingAnalyzer

    try:
        base_analyzer = EmbeddingAnalyzer()
        available_models = base_analyzer.available_models

        if not available_models:
            logger.error("ERROR: No available models in the Chroma database!")
            return None

        models_to_analyze = [model_name] if model_name else available_models
        logger.info(f"Models queued for analysis: {models_to_analyze}")

        for current_model in models_to_analyze:
            logger.info(f"Starting model analysis: {current_model}")

            analyzer = EmbeddingAnalyzer(model_name=current_model)

            if not analyzer.data:
                logger.warning(f"No data found for model {current_model} has no data, skipping...")
                continue

            analyzer.print_statistics()
            analyzer.save_summary()
            analyzer.save_models_list()

            if generate_all_plots and analyzer.data:
                data = analyzer.filter_by_model()

                logger.info("Generating visualizations with hyperparameter variations...")

                config = settings.projection
                umap_configs = config.umap_configs
                tsne_configs = config.tsne_configs
                pca_configs = config.pca_configs
                baseline_configs = config.baseline_configs

                configs_map = {"umap": umap_configs, "tsne": tsne_configs, "pca": pca_configs}

                for method, configs in configs_map.items():
                    if method == "umap" and not _check_umap_available():
                        continue

                    logger.info(f"  - Generating individual {method.upper()} plots...")
                    for cfg in configs:
                        try:
                            plot_interactive_2d(
                                data,
                                sample_size=DEFAULT_SAMPLE_SIZE,
                                output_dir=analyzer.output_dir,
                                model_name=analyzer.model_name,
                                method=method,
                                reducer_kwargs=cfg,
                            )
                        except Exception as e:
                            logger.error(f"    Error creating {method.upper()} with {cfg}: {e}")

                logger.info("  - Generating hyperparameter tuning dashboards...")
                try:
                    if _check_umap_available():
                        plot_hyperparameter_tuning_dashboard(
                            data,
                            method="umap",
                            param_configs=umap_configs,
                            output_dir=analyzer.output_dir,
                            model_name=analyzer.model_name,
                        )
                    plot_hyperparameter_tuning_dashboard(
                        data,
                        method="tsne",
                        param_configs=tsne_configs,
                        output_dir=analyzer.output_dir,
                        model_name=analyzer.model_name,
                    )
                except Exception as e:
                    logger.error(f"    Error creating hyperparameter dashboards: {e}")

                logger.info("  - Generating cross-method comparison dashboard...")
                try:
                    plot_comparison_dashboard(
                        data,
                        output_dir=analyzer.output_dir,
                        model_name=analyzer.model_name,
                        baseline_configs=baseline_configs,
                    )
                except Exception as e:
                    logger.error(f"    Error creating comparison dashboard: {e}")

                logger.info("  - Distance heatmap...")
                try:
                    plot_distance_heatmap(data, output_dir=analyzer.output_dir, model_name=analyzer.model_name)
                except Exception as e:
                    logger.error(f"    Error creating heatmap: {e}")

                logger.info("  - Tradition distribution chart...")
                try:
                    plot_tradition_distribution(data, output_dir=analyzer.output_dir, model_name=analyzer.model_name)
                except Exception as e:
                    logger.error(f"    Error creating distribution chart: {e}")

                logger.info("  - Adding click handlers...")
                try:
                    if analyzer.model_name:
                        generate_clickable_plots(analyzer.output_dir, analyzer.model_name)
                except Exception as e:
                    logger.error(f"    Error adding click handlers: {e}")

                logger.info(f"\nAll visualizations for {current_model} saved to: {analyzer.output_dir}")

        return analyzer

    except Exception as e:
        logger.error(f"Critical error during embedding analysis: {e}")
        import traceback

        traceback.print_exc()
        return None
