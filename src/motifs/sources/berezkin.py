"""Berezkin & Duvakin areal motif catalogue (areasofmyths.com).

The whole motif inventory lives in one navigation page (``index-left.html``):
each ``<li>`` gives a motif code, name, optional internal see-also codes, and a
trailing list of areal indices. Per-motif detail pages add a short definition.

The areal indices decode to the macro-area names published verbatim in the
catalogue's introduction (``intro.html`` — "Цифры соответствуют следующим
регионам"). That list is the authoritative key (codes 10–74, with 58 a defunct
code now folded into 59), so we hard-code it as ``_CANONICAL_AREAS`` rather than
inferring it. (The finer per-region legend on ``areas1.html`` is a separate,
differently-numbered ethnos list and does not apply.)

Parsing is split from fetching so it can be unit-tested on static fixtures.
"""

from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from settings import settings

from . import mapsofmyths
from .fetch import fetch_text

logger = logging.getLogger(__name__)

# A Berezkin motif code: latin letter(s), a digit, then any letters/digits — e.g.
# A1, A1A, A2a1, B12. Used to read the leading code of an entry.
_CODE = r"[A-Za-z]+[0-9][A-Za-z0-9]*"
_LEADING_CODE_RE = re.compile(rf"^({_CODE})\.\s*")
# A see-also reference to another Berezkin motif (uppercase-initial code). Some
# codes trail a stray ".I"/".I.I" artifact in the source — consumed but dropped.
_SEE_ALSO_RE = re.compile(r"\b([A-Z][A-Za-z]*[0-9][A-Za-z0-9]*)(?:\.I+)*")
# An "ATU …" clause, possibly a comma-separated list ("ATU 311, 312", "ATU 328A*").
_ATU_CLAUSE_RE = re.compile(r"ATU\s+(\d[\dA-Za-z*]*(?:\s*,\s*\d[\dA-Za-z*]*)*)")
# A bare tale-type reference left in a title ("…, 804A", "–653B"): digits followed
# by a letter (so it can't be confused with an areal index, which is pure digits).
_BARE_ATU_RE = re.compile(r"(?<![A-Za-z0-9])(\d{2,4}[A-Za-z][A-Za-z0-9]*\*?)")
# Leftover Thompson notation ("… Th .1.4.1; .2.2", "… Th") — stripped from names.
_THOMPSON_RE = re.compile(r"\bTh\b[\s.,;0-9]*")
# A Thompson (TMI) motif id in a title — a code carrying a dotted sub-number
# ("A736.2", "A736.2."), which the source appends as a cross-reference. Berezkin's
# own ids never use a dotted sub-number, so stripping this never eats a real
# see-also; the ref itself is captured via the mapsofmyths cross-walk (tmi_refs).
# The lead letter may be a Cyrillic homoglyph (the source sometimes types "С15.1"
# with a Cyrillic С); the dotted sub-number keeps that from matching plain words.
_THOMPSON_ID_RE = re.compile(r"\b[A-ZА-Я]\d[A-Za-z0-9]*(?:\.\d+)+\.?")
# Berezkin's own see-also marker in a title: the literal abbreviation "см." ("see"),
# at a token boundary so it isn't matched inside words like "смерти"/"Смоляная".
# Captures the rest of the title, from which the cross-referenced codes are pulled.
_SEE_MARKER_RE = re.compile(r"(?:^|[\s,;(])см\.\s*(.+)$", re.IGNORECASE)
# A chapter header in the nav, e.g. "A. СОЛНЦЕ И ЛУНА" or
# "K. ПРИКЛЮЧЕНИЯ I(1): ДЕЯНИЯ ГЕРОЕВ" — name starts with a Cyrillic capital,
# then anything (colon/parens/roman numerals appear in some headers).
_CHAPTER_RE = re.compile(r"^\s*([A-Z])\.\s+([А-ЯЁ].+?)\s*$")
# The trailing areal-index list: preceded by whitespace/comma, may open with "(".
_AREA_RE = re.compile(r"[\s,]+[.(]*\d[\d.()\s,\-]*$")
# Berezkin groups societies into ~70 areal units; anything well above that is a
# parsing artifact (e.g. a digit that leaked out of a name or a tale-type code).
_MAX_AREA = 150

