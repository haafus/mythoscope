"""Trilogy dataset (j-hagedorn/trilogy): TMI + ATU as tidy CSVs.

We pull four files: ``tmi`` (Thompson motifs with parsed hierarchy), ``atu_df``
(tale types), ``atu_seq`` (the ordered TMI motifs that make up each tale type —
the bridge that powers the ATU<->TMI cross-walk) and ``atu_combos`` (tale types
commonly told together).
"""

from __future__ import annotations

import collections
import csv
import io
import logging
import re
from pathlib import Path

from settings import settings

from . import atu_regions
from .culture_dict import build_legend
from .fetch import fetch_to_cache
from .tmi_notes import parse_notes

logger = logging.getLogger(__name__)

# TMI ``notes`` cells (long bibliographies) blow past the default 128 KB cell cap.
csv.field_size_limit(16 * 1024 * 1024)

_NA = {"", "NA", "N/A", "na"}

# An unclosed `notes` cell in the source CSV (motif A736.1.1) runs on and swallows
# the serialized text of ~4,200 later rows, each starting with `<code>. †<code>.`.
# That dagger form never occurs in a genuine note, so we cut at the first one.
_NOTES_BLEED_RE = re.compile(r"([A-Z]\d[\dA-Za-z.]*)\.\s*†\1\.")


# The Trilogy ATU cells carry a baked-in mojibake: a lost character shows up as
# the 3-char sequence "ï¿½" (an upstream U+FFFD that was latin1-decoded then
# re-UTF-8-encoded). We heal it in three passes: (1) a curated dictionary of the
# recurring folklore-scholar names / journals it corrupts, (2) digit–digit → a
# page-range en-dash, (3) anything left → a single replacement char (a genuinely
# lost diacritic we won't guess).
_MOJIBAKE = "ï¿½"  # ï¿½
# Range en-dashes the mojibake swallowed: between numbers/type-ids (998ï¿½1005,
# 400Aï¿½C, 400Aï¿½400D, 851A*ï¿½C*) or between roman numerals (XIï¿½XXVIII). Both
# sides must be a proper range endpoint, so a lost diacritic inside a name
# (Rï¿½hle) is never mistaken for a dash.
_MOJIBAKE_TYPE_RANGE = re.compile(
    rf"(\*?\d+[A-Za-z]*\*?){re.escape(_MOJIBAKE)}(\*?\d+[A-Za-z]*\*?|\*?[A-Za-z]{{1,3}}\*?)")
_MOJIBAKE_ROMAN_RANGE = re.compile(rf"\b([IVXLCDM]+){re.escape(_MOJIBAKE)}([IVXLCDM]+)\b")

