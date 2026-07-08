# How To: MythoScope

Краткая карта проекта: что делает каждый модуль, какие файлы он читает и пишет, и как его запускать. Все команды ниже предполагают запуск из корня проекта.

## Структура проекта

```
config/          — статические конфиги, шаблоны, models.json, corpus.json
outputs/         — всё, что генерируется при запуске (corpus, embeddings, projections, …)
src/             — исходный код (все Python-пакеты, settings.py, main.py, cli.py)
docs/            — документация (motifs/, research/, reviews/, paper/)
mockups/         — автономные прототипы фич поверх индексов мотивов (self-contained HTML)
tests/           — тесты
pyproject.toml   — конфигурация проекта, зависимости, ruff, mypy
```

## Архитектура

Поток данных линейный, каждый шаг идемпотентен и возобновляем:

```
CLI (cli.py) ──► settings.py (+ config/*.json, model_registry.py)
   │
   ├─ corpus/      ──► outputs/corpus/      (тексты + corpus.json)
   ├─ embeddings/  ──► outputs/embeddings/  (ChromaDB)
   ├─ projections/ ──► outputs/projections/ (UMAP/heatmap JSON, summaries-UMAP)
   ├─ graphs/      ──► outputs/graphs/       (beings/realms/ages JSON)
   ├─ motifs/      ──► outputs/motifs/       (berezkin/tmi/atu JSON + crosswalk)
   └─ server/      ◄── читает outputs/ и отдаёт SPA + REST API

corpus → embeddings → {projections, graphs} → server
motifs (независим от корпуса) → server
```

Доменные пакеты (`corpus`, `embeddings`, `projections`, `graphs`, `motifs`, `server`) — по шагу пайплайна. Общая инфраструктура, не привязанная к шагу:

- **`llm/`** — работа с LLM: `client.py` (`LLMProcessor` — OpenAI-compatible вызовы, классификация ошибок, ретраи), `rate_limiter.py` (`RateGovernor` — лимиты RPM/TPM + circuit breaker), `concurrency.py` (`map_concurrent` — параллельный фан-аут с быстрой отменой).
- **`chunk_cache.py`** — append-only content-hash JSONL-кэш (graphs, summaries): возобновление по содержимому.
- **`json_utils.py`** — атомарная запись JSON (`save_json`).
- **`model_registry.py`** — резолв алиасов моделей и LLM-провайдеров из `config/models.json`.
- **`settings.py`** — pydantic-settings, единый источник путей/параметров (env `MYTHO_*`).

Как устроен троттлинг и параллелизм LLM-шагов:

1. Потребитель (graphs/summaries) гонит элементы через `map_concurrent` с `max_concurrent` воркерами.
2. Каждый вызов идёт через `LLMProcessor` → `RateGovernor` (общий синглтон на модель): два token-bucket'а (RPM/TPM), пред-оплата по оценке токенов и сверка по факту из `usage` ответа.
3. На устойчивом rate-limit взводится circuit breaker (`DailyLimitReached`) → штатная остановка; фатальные ошибки (`FatalLLMError`) → немедленная.
4. Результат пишется в content-hash кэш → повторный запуск продолжает с места.

CLI грузит тяжёлые зависимости (torch, transformers, chromadb) **лениво**, в момент запуска шага, поэтому первый запуск шага начинается с паузы на импорт.