# Authoritative areal-index -> macro-area key, copied verbatim from the catalogue
# introduction (intro.html, "Цифры соответствуют следующим регионам"). Numbering
# starts at 10; code 58 (Дельта Ориноко) is defunct, now folded into 59 (Гвиана),
# but it still tags older entries in the inventory, so it is kept here.
_CANONICAL_AREAS: dict[str, str] = {
    "10": "ЮЗ Африка",
    "11": "Бантуязычная Африка",
    "12": "Западная Африка",
    "13": "Судан – Восточная Африка",
    "14": "Северная Африка",
    "15": "Южная Европа",
    "16": "Западная Европа",
    "17": "Передняя Азия",
    "18": "Австралия",
    "19": "Меланезия",
    "20": "Полинезия – Микронезия",
    "21": "Тибет – Северо-Восток Индии",
    "22": "Бирма – Индокитай",
    "23": "Южная Азия",
    "24": "Малайзия – Индонезия",
    "25": "Тайвань – Филиппины",
    "26": "Китай – Корея",
    "27": "Балканы",
    "28": "Средняя Европа",
    "29": "Кавказ – Малая Азия",
    "30": "Иран – Средняя Азия",
    "31": "Северная Европа",
    "32": "Волга – Пермь",
    "33": "Туркестан",
    "34": "Южная Сибирь – Монголия",
    "35": "Западная Сибирь",
    "36": "Восточная Сибирь",
    "37": "Амур – Сахалин",
    "38": "Япония",
    "39": "СВ Азия",
    "40": "Арктика",
    "41": "Субарктика",
    "42": "СЗ побережье",
    "43": "Побережье – Плато",
    "44": "Средний Запад",
    "45": "Северо-Восток",
    "46": "Равнины",
    "47": "Юго-Восток США",
    "48": "Калифорния",
    "49": "Большой Бассейн",
    "50": "Большой Юго-Запад",
    "51": "СЗ Мексика",
    "52": "Мезоамерика",
    "53": "Гондурас – Панама",
    "54": "Антилы",
    "55": "Северные Анды",
    "56": "Льяносы",
    "57": "Южная Венесуэла",
    "58": "Дельта Ориноко",
    "59": "Гвиана",
    "60": "Эквадор",
    "61": "Западная Амазония",
    "62": "СЗ Амазония",
    "63": "Центральная Амазония",
    "64": "Восточная Амазония",
    "65": "Центральные Анды",
    "66": "Монтанья – Журуа",
    "67": "Боливия – Гуапоре",
    "68": "Южная Амазония",
    "69": "Арагуая",
    "70": "Восточная Бразилия",
    "71": "ЮВ Бразилия",
    "72": "Чако",
    "73": "Южная Бразилия",
    "74": "Южный Конус",
}


def canonical_area_legend() -> dict[str, str]:
    """The published areal-index -> macro-area key (a fresh copy each call)."""
    return dict(_CANONICAL_AREAS)

# Latin letters that are visual twins of Cyrillic ones — the source occasionally
# types the Latin form inside a Cyrillic word ("Cупруг" for "Супруг").
_HOMOGLYPHS = {
    "A": "А", "a": "а", "B": "В", "C": "С", "c": "с", "E": "Е", "e": "е",
    "H": "Н", "K": "К", "k": "к", "M": "М", "O": "О", "o": "о", "P": "Р",
    "p": "р", "T": "Т", "X": "Х", "x": "х", "y": "у",
}


def _is_cyrillic(ch: str) -> bool:
    return bool(ch) and ("Ѐ" <= ch <= "ӿ")


def _fix_homoglyphs(name: str) -> str:
    """Replace a Latin letter with its Cyrillic twin when it sits in Cyrillic text."""
    chars = list(name)
    for i, ch in enumerate(chars):
        twin = _HOMOGLYPHS.get(ch)
        if twin and (_is_cyrillic(name[i - 1] if i else "") or _is_cyrillic(name[i + 1] if i + 1 < len(name) else "")):
            chars[i] = twin
    name = "".join(chars)
    # A lone Latin homoglyph word between Cyrillic words (e.g. the preposition
    # "c" typed Latin in "Существо c четным") — both neighbours are Cyrillic.
    return re.sub(
        r"(?<=[А-Яа-яЁё] )([A-Za-z])(?= [А-Яа-яЁё])",
        lambda mt: _HOMOGLYPHS.get(mt.group(1), mt.group(1)),
        name,
    )