# Keys use "#" for the lost character so the exact mojibake code points are
# substituted in (never mistyped); each key always contains the mojibake, so as a
# plain substring it only ever matches damaged text. Applied longest-key-first.
_MOJIBAKE_REPAIRS_TEMPLATE = {
    # German (ä/ö/ü/ß)
    "K#hler-Z#lch": "Köhler-Zölch", "K#hler": "Köhler", "R#hrich": "Röhrich",
    "R#th": "Röth", "R#lleke": "Rölleke", "D#hnhardt": "Dähnhardt",
    "Grubm#ller": "Grubmüller", "M#ller": "Müller", "M#nchhausen": "Münchhausen",
    "B#rger": "Bürger", "Hen#en": "Henßen", "Lang-Reitst#tter": "Lang-Reitstätter",
    "B#chli": "Büchli", "L#thi": "Lüthi", "Bl#mml": "Blümml", "B#hme": "Böhme",
    "Bergstr#sser": "Bergsträsser", "L#wis": "Löwis", "H#ger": "Höger",
    "Pr#hle": "Pröhle", "P#gl": "Pögl", "M#derndorfer": "Möderndorfer",
    "L#ders": "Lüders", "Gr#ner": "Grüner", "Sch#tz": "Schütz",
    "Br#ckner": "Brückner", "W#nsche": "Wünsche", "J#lg": "Jülg",
    "Str#hl": "Strähl", "Schwerh#riger": "Schwerhöriger",
    "Schwerh#rigkeit": "Schwerhörigkeit", "Preu#": "Preuß", "f#r": "für",
    # Hungarian
    "Kecskem#ti": "Kecskeméti", "D#m#t#r": "Dömötör", "Gy#rgy": "György",
    "Kov#cs": "Kovács", "R#dei": "Rédei", "M#sz#ros": "Mészáros",
    "D#gh": "Dégh", "Ban#": "Banó", "Ga#l": "Gaál",
    "Munk#csi": "Munkácsi", "Erd#sz": "Erdész",
    # Czech/Slovak
    "Pol#vka": "Polívka", "Dvo#k": "Dvořák", "Kl#mov#": "Klímová",
    "Ga#par#kov#": "Gašparíková", "Filov#": "Filová", "Sirov#tka": "Sirovátka",
    "Jarn#k": "Jarník", "Hor#lek": "Horálek", "Hor#k": "Horák",
    # French
    "Ten#ze": "Ténèze", "S#billot": "Sébillot", "Blad#": "Bladé",
    "B#dier": "Bédier", "Carri#re": "Carrière", "Lacourci#re": "Lacourcière",
    "P#riers": "Périers", "R#cr#ations": "Récréations", "Mouli#ras": "Mouliéras",
    # Spanish/Portuguese
    "Gonz#lez": "González", "Pe#alosa": "Peñalosa", "Alb#n": "Albán",
    "V#lez": "Vélez", "Palac#n": "Palacín", "Jim#nez": "Jiménez", "P#rez": "Pérez",
    # Italian / Romanian
    "Pitr#": "Pitrè", "B#rlea": "Bârlea", "Rivi#re": "Rivière",
    "To#ev": "Tošev", "M#llenhoff": "Müllenhoff",
    # Irish / English apostrophe — the standalone leading Ó is lost too; the longer
    # key wins over "S#illeabh#in" via longest-first, healing both mojibakes at once.
    "# S#illeabh#in": "Ó Súilleabháin",
    "S#illeabh#in": "Súilleabháin", "O#Sullivan": "O'Sullivan",
    "O#Connor": "O'Connor",
    # Nordic
    "B#dker": "Bødker", "S#ve": "Säve", "Eir#ksson": "Eiríksson",
    # East-Slavic soft sign / apostrophe
    "Afanas#ev": "Afanas'ev", "Sidel#nikov": "Sidel'nikov",
    "Dobrovol#skij": "Dobrovol'skij", "Rozenfel#d": "Rozenfel'd",
    "Pu#kareva": "Puškareva",
    # South-Slavic / Baltic (š/ć/đ)
    "Bo#kovi-Stulli": "Bošković-Stulli", "Milo#evi": "Milošević",
    "jorjevi/Milo#evi-jorjevi": "Đorđević/Milošević-Đorđević",
    "Gabr#ek": "Gabršček", "#a#elj": "Šašelj", "#mits": "Šmits",
    "#akryl": "Šakryl", "epenkov/Penu#liski": "Cepenkov/Penušliski",
    "Penu#liski": "Penušliski",
    # German (extended tail)
    "Koch-Gr#nberg": "Koch-Grünberg", "Bar#ske": "Barüske", "Tr#mpy": "Trümpy",
    "B#nker": "Bünker", "Wigstr#m": "Wigström", "F#hnrich": "Fähnrich",
    "P#ge-Alder": "Pöge-Alder", "Sz#v#rffy": "Szövérffy", "W#rtlich": "Wörtlich",
    "Sch#ne": "Schöne", "G#nter": "Günter", "gef#hrliche": "gefährliche",
    # Hungarian (extended tail)
    "K#nos": "Kúnos", "G#czi": "Géczi", "G#r#g-Karady": "Görög-Karady",
    "Kosov#-Kole#nyi": "Kosová-Kolečányi",
    # French (extended tail)
    "Bl#court": "Blécourt", "Tch#raz": "Tchéraz", "Courri#re": "Courrière",
    "D#jeux": "Déjeux", "Dum#zil": "Dumézil", "J#sus": "Jésus", "#sope": "Ésope",
    "S#urs": "Sœurs",
    # Spanish/Portuguese/Basque (extended tail)
    "R#o": "Río", "An#barro": "Añibarro", "Cust#dio": "Custódio",
    # Slavic/Baltic (extended tail)
    "K#har": "Kühar", "Kaba#nikau": "Kabašnikau", "#r#mkov#": "Šrámková",
    "#lekonyt": "Šlekonyt",
    # Nordic (extended tail)
    "Asbj#rnsen": "Asbjørnsen", "Gr#nborg": "Grønborg",
    "Set#l#/Kyr#l#": "Setälä/Kyrölä",
    # Irish / Italian apostrophe (extended tail)
    "O#Faolain": "O'Faolain", "D#Aronco": "D'Aronco",
    # German / Nordic / Baltic / French (residual tail)
    "Scheinbu#e": "Scheinbuße", "Taufschw#nke": "Taufschwänke",
    "B#ckstr#m": "Bäckström", "H#rodote": "Hérodote", "K#stlin": "Köstlin",
    "J#rv": "Järv", "M#giste": "Mägiste",
    # Journals
    "Laogr#phia": "Laographia", "B#aloideas": "Béaloideas",
    "Pa#catantra": "Pañcatantra", "Krypt#dia": "Kryptádia", "M#lusine": "Mélusine",
}
_MOJIBAKE_REPAIRS = sorted(
    ((k.replace("#", _MOJIBAKE), v) for k, v in _MOJIBAKE_REPAIRS_TEMPLATE.items()),
    key=lambda kv: len(kv[0]), reverse=True,  # longest key first
)

# A related corruption drops a name's leading diacritic capital outright (no
# marker): "Ėrgis" -> "rgis", "Čajkanović" -> "ajkanovi". These surface as a
# lowercase-initial surname in citation position. Repaired as whole words only
# (\b…\b), so a fragment inside a real word is never touched.
_BARE_NAME_REPAIRS = {
    "rgis": "Ėrgis",           # Ėrgis (Yakut)
    "ajkanovi": "Čajkanović",  # Čajkanović (Serbian)
    "liasov": "Ėliasov",       # Ėliasov (Buryat)
    "epenkov": "Cepenkov",     # Cepenkov (Macedonian)
    "istov": "Čistov",         # Čistov (Karelian/Russian)
    "etkarev": "Četkarev",     # Četkarev (Mari)
}
_BARE_NAME_RE = re.compile(r"\b(" + "|".join(map(re.escape, _BARE_NAME_REPAIRS)) + r")\b")


def _fix_mojibake(value: str) -> str:
    if _BARE_NAME_RE.search(value):  # dropped-leading-capital names (no mojibake marker)
        value = _BARE_NAME_RE.sub(lambda m: _BARE_NAME_REPAIRS[m.group(0)], value)
    if _MOJIBAKE not in value:
        return value
    for mangled, fixed in _MOJIBAKE_REPAIRS:
        if mangled in value:
            value = value.replace(mangled, fixed)
    value = _MOJIBAKE_TYPE_RANGE.sub(r"\1–\2", value)   # number/type-id range → en-dash
    value = _MOJIBAKE_ROMAN_RANGE.sub(r"\1–\2", value)  # roman-numeral range → en-dash
    return value.replace(_MOJIBAKE, "�")                # residual: a genuinely lost char


def _clean(value: str | None) -> str:
    value = (value or "").strip()
    return "" if value in _NA else value


