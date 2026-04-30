import json
import os
import logging
import colorsys
from typing import List, Dict, Optional, Tuple, Any
from warnings import warn

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.metrics.pairwise import cosine_distances

from .config import get_analyzer_config
from .utils import reduce_dimensions

MAX_TEXT_PREVIEW_LEN = 200
MAX_VIS_SAMPLES = 3000
DEFAULT_SAMPLE_SIZE = -1
HEATMAP_WIDTH = 1000
HEATMAP_HEIGHT = 900
DASHBOARD_HEIGHT = 700
DISTRIBUTION_HEIGHT = 600
DISTRIBUTION_WIDTH = 900

logger = logging.getLogger(__name__)


def _ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def _check_umap_available() -> bool:
    try:
        import umap
        return True
    except ImportError:
        logger.warning("UMAP not installed. Install with: pip install umap-learn")
        return False


def _get_color_map(traditions: List[str]) -> Dict[str, str]:
    n_traditions = len(traditions)
    base_colors = px.colors.qualitative.Plotly

    colors = [base_colors[i % len(base_colors)] for i in range(n_traditions)]

    if n_traditions > len(base_colors):
        additional_needed = n_traditions - len(base_colors)
        additional_colors = []
        for i in range(additional_needed):
            hue = (i * 0.618033988749895) % 1.0
            rgb = colorsys.hsv_to_rgb(hue, 0.7, 0.9)
            hex_color = '#{:02x}{:02x}{:02x}'.format(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
            additional_colors.append(hex_color)
        colors = colors[:-additional_needed] + additional_colors

    return {trad: colors[i] for i, trad in enumerate(sorted(traditions))}


def _reduce_dimensions_safe(
        embeddings: np.ndarray,
        method: str = 'umap',
        n_components: int = 2,
        max_samples: int = MAX_VIS_SAMPLES
) -> Optional[np.ndarray]:
    if len(embeddings) > max_samples and method in ['tsne']:
        logger.info(f"Too many samples ({len(embeddings)}) for {method.upper()}, sampling {max_samples}")
        indices = np.random.choice(len(embeddings), max_samples, replace=False)
        embeddings = embeddings[indices]

    try:
        return reduce_dimensions(embeddings, method=method, n_components=n_components)
    except Exception as e:
        logger.error(f"Dimension reduction failed for {method}: {e}")
        return None


def _create_interactive_figure_2d(
        df_plot: pd.DataFrame,
        x_col: str,
        y_col: str,
        title: str,
        color_map: dict,
        model_name: str = None,
        output_dir: str = None,
        filename: str = None
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
                customdata.append([
                    row["id"],
                    row["tradition"],
                    row["chunk_index"],
                    text_preview
                ])

            fig.add_trace(go.Scatter(
                x=trad_data[x_col],
                y=trad_data[y_col],
                mode='markers',
                name=tradition,
                marker=dict(
                    size=8,
                    opacity=0.7,
                    color=color,
                    line=dict(width=1, color='white')
                ),
                customdata=customdata,
                hovertemplate="<b>%{customdata[1]}</b><br>"
                              "ID: %{customdata[0]}<br>"
                              "Chunk: %{customdata[2]}<br>"
                              "Text: %{customdata[3]}<extra></extra>"
            ))

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=16, family='Arial, sans-serif'),
            x=0.5,
            xanchor='center'
        ),
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.15,
            xanchor='center',
            x=0.5,
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='rgba(0,0,0,0.2)',
            borderwidth=1,
            font=dict(size=11)
        ),
        hovermode='closest',
        margin=dict(l=50, r=50, t=80, b=100),
        plot_bgcolor='rgba(240,240,240,0.5)',
        paper_bgcolor='white',
        xaxis=dict(
            title=dict(text=f"{x_col.split('_')[0].upper()} component 1", font=dict(size=12)),
            gridcolor='rgba(200,200,200,0.5)',
            zerolinecolor='rgba(150,150,150,0.5)'
        ),
        yaxis=dict(
            title=dict(text=f"{y_col.split('_')[0].upper()} component 2", font=dict(size=12)),
            gridcolor='rgba(200,200,200,0.5)',
            zerolinecolor='rgba(150,150,150,0.5)'
        )
    )

    if filename and output_dir:
        path = os.path.join(output_dir, filename)
        fig.write_html(path, include_plotlyjs='cdn', full_html=True)
        logger.info(f"Saved: {path}")

    return fig