def chapter_of(code: str) -> str:
    """Leading-letter chapter for a Berezkin code (``B12`` -> ``B``)."""
    m = re.match(r"[A-Za-z]+", code)
    return (m.group(0)[0].upper() if m else code[:1]).upper()


def _parse_area_seq(area_text: str) -> list[tuple[int, bool]]:
    """Parse a dotted area list into ordered ``(index, parenthetical)`` pairs.

    A ``-`` between two numbers denotes an inclusive range; parentheses mark a
    comparative entry (``(.44.)``) — the flag lets us exclude those when aligning
    indices to detail-page headers. Implausibly large numbers (a digit that leaked
    out of a name) are dropped.
    """
    tokens = re.findall(r"\(|\)|\d+|-", area_text)
    out: list[tuple[int, bool]] = []
    depth = 0
    i = 0

    def add(n: int) -> None:
        if 1 <= n <= _MAX_AREA:
            out.append((n, depth > 0))

    while i < len(tokens):
        tok = tokens[i]
        if tok == "(":
            depth += 1
        elif tok == ")":
            depth = max(0, depth - 1)
        elif tok == "-":
            pass
        else:
            start = int(tok)
            if i + 2 < len(tokens) and tokens[i + 1] == "-" and tokens[i + 2] not in ("(", ")", "-"):
                end = int(tokens[i + 2])
                if 0 <= end - start <= 300:
                    for k in range(start, end + 1):
                        add(k)
                else:
                    add(start)
                    add(end)
                i += 2
            else:
                add(start)
        i += 1
    return out


def _expand_areas(area_text: str) -> list[int]:
    """Sorted unique areal indices from a dotted area list (faithful numbers)."""
    return sorted({n for n, _ in _parse_area_seq(area_text)})


def parse_motif_entry(text: str, page: str) -> dict | None:
    """Parse one nav ``<li>`` link into a motif record, or None if it has no code.

    Layout is ``CODE. Name. [SEE-ALSO codes] .area.area.`` — the areal list is
    introduced by a space-dot before the first number (``... .19.21.``), which
    lets us split it off without eating the digits of a see-also code (``A50.``).
    """
    text = " ".join(text.split())
    m = _LEADING_CODE_RE.match(text)
    if not m:
        return None
    code = m.group(1)
    rest = text[m.end():].strip()

    # ATU tale-type cross-references in the title — "ATU 294", "ATU 328A*", or a
    # comma-separated list "ATU 311, 312". Capturing the whole clause keeps the
    # trailing numbers from leaking into the areal-index list.
    atu_refs: list[str] = []
    for clause in _ATU_CLAUSE_RE.findall(rest):
        atu_refs.extend(part.strip().rstrip(".,") for part in clause.split(","))
    rest = _ATU_CLAUSE_RE.sub("", rest)

    # Trailing areal index list (whitespace/comma-introduced; may open with "(").
    areas: list[int] = []
    before = rest
    area_match = _AREA_RE.search(rest)
    if area_match:
        areas = sorted({n for n, _ in _parse_area_seq(rest[area_match.start():])})
        before = rest[: area_match.start()].strip()

    # Bare tale-type references the source wrote without the "ATU" prefix
    # ("…, 804A", "–653B") — digits + a letter, so never an areal index.
    atu_refs = _dedup(atu_refs + _BARE_ATU_RE.findall(before))

    # What remains is the name plus see-also codes (cross-references to other
    # Berezkin motifs). Codes are latin; the name is Cyrillic, so pulling the code
    # tokens out — along with bare refs and leftover Thompson notation — leaves a
    # clean name. A latin glyph glued to Cyrillic is then de-homoglyphed.
    # Drop Thompson (TMI) cross-refs like "A736.2" first: their code stem must not
    # be read as a Berezkin see-also, nor their ".2" tail left glued to the name.
    before = _THOMPSON_ID_RE.sub(" ", before)
    # A title's trailing codes are foreign (Thompson) equivalences — already carried
    # by the mapsofmyths cross-walk (tmi_refs). Berezkin's own see-also references
    # are the ones marked "см." ("see"); take see-also codes only from that clause.
    m_see = _SEE_MARKER_RE.search(before)
    see_also = _dedup(c for c in _SEE_ALSO_RE.findall(m_see.group(1)) if c != code) if m_see else []
    name = _THOMPSON_RE.sub(" ", before)
    name = _BARE_ATU_RE.sub(" ", name)
    name = _SEE_ALSO_RE.sub(" ", name)
    name = _fix_homoglyphs(name)
    name = re.sub(r"\(\s*\)", " ", name)
    name = re.sub(r"\s+", " ", name).strip(" .,;–-").strip()

    return {
        "id": code,
        "chapter": chapter_of(code),
        "name": name,
        "areas": areas,
        "see_also": see_also,
        "atu_refs": atu_refs,
        "page": page,
    }