def _strip_notes_bleed(notes: str) -> str:
    m = _NOTES_BLEED_RE.search(notes)
    return notes[: m.start()].strip() if m else notes


def _read_csv(config: dict, key: str, *, force: bool) -> list[dict]:
    base = config["base_url"].rstrip("/")
    filename = config["files"][key]
    cache = Path(settings.motifs_dir) / "raw" / "trilogy" / filename
    raw = fetch_to_cache(f"{base}/{filename}", cache, force=force)
    text = raw.decode("utf-8", errors="replace")
    return list(csv.DictReader(io.StringIO(text)))


_NAT_RE = re.compile(r"\d+|\D+")


def tmi_sort_key(motif_id: str) -> list:
    """Hierarchical key so a parent precedes its descendants and numbers sort
    numerically: A1 < A1.4 < A10 < A100, C12.5 < C12.5.8."""
    return [(1, int(t)) if t.isdigit() else (0, t) for t in _NAT_RE.findall(motif_id)]


def _is_zero_family(motif_id: str) -> bool:
    """True if the id has a ``.0`` grouping segment (e.g. A52.0, A52.0.1)."""
    return "0" in motif_id.split(".")[1:]


def _id_trim_parent(code: str, idset: set[str]) -> str:
    """Recover an ancestor by trimming dotted segments (A52.0.1 -> A52.0 -> A52)."""
    trimmed = code
    while "." in trimmed:
        trimmed = trimmed.rsplit(".", 1)[0]
        if trimmed in idset:
            return trimmed
    return ""


def _finalize_tmi(motifs: list[dict]) -> list[dict]:
    """Repair the known Trilogy TMI defects, annotate, and hierarchically sort.

    - Duplicate codes (one code reused for distinct motifs): the first keeps the
      bare code, the rest get a lowercase letter sub-index (Z64 -> Z64, Z64b) so
      they are distinguishable; all are flagged ``duplicate``. ``code`` keeps the
      original. Cross-walk/parent references to the bare code resolve to the first.
    - ``parent`` is corrected to the effective parent (stored, else id-trimmed).
    - ``level`` keeps the dataset's place-value value for ordinary motifs; only
      the broken '.0' interpolations get a depth computed from corrected parents.
    All defects are logged.
    """
    counts = collections.Counter(m["id"] for m in motifs)
    used = set(counts)
    dup_codes = {code for code, n in counts.items() if n > 1}

    occ: dict[str, int] = {}
    for m in motifs:
        m["code"] = m["id"]
        if m["id"] in dup_codes:
            m["duplicate"] = True
            occ[m["id"]] = occ.get(m["id"], 0) + 1
            if occ[m["id"]] > 1:  # first keeps the bare code
                letter = occ[m["id"]] - 1
                while True:
                    cand = f"{m['code']}{chr(ord('a') + letter)}"
                    if cand not in used:
                        break
                    letter += 1
                used.add(cand)
                m["id"] = cand

    idset = {m["id"] for m in motifs}

    # Correct parents. The most specific existing dotted ancestor wins (so
    # A52.0.1 -> A52); dot-less codes (A111, whose place-value parent A110
    # isn't an id-prefix) fall back to the stored source parent. A dotted id with
    # no source parent is a real defect (the dataset dropped its level path);
    # a dot-less one with no parent is just a root (A0, A100, …) — not a defect.
    recovered = unresolved = 0
    for m in motifs:
        stored = m.get("parent", "")
        eff = _id_trim_parent(m["code"], idset) or (stored if stored in idset else "")
        if not stored and "." in m["code"]:
            recovered += eff != ""
            unresolved += eff == ""
        m["parent"] = eff

    # Level: keep the source value for ordinary motifs (the dataset's place-value
    # level is authoritative). Only the broken '.0' interpolations get a depth
    # computed from the corrected parents.
    by_id = {m["id"]: m for m in motifs}
    src_level = {m["id"]: m.get("level", 0) for m in motifs}
    memo: dict[str, int] = {}

    def resolve_level(mid: str, stack: frozenset) -> int:
        if mid in memo:
            return memo[mid]
        m = by_id[mid]
        if not _is_zero_family(m["id"]):
            memo[mid] = src_level.get(mid, 0)
        else:
            parent = m["parent"]
            memo[mid] = resolve_level(parent, stack | {mid}) + 1 \
                if (parent and parent in by_id and parent not in stack) else 0
        return memo[mid]

    for m in motifs:
        m["level"] = resolve_level(m["id"], frozenset())
        m.pop("source_level", None)

    if dup_codes:
        logger.warning("TMI defect: %d duplicate codes given letter sub-indices: %s",
                       len(dup_codes), ", ".join(sorted(dup_codes)))
    if recovered or unresolved:
        logger.warning("TMI defect: %d dotted ids had no source parent — reattached %d via id-trim, %d unresolved",
                       recovered + unresolved, recovered, unresolved)

    motifs.sort(key=lambda m: tmi_sort_key(m["id"]))
    return motifs


def _tmi_chapters(motifs: list[dict]) -> dict[str, str]:
    """Letter chapter -> name (e.g. ``A`` -> ``Myths``), in first-seen order."""
    chapters: dict[str, str] = {}
    for m in motifs:
        chapter = m["chapter"]
        if chapter and chapter not in chapters and m["chapter_name"]:
            chapters[chapter] = m["chapter_name"]
    return chapters


def _parse_tmi(rows: list[dict]) -> list[dict]:
    motifs = []
    for row in rows:
        code = _clean(row.get("id"))
        if not code:
            continue
        try:
            level = int(_clean(row.get("level")) or 0)
        except ValueError:
            level = 0
        parent = _clean(row.get(f"level_{level - 1}")) if level > 0 else ""
        notes = _strip_notes_bleed(_clean(row.get("notes")))
        motifs.append({
            "id": code,
            "chapter": _clean(row.get("chapter_id")) or code[:1],
            "chapter_name": _clean(row.get("chapter_name")),
            "name": _clean(row.get("motif_name")),
            "notes": notes,
            **parse_notes(notes, code),  # definition, cultures, references, see_also, atu_inline
            "level": level,
            "parent": parent if parent and parent != code else "",
        })
    return motifs