def plot_interactive_2d(
        data: List[Dict],
        sample_size: int = DEFAULT_SAMPLE_SIZE,
        save_html: bool = True,
        output_dir: str = None,
        model_name: str = None,
        method: str = 'umap'
) -> Optional[go.Figure]:
    if not data:
        logger.warning("No data for visualization.")
        return None

    if method == 'umap' and not _check_umap_available():
        logger.warning("UMAP not available, falling back to PCA")
        method = 'pca'

    if output_dir is None:
        output_dir = get_analyzer_config().output_dir

    output_dir = _ensure_dir(output_dir)

    if sample_size == DEFAULT_SAMPLE_SIZE:
        sample = data
    else:
        sample_size = min(sample_size, len(data))
        sample = data[:sample_size]

    try:
        embeddings = np.stack([item["embedding"] for item in sample])
    except Exception as e:
        logger.error(f"Failed to stack embeddings: {e}")
        return None

    embedding_2d = _reduce_dimensions_safe(embeddings, method=method, n_components=2)
    if embedding_2d is None:
        return None

    df_plot = pd.DataFrame({
        f"{method}_x": embedding_2d[:, 0],
        f"{method}_y": embedding_2d[:, 1],
        "tradition": [item["tradition"] for item in sample],
        "id": [item["id"] for item in sample],
        "chunk_index": [item["chunk_index"] for item in sample],
        "text": [item["text"] for item in sample],
    })

    traditions = sorted(df_plot["tradition"].unique())
    color_map = _get_color_map(traditions)

    title = f"{method.upper()} visualization of embeddings by tradition"
    if model_name:
        title += f" - {model_name}"

    filename = f"{method}_2d_traditions.html" if save_html else None

    fig = _create_interactive_figure_2d(
        df_plot=df_plot,
        x_col=f"{method}_x",
        y_col=f"{method}_y",
        title=title,
        color_map=color_map,
        model_name=model_name,
        output_dir=output_dir if save_html else None,
        filename=filename
    )

    return fig


def plot_distance_heatmap(
        data: List[Dict],
        output_dir: str = None,
        model_name: str = None,
        save_html: bool = True
) -> Optional[go.Figure]:
    if not data:
        logger.warning("No data for visualization.")
        return None

    if output_dir is None:
        output_dir = get_analyzer_config().output_dir

    output_dir = _ensure_dir(output_dir)

    traditions_data = {}
    for item in data:
        trad = item["tradition"]
        if trad not in traditions_data:
            traditions_data[trad] = []
        traditions_data[trad].append(item["embedding"])

    centroids = {}
    for trad, embeddings in traditions_data.items():
        centroids[trad] = np.mean(embeddings, axis=0)

    trad_list = sorted(centroids.keys())
    n_trads = len(trad_list)
    distance_matrix = np.zeros((n_trads, n_trads))

    for i, trad1 in enumerate(trad_list):
        for j, trad2 in enumerate(trad_list):
            if i <= j:
                dist = cosine_distances([centroids[trad1]], [centroids[trad2]])[0][0]
                distance_matrix[i, j] = dist
                distance_matrix[j, i] = dist

    fig = px.imshow(
        distance_matrix,
        x=trad_list,
        y=trad_list,
        text_auto='.3f',
        aspect="auto",
        color_continuous_scale="Viridis",
        title=f"Heatmap of distances between traditions{' - ' + model_name if model_name else ''}",
        labels=dict(x="Tradition", y="Tradition", color="Cosine distance")
    )

    fig.update_layout(
        width=HEATMAP_WIDTH,
        height=HEATMAP_HEIGHT,
        title=dict(
            font=dict(size=16),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            tickangle=45,
            tickfont=dict(size=11),
            side='bottom'
        ),
        yaxis=dict(
            tickfont=dict(size=11),
            title=dict(text="Tradition", font=dict(size=12))
        ),
        margin=dict(l=100, r=50, t=80, b=150)
    )

    fig.update_traces(
        textfont=dict(size=10, color='white' if distance_matrix.max() > 0.5 else 'black'),
        hovertemplate="Distance between %{x} and %{y}: %{z:.4f}<extra></extra>"
    )

    if save_html and output_dir:
        output_path = os.path.join(output_dir, "distance_heatmap.html")
        fig.write_html(output_path)
        logger.info(f"Heatmap saved: {output_path}")

    return fig