## Подготовка окружения

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .\.venv\Scripts\Activate.ps1   # Windows PowerShell
pip install --upgrade pip
```

Дальше выбери профиль установки под свой сценарий — они отличаются весом на порядки.

### Сценарии установки

| Профиль | Команда | Вес | Что умеет |
|---|---|---|---|
| **viewer** | `pip install -e ".[viewer]"` | ~300 МБ | поднять веб-сервер на уже готовых данных: тексты, графы, проекции **+ поиск соседей по точкам**. Без torch. |
| **search** | `pip install -e ".[search]"` | ~5 ГБ (или ~640 МБ с CPU-torch) | то же + **семантический поиск по текстовому запросу** (тянет torch и модели эмбеддингов) |
| **all** (сборка/разработка) | `pip install -e ".[all,dev]"` | ~5 ГБ | весь пайплайн: скачивание корпуса, эмбеддинги, проекции, графы + тесты/линтеры |

Профили вложены: `viewer ⊂ search ⊂ all`. Низкоуровневые extras-кирпичики (`vectorstore`, `embeddings`, `analysis`, `corpus`, `graphs`) можно ставить и по отдельности.

`dev` (pytest, ruff, mypy) — инструменты разработчика, не входит в `all`. Добавляй его явно при работе над кодом: `pip install -e ".[all,dev]"` (или `".[viewer,dev]"` и т.п.).

Тесты бэка — `pytest`. Юнит-тесты фронта (чистые функции `core.js`/`search-utils.js`) — `npm test` (он же `node --test "tests/js/*.test.mjs"`), без npm-зависимостей: используется встроенный тест-раннер Node ≥18.

- **viewer** не требует torch и скрейпинг-либ — это гарантируется тестом `tests/test_viewer_imports.py`. Эндпоинт `/api/similarity/search` (текст-поиск) в этом профиле отвечает `503`; поиск соседей по точкам и остальные страницы работают. Фронт в такой сборке поле текст-поиска не показывает вовсе: `/api/similarity/models` отдаёт `text_search` по факту наличия пакетов эмбеддингов (`sentence_transformers` + `torch`, `find_spec` без импорта), и страница Similarity прячет поиск, оставляя разбор соседей по точкам. Конфига-переключателя нет — сигнал берётся из установленной сборки автоматически.
- **search** добавляет текст-поиск: при первом запросе модель эмбеддингов скачивается с HuggingFace (нужен доступ к `huggingface.co`).
- Если GPU нет, для `search`/`all` ставь CPU-only torch, чтобы не тянуть ~3.4 ГБ CUDA-библиотек:
  ```bash
  pip install torch --index-url https://download.pytorch.org/whl/cpu
  pip install -e ".[search]"   # или ".[all,dev]"
  ```

Часть команд скачивает модели, обращается к внешним сайтам или пишет большие артефакты в `outputs/embeddings/`, `outputs/projections/`, `outputs/corpus/`, `outputs/graphs/` и `outputs/logs/`.

## Конфигурация

- **`src/settings.py`** — единый источник путей и параметров. Все директории (`outputs/corpus`, `outputs/embeddings`, …), параметры chunking, LLM, сервера и т.д. Переопределяется через переменные окружения с префиксом `MYTHO_` или файл `.env` / `config/.env` (например, `MYTHO_CORPUS_DIR=/data/corpus`). Вложенные параметры через `__`: `MYTHO_LLM__MODEL=gpt4o-mini`. Полный список переменных — в `.env.example`.
- **`config/models.json`** — реестр LLM-провайдеров (base_url, model, env_key) и алиасов embedding-моделей. Алиасы позволяют писать `bge-m3` вместо `BAAI/bge-m3` в CLI и конфигах. У LLM-провайдера можно задать необязательные лимиты `rpm`/`tpm`/`rpd` (запросов и токенов в минуту, запросов в сутки) — по ним rate-governor троттлит вызовы при параллельном извлечении графов. Без них параллелизм ограничен только `max_concurrent`. `rpd` — справочный (жёсткой остановки по нему нет; см. раздел graphs).
- **`config/corpus.json`** — каталог текстов корпуса (источники, традиции, URL). Книга несёт только `tradition`; её мажор-группа резолвится из `traditions.json`.
- **`config/traditions.json`** — иерархическое дерево `major → {traditions: {tradition → {description, coordinates}}}`. Единый источник группировки: `major_tradition` живёт здесь по одному разу на традицию (а не дублируется в каждой книге). Сборка раскладывает дерево в плоский `outputs/corpus/traditions.json`.
- **`config/graphs_prompts.json`** — промпты для LLM-извлечения сущностей.

## LLM-провайдеры

Реестр LLM — `config/models.json`, секция `llm`:
- `models` — активные алиасы (видны в `mytho graphs --model ...`);
- `inactive` — заготовки (например, локальные модели), не предлагаются, пока не перенесены в `models`.

Запись провайдера:

```json
"gpt4o-mini": {
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4o-mini",
  "env_key": "OPENAI_API_KEY",
  "rpm": 500, "tpm": 200000, "rpd": 10000
}
```

- `base_url` — любой **OpenAI-compatible** эндпоинт.
- `model` — имя модели у провайдера.
- `env_key` — имя переменной окружения с API-ключом (читается SDK, не pydantic).
- `rpm`/`tpm`/`rpd` — необязательные лимиты (см. «Тюнинг throughput» в разделе graphs); `rpd` справочный. Без них параллелизм ограничен только `max_concurrent`.

Из коробки: OpenAI (`gpt4o-mini`, `gpt4o`), Gemini через OpenAI-слой (`gemini25-flash`, `gemini25-pro`), DeepSeek (`deepseek-v3`); в `inactive` — локальные через Ollama (`qwen3-8b`, `gemma3-27b`, …).

**API-ключи** — в `.env` / `config/.env` под нужным `env_key`:

```
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...
DEEPSEEK_API_KEY=sk-...
```

**Добавить провайдера** — новая запись в `llm.models` с его OpenAI-compatible `base_url`, именем модели и `env_key`. Выбрать модель: `mytho graphs --model <алиас>` или дефолт `MYTHO_LLM__MODEL`.

**Локальная модель (Ollama)** — перенеси нужный алиас из `inactive` в `models` (или добавь свой) с `base_url: http://localhost:11434/v1`, **без** `env_key` и без лимитов. Приватность: при облачном провайдере текст корпуса уходит в его API — если это нежелательно, используй локальную модель.

## CLI

Все команды проекта доступны через единую точку входа `mytho`:

