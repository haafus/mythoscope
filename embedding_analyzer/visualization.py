import os
from typing import List, Dict

import numpy as np
import pandas as pd
import plotly.express as px

from .analyzer import EmbeddingAnalyzer
from .config import OUTPUT_DIR
from .utils import _reduce_dimensions


def plot_interactive_2d(data: List[Dict], sample_size: int = -1, save_html: bool = True):
    if not data:
        print("Нет данных для визуализации.")
        return

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
        "model": [item["model"] for item in sample]
    })

    traditions = df_plot["tradition"].unique()
    colors = px.colors.qualitative.Plotly + px.colors.qualitative.Set3 + px.colors.qualitative.Dark24
    color_map = {trad: colors[i % len(colors)] for i, trad in enumerate(traditions)}

    fig = px.scatter(
        df_plot,
        x="umap_x",
        y="umap_y",
        color="tradition",
        color_discrete_map=color_map,
        hover_data={"id": True, "chunk_index": True, "text": True, "model": False},
        title="UMAP визуализация эмбеддингов по традициям",
        labels={"tradition": "Традиция", "umap_x": "UMAP 1", "umap_y": "UMAP 2"},
        width=1200,
        height=800
    )

    fig.update_traces(
        marker=dict(size=6, opacity=0.8),
        hovertemplate="<b>Традиция:</b> %{color}<br>"
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
        output_path = os.path.join(OUTPUT_DIR, "umap_traditions.html")
        fig.write_html(output_path)

    fig.show()


def save_summary_to_files(data: List[Dict], stats: Dict):
    df_summary = pd.DataFrame(data)
    csv_path = os.path.join(OUTPUT_DIR, "umap_traditions_data.csv")
    df_summary.to_csv(csv_path, index=False, encoding="utf-8")

    txt_path = os.path.join(OUTPUT_DIR, "analysis_summary.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"Обзор анализа\n")
        f.write(f"Чанков: {stats['n_samples']}\n")
        f.write(f"Размерность: {stats['embedding_dim']}\n")
        f.write(f"Традиций: {stats['traditions']}\n")
        f.write(f"\nРаспределение по традициям:\n")
        for trad, count in sorted(stats['tradition_counts'].items(), key=lambda x: -x[1]):
            f.write(f"  {trad}: {count}\n")

    print(f"Сводка сохранена в: {csv_path} и {txt_path}")


def analyze_embeddings():
    analyzer = EmbeddingAnalyzer(collection_name="corpus")
    analyzer.print_statistics()
    analyzer.save_summary()
    plot_interactive_2d(analyzer.df, sample_size=-1)
