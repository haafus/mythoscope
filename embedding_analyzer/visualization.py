import os
from typing import List, Dict, Any

import numpy as np
import pandas as pd
import plotly.express as px
import json

from embeddings_builder.config import OUTPUT_DIR, get_model_output_dir
from .utils import _reduce_dimensions


def _ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def plot_interactive_2d(data: List[Dict], sample_size: int = -1, save_html: bool = True,
                        output_dir: str = None, model_name: str = None):
    if not data:
        print("Нет данных для визуализации.")
        return

    if output_dir is None:
        output_dir = OUTPUT_DIR

    output_dir = _ensure_dir(output_dir)

    if sample_size == -1:
        sample = data
    else:
        sample_size = min(sample_size, len(data))
        sample = data[:sample_size]

    embeddings = np.stack([item["embedding"] for item in sample])
    embedding_2d = _reduce_dimensions(embeddings)

    df_plot = pd.DataFrame({
        "umap_x": embedding_2d[:, 0],
        "umap_y": embedding_2d[:, 1],
        "tradition": [item["tradition"] for item in sample],
        "id": [item["id"] for item in sample],
        "chunk_index": [item["chunk_index"] for item in sample],
        "text": [item["text"] for item in sample],
        "text_short": [item["text"] if len(item["text"]) < 100 else item["text"][:100] + "…" for item in sample],
        "model": [item.get("model", "unknown") for item in sample]
    })

    traditions = df_plot["tradition"].unique()
    colors = px.colors.qualitative.Plotly + px.colors.qualitative.Set3 + px.colors.qualitative.Dark24
    color_map = {trad: colors[i % len(colors)] for i, trad in enumerate(traditions)}

    title = "UMAP визуализация эмбеддингов по традициям"
    if model_name:
        title += f" — {model_name}"

    fig = px.scatter(
        df_plot,
        x="umap_x",
        y="umap_y",
        color="tradition",
        color_discrete_map=color_map,
        hover_data=["id", "chunk_index", "text_short", "tradition"],
        title=title,
        labels={"tradition": "Традиция", "umap_x": "UMAP 1", "umap_y": "UMAP 2"},
        width=1200,
        height=800
    )

    fig.update_traces(
        marker=dict(size=6, opacity=0.8),
        hovertemplate="<b>Традиция:</b> %{customdata[3]}<br>"
                      "<b>ID:</b> %{customdata[0]}<br>"
                      "<b>Чанк:</b> %{customdata[1]}<br>"
                      "<b>Текст:</b> %{customdata[2]}<br>"
                      "<extra></extra>"
    )

    fig.update_layout(
        legend_title_text="Традиции",
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="rgba(0,0,0,0.2)",
            borderwidth=1
        ),
        margin=dict(l=20, r=20, t=50, b=20),
        title_font_size=18,
        xaxis_title_font_size=14,
        yaxis_title_font_size=14
    )

    if save_html:
        output_path = os.path.join(output_dir, "umap_traditions.html")
        fig.write_html(output_path)
        print(f"График сохранен: {output_path}")

    return fig


def save_summary_to_files(data: List[Dict], stats: Dict, output_dir: str = None):
    if output_dir is None:
        from embeddings_builder.config import OUTPUT_DIR
        output_dir = OUTPUT_DIR

    output_dir = _ensure_dir(output_dir)

    df_summary = pd.DataFrame(data)
    csv_path = os.path.join(output_dir, "umap_traditions_data.csv")
    df_summary.to_csv(csv_path, index=False, encoding="utf-8")

    txt_path = os.path.join(output_dir, "analysis_summary.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"Обзор анализа\n")
        f.write(f"{'=' * 50}\n")
        if stats.get("model"):
            f.write(f"Модель: {stats['model']}\n")
        f.write(f"Всего чанков: {stats.get('total_chunks_in_db', stats['n_samples'])}\n")
        f.write(f"Чанков выбранной модели: {stats['n_samples']}\n")
        f.write(f"Размерность: {stats['embedding_dim']}\n")
        f.write(f"Традиций: {stats['traditions']}\n")
        f.write(f"\nРаспределение по традициям:\n")
        f.write(f"{'-' * 50}\n")
        for trad, count in sorted(stats['tradition_counts'].items(), key=lambda x: -x[1]):
            f.write(f"  {trad}: {count}\n")
        f.write(f"{'=' * 50}\n")

    print(f"Сводка сохранена:\n  - {csv_path}\n  - {txt_path}")


def save_models_list(models: List[str], output_dir: str = None):
    if output_dir is None:
        output_dir = OUTPUT_DIR

    output_dir = _ensure_dir(output_dir)

    list_path = os.path.join(output_dir, "models.json")

    existing_models = []
    if os.path.exists(list_path):
        try:
            with open(list_path, 'r', encoding='utf-8') as f:
                existing_models = json.load(f)
        except:
            pass

    all_models = list(set(existing_models + models))
    all_models.sort()

    with open(list_path, 'w', encoding='utf-8') as f:
        json.dump(all_models, f, ensure_ascii=False, indent=2)

    print(f"Список моделей сохранен: {list_path}")
    return list_path


def analyze_embeddings(collection_name: str = "corpus", model_name: str = None):
    from .analyzer import EmbeddingAnalyzer

    analyzer = EmbeddingAnalyzer(collection_name=collection_name, model_name=model_name)
    analyzer.print_statistics()
    analyzer.save_summary()

    analyzer.save_models_list()

    fig = plot_interactive_2d(
        analyzer.filter_by_model(),
        sample_size=-1,
        output_dir=analyzer.output_dir,
        model_name=analyzer.model_name
    )

    return analyzer