```bash
mytho --help
mytho corpus --help
mytho embeddings --help
mytho projections --help
mytho graphs --help
mytho server --help
mytho build --help
mytho status
mytho clean
mytho export --help
```

## corpus

Модуль сборки корпуса из `config/corpus.json` (каталог источников). Тексты с Project Gutenberg автоматически очищаются от лицензионных заголовков и хвостов при скачивании.

Основные файлы:
- `src/corpus/downloader.py` скачивает источники.
- `src/corpus/extraction.py` извлекает текст из HTML/PDF/TXT.
- `src/corpus/utils.py` утилиты: пути, нормализация текста, подсчёт слов/предложений, работа с традициями.
- `src/corpus/iterator.py` итерация по файлам корпуса (`iter_files`, `CorpusFileInfo`).
- `src/corpus/builder.py` строит структуру `outputs/corpus/`, метаданные и каталог.
- `src/corpus/clean_gutenberg.py` автоматически удаляет Gutenberg-боллерплейт.

Возможности:
- Скачать и обработать источники.
- Автоматически очистить Gutenberg-тексты (по маркерам в содержимом).
- Сохранить тексты в `outputs/corpus/<major>/<tradition>/<title>.txt`.
- Создать `outputs/corpus/corpus.json` (метаданные), `outputs/corpus/traditions.json`.

Запуск сборки корпуса:

```bash
mytho corpus
```

Пересобрать с перезаписью:

```bash
mytho corpus --force
```

## embedding

Модуль генерации эмбеддингов и записи в Chroma DB.

Основные файлы:
- `src/embeddings/build_embeddings.py` оркестрирует генерацию для нескольких моделей (skip/resume по метаданным коллекции); читает корпус, режет тексты на чанки, считает эмбеддинги и пишет в Chroma.
- `src/embeddings/chunking.py` разбивает тексты на чанки с перекрытием (используется и для embeddings, и для graphs).
- `src/embeddings/chroma_manager.py` хранилище ChromaDB: module-level функции (создание/удаление коллекций, список моделей) и `ChromaCollection` (upsert, загрузка данных, existing_ids).
- `src/embeddings/model_manager.py` загрузка/выгрузка SentenceTransformer моделей (`EmbeddingEncoder`).
- `src/model_registry.py` резолвит алиасы моделей из `config/models.json`.

Возможности:
- Построить эмбеддинги для нескольких моделей.
- Сохранить индекс в `outputs/embeddings/`.

Сгенерировать эмбеддинги для всех активных моделей:

```bash
mytho embeddings
```

Сгенерировать для конкретной модели:

```bash
mytho embeddings --model bge-m3
```

Пересоздать с нуля:

```bash
mytho embeddings --model bge-m3 --force
```

Загруженные модели кэшируются локально — чтобы очистить кэш и скачать модель заново, удалите её папку из кэша:

```bash
rm -rf ~/.cache/huggingface/hub/models--BAAI--bge-m3
```

## projections

Модуль анализа эмбеддингов из Chroma DB и генерации JSON-артефактов в `outputs/projections/`.

Основные файлы:
- `src/projections/analyzer.py` загружает данные из Chroma и собирает статистику.
- `src/projections/visualization.py` вычисляет UMAP-проекции, heatmap расстояний и distribution, сохраняет как JSON.
- `src/projections/summaries.py` строит LLM-саммари сюжетов (параллельно, с кэшем `summaries.jsonl`) и summaries-UMAP по ним.
- `src/projections/build_projections.py` оркестрирует анализ для нескольких моделей.

Возможности:
- Получить статистику по модели.
- Сохранить `model_info.json`, `models.json`, `embeddings_data.csv`.
- Построить интерактивные графики семантического пространства.

Запустить анализ всех доступных моделей:

```bash
mytho projections
```

Запустить анализ одной модели:

```bash
mytho projections --model bge-m3
```

Дополнительно построить summaries-UMAP из LLM-саммари сюжетов:

```bash
mytho projections --summaries
```

## graphs

Модуль извлечения персонажей, отношений, мест и времени через LLM и генерации графов.

Основные файлы:
- `config/graphs_prompts.json` содержит промпты для извлечения сущностей.
- `src/graphs/build_graphs.py` оркестрирует генерацию: итерация по текстам, чанкинг, параллельное извлечение, агрегация.
- `src/graphs/extraction.py` извлекает сущности из чанка через LLM (4 последовательных вызова на чанк) и дедуплицирует их.
- `src/embeddings/chunking.py` разбивает тексты на чанки (общий модуль).
- `src/chunk_cache.py` content-hash кэш чанков (JSONL): возобновление по содержимому, общий для graphs и summaries.
- `src/graphs/graph_generator.py` строит граф через NetworkX и сохраняет JSON.
- `src/llm/` — пакет работы с LLM: `client.py` (`LLMProcessor`, вызовы OpenAI-compatible API), `rate_limiter.py` (rate-governor: лимиты RPM/TPM + circuit breaker), `concurrency.py` (`map_concurrent` — параллельный прогон с ранней остановкой).

