import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Any, Optional, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix
from sklearn.preprocessing import StandardScaler

try:
    import umap

    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False
    print("Предупреждение: umap-learn не установлен. Используется PCA вместо UMAP.")

try:
    from sklearn.decomposition import PCA
    from sklearn.manifold import TSNE

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Предупреждение: sklearn не установлен полностью.")


def reduce_dimensions(embeddings: np.ndarray, method: str = 'umap', n_components: int = 2) -> np.ndarray:
    """Уменьшение размерности эмбеддингов"""
    if len(embeddings) == 0:
        return np.array([])

    if len(embeddings) < 3:
        print(f"Предупреждение: слишком мало точек ({len(embeddings)}) для уменьшения размерности")
        # Возвращаем нулевые координаты
        return np.zeros((len(embeddings), n_components))

    scaler = StandardScaler()
    embeddings_scaled = scaler.fit_transform(embeddings)

    if method == 'umap' and UMAP_AVAILABLE:
        try:
            reducer = umap.UMAP(n_components=n_components, random_state=42, n_neighbors=min(15, len(embeddings) - 1))
            return reducer.fit_transform(embeddings_scaled)
        except Exception as e:
            print(f"Ошибка при использовании UMAP: {e}, используем PCA")
            method = 'pca'

    if method == 'pca' and SKLEARN_AVAILABLE:
        try:
            reducer = PCA(n_components=n_components, random_state=42)
            return reducer.fit_transform(embeddings_scaled)
        except Exception as e:
            print(f"Ошибка при использовании PCA: {e}")
            return np.zeros((len(embeddings), n_components))

    if method == 'tsne' and SKLEARN_AVAILABLE:
        try:
            perplexity = min(30, len(embeddings) - 1)
            reducer = TSNE(n_components=n_components, random_state=42, perplexity=perplexity)
            return reducer.fit_transform(embeddings_scaled)
        except Exception as e:
            print(f"Ошибка при использовании t-SNE: {e}, используем PCA")
            if SKLEARN_AVAILABLE:
                reducer = PCA(n_components=n_components, random_state=42)
                return reducer.fit_transform(embeddings_scaled)

    # Фолбэк: возвращаем нули
    print("Не удалось выполнить уменьшение размерности")
    return np.zeros((len(embeddings), n_components))


def plot_clustering_results_2d(
        embeddings_2d: np.ndarray,
        predicted_labels: np.ndarray,
        true_labels: Optional[np.ndarray] = None,
        title: str = "Результаты кластеризации",
        output_path: str = None
) -> Optional[go.Figure]:
    """Визуализация результатов кластеризации в 2D"""

    if len(embeddings_2d) == 0:
        print("Нет данных для визуализации")
        return None

    if embeddings_2d.shape[1] < 2:
        print(f"Предупреждение: недостаточно размерностей для визуализации: {embeddings_2d.shape[1]}")
        return None

    df = pd.DataFrame({
        'x': embeddings_2d[:, 0],
        'y': embeddings_2d[:, 1] if embeddings_2d.shape[1] >= 2 else np.zeros(len(embeddings_2d)),
        'cluster': predicted_labels.astype(str)
    })

    if true_labels is not None:
        df['tradition'] = true_labels

    unique_clusters = sorted(set(predicted_labels))
    n_clusters = len([c for c in unique_clusters if c != -1])

    colors = px.colors.qualitative.Set3 + px.colors.qualitative.Dark24
    color_map = {str(c): colors[i % len(colors)] for i, c in enumerate(unique_clusters)}

    fig = go.Figure()

    for cluster in unique_clusters:
        cluster_data = df[df['cluster'] == str(cluster)]
        if len(cluster_data) == 0:
            continue

        cluster_name = f"Кластер {cluster}" if cluster != -1 else "Шум"

        fig.add_trace(go.Scatter(
            x=cluster_data['x'],
            y=cluster_data['y'],
            mode='markers',
            name=cluster_name,
            marker=dict(
                size=6,
                opacity=0.7,
                color=color_map[str(cluster)],
                symbol='circle' if cluster != -1 else 'x'
            ),
            text=cluster_data['tradition'] if true_labels is not None else None,
            hovertemplate="<b>Кластер:</b> %{text}<br>" +
                          "<b>Традиция:</b> %{customdata}<br>" +
                          "<extra></extra>" if true_labels is not None else None,
            customdata=cluster_data['tradition'] if true_labels is not None else None
        ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=18)),
        width=1000,
        height=800,
        showlegend=True,
        legend=dict(
            title="Кластеры",
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )

    if output_path:
        try:
            fig.write_html(output_path)
            print(f"Визуализация сохранена: {output_path}")
        except Exception as e:
            print(f"Ошибка при сохранении визуализации: {e}")

    return fig