def _parse_atu_seq(rows: list[dict]) -> dict[str, list[str]]:
    """Group ``atu_seq`` rows into ``{atu_id: [ordered unique TMI motif codes]}``.

    (``atu_seq`` also carries a ``tale_variant`` column, but it is not a clean set
    of documented variants — a couple of catch-all types expand into tens of
    thousands of synthetic sequences — so we collapse across variants and keep only
    the ordered unique motif set per type.)"""
    ordered: dict[str, list[tuple[float, str]]] = {}
    for row in rows:
        atu_id = _clean(row.get("atu_id"))
        motif = _clean(row.get("motif"))
        if not atu_id or not motif:
            continue
        try:
            order = float(_clean(row.get("motif_order")) or 0)
        except ValueError:
            order = 0.0
        ordered.setdefault(atu_id, []).append((order, motif))

    result: dict[str, list[str]] = {}
    for atu_id, pairs in ordered.items():
        pairs.sort(key=lambda p: p[0])
        seen: set[str] = set()
        motifs: list[str] = []
        for _, motif in pairs:
            if motif not in seen:
                seen.add(motif)
                motifs.append(motif)
        result[atu_id] = motifs
    return result


def _parse_atu_combos(rows: list[dict]) -> dict[str, list[str]]:
    combos: dict[str, set[str]] = {}
    for row in rows:
        atu_id = _clean(row.get("atu_id"))
        combo = _clean(row.get("combos") or row.get("combo"))
        # a stray space inside a type id ("130 B" -> "130B") leaves it un-linkable
        combo = re.sub(r"(?<=\d) +(?=[A-Za-z]\b)", "", combo)
        if atu_id and combo:
            combos.setdefault(atu_id, set()).add(combo)
    return {k: sorted(v) for k, v in combos.items()}


# An ATU id is a number, optional letter suffix(es), optional "*" (313, 313A, 1861*).
_ATU_NUM = re.compile(r"^(\d+)")
# A division label carries its number range: "Supernatural Adversaries 300-399".
_ATU_RANGE = re.compile(r"^(.*?)\s*(\d+)\s*-\s*(\d+)\s*$")


def _atu_num(atu_id: str) -> int | None:
    m = _ATU_NUM.match(atu_id)
    return int(m.group(1)) if m else None


def _atu_sort_key(atu_id: str) -> tuple:
    """(number, suffix) so 313 < 313A < 313A* < 1861."""
    m = _ATU_NUM.match(atu_id)
    return (int(m.group(1)) if m else 1 << 30, atu_id[m.end():] if m else atu_id)


# Abbreviations that carry a period mid-title but do NOT end the title sentence,
# so Trilogy's naive "cut at first period" wrongly split on them (``St. Peter``).
# ``etc`` is deliberately absent: at bracket-depth 0 ``…, etc.`` closes a list and
# its period IS a real boundary; the only place ``etc.`` should be skipped is
# inside a bracketed aside (``[Cat, Frog, etc.]``), which the depth check already
# handles — keeping ``etc`` here instead over-absorbed the summary (type 572*).
_TITLE_ABBREV = frozenset({"st", "mt", "dr", "mrs", "mr", "ms", "vs", "cf",
                           "no", "nos", "ca", "fig", "sr", "jr", "op", "al", "ff", "viz"})
# A closing quote (vs. an apostrophe in ``'s``/``'t``): followed by space/end/punct.
_CLOSE_QUOTE = re.compile(r"'(?=\s|$|[.!?,;:])")
_TRAIL_WORD = re.compile(r"([A-Za-z]+)$")
# Apparatus blocks that always FOLLOW the complete label, so the label ends where
# they begin. ``(previously …)`` (either case) is the former name or number.
# ``(Including … Type N)`` is a merge-note — keyed on a capital ``I`` *and* a type
# id, which distinguishes it from lowercase prose ``(including honey)``.
_APP_PREV = re.compile(r"\(previously\b", re.I)
_APP_INCL = re.compile(r"\(Including\b[^)]*\bTypes?\s+\d")


def _split_title(text: str) -> tuple[str, str | None]:
    """Split Uther's run-on ``<title>. <description>`` into ``(title, description)``.

    The label ends at the EARLIEST of:

      * a **quoted catch-phrase** — if the text opens with ``'…'`` (jokes, anecdotes,
        formula tales); the closing quote is a ``'`` before whitespace/end/punctuation
        (apostrophes in ``'s``/``'t`` are skipped);
      * an **apparatus block** at bracket-depth 0 — ``(previously …)`` or
        ``(Including … Type N)``. These always trail the complete label, so cutting
        before them drops the whole apparatus into the summary. A word-variant
        ``(Jackal)`` and lowercase prose ``(including honey)`` are not apparatus and
        do not cut;
      * the first **sentence period** at bracket-depth 0 (over ``()`` and ``[]``)
        that is neither an abbreviation (``St.``, ``Cf.``…) nor a decimal in a code.

    ``description`` is ``None`` when none is found — an opening quote that never
    closes, or a scan that never reaches depth 0 (an unclosed bracket in the source);
    the caller decides. A heading motif code ``[K123]`` is left on whichever side the
    boundary falls — it is not apparatus and is never moved."""
    text = text.strip()
    if not text:
        return "", ""
    if text.startswith("'"):
        body = text[1:]
        m = _CLOSE_QUOTE.search(body)
        if m:
            return f"'{body[:m.start()].strip()}'", body[m.end():].strip()
        return text, None            # unterminated opening quote: no boundary
    depth = 0
    for i, ch in enumerate(text):
        if ch == "(" and depth == 0 and (_APP_PREV.match(text, i) or _APP_INCL.match(text, i)):
            return text[:i].strip(), text[i:].strip()
        if ch in "[(":
            depth += 1
        elif ch in "])":
            depth = max(0, depth - 1)
        elif ch == "." and depth == 0:
            prev = text[i - 1] if i else ""
            nxt = text[i + 1] if i + 1 < len(text) else ""
            if prev.isdigit() and nxt.isdigit():     # decimal in a motif/type code
                continue
            word = _TRAIL_WORD.search(text[:i])
            if word and word.group(1).lower() in _TITLE_ABBREV:
                continue
            return text[:i].strip(), text[i + 1:].strip()
    return text, None                # no sentence boundary found