Возможности:
- Пройти по книгам из `outputs/corpus/corpus.json`.
- Извлечь сущности и связи через локальный или внешний LLM.
- Сохранить три графа на книгу в `outputs/graphs/<text_id>/`:
  - `beings.json` — персонажи (включая без связей) и отношения между ними.
  - `realms.json` — локации и связи смежности (поле "Adjacent To").
  - `ages.json` — эпохи как **таймлайн**: связаны по порядку появления в нарративе (рёбра "followed by"); `KeyActors`/`KeyEvents` хранятся в метаданных узла.

  Имена сущностей сопоставляются регистро-независимо (узлы дедуплицируются, метаданные прицепляются даже при разном написании). Файлы пишутся атомарно.

`settings.py` → `graphs.max_entities` (env `MYTHO_GRAPHS__MAX_ENTITIES`, по умолчанию 50; `None` = оставить всё) ограничивает каждый граф **N самыми часто упоминаемыми** сущностями (по числу упоминаний до дедупа); рёбра остаются только между оставленными. В логе пишется, сколько найдено всего и сколько оставлено по каждому типу.

Запуск с моделью по умолчанию (из `settings.py` → `llm.model`):

```bash
mytho graphs
```

Запуск с конкретной LLM из реестра `config/models.json`:

```bash
mytho graphs --model gemini25-flash
```

По умолчанию `mytho graphs` **каждый раз пересобирает все графы из уже извлечённого кэша** (`extraction_cache.jsonl`); LLM вызывается только для ещё не извлечённых чанков и создаётся лениво — если кэш полон, ключ не нужен (удобно после изменения логики построения графов). `--force` чистит кэш и извлекает заново через LLM:

```bash
mytho graphs           # пересобрать графы из кэша (LLM — только для новых чанков)
mytho graphs --force   # извлечь заново с нуля (через LLM)
```

(В отличие от `--force`, который **стирает** `extraction_cache.jsonl` и переизвлекает всё заново через LLM.)

### Параллелизм и лимиты

Чанки извлекаются параллельно. Настоящий троттл — **rate-governor**: по лимитам `rpm`/`tpm` из `config/models.json` он не даёт превысить квоту провайдера (бюджет общий на модель, считается по фактическому расходу токенов из ответа, поэтому работает и с Gemini/DeepSeek). `max_concurrent` (`settings.py` → `graphs.max_concurrent`, по умолчанию 18) — это **потолок одновременных вызовов**: при заданных лимитах достаточно держать его на уровне насыщения или выше (throughput выше не растёт, лишние потоки просто ждут); без лимитов он становится единственным регулятором нагрузки.

- **Возобновление**: успешно извлечённые чанки кэшируются (`extraction_cache.jsonl`); чанк с нефатальным сбоем вызова **не** кэшируется и повторится на следующем прогоне. Книга финализируется (помечается готовой) только когда извлеклись все её чанки.
- **Дневной лимит / устойчивый rate-limit**: если ограничение перестаёт восстанавливаться, прогон останавливается штатно (circuit breaker) — кэш сохранён, перезапуск продолжит с места остановки. Жёсткого счётчика по `rpd` нет: дневной лимит ловится по устойчивым 429.
- **Фатальные ошибки** (нет ключа/квоты/модели) останавливают прогон сразу.
- **Прерывание `Ctrl+C`**: отменяет ещё не начатые чанки и завершается, дождавшись лишь уже летящих вызовов (потоки нельзя убить мгновенно; максимум — request-timeout 120с). На первом нажатии печатается подсказка; второе нажатие пропускает ожидание летящих вызовов. Безопасно в любой момент: кэш append-only с устойчивостью к оборванной строке, выходные графы пишутся атомарно. Для мгновенной остановки — `kill -9 <pid>` из другого терминала, тоже без порчи данных. Перезапуск продолжит с места.
- **Сон / закрытие крышки (macOS)**: процесс не убивается — он замораживается и продолжает после пробуждения. Летящие в момент засыпания вызовы оборвутся, но это transient-ошибки → переретраиваются; прогресс не теряется. Для долгого фонового прогона держи Мак бодрым:
  ```bash
  caffeinate -i mytho graphs      # запрет idle-сна на время прогона
  ```
  Закрытие крышки усыпит всё равно (нет внешнего монитора/питания) — держи крышку открытой.
- В логах периодически печатается утилизация (`% TPM`/`% RPM`, throttled %), и итоговая сводка в конце.

Те же механизмы (governor, `map_concurrent`, кэш) использует и `mytho projections --summaries` для LLM-саммари; его параллелизм — `projection.max_concurrent` (по умолчанию 5).

### Тюнинг throughput

Как разогнать (или успокоить) LLM-шаг. Ключ — периодическая строка в логе:

```
LLM usage [gpt-4o-mini]: 200 requests, 315,901 tokens, ~72 req/min, 57% TPM, 14% RPM, throttled 0%
```

- `% TPM` / `% RPM` — утилизация заданных лимитов; **биндит та, что выше** (для многословного извлечения обычно TPM).
- `throttled %` — доля времени, которую вызовы простояли в ожидании лимитера.