def plot_comparison_dashboard(
        data: List[Dict],
        output_dir: str = None,
        model_name: str = None,
        save_html: bool = True
) -> Optional[go.Figure]:
    if not data:
        logger.warning("No data for visualization.")
        return None

    if output_dir is None:
        output_dir = get_analyzer_config().output_dir

    output_dir = _ensure_dir(output_dir)

    if len(data) > MAX_VIS_SAMPLES:
        logger.info(f"Too much data ({len(data)}). Using sample of {MAX_VIS_SAMPLES} for visualization")
        indices = np.random.choice(len(data), MAX_VIS_SAMPLES, replace=False)
        sample_data = [data[i] for i in indices]
    else:
        sample_data = data

    try:
        embeddings = np.stack([item["embedding"] for item in sample_data])
    except Exception as e:
        logger.error(f"Failed to stack embeddings: {e}")
        return None

    methods_to_use = []
    if _check_umap_available():
        methods_to_use.append('umap')
    methods_to_use.extend(['pca', 'tsne'])

    coords_dict = {}
    for method in methods_to_use:
        logger.info(f"Computing {method.upper()}...")
        coords = _reduce_dimensions_safe(embeddings, method=method, n_components=2)
        if coords is not None:
            coords_dict[method] = coords

    if not coords_dict:
        logger.error("No visualization methods succeeded")
        return None

    traditions = [item["tradition"] for item in sample_data]
    unique_traditions = sorted(set(traditions))
    color_map = _get_color_map(unique_traditions)

    fig = make_subplots(
        rows=1, cols=len(coords_dict),
        subplot_titles=[f"<b>{m.upper()}</b>" for m in coords_dict.keys()],
        horizontal_spacing=0.12
    )

    traditions_array = np.array(traditions)

    for idx, (method, coords) in enumerate(coords_dict.items(), 1):
        for tradition in unique_traditions:
            mask = traditions_array == tradition
            indices = np.where(mask)[0]

            if len(indices) > 0:
                fig.add_trace(
                    go.Scatter(
                        x=coords[indices, 0],
                        y=coords[indices, 1],
                        mode='markers',
                        name=tradition if idx == 1 else None,
                        marker=dict(
                            size=6,
                            opacity=0.7,
                            color=color_map[tradition],
                            line=dict(width=0.5, color='white')
                        ),
                        legendgroup=tradition,
                        showlegend=(idx == 1),
                        hovertemplate=f"<b>{tradition}</b><br>"
                                      f"{method.upper()}1: %{{x:.3f}}<br>"
                                      f"{method.upper()}2: %{{y:.3f}}<extra></extra>"
                    ),
                    row=1, col=idx
                )

        fig.update_xaxes(
            title_text=f"<b>{method.upper()} 1</b>",
            row=1, col=idx,
            gridcolor='rgba(200,200,200,0.3)',
            zerolinecolor='rgba(150,150,150,0.5)'
        )
        fig.update_yaxes(
            title_text=f"<b>{method.upper()} 2</b>" if idx == 1 else None,
            row=1, col=idx,
            gridcolor='rgba(200,200,200,0.3)',
            zerolinecolor='rgba(150,150,150,0.5)'
        )

    title = f"Comparison of visualization methods{' - ' + model_name if model_name else ''}"
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=18),
            x=0.5,
            xanchor='center'
        ),
        height=DASHBOARD_HEIGHT,
        width=550 * len(coords_dict),
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.2,
            xanchor='center',
            x=0.5,
            bgcolor='rgba(255,255,255,0.95)',
            bordercolor='rgba(0,0,0,0.3)',
            borderwidth=1,
            font=dict(size=10),
            itemclick='toggle',
            itemdoubleclick='toggleothers'
        ),
        plot_bgcolor='rgba(240,240,240,0.3)',
        paper_bgcolor='white',
        hovermode='closest',
        margin=dict(l=60, r=60, t=80, b=120)
    )

    if save_html and output_dir:
        output_path = os.path.join(output_dir, "methods_comparison.html")
        fig.write_html(output_path)
        logger.info(f"Comparison dashboard saved: {output_path}")

    return fig