def _repair_atu_name(name: str, summary: str) -> tuple[str, str]:
    """Recover the title/description boundary from Trilogy's two ATU columns.

    Trilogy cut Uther's single ``<title>. <description>`` run-on at the first period
    (consuming exactly ``". "``), which frequently lands *inside* the title — an
    abbreviation (``St.``), a bracketed aside (``[Cat, etc.]``), or, for quoted
    catch-phrase titles, deep in the prose — leaking one side into the other. We
    rejoin the two columns and re-split with a boundary rule (``_split_title``) that
    understands quotes, apparatus blocks, abbreviations, decimals and bracket depth,
    which subsumes the old unbalanced-bracket patch. Because the label ends at the
    first ``(previously …)`` / ``(Including … Type N)`` apparatus block, that
    apparatus lands uniformly in the summary (not stranded in the title). A doubled
    apostrophe is always a source artifact (a doubled quote mark, or a lost accented
    letter) — collapsed first so the quote detection is reliable.

    The seam re-inserts the consumed period plus a space, EXCEPT where the cut fell
    inside a token — the summary then resumes on a digit / ``)`` / ``]`` / closing
    quote (``[J2066`` + ``1]``, ``…1810A*`` + ``)``, ``'No`` + ``' A king``) and a
    space would be spurious. A real word/clause boundary (``St`` + ``Peter``) keeps
    its space.

    When ``_split_title`` finds no boundary we keep the reunited one-line title only
    if the brackets balance (a genuine title with no plot, ``St. Peter…``); when they
    don't, the depth scan was defeated by an unclosed bracket in the source (``425D``
    is missing a ``)``), so we fall back to Trilogy's raw column split untouched."""
    name, summary = name.replace("''", "'"), summary.replace("''", "'")
    if not summary:
        full = name
    else:
        gap = "" if summary[0] in "0123456789)]'" else " "
        full = f"{name}.{gap}{summary}"
    title, description = _split_title(full)
    if description is None:
        if full.count("(") != full.count(")") or full.count("[") != full.count("]"):
            return name, summary          # unclosed bracket — keep the raw split
        return title, ""                  # balanced one-line title, no plot text
    return title, description


# A curated label for the handful of types whose real title runs, in the source,
# straight into the plot with no separating period, apparatus or quote — so no
# boundary rule can find where the label ends ("The Fox Buys himself a Pipe" |
# "and goes into the barn to smoke. The hay begins to burn…"). Cut points verified
# against the run-on text; the leaked tail folds back to the front of the summary.
_TITLE_OVERRIDES = {
    "66A*": "The Fox Buys himself a Pipe",
    "132": "The Goat Admires his Horns in the Water",
    "232C*": "Which Bird Is Father",
    "285A*": "The Adder Poisons the Children's Food",
    "410": "Sleeping Beauty",           # alt-names + "…a daughter is born…" prose → summary
    "860": "Nuts of 'Ay ay ay!'",
    "1832B*": "What Kind of Dung",
    "1641B*": "Who Stole from the Church",
}


def _apply_title_override(atu_id: str, name: str, summary: str) -> tuple[str, str]:
    """Replace a run-on ``name`` with its curated label, folding the leaked tail
    (the plot that had merged into the title) back to the front of the summary."""
    title = _TITLE_OVERRIDES.get(atu_id)
    if not title or not name.startswith(title):
        return name, summary
    tail = name[len(title):].lstrip(" ,.")     # drop only the leading separator
    return title, ". ".join(p for p in (tail, summary) if p)


# Accented letters the extraction flattened to a bare apostrophe — a variant of the
# ``ï¿½`` mojibake where the diacritic collapsed to ``'`` (``Fianc'e`` → ``Fiancée``,
# ``Dornr'schen`` → ``Dornröschen``). ``_fix_mojibake`` keys on the ``ï¿½`` marker,
# which never appears in the tale name/summary; and a bare ``'`` is ambiguous with a
# contraction/possessive, so we heal a curated set of the specific damaged foreign
# words rather than touching ``'`` blindly. Substring replacement; entries are
# distinctive enough not to collide, and inflections fall out (``fianc'es`` →
# ``fiancées`` via the ``fianc'e`` rule).
_ACCENT_REPAIRS = {
    "Fianc'e": "Fiancée", "fianc'e": "fiancée",
    "M'nchhausen": "Münchhausen",
    "Dornr'schen": "Dornröschen",
    "Rotk'ppchen": "Rotkäppchen",
    "Sch'pfer": "Schöpfer",
    "Geschw'tzigkeit": "Geschwätzigkeit",
    "v'llig": "völlig",
    "auff'llig": "auffällig",
    "schlie'lich": "schließlich",
    "Kecskem'ti": "Kecskeméti",
    "K'mmernis": "Kümmernis",
    "Milo'evi": "Milošević",
    "Tepeg'z": "Tepegöz",
    "T'nd'r": "Tündér",
    "Anu'irwn": "Anushirwan",
    "Peau d'ne": "Peau d'âne",
}


