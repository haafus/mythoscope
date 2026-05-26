# How To: MythoSemantic

Краткая карта проекта: что делает каждый модуль, какие файлы он читает и пишет, и как его запускать. Все команды ниже предполагают запуск из корня проекта.

## Подготовка окружения

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Часть команд скачивает модели, обращается к внешним сайтам или пишет большие артефакты в `cache/`, `chroma_db/`, `analysis/`, `corpus_chunked/`, `graphs/` и `logs/`.

## main.py

Главная точка для FastAPI-приложения: создает `app = create_app()`. При прямом запуске сейчас запускает анализ эмбеддингов через `analyze_embeddings()`.

Запуск веб-сервера:

```powershell
py -3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Прямой запуск текущего поведения:

```powershell
py -3 main.py
```

## ui_server

Современный FastAPI-сервер и SPA-интерфейс.

Возможности:
- API для списка моделей, корпуса, географии, похожих фрагментов и кластеризации.
- Раздача веб-интерфейса из `ui_server/web`.
- Раздача готовых HTML-артефактов из `analysis/`, `template/`, `corpus/`, `corpus_chunked/`.

Запуск:

```powershell
py -3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Проверка:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/api/health
```

Открыть интерфейс: `http://127.0.0.1:8000/`.

## UI.py

Старый HTTP-сервер на `SimpleHTTPRequestHandler`. Он поддерживает старые HTML-шаблоны из `template/` и старые API-ручки.

Возможности:
- Открывает домашнюю страницу из `template/home.html`.
- Отдает старые страницы и часть API для поиска, соседей и корпуса.

Запуск:

```powershell
py -3 -c "from UI import start_home_page; start_home_page()"
```

Примечание: для обычной работы лучше использовать `ui_server`, потому что старый сервер шире раздает файлы проекта.

## corpus_builder

Модуль сборки корпуса из `download_list.json`.

Основные файлы:
- `corpus_builder/downloader.py` скачивает источники.
- `corpus_builder/utils.py` извлекает текст из HTML/PDF/TXT и нормализует его.
- `corpus_builder/builder.py` строит структуру `corpus/`, метаданные и каталог.
- `corpus_builder/build_corpus.py` содержит CLI-обертку `build_and_save_corpus()`.

Возможности:
- Скачать и обработать источники.
- Сохранить тексты в `corpus/<major>/<tradition>/<title>/<title>.txt`.
- Создать `corpus/corpus_metadata.json`, `corpus/corpus_catalog.csv`, `corpus/traditions_info.json`.

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

## clean_gutenberg.py

Утилита очистки текстов Project Gutenberg от лицензии, служебных заголовков и хвостов.

Возможности:
- Найти Gutenberg-тексты в корпусе.
- Очистить один файл или директорию.
- Сохранить оригиналы в `sources_backup/`.
- Вести `sources_backup/changelog.txt`.

Предпросмотр файлов:

```powershell
py -3 clean_gutenberg.py --preview --dir corpus
```

Очистить весь корпус:

```powershell
py -3 clean_gutenberg.py --dir corpus
```

Очистить один файл:

```powershell
py -3 clean_gutenberg.py --file "corpus\...\book.txt"
```

Показать статистику бэкапов:

```powershell
py -3 clean_gutenberg.py --backup-stats
```

## embeddings_builder

Модуль генерации эмбеддингов и записи в Chroma DB.

Основные файлы:
- `embeddings_builder/config.yaml` задает пути, модели, chunking и batch size.
- `embeddings_builder/cli.py` предоставляет CLI.
- `embeddings_builder/builder.py` читает корпус, режет тексты на чанки, считает эмбеддинги и пишет в Chroma.
- `embeddings_builder/chunking.py` содержит стратегии chunking.
- `embeddings_builder/cache_utils.py` и `cache_validator.py` работают с кешем.

Возможности:
- Построить эмбеддинги для нескольких моделей.
- Сохранить чанки в `corpus_chunked/`.
- Сохранить индекс в `chroma_db/`.
- Кешировать эмбеддинги в `cache/`.
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

Модуль анализа эмбеддингов из Chroma DB и генерации HTML/CSV/JSON-артефактов в `analysis/`.

