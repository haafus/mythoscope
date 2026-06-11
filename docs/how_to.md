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

## 06_web

Современный FastAPI-сервер и SPA-интерфейс.

Возможности:
- API для списка моделей, корпуса, географии, похожих фрагментов и кластеризации.
- Раздача веб-интерфейса из `src/06_web/web`.
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

## 01_corpus

Модуль сборки корпуса из `config/download_list.json`.

Основные файлы:
- `src/01_corpus/downloader.py` скачивает источники.
- `src/01_corpus/utils.py` извлекает текст из HTML/PDF/TXT и нормализует его.
- `src/01_corpus/builder.py` строит структуру `outputs/corpus/`, метаданные и каталог.
- `src/01_corpus/build_corpus.py` содержит CLI-обертку `build_and_save_corpus()`.

Возможности:
- Скачать и обработать источники.
- Сохранить тексты в `outputs/corpus/<major>/<tradition>/<title>/<title>.txt`.
- Создать `outputs/corpus/corpus_metadata.json`, `outputs/corpus/corpus_catalog.csv`, `outputs/corpus/traditions_info.json`.

Запуск сборки всего корпуса:

```powershell
mytho-corpus --type all
```

Только переводы:

```powershell
mytho-corpus --type translation
```

Только оригиналы:

```powershell
mytho-corpus --type original
```

Пересобрать с перезаписью:

```powershell
mytho-corpus --type all --force
```

## 01_corpus.clean_gutenberg

Утилита очистки текстов Project Gutenberg от лицензии, служебных заголовков и хвостов. Входит в пакет `01_corpus`.

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

## 02_embed

Модуль генерации эмбеддингов и записи в Chroma DB.

Основные файлы:
- `config/02_embed.yaml` задает пути, модели, chunking и batch size.
- `src/02_embed/cli.py` предоставляет CLI.
- `src/02_embed/builder.py` читает корпус, режет тексты на чанки, считает эмбеддинги и пишет в Chroma.
- `src/02_embed/chunking.py` содержит стратегии chunking.
- `src/02_embed/cache_utils.py` и `cache_validator.py` работают с кешем.

Возможности:
- Построить эмбеддинги для нескольких моделей.
- Сохранить чанки в `outputs/corpus_chunked/`.
- Сохранить индекс в `outputs/chroma_db/`.
- Кешировать эмбеддинги в `outputs/cache/`.
- Делать запросы к Chroma.

Посмотреть конфиг:

```powershell
mytho-embeddings show-config
```

Сгенерировать эмбеддинги по конфигу:

```powershell
mytho-embeddings generate
```

Сгенерировать для конкретной модели:

```powershell
mytho-embeddings generate --model "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
```

Выбрать chunking и тип текста:

```powershell
mytho-embeddings generate --chunking paragraph --text-type all
```

Поиск по индексу:

```powershell
mytho-embeddings query "creation of the world" --model "BAAI/bge-m3" --top-k 5
```

Проверить кеш:

```powershell
mytho-embeddings validate-cache
```

Удалить коллекцию модели:

```powershell
mytho-embeddings clear-cache --model "BAAI/bge-m3"
```

Важно: текущая генерация эмбеддингов по умолчанию пересоздает Chroma DB. Перед запуском убедитесь, что старый индекс можно заменить.

## 03_project

Модуль анализа эмбеддингов из Chroma DB и генерации HTML/CSV/JSON-артефактов в `outputs/analysis/`.

Основные файлы:
- `src/03_project/loader.py` читает данные из Chroma.
- `src/03_project/analyzer.py` собирает статистику.
- `src/03_project/visualization.py` строит PCA, UMAP, t-SNE, heatmap и dashboard.
- `config/03_project.yaml` задает пути и параметры визуализации.

Возможности:
- Получить статистику по модели.
- Сохранить `model_info.json`, `models.json`, `embeddings_data.csv`.
- Построить интерактивные графики семантического пространства.

Запустить анализ всех доступных моделей:

```powershell
py -3 -c "from importlib import import_module; import_module('03_project').analyze_embeddings()"
```

Запустить анализ одной модели:

```powershell
py -3 -c "from importlib import import_module; import_module('03_project').analyze_embeddings('BAAI/bge-m3')"
```