def _heal_accents(text: str) -> str:
    """Repair accented letters the extraction flattened to a bare apostrophe, from
    the curated ``_ACCENT_REPAIRS`` word list. A no-op when ``text`` has no ``'``."""
    if "'" not in text:
        return text
    for bad, good in _ACCENT_REPAIRS.items():
        if bad in text:
            text = text.replace(bad, good)
    return text


# One or more comma-separated TMI motif codes (``J2066.1``, ``B296, F1025``). The
# leading ``[A-Z]\d`` distinguishes a code from a word-variant aside (``[Bear]``).
_DEF_CODE = r"[A-Z]\d[\dA-Z.]*(?:,\s*[A-Z]\d[\dA-Z.]*)*"
_TRAIL_CODE = re.compile(r"\s*\[(" + _DEF_CODE + r")\]\s*$")           # trailing the label
_LEAD_CODE = re.compile(r"^((?:\([^)]*\)\s*)*)\[(" + _DEF_CODE + r")\]")  # after apparatus, in summary
# Types whose defining code sits at the very end of the summary (quote-class jokes),
# positionally indistinguishable from an inline plot code — extracted by this explicit
# list rather than a heuristic, to keep auto-extraction free of false positives.
_DEFINING_OVERRIDES = {"1446", "860"}


def _clean_gap(text: str) -> str:
    """Tidy the seam left after removing a bracketed code / apparatus block: collapse
    spaces, drop a space before punctuation, and strip a separator orphaned at the
    front (the other caller starts with a paren or a word, so it is unaffected)."""
    text = re.sub(r"\s{2,}", " ", re.sub(r"\s+([.,;:])", r"\1", text)).strip()
    return text.lstrip(" .,;:")


def _extract_defining_motifs(atu_id: str, name: str, summary: str) -> tuple[str, str, list[str]]:
    """Pull the **defining** motif code(s) — the ``[code]`` group *adjacent to the
    label* (trailing the name, or leading the summary after any apparatus) — into a
    list, leaving inline plot codes untouched. A short curated set whose code trails
    a quote-class summary is handled explicitly (``_DEFINING_OVERRIDES``)."""
    if m := _TRAIL_CODE.search(name):                      # trailing the label
        return name[:m.start()].rstrip(), summary, _split_ids(m.group(1))
    if m := _LEAD_CODE.match(summary):                     # leading the summary
        rest = _clean_gap(summary[:m.end(1)] + summary[m.end():])
        return name, rest, _split_ids(m.group(2))
    if atu_id in _DEFINING_OVERRIDES and (m := _TRAIL_CODE.search(summary)):
        return name, summary[:m.start()].rstrip(), _split_ids(m.group(1))
    return name, summary, []


def _split_ids(group: str) -> list[str]:
    return [c.strip() for c in group.split(",") if c.strip()]


# Provenance apparatus in the summary: (previously <Name>) / (previously Type X) /
# (Including … Type X). The Including anchor needs a capital ``I`` *and* a type id,
# to skip lowercase prose ``(including honey)``.
_APP_START = re.compile(r"\((?:previously|Previously|Including)\b")
_PREV_CODE = re.compile(r"^(?:also\s+)?Types?\s+\d", re.I)   # a (previously) that names a number
_ATU_ID_TOKEN = re.compile(r"\d[\dA-Z*]*")                   # 64, 1810A*, 1525H2, 1316***


def _balanced_end(text: str, start: int) -> int | None:
    """Index just past the ``)`` closing the ``(`` at ``start`` (handles nesting),
    or ``None`` if it never closes."""
    depth = 0
    for j in range(start, len(text)):
        if text[j] == "(":
            depth += 1
        elif text[j] == ")":
            depth -= 1
            if depth == 0:
                return j + 1
    return None


def _apparatus_spans(text: str) -> list[tuple[int, int, str]]:
    """``(start, end, content)`` for each balanced ``(previously …)`` / ``(Including
    … Type N)`` block; unbalanced blocks (a source defect) are skipped."""
    spans, pos = [], 0
    for m in _APP_START.finditer(text):
        if m.start() < pos:                      # inside a block already taken
            continue
        end = _balanced_end(text, m.start())
        if end is None:                          # unclosed — leave it in place
            continue
        content = text[m.start() + 1:end - 1]
        if content.startswith("Including") and not re.search(r"\bTypes?\s+\d", content):
            continue                             # prose "(including honey)"
        spans.append((m.start(), end, content))
        pos = end
    return spans


def _parse_type_ids(content: str) -> list[str]:
    """Old type ids named after ``Type``/``Types`` — dropping a ``cf. Type …``
    cross-reference and any bracketed motif code."""
    content = re.split(r"\bcf\.", content, flags=re.I)[0]
    content = re.sub(r"\[[^\]]*\]", "", content)
    return _ATU_ID_TOKEN.findall(content)