Основные файлы:
- `embedding_analyzer/loader.py` читает данные из Chroma.
- `embedding_analyzer/analyzer.py` собирает статистику.
- `embedding_analyzer/visualization.py` строит PCA, UMAP, t-SNE, heatmap и dashboard.
- `embedding_analyzer/config.yaml` задает пути и параметры визуализации.

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
- `embeddings_clustering/models.py` содержит KMeans, HDBSCAN из sklearn, Spectral, Birch, GMM, MeanShift, OPTICS.
- `embeddings_clustering/metrics.py` считает метрики кластеризации.
- `embeddings_clustering/visualization.py` строит HTML-графики и матрицы.
- `embeddings_clustering/run_clustering.py` содержит запуск анализа.

Возможности:
- Кластеризовать эмбеддинги одной или всех моделей.
- Сохранить метрики и labels в `analysis/<model>/clustering/`.
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
- `graphs_generator/config.yaml` задает LLM, пути и параметры чанков.
- `graphs_generator/prompts.txt` содержит промпты.
- `graphs_generator/llm_processing.py` вызывает OpenAI-compatible API.
- `graphs_generator/run_graph_generation.py` режет тексты и агрегирует сущности.
- `graphs_generator/graph_generator.py` строит HTML-граф через NetworkX и Cytoscape.

Возможности:
- Пройти по книгам из `corpus/corpus_metadata.json`.
- Извлечь сущности и связи через локальный или внешний LLM.
- Сохранить графы в `graphs/<book_id>/characters.html`.

Запуск по конфигу:

```powershell
py -3 -c "from graphs_generator import run_generate_graphs; run_generate_graphs()"
```

Запуск с перезаписью готовых графов:

```powershell
py -3 -c "from graphs_generator import run_generate_graphs; run_generate_graphs(force=True)"
```

Перед запуском проверьте `graphs_generator/config.yaml`: по умолчанию выбран локальный OpenAI-compatible сервер `http://127.0.0.1:1234/v1/`.

## template

HTML-шаблоны для старого UI.

Возможности:
- Страницы `home.html`, `corpus.html`, `geography.html`, `embeddings_analysis.html`, `cluster_analysis.html`.
- Общая навигация `navbar.html`.
- Логотип `Logo.jpg`.

Запускается через старый сервер:

```powershell
py -3 -c "from UI import start_home_page; start_home_page()"
```

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

## corpus

Основной текстовый корпус.

Содержит:
- исходные обработанные тексты;
- `corpus_metadata.json`;
- `corpus_catalog.csv`;
- `traditions_info.json`;
- `processed_urls.json`.

Создается и обновляется через `corpus_builder`.

## corpus_chunked

Корпус после разбиения на чанки.

Создается через `embeddings_builder`. Используется UI и анализом для просмотра фрагментов.

## chroma_db

Локальная Chroma DB с векторными коллекциями.

Создается через `embeddings_builder`. Читается `embedding_analyzer`, `embeddings_clustering`, `ui_server` и старым `UI.py`.

## analysis

Готовые результаты анализа.

Содержит:
- `models.json`;
- папки моделей;
- `model_info.json`;
- `embeddings_data.csv`;
- HTML-графики PCA/UMAP/t-SNE;
- результаты кластеризации.

Создается через `embedding_analyzer` и `embeddings_clustering`. Раздается веб-сервером по `/analysis/...`.

## graphs

Готовые HTML-графы персонажей и связей.

Создается через `graphs_generator`.

## cache

Кеш эмбеддингов в `.npy` и `.json`.

Создается через `embeddings_builder`. Проверка:

```powershell
py -3 -m embeddings_builder.cli validate-cache
```

## logs

Логи сборки корпуса, эмбеддингов, анализа, кластеризации и генерации графов.

Создается автоматически почти всеми пайплайнами.

## sources_backup

Бэкапы исходных текстов перед очисткой Gutenberg.

Создается `clean_gutenberg.py`.

## Типовой пайплайн

```powershell
# 1. Собрать корпус
py -3 -c "from corpus_builder.build_corpus import build_and_save_corpus; build_and_save_corpus()" --type all

# 2. Очистить Gutenberg-тексты, если нужно
py -3 clean_gutenberg.py --preview --dir corpus
py -3 clean_gutenberg.py --dir corpus

# 3. Построить эмбеддинги и Chroma DB
py -3 -m embeddings_builder.cli generate

# 4. Построить визуальный анализ эмбеддингов
py -3 -c "from embedding_analyzer import analyze_embeddings; analyze_embeddings()"

# 5. Построить кластеризацию
py -3 -c "from embeddings_clustering.run_clustering import build_clusters; build_clusters()"

# 6. Запустить веб-интерфейс
py -3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