def plot_confusion_matrix_heatmap(
        true_labels: np.ndarray,
        predicted_labels: np.ndarray,
        output_path: str = None
) -> go.Figure:
    mask = predicted_labels != -1
    if np.sum(mask) == 0:
        print("Нет данных для построения матрицы (все точки - шум)")
        return None

    clean_true = true_labels[mask]
    clean_pred = predicted_labels[mask]

    # Преобразуем строковые метки в числовые для матрицы
    from sklearn.preprocessing import LabelEncoder
    le_true = LabelEncoder()
    le_pred = LabelEncoder()

    clean_true_encoded = le_true.fit_transform(clean_true.astype(str))
    clean_pred_encoded = le_pred.fit_transform(clean_pred.astype(str))

    unique_true = le_true.classes_
    unique_pred = le_pred.classes_

    cm = confusion_matrix(clean_true_encoded, clean_pred_encoded)

    fig = px.imshow(
        cm,
        x=[f"Кластер {c}" for c in unique_pred],
        y=unique_true,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="Blues",
        title="Матрица соответствия традиций и кластеров"
    )

    fig.update_layout(
        xaxis_title="Кластеры",
        yaxis_title="Традиции",
        width=800,
        height=600
    )

    if output_path:
        fig.write_html(output_path)
        print(f"Матрица ошибок сохранена: {output_path}")

    return fig


def plot_metrics_dashboard(
        metrics: Dict[str, Dict],
        output_path: str = None
) -> go.Figure:
    models = []
    scores = []
    score_types = ['silhouette_score', 'adjusted_rand_score', 'normalized_mutual_info', 'v_measure']

    plot_data = []
    for model_name, model_metrics in metrics.items():
        if 'error' not in model_metrics and model_metrics:
            for score_type in score_types:
                value = model_metrics.get(score_type)
                if value is not None and not isinstance(value, str):
                    plot_data.append({
                        'Модель': model_name,
                        'Метрика': score_type,
                        'Значение': float(value)
                    })

    if len(plot_data) == 0:
        print("Нет данных для построения дашборда")
        return None

    df_plot = pd.DataFrame(plot_data)

    fig = px.bar(
        df_plot,
        x='Модель',
        y='Значение',
        color='Метрика',
        barmode='group',
        title="Сравнение метрик качества кластеризации",
        text='Значение'
    )

    fig.update_layout(
        height=500,
        width=1000,
        yaxis_range=[0, 1.1]
    )

    if output_path:
        fig.write_html(output_path)
        print(f"Дашборд метрик сохранен: {output_path}")

    return fig


