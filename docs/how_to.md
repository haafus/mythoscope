# How To: MythoSemantic

Краткая карта проекта: что делает каждый модуль, какие файлы он читает и пишет, и как его запускать. Все команды ниже предполагают запуск из корня проекта.

## Структура проекта

```
config/          — статические конфиги, шаблоны, download_list.json
outputs/         — всё, что генерируется при запуске (corpus, analysis, logs, …)
src/             — исходный код (все Python-пакеты, settings.py, main.py)
docs/            — документация
tests/           — тесты
pyproject.toml   — конфигурация проекта, зависимости, ruff, mypy
```

## Подготовка окружения

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[all,dev]"
```

Часть команд скачивает модели, обращается к внешним сайтам или пишет большие артефакты в `outputs/cache/`, `outputs/chroma_db/`, `outputs/analysis/`, `outputs/corpus_chunked/`, `outputs/graphs/` и `outputs/logs/`.

## main.py

Главная точка для FastAPI-приложения: создает `app = create_app()`. При прямом запуске сейчас запускает анализ эмбеддингов через `analyze_embeddings()`.

Запуск веб-сервера:

```powershell
py -3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Прямой запуск текущего поведения:

```powershell
py -3 src/main.py
```

## ui_server

Современный FastAPI-сервер и SPA-интерфейс.

Возможности:
- API для списка моделей, корпуса, географии, похожих фрагментов и кластеризации.
- Раздача веб-интерфейса из `src/ui_server/web`.
- Раздача готовых HTML-артефактов из `outputs/analysis/`, `config/template/`, `outputs/corpus/`, `outputs/corpus_chunked/`.

Запуск:

```powershell
py -3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Проверка:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/api/health
```

Открыть интерфейс: `http://127.0.0.1:8000/`.

## corpus_builder

Модуль сборки корпуса из `config/download_list.json`.

Основные файлы:
- `src/corpus_builder/downloader.py` скачивает источники.
- `src/corpus_builder/utils.py` извлекает текст из HTML/PDF/TXT и нормализует его.
- `src/corpus_builder/builder.py` строит структуру `outputs/corpus/`, метаданные и каталог.
- `src/corpus_builder/build_corpus.py` содержит CLI-обертку `build_and_save_corpus()`.

Возможности:
- Скачать и обработать источники.
- Сохранить тексты в `outputs/corpus/<major>/<tradition>/<title>/<title>.txt`.
- Создать `outputs/corpus/corpus_metadata.json`, `outputs/corpus/corpus_catalog.csv`, `outputs/corpus/traditions_info.json`.

Запуск сборки всего корпуса:

```powershell
py -3 -c "from corpus_builder.build_corpus import build_and_save_corpus; build_and_save_corpus()" --type all
```

Только переводы:

```powershell
py -3 -c "from corpus_builder.build_corpus import build_and_save_corpus; build_and_save_corpus()" --type translation
```

Только оригиналы:

```powershell
py -3 -c "from corpus_builder.build_corpus import build_and_save_corpus; build_and_save_corpus()" --type original
```

Пересобрать с перезаписью:

```powershell
py -3 -c "from corpus_builder.build_corpus import build_and_save_corpus; build_and_save_corpus()" --type all --force
```

## corpus_builder.clean_gutenberg

Утилита очистки текстов Project Gutenberg от лицензии, служебных заголовков и хвостов. Входит в пакет `corpus_builder`.

Возможности:
- Найти Gutenberg-тексты в корпусе.
- Очистить один файл или директорию.
- Сохранить оригиналы в `outputs/sources_backup/`.
- Вести `outputs/sources_backup/changelog.txt`.

Предпросмотр файлов:

```powershell
mytho-clean-gutenberg --preview --dir outputs/corpus
```

Очистить весь корпус:

```powershell
mytho-clean-gutenberg --dir outputs/corpus
```

Очистить один файл:

```powershell
mytho-clean-gutenberg --file "outputs\corpus\...\book.txt"
```

Показать статистику бэкапов:

```powershell
mytho-clean-gutenberg --backup-stats
```

## embeddings_builder

Модуль генерации эмбеддингов и записи в Chroma DB.

Основные файлы:
- `config/embeddings_builder.yaml` задает пути, модели, chunking и batch size.
- `src/embeddings_builder/cli.py` предоставляет CLI.
- `src/embeddings_builder/builder.py` читает корпус, режет тексты на чанки, считает эмбеддинги и пишет в Chroma.
- `src/embeddings_builder/chunking.py` содержит стратегии chunking.
- `src/embeddings_builder/cache_utils.py` и `cache_validator.py` работают с кешем.

Возможности:
- Построить эмбеддинги для нескольких моделей.
- Сохранить чанки в `outputs/corpus_chunked/`.
- Сохранить индекс в `outputs/chroma_db/`.
- Кешировать эмбеддинги в `outputs/cache/`.
- Делать запросы к Chroma.

Посмотреть конфиг:

```powershell
py -3 -m embeddings_builder.cli show-config
```

Сгенерировать эмбеддинги по конфигу:

```powershell
py -3 -m embeddings_builder.cli generate
```

Сгенерировать для конкретной модели:

```powershell
py -3 -m embeddings_builder.cli generate --model "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
```

Выбрать chunking и тип текста:

```powershell
py -3 -m embeddings_builder.cli generate --chunking paragraph --text-type all
```

Поиск по индексу:

```powershell
py -3 -m embeddings_builder.cli query "creation of the world" --model "BAAI/bge-m3" --top-k 5
```

Проверить кеш:

```powershell
py -3 -m embeddings_builder.cli validate-cache
```

Удалить коллекцию модели:

```powershell
py -3 -m embeddings_builder.cli clear-cache --model "BAAI/bge-m3"
```

Важно: текущая генерация эмбеддингов по умолчанию пересоздает Chroma DB. Перед запуском убедитесь, что старый индекс можно заменить.

## embedding_analyzer

Модуль анализа эмбеддингов из Chroma DB и генерации HTML/CSV/JSON-артефактов в `outputs/analysis/`.

Основные файлы:
- `src/embedding_analyzer/loader.py` читает данные из Chroma.
- `src/embedding_analyzer/analyzer.py` собирает статистику.
- `src/embedding_analyzer/visualization.py` строит PCA, UMAP, t-SNE, heatmap и dashboard.
- `config/embedding_analyzer.yaml` задает пути и параметры визуализации.

Возможности:
- Получить статистику по модели.
- Сохранить `model_info.json`, `models.json`, `embeddings_data.csv`.
- Построить интерактивные графики семантического пространства.

Запустить анализ всех доступных моделей:

```powershell
py -3 -c "from embedding_analyzer import analyze_embeddings; analyze_embeddings()"
```

Запустить анализ одной модели:

```powershell
py -3 -c "from embedding_analyzer import analyze_embeddings; analyze_embeddings('BAAI/bge-m3')"
```

## embeddings_clustering

Модуль кластеризации эмбеддингов и сравнения алгоритмов.

Основные файлы:
- `src/embeddings_clustering/models.py` содержит KMeans, HDBSCAN из sklearn, Spectral, Birch, GMM, MeanShift, OPTICS.
- `src/embeddings_clustering/metrics.py` считает метрики кластеризации.
- `src/embeddings_clustering/visualization.py` строит HTML-графики и матрицы.
- `src/embeddings_clustering/run_clustering.py` содержит запуск анализа.

Возможности:
- Кластеризовать эмбеддинги одной или всех моделей.
- Сохранить метрики и labels в `outputs/analysis/<model>/clustering/`.
- Построить `clusters_*.html`, `confusion_matrix_*.html`, `metrics_dashboard.html`.

Запустить все алгоритмы для всех доступных моделей:

```powershell
py -3 -c "from embeddings_clustering.run_clustering import build_clusters; build_clusters()"
```

Запустить один алгоритм для одной модели:

```powershell
py -3 -c "from embeddings_clustering.run_clustering import build_clusters; build_clusters()" --model "BAAI/bge-m3" --single-model --clustering kmeans
```

Запустить без визуализаций:

```powershell
py -3 -c "from embeddings_clustering.run_clustering import build_clusters; build_clusters()" --single-model --clustering kmeans --no-viz
```

## graphs_generator

Модуль извлечения персонажей, отношений, мест и времени через LLM и генерации графов.

Основные файлы:
- `config/graphs_generator.yaml` задает LLM, пути и параметры чанков.
- `config/graphs_generator_prompts.txt` содержит промпты.
- `src/graphs_generator/llm_processing.py` вызывает OpenAI-compatible API.
- `src/graphs_generator/run_graph_generation.py` режет тексты и агрегирует сущности.
- `src/graphs_generator/graph_generator.py` строит HTML-граф через NetworkX и Cytoscape.

Возможности:
- Пройти по книгам из `outputs/corpus/corpus_metadata.json`.
- Извлечь сущности и связи через локальный или внешний LLM.
- Сохранить графы в `outputs/graphs/<book_id>/characters.html`.

Запуск по конфигу:

```powershell
py -3 -c "from graphs_generator import run_generate_graphs; run_generate_graphs()"
```

Запуск с перезаписью готовых графов:

```powershell
py -3 -c "from graphs_generator import run_generate_graphs; run_generate_graphs(force=True)"
```

Перед запуском проверьте `config/graphs_generator.yaml`: по умолчанию выбран локальный OpenAI-compatible сервер `http://127.0.0.1:1234/v1/`.

## config/template

HTML-шаблоны для старого UI.

Возможности:
- Страницы `home.html`, `corpus.html`, `geography.html`, `embeddings_analysis.html`, `cluster_analysis.html`.
- Общая навигация `navbar.html`.
- Логотип `Logo.jpg`.

## ui_server/web

Современный SPA-фронтенд.

Основные файлы:
- `index.html` подключает стили и JS.
- `assets/app.js` содержит маршруты и экраны.
- `assets/core.js` содержит API helpers и состояние.
- `assets/plot-utils.js` работает с Plotly-графиками.
- `assets/app.css` содержит стили.

Запускается через FastAPI:

```powershell
py -3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

## Директории outputs/

Все генерируемые данные хранятся в `outputs/`:

- `outputs/corpus/` — основной текстовый корпус с метаданными и каталогом. Создается через `corpus_builder`.
- `outputs/corpus_chunked/` — корпус после разбиения на чанки. Создается через `embeddings_builder`.
- `outputs/chroma_db/` — локальная Chroma DB с векторными коллекциями. Создается через `embeddings_builder`.
- `outputs/analysis/` — результаты анализа: `models.json`, HTML-графики, кластеризация. Создается через `embedding_analyzer` и `embeddings_clustering`.
- `outputs/graphs/` — готовые HTML-графы персонажей и связей. Создается через `graphs_generator`.
- `outputs/cache/` — кеш эмбеддингов в `.npy` и `.json`. Создается через `embeddings_builder`.
- `outputs/logs/` — логи всех пайплайнов.
- `outputs/sources_backup/` — бэкапы исходных текстов перед очисткой Gutenberg.

## Типовой пайплайн

```powershell
# 1. Собрать корпус
py -3 -c "from corpus_builder.build_corpus import build_and_save_corpus; build_and_save_corpus()" --type all

# 2. Очистить Gutenberg-тексты, если нужно
mytho-clean-gutenberg --preview --dir outputs/corpus
mytho-clean-gutenberg --dir outputs/corpus

# 3. Построить эмбеддинги и Chroma DB
py -3 -m embeddings_builder.cli generate

# 4. Построить визуальный анализ эмбеддингов
py -3 -c "from embedding_analyzer import analyze_embeddings; analyze_embeddings()"

# 5. Построить кластеризацию
py -3 -c "from embeddings_clustering.run_clustering import build_clusters; build_clusters()"

# 6. Запустить веб-интерфейс
py -3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
