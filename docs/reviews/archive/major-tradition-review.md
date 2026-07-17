# Разбор поля `major_tradition` (макро-ареал; бэк + config + фронт)

Аудит того, где `major_tradition` (в UI — «macro-area» / «major») выводится,
хранится, передаётся и используется, со всеми местами хранения, дублями и
нелогичностями. Состояние на коммит `ba7656a`. Это аналитический документ —
код по нему ещё не менялся.

Одной фразой: `major_tradition` — **производное, денормализованное** поле. Книги
его не хранят; он один раз выводится на сборке из дерева `config/traditions.json`
(имя major = ключ дерева), затем копируется в каждую строку `corpus.json`, в путь
каждого текстового файла и в метаданные каждого чанка эмбеддингов, а на фронт
уезжает только через `/api/corpus/catalog`.

> **Канон.** Единый top-level классификатор традиций — ось `region` — канонически задан в
> [`research/regions.md`](../../../research/regions.md): окончательная спецификация **14 регионов** (названия,
> описания, подрубрики, страты, традиции, палитра). Он — корпус-first преемник ретайрнутого `major_tradition`
> и берёзкинского 12-ареального `area`; **при расхождении этого разбора с `regions.md` истина в `regions.md`.**

## 1. Где выводится (бэк, build-time)

Вся резолюция — в `corpus/builder.py`. Дерево грузится и из него строятся две
производные карты:

```python
# builder.py:107-134
def _load_traditions_config() -> dict:           # config/traditions.json (или {} при ошибке)
    ...
def _flat_tradition_info(tree) -> dict:           # tradition -> info (major отбрасывается)
    for node in tree.values():
        for trad, info in (node.get("traditions") or {}).items():
            flat[trad] = info
def _tradition_major_map(tree) -> dict:           # tradition -> major (та самая lookup)
    for major, node in tree.items():
        for trad in (node.get("traditions") or {}):
            mapping[trad] = major
```

Применяется к каждому документу в `build_corpus` (`builder.py:183-190`):

```python
trad_major = _tradition_major_map(_load_traditions_config())
for item in download_list:
    item["major_tradition"] = trad_major.get(item.get("tradition"), "")
    if not item["major_tradition"]:
        logger.warning("No major_tradition for tradition %r ...", ...)
```

**Дефолт при отсутствии традиции в дереве — пустая строка `""`** (плюс WARNING).
Не падает. Дальше это значение задаёт путь на диске (`builder.py:91` →
`text_path`, `utils.py:63-67`): `corpus_dir/<major>/<tradition>/<title>.txt` —
при пустом major файл ложится прямо в `corpus_dir/`.

То есть major рождается **на сборке корпуса**, детерминированно (в отличие от
цвета — см. `color-system-review.md`), как чистая функция дерева.

## 2. Где config определяет дерево

`config/traditions.json`. Верхнеуровневые ключи **и есть** макро-ареалы; у каждого
один словарь `"traditions"`. Имя major — **только ключ дерева**, отдельным полем на
традиции его нет (у узла-традиции лишь `description` + `coordinates`):

```json
{ "Near Eastern":  { "traditions": { "Ancient Egyptian": { "description": "...", "coordinates": [...] } } },
  "Indo-European": { "traditions": { "Anglo-Saxon": {...}, "Greek": {...}, ... } }, ... }
```

Ареалы: `Near Eastern, Indo-European, Indigenous Australian, Mesopotamian, Indian,
Chinese, Abrahamic, Finno-Ugric, Buddhist, Polynesian, Mesoamerican, African`.
`config/corpus.json` (список книг) несёт только `tradition` — потому резолюция и нужна.

## 3. Где хранятся (все места)

| Место | Что | Жизнь |
|---|---|---|
| `outputs/corpus/corpus.json` → `rows[i].major_tradition` | канонический стор при сервинге | на диске, перезаписывается каждой сборкой |
| **Структура каталогов на диске** | major = первый сегмент пути (`utils.py:63-67`) | на диске |
| Метаданные чанков в ChromaDB | `major_tradition` в каждом чанке (`build_embeddings.py:157-163`, из `CorpusFileInfo`) | в `outputs/embeddings/` |
| **Каждая строка catalog-ответа** `documents[i].major_tradition` | копия на *каждом* документе | в ответе `/api/corpus/catalog` |
| `state.corpusDocuments` (фронт, `core.js:8`) | полные строки, включая major | на сессию |
| `state.corpusCollapsedMajors` (`core.js:12`) | `Set` имён major как ключей сворачивания | на сессию |
| `state.corpusOpenTraditions` (`core.js:10`) | составные ключи `major|tradition` | на сессию |