def save_clustering_summary(
        results: Dict,
        output_dir: str,
        model_name: str,
        clustering_model: str
):
    os.makedirs(output_dir, exist_ok=True)
    summary_path = os.path.join(output_dir, f"clustering_summary_{clustering_model}.txt")

    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write(f"АНАЛИЗ КЛАСТЕРИЗАЦИИ\n")
        f.write(f"{'=' * 70}\n\n")

        f.write(f"Модель эмбеддингов: {model_name}\n")
        f.write(f"Алгоритм кластеризации: {clustering_model}\n\n")

        f.write(f"{'=' * 70}\n")
        f.write("МЕТРИКИ КАЧЕСТВА\n")
        f.write(f"{'=' * 70}\n\n")

        metrics = results.get('metrics', {})

        f.write("Внутренние метрики (без использования истинных меток):\n")
        f.write("-" * 50 + "\n")

        if metrics.get('silhouette_score') is not None:
            f.write(f"  Silhouette Score:           {metrics['silhouette_score']:.4f}\n")
            f.write(f"    (от -1 до 1, чем выше, тем лучше)\n")

        if metrics.get('davies_bouldin_score') is not None:
            f.write(f"  Davies-Bouldin Score:       {metrics['davies_bouldin_score']:.4f}\n")
            f.write(f"    (чем меньше, тем лучше)\n")

        if metrics.get('calinski_harabasz_score') is not None:
            f.write(f"  Calinski-Harabasz Score:    {metrics['calinski_harabasz_score']:.2f}\n")
            f.write(f"    (чем выше, тем лучше)\n")

        f.write(f"\n  Найдено кластеров:          {metrics.get('n_clusters_found', 0)}\n")
        f.write(f"  Шумовых точек:              {metrics.get('n_noise_points', 0)}\n")
        f.write(f"  Доля шума:                  {metrics.get('noise_ratio', 0):.2%}\n\n")

        f.write("Структура кластеров:\n")
        f.write("-" * 50 + "\n")
        f.write(f"  Среднее внутрикластерное расстояние: {metrics.get('avg_intra_distance', 0):.4f}\n")
        f.write(f"  Среднее межкластерное расстояние:    {metrics.get('avg_inter_distance', 0):.4f}\n")
        f.write(f"  Коэффициент разделения:              {metrics.get('separation_ratio', 0):.4f}\n")

        if metrics.get('separation_ratio', 0) > 1.5:
            f.write(f"    ✓ Отличное разделение кластеров\n")
        elif metrics.get('separation_ratio', 0) > 1.0:
            f.write(f"    ✓ Хорошее разделение кластеров\n")
        elif metrics.get('separation_ratio', 0) > 0.5:
            f.write(f"    ! Удовлетворительное разделение\n")
        else:
            f.write(f"    ✗ Плохое разделение кластеров\n")

        f.write(f"\n{'=' * 70}\n")
        f.write("ВНЕШНИЕ МЕТРИКИ (сравнение с традициями)\n")
        f.write(f"{'=' * 70}\n\n")

        if metrics.get('adjusted_rand_score') is not None:
            f.write(f"  Adjusted Rand Index:        {metrics['adjusted_rand_score']:.4f}\n")
            f.write(f"    (от -1 до 1, 1 - идеальное совпадение)\n")

        if metrics.get('normalized_mutual_info') is not None:
            f.write(f"  Normalized Mutual Info:     {metrics['normalized_mutual_info']:.4f}\n")
            f.write(f"    (от 0 до 1, 1 - идеальное совпадение)\n")

        if metrics.get('adjusted_mutual_info') is not None:
            f.write(f"  Adjusted Mutual Info:       {metrics['adjusted_mutual_info']:.4f}\n")

        if metrics.get('homogeneity') is not None:
            f.write(f"  Homogeneity:                {metrics['homogeneity']:.4f}\n")
            f.write(f"    (каждый кластер содержит только один класс)\n")

        if metrics.get('completeness') is not None:
            f.write(f"  Completeness:               {metrics['completeness']:.4f}\n")
            f.write(f"    (все члены класса отнесены к одному кластеру)\n")

        if metrics.get('v_measure') is not None:
            f.write(f"  V-measure:                  {metrics['v_measure']:.4f}\n")
            f.write(f"    (гармоническое среднее homogeneity и completeness)\n")

        f.write(f"\n{'=' * 70}\n")
        f.write("РАСПРЕДЕЛЕНИЕ ПО КЛАСТЕРАМ\n")
        f.write(f"{'=' * 70}\n\n")

        cluster_counts = results.get('cluster_counts', {})
        all_labels = results.get('all_labels', [])
        total_points = len(all_labels) if all_labels else 1

        for cluster, count in sorted(cluster_counts.items()):
            if cluster == -1:
                f.write(f"  Шум (некластеризовано): {count} точек ({count / total_points * 100:.1f}%)\n")
            else:
                f.write(f"  Кластер {cluster:3d}: {count:4d} точек ({count / total_points * 100:.1f}%)\n")

        f.write(f"\n{'=' * 70}\n")
        f.write("СООТВЕТСТВИЕ ТРАДИЦИЙ И КЛАСТЕРОВ\n")
        f.write(f"{'=' * 70}\n\n")

        tradition_cluster_map = results.get('tradition_cluster_map', {})
        for tradition, clusters in tradition_cluster_map.items():
            f.write(f"  {tradition}:\n")
            for cluster, count in sorted(clusters.items(), key=lambda x: -x[1]):
                if cluster == -1:
                    f.write(f"      - Шум: {count} чанков\n")
                else:
                    f.write(f"      - Кластер {cluster}: {count} чанков\n")

        f.write(f"\n{'=' * 70}\n")
        f.write("РЕКОМЕНДАЦИИ\n")
        f.write(f"{'=' * 70}\n\n")

        silhouette = metrics.get('silhouette_score')
        if silhouette is not None:
            if silhouette > 0.5:
                f.write("  ✓ Кластеризация показала отличные результаты.\n")
            elif silhouette > 0.3:
                f.write("  ! Кластеризация показала хорошие результаты, но есть пространство для улучшения.\n")
            else:
                f.write("  ✗ Кластеризация показала низкие результаты. Рекомендуется:\n")
                f.write("      - Попробовать другой алгоритм кластеризации\n")
                f.write("      - Настроить параметры текущего алгоритма\n")
                f.write("      - Увеличить размерность или качество эмбеддингов\n")

        if metrics.get('noise_ratio', 0) > 0.3:
            f.write("  ! Высокая доля шумовых точек. Рассмотрите:\n")
            f.write("      - Использование HDBSCAN для лучшего определения шума\n")
            f.write("      - Настройку параметров eps/min_samples для DBSCAN\n")

        if metrics.get('separation_ratio', 0) < 0.8 and metrics.get('separation_ratio', 0) > 0:
            f.write("  ! Кластеры плохо разделены. Возможно:\n")
            f.write("      - Эмбеддинги не достаточно качественные\n")
            f.write("      - Нужно попробовать другой метод кластеризации\n")

    print(f"Сводка сохранена: {summary_path}")
    return summary_path