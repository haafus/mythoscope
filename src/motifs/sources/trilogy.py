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
            **parse_notes(notes),  # definition, cultures, references, see_also, atu_inline
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
        if atu_id and combo:
            combos.setdefault(atu_id, set()).add(combo)
    return {k: sorted(v) for k, v in combos.items()}


def _parse_aft(rows: list[dict]) -> dict[str, list[dict]]:
    """Group ``aft.csv`` (Ashliman's Annotated Folk Tales) into example tales per
    type: ``{atu_id: [{title, provenance, source, notes}]}``. Metadata only — the
    full ``text`` is deliberately dropped (licensing; keeps the index lean).
    Ordered by provenance then title for a stable read."""
    tales: dict[str, list[dict]] = {}
    for row in rows:
        atu_id = _clean(row.get("atu_id"))
        title = _fix_mojibake(_clean(row.get("tale_title")))
        if not atu_id or not title:
            continue
        tales.setdefault(atu_id, []).append({
            "title": title,
            "provenance": _fix_mojibake(_clean(row.get("provenance"))),
            "source": _fix_mojibake(_clean(row.get("source"))),
            "notes": _fix_mojibake(_clean(row.get("notes"))),
        })
    for entries in tales.values():
        entries.sort(key=lambda t: (t["provenance"].lower(), t["title"].lower()))
    return tales


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


def _repair_atu_name(name: str, summary: str) -> tuple[str, str]:
    """Repair a tale name Trilogy truncated mid-bracket.

    Trilogy split ``tale_name`` at the first period, which sometimes lands inside a
    bracketed aside (``The Mouse [Cat, Frog, etc.] as Bride``): the name is cut at
    ``etc`` and the tail (``] as Bride).``) leaks into the summary. When the name has
    an unbalanced ``[`` or ``(``, rejoin name + summary and re-split at the first
    period that sits outside all brackets."""
    if name.count("[") == name.count("]") and name.count("(") == name.count(")"):
        return name, summary
    if not summary:
        return name, summary
    full = f"{name}.{summary}"
    depth = 0
    for i, ch in enumerate(full):
        if ch in "[(":
            depth += 1
        elif ch in "])":
            depth = max(0, depth - 1)
        elif ch == "." and depth == 0:
            return full[:i].strip(), full[i + 1:].strip()
    return name, summary


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


def _parse_atu(df_rows: list[dict], seq: dict[str, list[str]], combos: dict[str, list[str]],
               tales: dict[str, list[dict]] | None = None) -> list[dict]:
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
        # A doubled apostrophe is always a source artifact (a closing quote rendered
        # as '', or a lost accented letter): collapse it to a single apostrophe.
        tale_name, tale_summary = tale_name.replace("''", "'"), tale_summary.replace("''", "'")
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
            # Uther's per-type apparatus (mojibake-cleaned): key scholarly
            # references (litvar), attestations by tradition (provenance) and
            # historical/textual notes (remarks).
            "references": _fix_mojibake(_clean(row.get("litvar"))),
            "attestations": _fix_mojibake(_clean(row.get("provenance"))),
            "remarks": _fix_mojibake(_clean(row.get("remarks"))),
            "motifs": seq.get(atu_id, []),
            "combos": combos.get(atu_id, []),
            # Example folktales of this type (Ashliman AFT), metadata only.
            "tales": (tales or {}).get(atu_id, []),
        })

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
    return types


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
    tales = _parse_aft(_read_csv(config, "aft", force=force)) if "aft" in config.get("files", {}) else {}
    atu = _parse_atu(_read_csv(config, "atu_df", force=force), seq, combos, tales)
    return {
        "label": "ATU tale types",
        "long_label": "Aarne-Thompson-Uther tale-type index",
        "attribution": config.get("attribution", ""),
        "homepage": config.get("homepage", ""),
        "divisions": _atu_divisions(atu),
        "subdivisions": _atu_subdivisions(atu),
        "types": atu,
    }, seq


def build(config: dict, *, force: bool = False) -> dict:
    """Download and parse the Trilogy CSVs into TMI + ATU store dicts and the seq map."""
    tmi = build_tmi(config, force=force)
    atu, seq = build_atu(config, force=force)
    return {"tmi": tmi, "atu": atu, "atu_seq": seq}