def _dedup(items) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def parse_index(html: str) -> tuple[list[dict], dict[str, str]]:
    """Parse the nav page into (motifs, chapter-titles-by-letter)."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")

    # Chapter headers are inconsistently marked up: "A." sits in a <p>, the rest
    # ("C. КАТАСТРОФЫ" …) in <b>. Scan both.
    chapters: dict[str, str] = {}
    for tag in soup.find_all(["p", "b"]):
        cm = _CHAPTER_RE.match(tag.get_text(" ", strip=True))
        if cm:
            chapters[cm.group(1)] = cm.group(2).strip()

    motifs: list[dict] = []
    seen: set[str] = set()
    for a in soup.select("li a[href]"):
        href = a.get("href", "")
        if not href.endswith(".html"):
            continue
        entry = parse_motif_entry(a.get_text(" ", strip=True), href)
        if entry and entry["id"] not in seen:
            seen.add(entry["id"])
            motifs.append(entry)
    return motifs, chapters


def parse_definition(html: str) -> str:
    """Extract a motif's short definition (first ``NormalLis`` paragraph)."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    node = soup.find("p", class_="NormalLis")
    return " ".join(node.get_text(" ", strip=True).split()) if node else ""


# ---------------------------------------------------------------------------
# English enrichment (mapsofmyths.com)
# ---------------------------------------------------------------------------

# Enrichment scraped from the sister site mapsofmyths.com (same motif ids), keyed
# by upper-cased id. The files live next to the index JSONs in outputs/motifs/ and
# are (re)generated by the mapsofmyths pipeline step (motifs.sources.mapsofmyths);
# when absent (no credentials at build time) the enrichment is simply skipped.
def _load_json(name: str, key: str) -> dict:
    import json

    path = Path(settings.motifs_dir) / name
    try:
        return json.loads(path.read_text(encoding="utf-8")).get(key, {})
    except FileNotFoundError:
        return {}


def load_english() -> dict[str, dict]:
    """``{ID_UPPER: {name_eng, definition_eng}}`` from the mapsofmyths refresh."""
    return _load_json(mapsofmyths.EN_FILE, "motifs")


def load_nodes() -> dict[str, dict]:
    """``{ID_UPPER: {type, group, atu, tmi, traditions}}`` from mapsofmyths nodes."""
    return _load_json(mapsofmyths.NODES_FILE, "motifs")


def load_traditions() -> dict[str, dict]:
    """``{areal_id: {name, name_rus, areal_path, language}}`` — the tradition catalogue."""
    return _load_json(mapsofmyths.TRADITIONS_FILE, "traditions")


def _split_refs(value: str) -> list[str]:
    """A ``/``, ``,`` or ``;`` separated id field into a clean list."""
    return [p.strip() for p in re.split(r"[,;/]", value or "") if p.strip()]


def _attach_english(motifs: list[dict]) -> None:
    """Prefer the English name/definition from mapsofmyths (case-insensitive id).

    The English text (near-complete coverage) becomes the motif's primary ``name``
    and ``definition``; the Russian originals are kept as ``name_rus`` /
    ``definition_rus`` (shown as sub-titles on the motif page). Motifs without an
    English match keep their Russian text unchanged.
    """
    english = load_english()
    if not english:
        return
    hit = 0
    for motif in motifs:
        en = english.get(motif["id"].upper())
        if not en:
            continue
        hit += 1
        if en.get("name_eng"):
            motif["name_rus"] = motif.get("name", "")
            motif["name"] = en["name_eng"]
        if en.get("definition_eng"):
            motif["definition_rus"] = motif.get("definition", "")
            motif["definition"] = en["definition_eng"]
    logger.info("Berezkin: English name/definition preferred for %d/%d motifs (mapsofmyths)", hit, len(motifs))