Помечены `(cumulative)` — это **средние с начала прогона**, а не мгновенные. Вёдра стартуют полными, поэтому первые запросы идут бесплатно (`throttled ≈ 0`), а затем средние **разгоняются** и устаканиваются за ~1-2 минуты. Рост `throttled` с нуля в начале — это выход на насыщение, а не деградация; читай метрику после того, как она вышла на плато.

Диагностика:

| Что в логе | Значит | Что делать |
|---|---|---|
| `throttled ~0%`, `% TPM/RPM` низкие | недогруз: упираешься в латентность, не в лимит | **поднять** `max_concurrent` |
| `throttled` заметный или `% TPM/RPM` ~100 | насыщение: упёрся в квоту | оставить — выше не разгонится |
| нет `% TPM/RPM` (лимиты не заданы) | троттла нет, `max_concurrent` — единственный регулятор | крутить по железу/провайдеру |

Насколько поднимать: throughput растёт ~линейно с `max_concurrent`, пока не упрёшься в биндящий лимит. Грубо `новый ≈ текущий × (целевой% / текущий%)`. Пример: 57% TPM при 18 воркерах, цель ~90% → `18 × 90/57 ≈ 28`.

Крутить через env (без правки кода) или дефолты в `settings.py`:

```bash
MYTHO_GRAPHS__MAX_CONCURRENT=28        # graphs
MYTHO_PROJECTIONS__MAX_CONCURRENT=10   # summaries
```

Нюансы:
- Перебор безвреден (вёдра троттлят), но стоит потоков/соединений; абсурдно высокое значение повышает риск 429.
- Точка насыщения плавает с латентностью — держи небольшой запас, а не точное значение.
- `% TPM` / `throttled` считаются из фактического `usage`, поэтому работают и без заголовков провайдера (Gemini/DeepSeek).

## motifs

Строит **базу мотивов** — машиночитаемый, перекрёстно связанный слой традиционных фольклорных индексов — и кладёт её в `outputs/motifs/`. Независим от корпуса: можно запускать отдельно.

Источники (`config/motifs.json`):
- **Berezkin** — аналитический каталог Ю. Е. Березкина и Е. Н. Дувакина (areasofmyths.com): скрейп одной навигационной страницы даёт все ~3 500 мотивов (код, название, ареальные индексы, внутренние see-also и ссылки `ATU NNN`); по детальным страницам добираются краткие определения.
- **Trilogy** (`j-hagedorn/trilogy`, CC-BY-SA 4.0) — TMI (~46 000 мотивов Томпсона с иерархией) и ATU (~2 250 типов сказок, каждый с упорядоченным списком мотивов TMI из `atu_seq`).

Основные файлы:
- `src/motifs/build_motifs.py` — оркестратор шага (каждый запуск пересобирает из кэша `raw/`; `--force` перезагружает источники).
- `src/motifs/sources/berezkin.py` — скрейп + парсинг каталога Березкина (парсинг отделён от загрузки и покрыт тестами).
- `src/motifs/sources/trilogy.py` — загрузка и разбор CSV Trilogy (TMI, ATU, `atu_seq`, `atu_combos`).
- `src/motifs/sources/fetch.py` — загрузка-в-кэш (`outputs/motifs/raw/`): повторный запуск не ходит в сеть.
- `src/motifs/crosswalk.py` — cross-walk: ATU↔TMI (constituent из `atu_seq`, defining, и два inline — заметки TMI и summary ATU), Berezkin↔ATU (из ссылок `ATU NNN` в названиях) и прямой Berezkin↔TMI. Полный справочник — [cross-walk.md](motifs/crosswalk.md).
- `src/motifs/parallels.py` — эвристические текстовые параллели (шаг `[5/5]`): лексические двойники мотивов без записанной связи, как подсказки на страницах. Разбор — [cross-walk.md §8](motifs/crosswalk.md) и папка [crosswalk/](motifs/crosswalk/).
- `src/motifs/store.py` — раскладка файлов и чтение (кэш на процесс), общий с сервером.

Выход (`outputs/motifs/`): `berezkin.json`, `tmi.json`, `atu.json`, `crosswalk.json`, `parallels.json`, `meta.json` и кэш сырья `raw/`.

**Воспроизводимость и перезапуск.** Сырьё кэшируется в `raw/`, поэтому повторный запуск дёшев и безопасен к прерыванию. По умолчанию `mytho motifs` **каждый раз заново парсит и генерирует** данные из кэша `raw/` (недостающее докачивает); `--force` дополнительно перезагружает все источники.

```bash
mytho motifs           # пересобрать из кэша (докачать недостающее)
mytho motifs --force   # пересобрать с нуля (заново скачать источники)
```