def plot_tradition_distribution(
        data: List[Dict],
        output_dir: str = None,
        model_name: str = None,
        save_html: bool = True
) -> Optional[go.Figure]:
    if not data:
        logger.warning("No data for visualization.")
        return None

    if output_dir is None:
        output_dir = get_analyzer_config().output_dir

    output_dir = _ensure_dir(output_dir)

    tradition_counts = {}
    for item in data:
        trad = item["tradition"]
        tradition_counts[trad] = tradition_counts.get(trad, 0) + 1

    sorted_traditions = sorted(tradition_counts.items(), key=lambda x: -x[1])
    traditions = [t[0] for t in sorted_traditions]
    counts = [t[1] for t in sorted_traditions]

    color_map = _get_color_map(traditions)
    colors = [color_map[t] for t in traditions]

    fig = go.Figure(data=[go.Pie(
        labels=traditions,
        values=counts,
        marker=dict(colors=colors, line=dict(color='white', width=2)),
        textinfo='label+percent',
        textposition='auto',
        hoverinfo='label+value+percent',
        hole=0.3,
        pull=[0.05 if i < 3 else 0 for i in range(len(traditions))]
    )])

    title = f"Distribution of texts by tradition{' - ' + model_name if model_name else ''}"
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=16),
            x=0.5,
            xanchor='center'
        ),
        showlegend=True,
        legend=dict(
            orientation='v',
            yanchor='top',
            y=1,
            xanchor='left',
            x=1.02,
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='rgba(0,0,0,0.2)',
            borderwidth=1
        ),
        height=DISTRIBUTION_HEIGHT,
        width=DISTRIBUTION_WIDTH,
        margin=dict(l=50, r=200, t=80, b=50)
    )

    if save_html and output_dir:
        output_path = os.path.join(output_dir, "tradition_distribution.html")
        fig.write_html(output_path)
        logger.info(f"Distribution chart saved: {output_path}")

    return fig


def save_summary_to_files(data: List[Dict], stats: Dict, output_dir: str = None):
    if output_dir is None:
        output_dir = get_analyzer_config().output_dir

    output_dir = _ensure_dir(output_dir)

    data_without_embeddings = []
    for item in data:
        item_copy = {k: v for k, v in item.items() if k != 'embedding'}
        data_without_embeddings.append(item_copy)

    df_summary = pd.DataFrame(data_without_embeddings)
    csv_path = os.path.join(output_dir, "embeddings_data.csv")
    df_summary.to_csv(csv_path, index=False, encoding="utf-8")
    logger.info(f"CSV saved: {csv_path}")

    txt_path = os.path.join(output_dir, "analysis_summary.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"Embedding Analysis Summary\n")
        f.write(f"{'=' * 60}\n")
        if stats.get("model"):
            f.write(f"Model: {stats['model']}\n")
        f.write(f"Total chunks in DB: {stats.get('total_chunks_in_db', stats['n_samples'])}\n")
        f.write(f"Chunks of selected model: {stats['n_samples']}\n")
        f.write(f"Embedding dimension: {stats['embedding_dim']}\n")
        f.write(f"Number of traditions: {stats['traditions']}\n")

        f.write(f"\n{'=' * 60}\n")
        f.write("DISTRIBUTION BY TRADITIONS\n")
        f.write(f"{'-' * 60}\n")
        for trad, count in sorted(stats['tradition_counts'].items(), key=lambda x: -x[1]):
            percentage = count / stats['n_samples'] * 100
            f.write(f"  {trad:<30}: {count:>4} ({percentage:>5.1f}%)\n")
        f.write(f"{'=' * 60}\n")

    logger.info(f"Text summary saved: {txt_path}")


def save_models_list(models: List[str], output_dir: str = None):
    if output_dir is None:
        output_dir = get_analyzer_config().output_dir

    output_dir = _ensure_dir(output_dir)

    list_path = os.path.join(output_dir, "models.json")

    existing_models = []
    if os.path.exists(list_path):
        try:
            with open(list_path, 'r', encoding='utf-8') as f:
                existing_models = json.load(f)
        except Exception:
            pass

    all_models = list(set(existing_models + models))
    all_models.sort()

    with open(list_path, 'w', encoding='utf-8') as f:
        json.dump(all_models, f, ensure_ascii=False, indent=2)

    logger.info(f"Models list saved: {list_path}")
    return list_path


def add_click_handler_to_html(html_path: str):
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if 'pointClickHandler' in content:
            return

        click_handler_js = '''
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
        '''

        if '</body>' in content:
            content = content.replace('</body>', click_handler_js)
        else:
            content += click_handler_js

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"Added click handler to {html_path}")
    except Exception as e:
        logger.warning(f"Failed to add click handler to {html_path}: {e}")