**Где major НЕ хранится (важно):** в `outputs/corpus/traditions.json`. `_update_traditions`
(`builder.py:137-158`) осознанно уплощает дерево до `tradition -> info` и **выбрасывает
major** (комментарий `builder.py:149-150`: «Built corpus/traditions.json stays flat …
the tree is only the source of truth in config/»). Соответственно `read_traditions`
(`utils.py:80-90`) и `traditions_with_books` (`services/corpus.py:39-49`) major не
добавляют. То есть у served-объекта традиции major-а нет вовсе.

## 4. Как передаётся на фронт

- **`/api/corpus/catalog`** (`api/corpus.py:12`) → `get_catalog_documents`
  (`services/corpus.py:10-36`) спредит всю строку (`{**row, "color": ...}`), поэтому
  `major_tradition` есть **на каждом документе**. Схема `CorpusDocument.major_tradition:
  str = ""` (`schemas.py:40`). **Это единственный канал, несущий major в UI.**
- **`/api/corpus/traditions`** (`api/corpus.py:33`) → `traditions_with_books` →
  `TraditionsResponse` — **major не несёт**.
- **`/api/corpus/documents`** (`api/corpus.py:18-30`) принимает `major_tradition`
  как **обязательный query-параметр** и использует его лишь для сборки пути к файлу
  (`utils.py:70-77`); фронт передаёт его из `buildCorpusApiUrl` (`core.js:164-172`).
- **`/api/similarity/search` и `/points/...`** (`similarity.py:50,82`) → `SearchResult.
  major_tradition: str = ""` (`schemas.py:30`), заполняется спредом Chroma-метаданных
  (`services/similarity.py:33,67`). **Но фронт его не читает** (в `page-embeddings.js`
  и `search-utils.js` нет ни одного упоминания major) — мёртвый payload.

## 5. Где используются (фронт)

Одна функция группировки, один scaffold дерева, два дерева + одна info-панель.

- **`core.js:178-192` `groupDocuments`** — единственное место группировки:
  `const major = doc.major_tradition || "Other";` строит `Map<major, Map<tradition, docs[]>>`.
  **Дефолт-метка: `"Other"`.**
- **`core.js:174-176` `corpusTraditionKey(major, tradition)`** →
  `` `${major || "Other"}|${tradition || "Unknown"}` `` — составной ключ open/collapse
  состояния традиции.
- **`tree-scaffold.js:5-32` `renderMajorTree`** — по одному
  `<section class="major-section" data-major="…">` на major, заголовок
  `<button class="major-title">${major}</button>`, состояние сворачивания из
  `state.corpusCollapsedMajors.has(major)`; `bindMajorToggles` пишет обратно по
  `data-major` (дефолт `"Other"`, `:39`). То есть major задаёт **существование
  секции, текст её заголовка и ключ сворачивания.**
- **`tree-sources.js`** (библиотека книг): `initOpenTraditions` сидит `corpusOpenTraditions`
  ключами `corpusTraditionKey(major, tradition)`; листья пересобирают тот же ключ из
  `section.dataset.major`. Major здесь кормит только составной ключ; цвет традиции —
  из `docs[0].color`, не из major.
- **`tree-traditions.js`** (список традиций): major даёт только секции/заголовки через
  scaffold (сам `renderTraditionPicks` аргумент `major` игнорирует).
- **`page-corpus.js:67`** — метка info-панели книги:
  `` `${doc.major_tradition || "Other"} / ${doc.tradition || "Unknown"}` `` — только показ.
- **`app.css:261-300`** — стили `.major-section` / `.major-title` (жирный заголовок
  17px, аффорданс ▾/▸) / `.major-body` (скрыт при `.collapsed`).
- **`page-geography.js`, `page-motifs.js`** — major не используют.

## 6. Сортировка / порядок

- Единственная сортировка по major — **на бэке**, в `get_catalog_documents`
  (`services/corpus.py:28-34`): ключ `(major_tradition, tradition, title)`. Значит
  массив каталога приходит **уже отсортированным по major алфавитно**.
