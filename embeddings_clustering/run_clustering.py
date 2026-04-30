#!/usr/bin/env python3

import os
import sys
import argparse
import json
import numpy as np
from pathlib import Path

# Добавляем корень проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from embedding_analyzer.analyzer import EmbeddingAnalyzer
except ImportError:
    print("Ошибка: embedding_analyzer не найден. Убедитесь, что он установлен или находится в проекте.")
    sys.exit(1)

# Импортируем функции из локального модуля visualization
from .visualization import (
    plot_clustering_results_2d,
    plot_confusion_matrix_heatmap,
    save_clustering_summary,
    plot_metrics_dashboard,
    reduce_dimensions
)
from .models import get_clustering_model, list_available_models
from .metrics import calculate_clustering_metrics, evaluate_all_models


def run_clustering_analysis(
        collection_name: str = "corpus",
        model_name: str = None,
        clustering_model: str = "kmeans",
        clustering_params: dict = None,
        generate_visualizations: bool = True,
        output_base_dir: str = "analysis",
        auto_detect: bool = True
):
    """Запуск анализа кластеризации с автоматическим определением числа кластеров"""

    print("\n" + "=" * 70)
    print("ЗАПУСК АНАЛИЗА КЛАСТЕРИЗАЦИИ")
    print("=" * 70)

    print("\n1. Загрузка эмбеддингов...")
    analyzer = EmbeddingAnalyzer(collection_name=collection_name, model_name=model_name)

    if not analyzer.available_models:
        print("Ошибка: Нет доступных моделей эмбеддингов!")
        return None

    if model_name is None:
        model_name = analyzer.available_models[0]
        analyzer.set_model(model_name)

    # Преобразуем model_name для безопасного имени папки
    safe_model_name = model_name.replace("/", "_").replace("\\", "_")

    print(f"\nАнализ для модели эмбеддингов: {model_name}")

    data = analyzer.filter_by_model()
    if not data:
        print(f"Ошибка: Нет данных для модели '{model_name}'")
        return None

    embeddings = np.stack([item["embedding"] for item in data])
    true_labels = np.array([item["tradition"] for item in data])

    print(f"  • Загружено точек: {len(embeddings)}")
    print(f"  • Размерность: {embeddings.shape[1]}")
    print(f"  • Уникальных традиций: {len(np.unique(true_labels))}")

    # СТРУКТУРА: analysis/{model_name}/clustering/{clustering_model}/
    base_analysis_dir = Path(project_root) / output_base_dir / safe_model_name / "clustering" / clustering_model
    base_analysis_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n2. Результаты будут сохранены в: {base_analysis_dir}")

    print(f"\n3. Запуск кластеризации (алгоритм: {clustering_model})...")

    if clustering_params is None:
        clustering_params = {}

    # АВТОМАТИЧЕСКОЕ ОПРЕДЕЛЕНИЕ ПО УМОЛЧАНИЮ
    if auto_detect:
        print("  • Режим: АВТОМАТИЧЕСКОЕ определение параметров")

        if clustering_model in ['kmeans', 'agglomerative', 'spectral']:
            # Не передаем n_clusters, пусть модель сама определит
            clustering_params.pop('n_clusters', None)
            print("  • Автоматическое определение числа кластеров")
        elif clustering_model == 'dbscan':
            # ДЛЯ DBSCAN ВКЛЮЧАЕМ AUTO_EPS ПО УМОЛЧАНИЮ
            if 'auto_eps' not in clustering_params:
                clustering_params['auto_eps'] = True
            if 'min_samples' not in clustering_params:
                clustering_params['min_samples'] = 5
            print(f"  • Автоматическое определение eps для DBSCAN (auto_eps={clustering_params['auto_eps']})")
        elif clustering_model == 'birch':
            if 'threshold' not in clustering_params:
                clustering_params['threshold'] = 0.5
            print(f"  • Birch с порогом {clustering_params['threshold']}")
    else:
        print("  • Режим: РУЧНОЕ управление параметрами")

    try:
        clusterer = get_clustering_model(clustering_model, **clustering_params)
        predicted_labels = clusterer.fit_predict(embeddings)
        n_clusters = len(set(predicted_labels)) - (1 if -1 in predicted_labels else 0)
        print(f"  • Найдено кластеров: {n_clusters}")
        if -1 in predicted_labels:
            print(f"  • Шумовых точек: {np.sum(predicted_labels == -1)}")
    except Exception as e:
        print(f"Ошибка при кластеризации: {e}")
        return None

    print("\n4. Вычисление метрик качества...")
    metrics = calculate_clustering_metrics(embeddings, predicted_labels, true_labels)

    unique, counts = np.unique(predicted_labels, return_counts=True)
    cluster_counts = dict(zip(unique.tolist(), counts.tolist()))

    tradition_cluster_map = {}
    for tradition in np.unique(true_labels):
        mask = true_labels == tradition
        trad_labels = predicted_labels[mask]
        unique_trad, counts_trad = np.unique(trad_labels, return_counts=True)
        tradition_cluster_map[tradition] = dict(zip(unique_trad.tolist(), counts_trad.tolist()))

    results = {
        'metrics': metrics,
        'cluster_counts': cluster_counts,
        'tradition_cluster_map': tradition_cluster_map,
        'all_labels': predicted_labels.tolist(),
        'true_labels': true_labels.tolist()
    }

    print("\n" + "-" * 50)
    print("МЕТРИКИ КЛАСТЕРИЗАЦИИ:")
    print("-" * 50)

    if metrics.get('silhouette_score'):
        print(f"  Silhouette Score:        {metrics['silhouette_score']:.4f}")
    if metrics.get('adjusted_rand_score'):
        print(f"  Adjusted Rand Index:     {metrics['adjusted_rand_score']:.4f}")
    if metrics.get('normalized_mutual_info'):
        print(f"  Normalized Mutual Info:  {metrics['normalized_mutual_info']:.4f}")
    if metrics.get('v_measure'):
        print(f"  V-measure:               {metrics['v_measure']:.4f}")
    if metrics.get('n_clusters_found'):
        print(f"  Найдено кластеров:       {metrics['n_clusters_found']}")
    if metrics.get('noise_ratio'):
        print(f"  Доля шума:               {metrics['noise_ratio']:.2%}")

    print("\n5. Сохранение результатов...")

    metrics_path = base_analysis_dir / "clustering_metrics.json"
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json_metrics = {}
        for k, v in metrics.items():
            if v is not None:
                if isinstance(v, (np.float32, np.float64)):
                    json_metrics[k] = float(v)
                elif isinstance(v, (np.int32, np.int64)):
                    json_metrics[k] = int(v)
                else:
                    json_metrics[k] = v
            else:
                json_metrics[k] = None
        json.dump(json_metrics, f, ensure_ascii=False, indent=2)
    print(f"  • Метрики сохранены: {metrics_path}")

    # Сохраняем сводку
    save_clustering_summary(
        results,
        str(base_analysis_dir),
        model_name,
        clustering_model
    )

    if generate_visualizations:
        print("\n6. Создание визуализаций...")

        try:
            print("  • Вычисление UMAP проекции...")
            embeddings_2d = reduce_dimensions(embeddings, method='umap', n_components=2)

            if embeddings_2d is not None and len(embeddings_2d) > 0:
                print("  • Создание графика кластеров...")
                clusters_path = base_analysis_dir / f"clusters_{clustering_model}.html"
                plot_clustering_results_2d(
                    embeddings_2d,
                    predicted_labels,
                    true_labels,
                    title=f"Кластеризация эмбеддингов ({clustering_model})",
                    output_path=str(clusters_path)
                )
                print(f"    ✓ Сохранен: {clusters_path}")

                print("  • Создание матрицы соответствия...")
                confusion_path = base_analysis_dir / f"confusion_matrix_{clustering_model}.html"
                plot_confusion_matrix_heatmap(
                    true_labels,
                    predicted_labels,
                    output_path=str(confusion_path)
                )
                print(f"    ✓ Сохранен: {confusion_path}")
            else:
                print("  • Предупреждение: Не удалось создать 2D проекцию для визуализации")
        except Exception as e:
            print(f"  • Ошибка при создании визуализаций: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print("АНАЛИЗ ЗАВЕРШЕН")
    print("=" * 70)
    print(f"\nРезультаты сохранены в: {base_analysis_dir}")

    return results


def run_all_clustering_models(
        collection_name: str = "corpus",
        model_name: str = None,
        models_to_run: list = None,
        output_base_dir: str = "analysis",
        auto_detect_clusters: bool = True
):
    """
    Сравнительный анализ всех моделей кластеризации

    Args:
        collection_name: Имя коллекции в ChromaDB
        model_name: Имя модели эмбеддингов
        models_to_run: Список моделей для запуска (если None - все доступные)
        output_base_dir: Директория для сохранения результатов
        auto_detect_clusters: Автоматически определять число кластеров для всех моделей (ПО УМОЛЧАНИЮ True)
    """

    if models_to_run is None:
        models_to_run = list_available_models()

    print("\n" + "=" * 70)
    print("СРАВНИТЕЛЬНЫЙ АНАЛИЗ ВСЕХ МОДЕЛЕЙ КЛАСТЕРИЗАЦИИ")
    print("=" * 70)
    print(f"Модели для запуска: {models_to_run}")
    print(f"Авто-определение кластеров: {'ВКЛЮЧЕНО' if auto_detect_clusters else 'ВЫКЛЮЧЕНО'}")

    analyzer = EmbeddingAnalyzer(collection_name=collection_name, model_name=model_name)

    if model_name is None and analyzer.available_models:
        model_name = analyzer.available_models[0]
        analyzer.set_model(model_name)

    print(f"Используется модель эмбеддингов: {model_name}")

    # Преобразуем model_name для безопасного имени папки
    safe_model_name = model_name.replace("/", "_").replace("\\", "_")

    data = analyzer.filter_by_model()
    if not data:
        print(f"Ошибка: Нет данных для модели '{model_name}'")
        return None

    embeddings = np.stack([item["embedding"] for item in data])
    true_labels = np.array([item["tradition"] for item in data])

    print(f"Загружено точек: {len(embeddings)}")
    print(f"Уникальных традиций: {len(np.unique(true_labels))}")

    all_results = {}

    # Заранее вычисляем 2D проекцию для всех визуализаций (один раз)
    print("\nВычисление UMAP проекции для визуализаций...")
    embeddings_2d = reduce_dimensions(embeddings, method='umap', n_components=2)
    if embeddings_2d is None or len(embeddings_2d) == 0:
        print("Предупреждение: Не удалось создать 2D проекцию")
        embeddings_2d = None

    # Словарь для хранения всех метрик для дашборда
    all_metrics_for_dashboard = {}

    for cl_model in models_to_run:
        print(f"\n{'=' * 50}")
        print(f"Модель: {cl_model.upper()}")
        print(f"{'=' * 50}")

        try:
            # СТРУКТУРА: analysis/{model_name}/clustering/{cl_model}/
            base_dir = Path(project_root) / output_base_dir / safe_model_name / "clustering" / cl_model
            base_dir.mkdir(parents=True, exist_ok=True)

            # Настройка параметров модели с авто-определением кластеров
            clustering_params = {}

            if auto_detect_clusters:
                print(f"  • Режим: АВТОМАТИЧЕСКОЕ определение параметров")

                # Для всех моделей используем автоматическое определение
                if cl_model in ['kmeans', 'agglomerative', 'spectral']:
                    # Не передаем n_clusters - модель сама определит
                    clustering_params = {}
                    print(f"  • Авто-определение числа кластеров для {cl_model}")
                elif cl_model == 'dbscan':
                    # ВКЛЮЧАЕМ AUTO_EPS ДЛЯ DBSCAN
                    clustering_params = {'auto_eps': True, 'min_samples': 5}
                    print(f"  • Авто-определение eps для DBSCAN (auto_eps=True)")
                elif cl_model == 'birch':
                    # Birch с автоматическим порогом
                    clustering_params = {'threshold': 0.5}
                    print(f"  • Birch с автоматическим порогом {clustering_params['threshold']}")
            else:
                print(f"  • Режим: РУЧНОЕ управление (используем {len(np.unique(true_labels))} кластеров)")
                # Если авто-определение выключено, используем количество истинных классов
                n_true_clusters = len(np.unique(true_labels))
                if cl_model in ['kmeans', 'agglomerative', 'spectral']:
                    clustering_params = {'n_clusters': n_true_clusters}

            # Получаем модель кластеризации
            clusterer = get_clustering_model(cl_model, **clustering_params)
            predicted_labels = clusterer.fit_predict(embeddings)

            n_clusters = len(set(predicted_labels)) - (1 if -1 in predicted_labels else 0)
            n_noise = np.sum(predicted_labels == -1) if -1 in predicted_labels else 0

            print(f"  • Найдено кластеров: {n_clusters}")
            if n_noise > 0:
                print(f"  • Шумовых точек: {n_noise} ({n_noise / len(predicted_labels) * 100:.1f}%)")

            # Вычисляем метрики
            metrics = calculate_clustering_metrics(embeddings, predicted_labels, true_labels)
            all_results[cl_model] = metrics
            all_metrics_for_dashboard[cl_model] = metrics

            # Выводим ключевые метрики
            print(f"\n  Ключевые метрики:")
            print(f"    • Silhouette Score:      {metrics.get('silhouette_score', 0):.4f}")
            print(f"    • Davies-Bouldin:        {metrics.get('davies_bouldin_score', 0):.4f}")
            print(f"    • Adjusted Rand Index:   {metrics.get('adjusted_rand_score', 0):.4f}")
            print(f"    • Normalized Mutual Info:{metrics.get('normalized_mutual_info', 0):.4f}")
            print(f"    • V-measure:             {metrics.get('v_measure', 0):.4f}")
            print(f"    • Separation Ratio:      {metrics.get('separation_ratio', 0):.4f}")

            # Сохраняем метрики для этой модели
            metrics_path = base_dir / "clustering_metrics.json"
            with open(metrics_path, 'w', encoding='utf-8') as f:
                json_metrics = {}
                for k, v in metrics.items():
                    if v is not None:
                        if isinstance(v, (np.float32, np.float64)):
                            json_metrics[k] = float(v)
                        elif isinstance(v, (np.int32, np.int64)):
                            json_metrics[k] = int(v)
                        else:
                            json_metrics[k] = v
                    else:
                        json_metrics[k] = None
                json.dump(json_metrics, f, ensure_ascii=False, indent=2)
            print(f"\n  • Метрики сохранены в: {metrics_path}")

            # Создаем визуализации для каждой модели
            if embeddings_2d is not None:
                try:
                    clusters_path = base_dir / f"clusters_{cl_model}.html"
                    plot_clustering_results_2d(
                        embeddings_2d,
                        predicted_labels,
                        true_labels,
                        title=f"Кластеризация эмбеддингов ({cl_model}) - {n_clusters} кластеров",
                        output_path=str(clusters_path)
                    )
                    print(f"  • Визуализация кластеров: {clusters_path}")

                    confusion_path = base_dir / f"confusion_matrix_{cl_model}.html"
                    plot_confusion_matrix_heatmap(
                        true_labels,
                        predicted_labels,
                        output_path=str(confusion_path)
                    )
                    print(f"  • Матрица соответствия: {confusion_path}")
                except Exception as viz_e:
                    print(f"  • Предупреждение: не удалось создать визуализации: {viz_e}")

            # Сохраняем сводку
            results_for_summary = {
                'metrics': metrics,
                'cluster_counts': dict(zip(*np.unique(predicted_labels, return_counts=True))),
                'tradition_cluster_map': {},
                'all_labels': predicted_labels.tolist(),
                'true_labels': true_labels.tolist()
            }

            for tradition in np.unique(true_labels):
                mask = true_labels == tradition
                trad_labels = predicted_labels[mask]
                unique_trad, counts_trad = np.unique(trad_labels, return_counts=True)
                results_for_summary['tradition_cluster_map'][tradition] = dict(
                    zip(unique_trad.tolist(), counts_trad.tolist()))

            save_clustering_summary(
                results_for_summary,
                str(base_dir),
                model_name,
                cl_model
            )
            print(f"  • Текстовая сводка сохранена")

            # Сохраняем метки кластеров для возможного дальнейшего анализа
            labels_path = base_dir / "cluster_labels.npy"
            np.save(labels_path, predicted_labels)
            print(f"  • Метки кластеров сохранены: {labels_path}")

        except Exception as e:
            print(f"\n  ✗ ОШИБКА при выполнении {cl_model}: {e}")
            import traceback
            traceback.print_exc()
            all_results[cl_model] = {'error': str(e)}
            all_metrics_for_dashboard[cl_model] = {'error': str(e)}

    # Создаем сравнительные визуализации
    print("\n" + "=" * 70)
    print("СОЗДАНИЕ СРАВНИТЕЛЬНЫХ ВИЗУАЛИЗАЦИЙ")
    print("=" * 70)

    try:
        if embeddings_2d is not None and len(all_results) > 0:
            # СТРУКТУРА: analysis/{model_name}/clustering/comparison/
            comparison_dir = Path(project_root) / output_base_dir / safe_model_name / "clustering" / "comparison"
            comparison_dir.mkdir(parents=True, exist_ok=True)

            # Дашборд метрик
            dashboard_path = comparison_dir / "metrics_dashboard.html"
            plot_metrics_dashboard(
                all_metrics_for_dashboard,
                output_path=str(dashboard_path)
            )
            print(f"  • Дашборд метрик: {dashboard_path}")

            # Сохраняем таблицу сравнения в CSV
            comparison_df = []
            for model, metrics in all_results.items():
                if 'error' not in metrics:
                    row = {'model': model}
                    for key in ['n_clusters_found', 'silhouette_score', 'davies_bouldin_score',
                                'adjusted_rand_score', 'normalized_mutual_info', 'v_measure',
                                'separation_ratio', 'noise_ratio']:
                        val = metrics.get(key)
                        if val is not None:
                            row[key] = float(val) if isinstance(val, (np.float32, np.float64)) else val
                        else:
                            row[key] = None
                    comparison_df.append(row)

            if comparison_df:
                import pandas as pd
                df_comparison = pd.DataFrame(comparison_df)
                csv_path = comparison_dir / "models_comparison.csv"
                df_comparison.to_csv(csv_path, index=False)
                print(f"  • Таблица сравнения (CSV): {csv_path}")

                # Сортируем по Adjusted Rand Index для выявления лучшей модели
                if 'adjusted_rand_score' in df_comparison.columns:
                    best_model = df_comparison.loc[df_comparison['adjusted_rand_score'].idxmax()] if df_comparison[
                        'adjusted_rand_score'].notna().any() else None
                    if best_model is not None:
                        print(
                            f"\n  ★ ЛУЧШАЯ МОДЕЛЬ по ARI: {best_model['model']} (ARI = {best_model['adjusted_rand_score']:.4f})")

                # Сортируем по Silhouette Score
                if 'silhouette_score' in df_comparison.columns:
                    best_sil = df_comparison.loc[df_comparison['silhouette_score'].idxmax()] if df_comparison[
                        'silhouette_score'].notna().any() else None
                    if best_sil is not None:
                        print(
                            f"  ★ ЛУЧШАЯ МОДЕЛЬ по Silhouette: {best_sil['model']} (Silhouette = {best_sil['silhouette_score']:.4f})")
    except Exception as e:
        print(f"Ошибка при создании сравнительных визуализаций: {e}")
        import traceback
        traceback.print_exc()

    # Сохраняем общее сравнение в JSON
    comparison_path = Path(
        project_root) / output_base_dir / safe_model_name / "clustering" / "all_models_comparison.json"
    comparison_path.parent.mkdir(parents=True, exist_ok=True)

    with open(comparison_path, 'w', encoding='utf-8') as f:
        json_compatible = {}
        for model, metrics in all_results.items():
            if 'error' not in metrics:
                json_compatible[model] = {
                    k: float(v) if isinstance(v, (np.float32, np.float64)) else (
                        int(v) if isinstance(v, (np.int32, np.int64)) else v)
                    for k, v in metrics.items() if v is not None
                }
            else:
                json_compatible[model] = {'error': metrics['error']}
        json.dump(json_compatible, f, ensure_ascii=False, indent=2)

    print(f"\n  • Полное сравнение (JSON): {comparison_path}")

    # Итоговый вывод
    print("\n" + "=" * 70)
    print("ИТОГОВЫЙ ОТЧЕТ О СРАВНЕНИИ МОДЕЛЕЙ")
    print("=" * 70)
    print(f"\nВсего протестировано моделей: {len([m for m in all_results if 'error' not in all_results[m]])}")
    print(f"Директория с результатами: {Path(project_root) / output_base_dir / safe_model_name / 'clustering'}")

    print("\nЛучшие результаты по каждой метрике:")

    # Находим лучшие модели по разным метрикам
    best_metrics = {
        'adjusted_rand_score': ('ARI', -1),
        'normalized_mutual_info': ('NMI', -1),
        'v_measure': ('V-measure', -1),
        'silhouette_score': ('Silhouette', -1),
        'separation_ratio': ('Separation Ratio', -1)
    }

    for model, metrics in all_results.items():
        if 'error' not in metrics:
            for metric_key, (metric_name, _) in best_metrics.items():
                val = metrics.get(metric_key)
                if val is not None and val > best_metrics[metric_key][1]:
                    best_metrics[metric_key] = (metric_name, val, model)

    for metric_key, (metric_name, val, model) in best_metrics.items():
        if val != -1:
            print(f"  • {metric_name:20} -> {model:15} ({val:.4f})")

    print("\n" + "=" * 70)
    print("АНАЛИЗ ЗАВЕРШЕН")
    print("=" * 70)

    return all_results


def run_auto_clustering_all_models(
        collection_name: str = "corpus",
        model_name: str = None,
        output_base_dir: str = "analysis"
):
    """
    Упрощенная функция для запуска всех моделей кластеризации с автоматическим определением кластеров

    Args:
        collection_name: Имя коллекции в ChromaDB
        model_name: Имя модели эмбеддингов
        output_base_dir: Директория для сохранения результатов
    """
    return run_all_clustering_models(
        collection_name=collection_name,
        model_name=model_name,
        models_to_run=None,  # Все доступные модели
        output_base_dir=output_base_dir,
        auto_detect_clusters=True  # Автоматическое определение кластеров
    )


def build_all_clusters():
    """
    Запуск всех моделей кластеризации с автоматическим определением параметров.
    Это упрощенная версия для быстрого запуска полного анализа.
    """
    parser = argparse.ArgumentParser(
        description='Запуск всех моделей кластеризации для анализа эмбеддингов',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python -m embedding_analyzer.clustering.run_clustering --all-models
  python -m embedding_analyzer.clustering.run_clustering --all-models --collection my_corpus
  python -m embedding_analyzer.clustering.run_clustering --all-models --model bert-base-multilingual-cased
  python -m embedding_analyzer.clustering.run_clustering --all-models --output-dir my_analysis
  python -m embedding_analyzer.clustering.run_clustering --all-models --no-viz
        """
    )

    parser.add_argument(
        '--collection',
        type=str,
        default='corpus',
        help='Имя коллекции в ChromaDB (по умолчанию: corpus)'
    )

    parser.add_argument(
        '--model',
        type=str,
        default=None,
        help='Имя модели эмбеддингов (если не указана, используется первая доступная)'
    )

    parser.add_argument(
        '--models',
        type=str,
        nargs='+',
        default=None,
        help='Список моделей кластеризации для запуска (по умолчанию: все доступные)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='analysis',
        help='Директория для сохранения результатов (по умолчанию: analysis)'
    )

    parser.add_argument(
        '--no-viz',
        action='store_true',
        help='Отключить создание визуализаций'
    )

    parser.add_argument(
        '--no-auto',
        action='store_true',
        help='ОТКЛЮЧИТЬ автоматическое определение числа кластеров (использовать истинные метки)'
    )

    parser.add_argument(
        '--save-embeddings-2d',
        action='store_true',
        help='Сохранить 2D проекцию эмбеддингов для последующего использования'
    )

    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("ЗАПУСК ВСЕХ МОДЕЛЕЙ КЛАСТЕРИЗАЦИИ")
    print("=" * 80)
    print(f"Коллекция: {args.collection}")
    print(f"Модель эмбеддингов: {args.model or 'авто-выбор'}")
    print(f"Модели кластеризации: {args.models or 'все доступные'}")
    print(f"Авто-определение параметров: {'ВЫКЛЮЧЕНО' if args.no_auto else 'ВКЛЮЧЕНО (ПО УМОЛЧАНИЮ)'}")
    print(f"Визуализации: {'ВЫКЛЮЧЕНЫ' if args.no_viz else 'ВКЛЮЧЕНЫ'}")
    print(f"Директория результатов: {args.output_dir}")
    print("=" * 80 + "\n")

    # Запускаем сравнение всех моделей
    results = run_all_clustering_models(
        collection_name=args.collection,
        model_name=args.model,
        models_to_run=args.models,
        output_base_dir=args.output_dir,
        auto_detect_clusters=not args.no_auto  # <-- ПО УМОЛЧАНИЮ True (если нет флага --no-auto)
    )

    # Дополнительно сохраняем 2D проекцию если запрошено
    if args.save_embeddings_2d and results:
        try:
            from embedding_analyzer.analyzer import EmbeddingAnalyzer
            import pickle

            analyzer = EmbeddingAnalyzer(collection_name=args.collection, model_name=args.model)
            if args.model is None and analyzer.available_models:
                model_name = analyzer.available_models[0]
                analyzer.set_model(model_name)
            else:
                model_name = args.model

            data = analyzer.filter_by_model()
            if data:
                embeddings = np.stack([item["embedding"] for item in data])
                true_labels = np.array([item["tradition"] for item in data])

                # Вычисляем 2D проекцию
                embeddings_2d = reduce_dimensions(embeddings, method='umap', n_components=2)

                if embeddings_2d is not None and len(embeddings_2d) > 0:
                    safe_model_name = model_name.replace("/", "_").replace("\\", "_")
                    projection_dir = Path(project_root) / args.output_dir / safe_model_name
                    projection_dir.mkdir(parents=True, exist_ok=True)

                    # Сохраняем проекцию
                    projection_path = projection_dir / "embeddings_2d_projection.pkl"
                    with open(projection_path, 'wb') as f:
                        pickle.dump({
                            'embeddings_2d': embeddings_2d,
                            'true_labels': true_labels,
                            'model_name': model_name
                        }, f)
                    print(f"\n2D проекция сохранена: {projection_path}")
        except Exception as e:
            print(f"Предупреждение: не удалось сохранить 2D проекцию: {e}")

    print("\n" + "=" * 80)
    print("ЗАВЕРШЕНО")
    print("=" * 80)

    return results


def build_clusters():
    """Основная функция для запуска анализа кластеризации из командной строки"""
    parser = argparse.ArgumentParser(description='Анализ кластеризации эмбеддингов')
    parser.add_argument('--collection', type=str, default='corpus',
                        help='Имя коллекции в ChromaDB')
    parser.add_argument('--model', type=str, default=None,
                        help='Имя модели эмбеддингов')
    parser.add_argument('--clustering', type=str, default='kmeans',
                        choices=list_available_models(),
                        help='Алгоритм кластеризации (используется только с --single-model)')
    parser.add_argument('--compare-all', action='store_true',
                        help='Сравнить все модели кластеризации с авто-определением кластеров')
    parser.add_argument('--all-models', action='store_true',
                        help='Запустить все модели кластеризации (аналог --compare-all)')
    parser.add_argument('--single-model', action='store_true',
                        help='Запустить только одну модель')
    parser.add_argument('--no-auto', action='store_true',
                        help='ОТКЛЮЧИТЬ автоматическое определение числа кластеров (использовать истинные метки)')
    parser.add_argument('--no-viz', action='store_true',
                        help='Не создавать визуализации')
    parser.add_argument('--output-dir', type=str, default='analysis',
                        help='Директория для сохранения результатов (по умолчанию: analysis)')
    parser.add_argument('--models-list', type=str, nargs='+', default=None,
                        help='Список моделей кластеризации для запуска (например: kmeans dbscan)')

    args = parser.parse_args()

    # ПО УМОЛЧАНИЮ: запуск всех моделей с АВТО-ОПРЕДЕЛЕНИЕМ
    if args.single_model:
        # Запуск одной модели с авто-определением (если не указан --no-auto)
        clustering_params = {}
        auto_detect = not args.no_auto  # <-- ПО УМОЛЧАНИЮ True

        print("=" * 80)
        print(f"ЗАПУСК ОДНОЙ МОДЕЛИ: {args.clustering}")
        print(f"Авто-определение: {'ВКЛЮЧЕНО' if auto_detect else 'ВЫКЛЮЧЕНО'}")
        print("=" * 80)

        run_clustering_analysis(
            collection_name=args.collection,
            model_name=args.model,
            clustering_model=args.clustering,
            clustering_params=clustering_params,
            generate_visualizations=not args.no_viz,
            output_base_dir=args.output_dir,
            auto_detect=auto_detect  # <-- ПЕРЕДАЕМ ПАРАМЕТР
        )
    else:
        # ПО УМОЛЧАНИЮ: запуск всех моделей с АВТО-ОПРЕДЕЛЕНИЕМ
        print("=" * 80)
        print("ЗАПУСК ВСЕХ МОДЕЛЕЙ КЛАСТЕРИЗАЦИИ (режим по умолчанию)")
        print(f"Авто-определение: {'ВКЛЮЧЕНО' if not args.no_auto else 'ВЫКЛЮЧЕНО'}")
        print("=" * 80)

        run_all_clustering_models(
            collection_name=args.collection,
            model_name=args.model,
            models_to_run=args.models_list,
            output_base_dir=args.output_dir,
            auto_detect_clusters=not args.no_auto  # <-- ПО УМОЛЧАНИЮ True
        )