Тюнинг скрейпа Березкина — через env (см. `.env.example`): `MYTHO_MOTIFS__MAX_WORKERS` (параллельные загрузки детальных страниц), `MYTHO_MOTIFS__BEREZKIN_DETAILS` (тянуть ли определения), `MYTHO_MOTIFS__MAX_MOTIFS` (ограничить число детальных страниц — используется `build --sample`).

**Обогащение из mapsofmyths.com** (английские названия/определения, таксономия type/group, прямые Thompson-id, распределение по традициям) — отдельный шаг пайплайна `mytho motifs`, кэшируется в `outputs/motifs/raw/mapsofmyths/`, результат — `outputs/motifs/mapsofmyths_*.json` (не коммитятся). Требует HTTP basic-auth: `MAPSOFMYTHS_AUTH=user:pass`; без кредов шаг пишет предупреждение и пропускается (каталог собирается без обогащения). Библиография Томпсона (folkmasa + курируемый список) — тоже шаг пайплайна, пишет `outputs/motifs/tmi_bibliography.json`. Сколько и каких сущностей дообогащено — видно в `mytho status`.

**Об ареалах (декодирование).** Ареальные индексы (`.19.21.29.`) — это глобальные номера макро-ареалов Березкина. Названия берутся напрямую из официального ключа во введении каталога (`intro.html`, раздел «Цифры соответствуют следующим регионам») — он захардкожен как `berezkin._CANONICAL_AREAS` (`canonical_area_legend()`). Нумерация начинается с 10 и идёт до 74 (~65 макро-ареалов: Африка → Европа → Азия → Океания → Сибирь → Сев. Америка → Мезоамерика → Юж. Америка); код 58 («Дельта Ориноко») упразднён и влит в 59 («Гвиана»), но всё ещё помечает часть старых записей, поэтому сохранён в ключе. Декодирование самих ареалов не требует детальных страниц; загрузка `berezkin_details` нужна лишь для коротких определений мотивов. Per-region легенда из `areas1.html` (список этносов с другой нумерацией) для этого **не** годится и не используется.

**Чистка названий мотивов.** Часть «опечаток» источника компенсируется на нашей стороне: латинские буквы-двойники внутри кириллических слов (`Cупруг` → `Супруг`) исправляются; ссылки на типы сказок без префикса (`, 804A`, `–653B`) и списки `ATU 311, 312` извлекаются в `atu_refs` (заодно убирая лишние числа из ареального списка); остаточная нотация Томпсона (`Th .1.4.1`) вырезается из названий. Оставшиеся единичные случаи — это легитимный контент (латинские имена вроде `Placidas`, англоязычные пометки) и не трогаются.

Cross-walk Berezkin↔TMI строится напрямую из кураторских Thompson-id (`tmi_refs`, из mapsofmyths) — единственный прямой мост, остальное через ATU; без обогащения mapsofmyths эта связь пуста. Подробный разбор источников — в [motif-index-data-sources.md](motifs/motif-index-data-sources.md).

## status

Показывает текущее состояние пайплайна: что построено, чего не хватает, размеры на диске.

```bash
mytho status
```

Вывод содержит секции Corpus, Embeddings, Projections, Graphs, Motifs с итоговым размером. В Graphs «готовыми» считаются только книги со всеми тремя графами (`beings.json`, `realms.json`, `ages.json`). В Motifs показываются счётчики по индексам (berezkin/tmi/atu). Размеры показываются **без** resumable-кэшей (их размер виден в `clean`).

## clean

Поиск и удаление осиротевших файлов: corpus-тексты без записи в каталоге, embedding-коллекции без модели в реестре, чанки без текста в корпусе, projections-директории без коллекции, graph-директории без текста в корпусе.

По умолчанию — dry run (только показывает что будет удалено):

```bash
mytho clean
```

Удалить орфаны:

```bash
mytho clean --apply
```

Resumable-кэши (`extraction_cache.jsonl`, `summaries.jsonl`, а также сырьё мотивов `outputs/motifs/raw/`) **показываются всегда** с размером, но удаляются только по явному `--caches` (они хранят оплаченные LLM-результаты и скачанные источники, позволяя дешёвую пересборку):

```bash
mytho clean --caches            # dry run: показать кэши
mytho clean --caches --apply    # удалить орфаны И все кэши
```

## export

Упаковывает построенные данные `outputs/` в переносимый zip, чтобы развернуть их на другой машине (без GPU/интернета/LLM, профиль `viewer`). Отдельной команды `import` нет — восстановление это просто распаковка.

```bash
mytho export            # mythoscope-export-<timestamp>.zip в корне проекта
mytho export --caches   # дополнительно включить resumable-кэши
```

Что внутри:
- **по умолчанию** — продукты `outputs/`: corpus, embeddings (каталог ChromaDB), projections, graphs, motifs; **без** кэшей и логов.
- **`--caches`** — добавляет resumable-кэши (`extraction_cache.jsonl`, `summaries.jsonl`, `outputs/motifs/raw/`). Логи не включаются никогда.

Члены архива — пути `outputs/...`, поэтому на целевой машине:

```bash
unzip mythoscope-export-<timestamp>.zip   # из корня проекта → воссоздаст outputs/
mytho server
```