- Порядок секций в UI поэтому определяется этой сортировкой, **а не порядком ключей в
  `config/traditions.json`**: `groupDocuments` строит `Map` в порядке итерации массива
  (insertion order), а массив уже major-отсортирован. Пустой/`Other` идёт первым
  (`"" < любой буквы`). Порядок дерева в конфиге на UI не влияет.

## 7. Дубли, избыточность, нелогичности

1. **Денормализация на каждый документ** (как было с цветом). Major принадлежит
   традиции (1:N), но копируется в каждую строку `corpus.json`, в каждый
   `/catalog`-документ и в метаданные каждого чанка. Ни разу не хранится один раз
   на served-объекте традиции.
2. **Асимметрия двух представлений традиции.** `outputs/corpus/traditions.json` (и,
   значит, `/api/corpus/traditions` → `state.traditionInfo`) major **выбрасывает**, а
   `/catalog`-документы его несут. Фронт не может узнать major традиции из
   `traditionInfo` — только через документные строки и `groupDocuments`. У традиции
   **без книг** major на фронте вообще неоткуда взять.
3. **Три разных дефолта «нет major»:**
   - резолюция в билдере → `""` (`builder.py:187`);
   - сортировка каталога → `""` (`services/corpus.py:30`);
   - итератор эмбеддингов → `"unknown"` (`iterator.py:57`);
   - схема `SearchResult` → `""` (`schemas.py:30`);
   - фронт (группировка / ключ / метка) → `"Other"` (`core.js:175,182`;
     `tree-scaffold.js:39`; `page-corpus.js:67`).
   Одна и та же ситуация «major нет» всплывает как `""`, `"unknown"` или `"Other"`
   в зависимости от пути. Особенно выбивается `"unknown"` в эмбеддингах — попав в
   группировку, он стал бы отдельной корзиной, отличной от `"Other"`.
4. **Transported-but-unused на similarity.** `SearchResult.major_tradition`
   сериализуется на каждый результат поиска, но ни один фронт-файл его не читает.
5. **Две независимые модели резолюции/потребления:** Python `_tradition_major_map`
   (дерево→lookup, на сборке) и JS `groupDocuments` (строка→группа, на рендере).
   Совпадают только потому, что сборка денормализует major в строки; единого
   served «tradition→major» источника правды нет.
6. **Порядок дерева в конфиге незначим для UI** (вопреки ожиданию): и
   `_tradition_major_map`, и `_flat_tradition_info` идут по дереву в insertion order,
   но UI пересортировывает алфавитно через сортировку каталога (п. 6). Порядок
   конфига влияет лишь на то, какой major «победит», если одно имя традиции попадёт
   под два ареала (в `_tradition_major_map` выигрывает последний).

## 8. Палитра `REGION_COLORS` в `page-motifs.js` — это НЕ major_tradition

`REGION_COLORS` (`page-motifs.js:1046-1052`, комментарий про «12-geographic-layer
mockup») ключуется по **географическим регионам** (`Europe`, `Near East`, `Central
Asia`, `South Asia`, `East Asia`, `Siberia`, `Arctic`, `Africa`, `Oceania`, …, `—`).
Эти имена **не совпадают** со значениями `major_tradition` (`Indo-European`,
`Abrahamic`, `Finno-Ugric`, …). Используется для overview-графиков индексов мотивов
по полю `region` на записях мотива (`regionColor`, сортировка `page-motifs.js:1350`).
Это **отдельная** классификация (гео-регион мотива), параллельная, но не тождественная
культурно-языковым ареалам традиций. Смешивать их нельзя.

## Что напрашивается (на будущее, не реализовано)

- **Один дефолт** «нет major» вместо трёх (`""` / `"unknown"` / `"Other"`).
- Хранить major **один раз на традиции** в served `traditions.json` (снять
  асимметрию с `/catalog` и дать фронту `tradition→major` без документов) — либо,
  наоборот, признать `/catalog`-денормализацию единственным каналом и убрать
  мёртвый `major_tradition` из `SearchResult`.
- Порядок секций в UI осознанно привязать к порядку дерева в конфиге (если он
  задуман осмысленным), а не к алфавиту — сейчас конфиг-порядок молча теряется.