def generate_clickable_plots(output_dir: str, model_name: str):
    viz_files = [
        'umap_2d_traditions.html',
        'pca_2d_traditions.html',
        'tsne_2d_traditions.html'
    ]

    for filename in viz_files:
        filepath = os.path.join(output_dir, filename)
        if os.path.exists(filepath):
            add_click_handler_to_html(filepath)


def analyze_embeddings(
        collection_name: str = "corpus",
        model_name: str = None,
        generate_all_plots: bool = True
):
    from .analyzer import EmbeddingAnalyzer

    try:
        analyzer = EmbeddingAnalyzer(collection_name=collection_name, model_name=model_name)

        if not analyzer.data:
            logger.error("=" * 60)
            logger.error("ERROR: Failed to load data for analysis!")
            logger.error("=" * 60)
            logger.error("Possible reasons:")
            logger.error("1. Chroma database is empty")
            logger.error("2. No embeddings with 'model' metadata in database")
            logger.error("3. Specified model does not exist")
            logger.error(f"\nAvailable models: {analyzer.available_models}")
            logger.error("=" * 60)
            return analyzer

        analyzer.print_statistics()
        analyzer.save_summary()
        analyzer.save_models_list()

        if generate_all_plots and analyzer.data:
            data = analyzer.filter_by_model()

            if not data:
                logger.warning("No data for visualization")
                return analyzer

            logger.info("Generating visualizations...")

            for method in ['umap', 'pca']:
                logger.info(f"  - 2D {method.upper()}...")
                try:
                    plot_interactive_2d(
                        data, sample_size=DEFAULT_SAMPLE_SIZE, output_dir=analyzer.output_dir,
                        model_name=analyzer.model_name, method=method
                    )
                except Exception as e:
                    logger.error(f"    Error creating {method.upper()}: {e}")

            logger.info("  - 2D t-SNE...")
            try:
                plot_interactive_2d(
                    data, sample_size=MAX_VIS_SAMPLES, output_dir=analyzer.output_dir,
                    model_name=analyzer.model_name, method='tsne'
                )
            except Exception as e:
                logger.error(f"    Error creating t-SNE: {e}")

            logger.info("  - Distance heatmap...")
            try:
                plot_distance_heatmap(data, output_dir=analyzer.output_dir, model_name=analyzer.model_name)
            except Exception as e:
                logger.error(f"    Error creating heatmap: {e}")

            logger.info("  - Comparison dashboard...")
            try:
                plot_comparison_dashboard(data, output_dir=analyzer.output_dir, model_name=analyzer.model_name)
            except Exception as e:
                logger.error(f"    Error creating comparison dashboard: {e}")

            logger.info("  - Tradition distribution chart...")
            try:
                plot_tradition_distribution(data, output_dir=analyzer.output_dir, model_name=analyzer.model_name)
            except Exception as e:
                logger.error(f"    Error creating distribution chart: {e}")

            logger.info("  - Adding click handlers...")
            try:
                generate_clickable_plots(analyzer.output_dir, analyzer.model_name)
            except Exception as e:
                logger.error(f"    Error adding click handlers: {e}")

            logger.info(f"\nAll visualizations saved to: {analyzer.output_dir}")

    except Exception as e:
        logger.error(f"Critical error during embedding analysis: {e}")
        import traceback
        traceback.print_exc()

    return analyzer