def _attach_nodes(motifs: list[dict]) -> None:
    """Attach the per-motif node data from mapsofmyths (case-insensitive id):

    - ``motif_type`` / ``motif_group`` — the 2-level thematic taxonomy;
    - ``tmi_refs`` — direct Thompson (TMI) motif ids (new: not derivable from ours);
    - ``atu_refs`` — merged with the ids already parsed from the Russian title;
    - ``traditions`` — areal ids of the traditions attesting the motif (§ hierarchy
      in ``mapsofmyths_traditions.json``).
    """
    nodes = load_nodes()
    if not nodes:
        return
    n_type = n_tmi = n_trad = 0
    for motif in motifs:
        nd = nodes.get(motif["id"].upper())
        if not nd:
            continue
        if nd.get("type"):
            motif["motif_type"] = nd["type"]
            n_type += 1
        if nd.get("group"):
            motif["motif_group"] = nd["group"]
            motif["motif_group_num"] = nd.get("group_num", "")
        if nd.get("tmi"):
            motif["tmi_refs"] = _split_refs(nd["tmi"])
            n_tmi += 1
        if nd.get("atu"):  # union with the title-parsed refs, order-preserving
            motif["atu_refs"] = _dedup(list(motif.get("atu_refs", [])) + _split_refs(nd["atu"]))
        if nd.get("traditions"):
            motif["traditions"] = nd["traditions"]
            n_trad += 1
    logger.info("Berezkin: mapsofmyths nodes — type:%d tmi:%d traditions:%d of %d motifs",
                n_type, n_tmi, n_trad, len(motifs))


# ---------------------------------------------------------------------------
# Fetch orchestration
# ---------------------------------------------------------------------------


def build(config: dict, *, force: bool = False) -> dict:
    """Scrape and parse the Berezkin catalogue into a store-ready dict."""
    base = config["base_url"].rstrip("/")
    encoding = config.get("encoding", "windows-1251")
    cache = Path(settings.motifs_dir) / "raw" / "berezkin"

    index_html = fetch_text(
        f"{base}/{config['index_page']}", cache / config["index_page"], encoding=encoding, force=force
    )
    motifs, chapters = parse_index(index_html)
    logger.info("Berezkin: parsed %d motifs across %d chapters", len(motifs), len({m["chapter"] for m in motifs}))

    if config.get("fetch_details", True) and settings.motifs.berezkin_details:
        _fetch_details(motifs, base, cache, encoding, force)

    _attach_english(motifs)
    _attach_nodes(motifs)

    return {
        "label": config.get("label", "Berezkin"),
        "long_label": config.get("long_label", ""),
        "attribution": config.get("attribution", ""),
        "homepage": config.get("homepage", ""),
        "chapters": chapters,
        "areas": canonical_area_legend(),
        "traditions": load_traditions(),  # areal_id -> name/hierarchy/language
        "motifs": motifs,
    }


def _fetch_details(motifs: list[dict], base: str, cache: Path, encoding: str, force: bool) -> None:
    """Fetch detail pages and attach each motif's short definition in place."""
    targets = motifs
    if settings.motifs.max_motifs is not None:
        targets = motifs[: settings.motifs.max_motifs]
    logger.info("Berezkin: fetching %d detail pages (definitions)...", len(targets))

    def fetch_one(motif: dict) -> tuple[dict, str, str | None]:
        url = f"{base}/{motif['page']}"
        try:
            html = fetch_text(url, cache / motif["page"], encoding=encoding, force=force)
            return motif, parse_definition(html), None
        except Exception as exc:  # a missing/odd page must not abort the whole build
            return motif, "", str(exc)

    workers = max(1, settings.motifs.max_workers)
    definitions: dict[str, str] = {}
    errors = 0
    no_definition = 0  # fetched fine, but the page carries no NormalLis definition
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for motif, definition, error in pool.map(fetch_one, targets):
            if error:
                errors += 1
                logger.warning("Berezkin: detail fetch FAILED — %s %s — %s/%s: %s",
                               motif["id"], motif.get("name", ""), base, motif["page"], error)
            elif definition:
                definitions[motif["id"]] = definition
            else:
                no_definition += 1

    for motif in motifs:
        motif["definition"] = definitions.get(motif["id"], "")
    if errors:
        logger.warning("Berezkin: %d detail-page fetches failed (listed above)", errors)
    logger.info("Berezkin: attached %d definitions (%d pages have no definition, %d fetch errors)",
                len(definitions), no_definition, errors)