## 04_cluster

Модуль кластеризации эмбеддингов и сравнения алгоритмов.

Основные файлы:
- `src/04_cluster/models.py` содержит KMeans, HDBSCAN из sklearn, Spectral, Birch, GMM, MeanShift, OPTICS.
- `src/04_cluster/metrics.py` считает метрики кластеризации.
- `src/04_cluster/visualization.py` строит HTML-графики и матрицы.
- `src/04_cluster/run_clustering.py` содержит запуск анализа.

Возможности:
- Кластеризовать эмбеддинги одной или всех моделей.
- Сохранить метрики и labels в `outputs/analysis/<model>/clustering/`.
- Построить `clusters_*.html`, `confusion_matrix_*.html`, `metrics_dashboard.html`.

Запустить все алгоритмы для всех доступных моделей:

```powershell
mytho-cluster
```

Запустить один алгоритм для одной модели:

```powershell
mytho-cluster --model "BAAI/bge-m3" --single-model --clustering kmeans
```

Запустить без визуализаций:

```powershell
mytho-cluster --single-model --clustering kmeans --no-viz
```

## 05_graphs

Модуль извлечения персонажей, отношений, мест и времени через LLM и генерации графов.

Основные файлы:
- `config/05_graphs.yaml` задает LLM, пути и параметры чанков.
- `config/05_graphs_prompts.txt` содержит промпты.
- `src/05_graphs/llm_processing.py` вызывает OpenAI-compatible API.
- `src/05_graphs/run_graph_generation.py` режет тексты и агрегирует сущности.
- `src/05_graphs/graph_generator.py` строит HTML-граф через NetworkX и Cytoscape.

Возможности:
- Пройти по книгам из `outputs/corpus/corpus_metadata.json`.
- Извлечь сущности и связи через локальный или внешний LLM.
- Сохранить графы в `outputs/graphs/<book_id>/characters.html`.

Запуск по конфигу:

```powershell
py -3 -c "from importlib import import_module; import_module('05_graphs').run_generate_graphs()"
```

Запуск с перезаписью готовых графов:

```powershell
py -3 -c "from importlib import import_module; import_module('05_graphs').run_generate_graphs(force=True)"
```

Перед запуском проверьте `config/05_graphs.yaml`: по умолчанию выбран локальный OpenAI-compatible сервер `http://127.0.0.1:1234/v1/`.

## config/template

HTML-шаблоны для старого UI.

Возможности:
- Страницы `home.html`, `corpus.html`, `geography.html`, `embeddings_analysis.html`, `cluster_analysis.html`.
- Общая навигация `navbar.html`.
- Логотип `Logo.jpg`.

## 06_web/web

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

- `outputs/corpus/` — основной текстовый корпус с метаданными и каталогом. Создается через `01_corpus`.
- `outputs/corpus_chunked/` — корпус после разбиения на чанки. Создается через `02_embed`.
- `outputs/chroma_db/` — локальная Chroma DB с векторными коллекциями. Создается через `02_embed`.
- `outputs/analysis/` — результаты анализа: `models.json`, HTML-графики, кластеризация. Создается через `03_project` и `04_cluster`.
- `outputs/graphs/` — готовые HTML-графы персонажей и связей. Создается через `05_graphs`.
- `outputs/cache/` — кеш эмбеддингов в `.npy` и `.json`. Создается через `02_embed`.
- `outputs/logs/` — логи всех пайплайнов.
- `outputs/sources_backup/` — бэкапы исходных текстов перед очисткой Gutenberg.

## Типовой пайплайн

```powershell
# 1. Собрать корпус
mytho-corpus --type all

# 2. Очистить Gutenberg-тексты, если нужно
mytho-clean-gutenberg --preview --dir outputs/corpus
mytho-clean-gutenberg --dir outputs/corpus

# 3. Построить эмбеддинги и Chroma DB
mytho-embeddings generate

# 4. Построить визуальный анализ эмбеддингов
py -3 -c "from importlib import import_module; import_module('03_project').analyze_embeddings()"

# 5. Построить кластеризацию
mytho-cluster

# 6. Запустить веб-интерфейс
py -3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