Нюансы:
- **Орфаны не блокируют.** Если в `outputs/` есть осиротевшие данные (коллекции отключённых моделей и чанки удалённых текстов в ChromaDB, осиротевшие тексты/графы/проекции), `export` их **предупредит и всё равно включит** (он ничего не удаляет). Для чистого бандла сначала `mytho clean --apply`.
- **Версия chromadb.** Каталог ChromaDB копируется как есть и надёжно открывается только при совместимой версии chromadb (пин `chromadb>=1.0,<2`). `export` печатает версию, которой собрана БД, — поставь совместимую на целевой машине.
- **Текстовый поиск по запросу** офлайн не работает (нужны веса модели, их не везём); просмотр, графики, **поиск соседей по точкам**, графы и мотивы — работают.

Ручной эквивалент (если не нужна команда): `zip -r out.zip outputs -x 'outputs/logs/*' 'outputs/motifs/raw/*' '*/extraction_cache.jsonl' '*/summaries.jsonl'`.

## server

FastAPI-сервер и SPA-интерфейс.

Основные файлы:
- `src/server/run_server.py` создание приложения, middleware, статика.
- `src/server/api/corpus.py` каталог текстов, чтение документов, архив, традиции.
- `src/server/api/graphs.py` данные графов (персонажи, связи).
- `src/server/api/motifs.py` индексы мотивов, список/детали мотивов, cross-walk.
- `src/server/api/similarity.py` модели, семантический поиск, точки, проекции.
- `src/server/schemas.py` Pydantic-схемы запросов и ответов.
- `src/server/services/` сервисный слой (каталог, ZIP-архив, проекции, поиск).

### API эндпоинты

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/corpus/catalog` | Каталог текстов корпуса |
| GET | `/api/corpus/documents` | Текст документа по title |
| GET | `/api/corpus/archive` | ZIP-архив корпуса |
| GET | `/api/corpus/traditions` | Традиции с координатами |
| GET | `/api/graphs/{text_id}/{graph_type}` | JSON-данные графа (nodes + edges) |
| GET | `/api/motifs/indexes` | Индексы мотивов (berezkin/tmi/atu) + главы и счётчики |
| GET | `/api/motifs/{index}/motifs` | Список мотивов (фильтры `?chapter=&q=&limit=&offset=`) |
| GET | `/api/motifs/{index}/motif?id=…` | Детали мотива + связи cross-walk |
| GET | `/api/similarity/models` | Список embedding-моделей |
| GET | `/api/similarity/methods` | Список методов проекций |
| GET | `/api/similarity/projections/{model}/{method}` | JSON-данные проекции |
| GET | `/api/similarity/points/{model}/{text_id}` | Информация о точке (+ соседи через `?chunk_index=N&top_k=N`) |
| POST | `/api/similarity/search` | Семантический поиск |

### Интерактивная документация

FastAPI автоматически генерирует документацию из Pydantic-схем:

- `http://localhost:8000/docs` — Swagger UI (интерактивное тестирование эндпоинтов)
- `http://localhost:8000/redoc` — ReDoc (читаемая документация)
- `http://localhost:8000/openapi.json` — OpenAPI-схема (для кодогенерации или Postman)

### Запуск

```bash
mytho server
```

С явным указанием хоста и порта:

```bash
mytho server --host 0.0.0.0 --port 9000
```

Открыть интерфейс: `http://127.0.0.1:8000/`. При старте uvicorn печатает этот адрес (`Uvicorn running on http://...`) — в большинстве терминалов по нему можно кликнуть. Если bind на `0.0.0.0`, открывать всё равно по `127.0.0.1` (по `0.0.0.0` браузер не ходит).

### Публикация в интернет (Caddy)