def _extract_apparatus(summary: str) -> tuple[str, str, list[str]]:
    """Pull provenance apparatus out of the summary into ``(summary, former_name,
    former_ids)``. Old numbers (from ``previously Type X`` and ``Including Type X``)
    are collected wherever they sit; the single former **name** comes from the first
    ``(previously <Name>)``. Only apparatus at the **edges** (a leading run or a pure
    trailing note) is stripped from the summary — a block embedded mid-sentence is
    part-level context (and often wraps an inline code), so it stays in place."""
    spans = _apparatus_spans(summary)
    if not spans:
        return summary.lstrip(" .,;:"), "", []      # tidy a rare orphaned leading separator
    former_name, former_ids = "", []
    for _start, _end, content in spans:
        if content.startswith("Including"):
            former_ids += _parse_type_ids(content)
        else:                                                # previously
            body = content[len("previously"):].strip()
            if _PREV_CODE.match(body):
                former_ids += _parse_type_ids(body)
            elif not former_name:
                former_name = body.rstrip(".").strip()
    # Strip a leading run of apparatus, and a pure trailing note; keep mid blocks.
    # Consecutive blocks are separated by ". ", so the gap may carry punctuation.
    _GAP = r"[\s.,;:]*"
    lead_end = 0
    for start, end, _ in spans:
        if re.fullmatch(_GAP, summary[lead_end:start]):
            lead_end = end
        else:
            break
    trail_start = len(summary)
    for start, end, _ in reversed(spans):
        if re.fullmatch(_GAP, summary[end:trail_start]):
            trail_start = start
        else:
            break
    summary = _clean_gap(summary[lead_end:max(lead_end, trail_start)])
    seen, ids = set(), []
    for x in former_ids:                                     # dedup, keep order
        if x not in seen:
            seen.add(x); ids.append(x)
    return summary, former_name, ids


def _split_division(s: str) -> tuple[str, int | None, int | None]:
    """'Supernatural Adversaries 300-399' -> ('Supernatural Adversaries', 300, 399)."""
    m = _ATU_RANGE.match(s or "")
    return (m.group(1).strip(), int(m.group(2)), int(m.group(3))) if m else ((s or "").strip(), None, None)


# Canonical ATU top-level chapters (Uther 2004), keyed by number range. The CSV's
# own `chapter` column is unreliable — it promotes sub-groups ("Other Animals And
# Objects", "Other Tales Of The Supernatural") to chapters and lumps Religious +
# Realistic + Stupid-Ogre into one — so we derive the chapter from the type number.
_ATU_CHAPTERS = [
    (1, 299, "Animal Tales"),
    (300, 749, "Tales Of Magic"),
    (750, 849, "Religious Tales"),
    (850, 999, "Realistic Tales"),
    (1000, 1199, "Tales Of The Stupid Ogre"),
    (1200, 1999, "Anecdotes And Jokes"),
    (2000, 2399, "Formula Tales"),
    (2400, 2499, "Unclassified"),
]


def _atu_chapter(num: int | None) -> str:
    for lo, hi, name in _ATU_CHAPTERS:
        if num is not None and lo <= num <= hi:
            return name
    return ""


# Canonical ATU sub-divisions the CSV omits entirely, so their types would carry
# no division. These fill the gaps: 700-749 (Tales Of Magic) and 750-779
# (Religious Tales) — standard Uther (2004) range labels — used only as a last
# resort after the CSV's own labelled ranges.
_ATU_CANON_DIVISIONS = [
    (700, 749, "Other Tales Of The Supernatural"),
    (750, 779, "God Rewards And Punishes"),
]


# A degenerate "See/Cf Type X" pointer entry — no real name or plot, just a redirect
# to X. Folded into the alias map and dropped as a page.
_STUB = re.compile(r"^(?:See|Cf\.?)\s+Type\s+(\d[\dA-Z*]*)", re.I)


def _atu_aliases(types: list[dict], stub_targets: dict[str, str]) -> dict[str, str]:
    """``{old_id: current_id}`` from ``former_ids`` (+ See/Cf stub redirects). Only ids
    that are NOT a live type map; an old id claimed by two types is dropped (ambiguous)."""
    live = {t["id"] for t in types}
    claims: dict[str, set[str]] = {}
    for t in types:
        for old in t.get("former_ids", []):
            if old not in live:
                claims.setdefault(old, set()).add(t["id"])
    for stub, target in stub_targets.items():
        claims.setdefault(stub, set()).add(target)
    return {old: next(iter(tg)) for old, tg in claims.items() if len(tg) == 1}