По умолчанию сервер слушает `127.0.0.1` и недоступен извне. Для публичного доступа используйте [Caddy](https://caddyserver.com) как reverse proxy — он автоматически получает и обновляет HTTPS-сертификаты от Let's Encrypt.

Установка (Ubuntu/Debian):

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install caddy
```

Создайте `/etc/caddy/Caddyfile`:

```
mythoscope.example.com {
    reverse_proxy localhost:8000
}
```

Запуск:

```bash
sudo systemctl enable caddy
sudo systemctl start caddy
```

Caddy сам получит TLS-сертификат, настроит редирект HTTP → HTTPS и проксирует запросы в uvicorn. В проекте ничего менять не нужно — `mytho server` продолжает слушать localhost.

## server/web

Vanilla JS SPA на нативных ES-модулях (без бандлера и фреймворков). Hash-роутинг:
смена `#/path` (`hashchange`) перерисовывает страницу. Каждая страница — функция
`render`, которая строит DOM и регистрирует свою уборку через `onCleanup`; роутер
вызывает её при уходе с роута.

Файлы:
- `index.html` — точка входа, CDN-библиотеки (Plotly, Leaflet, Cytoscape) с `defer`, навбар.
- `assets/app.js` — роутер: таблица `ROUTES` (path → title + render-функция), `hashchange`/`DOMContentLoaded`, активный пункт навбара.
- `assets/core.js` — сгруппирован по секциям: общее состояние, роутинг-примитивы (`parseHash`, `onCleanup`/`cleanupRoute`), `api`, утилиты, data-хелперы (модели/корпус/традиции).
- `assets/tree-scaffold.js` — общий каркас дерева: секции мажоров + сворачивание; листья задают потребители.
- `assets/tree-sources.js` — дерево документов (corpus, graphs): major → tradition → книги.
- `assets/tree-traditions.js` — список традиций (major → tradition) для similarity и geography.
- `assets/search-utils.js` — общие функции семантического поиска и рендеринга результатов.
- `assets/page-corpus.js` — библиотека текстов, ридер, информация о книге.
- `assets/page-embeddings.js` — визуализация эмбеддингов, поиск, информация о точке.
- `assets/page-graphs.js` — графы персонажей / мест / эпох (Cytoscape).
- `assets/page-geography.js` — карта Leaflet с традициями.
- `assets/page-motifs.js` — раздел Motifs: выбор индекса, главы, поиск, список и детали мотива с кликабельными cross-walk-ссылками между индексами.
- `assets/page-about.js` — страница About (вкладки Vision / Methodology / …).
- `assets/chart.js` — графики (scatter / heatmap / distribution) на Plotly.
- `assets/chart-tooltip.js`, `chart-color.js` — хелперы графиков: тултип точки и тонирование приглушённых традиций.
- `assets/app.css` — все стили (с комментариями-разделителями по секциям).

Запускается через:

```bash
mytho server
```

## mockups

Автономные прототипы фич **вне основного приложения** — каждый это самодостаточный
`index.html` (инлайн CSS/JS, без сборки и фреймворков), читающий снапшот `data.js`,
собранный из индексов в `outputs/motifs/`. Живут в `mockups/`, `data.js` не
коммитятся (регенерируемые артефакты). Полный список и инструкции запуска —
[`mockups/README.md`](../mockups/README.md).

```bash
# с уже собранной базой мотивов (mytho motifs):
python mockups/07-tradition-motif-combined/build_data.py
python -m http.server -d mockups 8890   # → http://127.0.0.1:8890/07-tradition-motif-combined/
```

## Директории outputs/

Все генерируемые данные хранятся в `outputs/`:

- `outputs/corpus/` — основной текстовый корпус с метаданными (`corpus.json`) и описаниями традиций (`traditions.json`). Создается через `mytho corpus`.
- `outputs/embeddings/` — локальная Chroma DB с векторными коллекциями. Создается через `mytho embeddings`.
- `outputs/projections/` — результаты анализа: JSON-данные проекций (UMAP, heatmap, distribution). Создается через `mytho projections`.
- `outputs/graphs/` — JSON-графы (characters, realms, ages) для каждого текста. Создается через `mytho graphs`.
- `outputs/motifs/` — база мотивов: `berezkin.json`, `tmi.json`, `atu.json`, `crosswalk.json`, `parallels.json`, `meta.json` + кэш сырья `raw/`. Создается через `mytho motifs`.
- `outputs/logs/` — логи всех пайплайнов.

## Типовой пайплайн

Запустить всё одной командой:

```bash
mytho build --model bge-m3
```

Указать отдельную LLM-модель для шага graphs (embedding-модель задаётся через `--model`):

```bash
mytho build --model bge-m3 --llm gemini25-flash
```

Быстрый прогон для проверки пайплайна — первая активная embedding-модель и ограниченное
число текстов (по умолчанию 2). Можно передать своё число `N`, чтобы прогнать больше:

```bash
mytho build --sample        # дефолтный лимит (2 текста)
mytho build --sample 50     # переопределить: 50 текстов (или -s 50)
```

`N` ограничивает и корпус/графы (`max_texts`), и число детальных страниц мотивов
(`MYTHO_MOTIFS__MAX_MOTIFS`).

Или по шагам:

```bash
# 1. Собрать корпус (Gutenberg-тексты очищаются автоматически)
mytho corpus

# 2. Построить эмбеддинги
mytho embeddings

# 3. Построить визуальный анализ эмбеддингов
mytho projections

# 4. Извлечь графы персонажей через LLM
mytho graphs

# 5. Построить базу мотивов (Berezkin + TMI + ATU); независим от шагов 1-4
mytho motifs

# 6. Запустить веб-интерфейс
mytho server
```

Каждый шаг идемпотентен — если результат уже есть, он будет пропущен. Длинные шаги (`corpus`, `graphs`, `projections --summaries`) можно безопасно прервать `Ctrl+C` в любой момент: незавершённая работа отменяется, уже сделанное сохранено (тексты на диске, графы — атомарно, LLM-кэши append-only), и повторный запуск продолжит с места. Для принудительной пересборки:

```bash
mytho build --force
```

Проверить состояние и найти мусор:

```bash
mytho status
mytho clean
```