def _parse_atu(df_rows: list[dict], seq: dict[str, list[str]],
               combos: dict[str, list[str]]) -> tuple[list[dict], dict[str, str]]:
    types = []
    for row in df_rows:
        atu_id = _clean(row.get("atu_id"))
        if not atu_id:
            continue
        num = _atu_num(atu_id)
        div_name, start, end = _split_division(_clean(row.get("division")))
        sub_name, sub_start, sub_end = _split_division(_clean(row.get("sub_division")))
        tale_name, tale_summary = _repair_atu_name(
            _clean(row.get("tale_name")), _clean(row.get("tale_type")))
        tale_name, tale_summary = _apply_title_override(atu_id, tale_name, tale_summary)
        tale_name, tale_summary = _heal_accents(tale_name), _heal_accents(tale_summary)
        tale_name, tale_summary, defining = _extract_defining_motifs(atu_id, tale_name, tale_summary)
        tale_summary, former_name, former_ids = _extract_apparatus(tale_summary)
        types.append({
            "id": atu_id,
            "num": num,
            "chapter": _atu_chapter(num),   # derived from the number, not the CSV column
            "division": div_name,
            "division_range": [start, end] if start is not None else None,
            "sub_division": sub_name,       # optional finer level below division
            "sub_division_range": [sub_start, sub_end] if sub_start is not None else None,
            "name": tale_name,
            "summary": tale_summary,
            # The defining TMI motif(s) Uther names right after the label (distinct
            # from the constituent `motifs` from atu_seq; see atu_regions/docs).
            "defining_motifs": defining,
            # Provenance apparatus pulled from the summary: the pre-2004 name and the
            # old ATU numbers this type was renumbered from / absorbed (Uther).
            "former_name": former_name,
            "former_ids": former_ids,
            # Uther's per-type apparatus (mojibake-cleaned): key scholarly
            # references (litvar), attestations by tradition (provenance) and
            # historical/textual notes (remarks).
            "references": _fix_mojibake(_clean(row.get("litvar"))),
            "attestations": (attestations := _fix_mojibake(_clean(row.get("provenance")))),
            # Peoples parsed out of the attestation prose, grouped by macro-region
            # (see atu_regions) — powers the per-type region breakdown and the
            # overview's people/region distributions.
            "attestations_grouped": atu_regions.group_by_region(atu_regions.parse(attestations)),
            "remarks": _fix_mojibake(_clean(row.get("remarks"))),
            "motifs": seq.get(atu_id, []),
            "combos": combos.get(atu_id, []),
            # Example folktales are sourced later, straight from Ashliman's site
            # (ashliman.refresh), not from a dataset.
        })

    # Drop See/Cf pointer stubs, recording their redirect. Done *before* the subtype
    # pass so its `base in by_id` guard naturally leaves no link dangling to a removed
    # stub (e.g. the live 1876* whose base 1876 is a stub).
    stub_targets = {t["id"]: m.group(1) for t in types if (m := _STUB.match(t["name"]))}
    types = [t for t in types if t["id"] not in stub_targets]

    # Fill an unlabelled division from the number range that contains the type —
    # first from the CSV's own labelled ranges, then from the canonical fallback
    # table for the sub-divisions the CSV omits (700-749, 750-779).
    ranges = {(t["division"], *t["division_range"]) for t in types if t["division_range"]}
    ranges |= {(nm, s, e) for s, e, nm in _ATU_CANON_DIVISIONS}
    for t in types:
        if t["division"] or t["num"] is None:
            continue
        for nm, s, e in ranges:
            if s <= t["num"] <= e:
                t["division"], t["division_range"] = nm, [s, e]
                break

    # Subtype families: a subtype (313A) hangs off its base number type (313), when
    # that base type exists; the base lists its subtypes (natural-sorted).
    by_id = {t["id"]: t for t in types}
    for t in types:
        base = str(t["num"]) if t["num"] is not None else ""
        t["parent"] = base if base and base != t["id"] and base in by_id else None
        t["subtypes"] = []
    for t in types:
        if t["parent"]:
            by_id[t["parent"]]["subtypes"].append(t["id"])
    for t in types:
        t["subtypes"].sort(key=_atu_sort_key)
    # The atu_df rows aren't globally ordered by number; sort so the sidebar list
    # reads 1 → 2399 (and ascending within a division).
    types.sort(key=lambda t: _atu_sort_key(t["id"]))
    return types, _atu_aliases(types, stub_targets)


def _atu_divisions(types: list[dict]) -> list[dict]:
    """Division hierarchy, ascending by number range: [{chapter, name, start, end, count}]."""
    counts: collections.Counter = collections.Counter()
    for t in types:
        if t["division_range"]:
            counts[(t["chapter"], t["division"], *t["division_range"])] += 1
    rows = [{"chapter": ch, "name": nm, "start": s, "end": e, "count": c}
            for (ch, nm, s, e), c in counts.items()]
    rows.sort(key=lambda r: r["start"])  # ascending by number range (1 → 2399)
    return rows


def _atu_subdivisions(types: list[dict]) -> list[dict]:
    """Sub-division hierarchy (the optional level below division), ascending by
    range: [{chapter, division, name, start, end, count}]. Only ~37% of types
    carry one, so this is sparse."""
    counts: collections.Counter = collections.Counter()
    for t in types:
        if t["sub_division_range"]:
            counts[(t["chapter"], t["division"], t["sub_division"], *t["sub_division_range"])] += 1
    rows = [{"chapter": ch, "division": dv, "name": nm, "start": s, "end": e, "count": c}
            for (ch, dv, nm, s, e), c in counts.items()]
    rows.sort(key=lambda r: r["start"])
    return rows


def build_tmi(config: dict, *, force: bool = False) -> dict:
    """Download and parse only the Trilogy TMI CSV into the TMI store dict.

    Uses just ``tmi.csv`` — disjoint from the ATU files — so it can be a step of
    its own (the caller logs the step header before invoking it, keeping any TMI
    parse warnings under that header).
    """
    tmi = _finalize_tmi(_parse_tmi(_read_csv(config, "tmi", force=force)))
    return {
        "label": "Thompson",
        "long_label": "Thompson Motif-Index of Folk-Literature",
        "attribution": config.get("attribution", ""),
        "homepage": config.get("homepage", ""),
        "chapters": _tmi_chapters(tmi),
        "culture_legend": build_legend(tmi),
        "motifs": tmi,
    }


def build_atu(config: dict, *, force: bool = False) -> tuple[dict, dict]:
    """Download and parse the Trilogy ATU CSVs into ``(atu store dict, atu_seq)``.

    Uses ``atu_seq``/``atu_combos``/``atu_df`` — disjoint from the TMI file.
    ``atu_seq`` (tale type -> ordered TMI motif codes) feeds the ATU<->TMI walk.
    """
    seq = _parse_atu_seq(_read_csv(config, "atu_seq", force=force))
    combos = _parse_atu_combos(_read_csv(config, "atu_combos", force=force))
    atu, aliases = _parse_atu(_read_csv(config, "atu_df", force=force), seq, combos)
    return {
        "label": "ATU tale types",
        "long_label": "Aarne-Thompson-Uther tale-type index",
        "attribution": config.get("attribution", ""),
        "homepage": config.get("homepage", ""),
        "divisions": _atu_divisions(atu),
        "subdivisions": _atu_subdivisions(atu),
        "culture_legend": atu_regions.build_legend(atu),
        "aliases": aliases,          # {old ATU number: current type id} — redirects
        "types": atu,
    }, seq


def build(config: dict, *, force: bool = False) -> dict:
    """Download and parse the Trilogy CSVs into TMI + ATU store dicts and the seq map."""
    tmi = build_tmi(config, force=force)
    atu, seq = build_atu(config, force=force)
    return {"tmi": tmi, "atu": atu, "atu_seq": seq}
