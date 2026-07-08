"""Chapter / section detector prototype — run over the whole corpus.

Fully isolated from the main project: it reads only the source list in
``config/corpus.json`` (the 28 Project Gutenberg URLs), downloads each raw
``.txt`` into a local, gitignored ``cache/`` folder, and runs a layered
heading detector on the *raw* text (blank-line structure intact — the main
pipeline's cleaner flattens those cues away, so we deliberately work upstream
of it here).

For every book it records which strategy fired and where each detected heading
sits, then emits a compact ``data.js`` (heading text + char offset + a short
context preview, not the full body) for the viewer to eyeball coverage.

Run from the repo root:

    python mockups/08-chapter-detector/build_data.py

Re-runs are fast: downloads are cached. Delete ``cache/`` to refetch.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CACHE = HERE / "cache"
OUT = HERE / "data.js"
CORPUS = ROOT / "config" / "corpus.json"


# --------------------------------------------------------------------------- #
# Fetch (curl through the environment proxy — works where python TLS is fiddly)
# --------------------------------------------------------------------------- #
def gutenberg_id(url: str) -> str:
    m = re.search(r"/(\d+)/pg\d+\.txt", url) or re.search(r"epub/(\d+)", url)
    return m.group(1) if m else re.sub(r"\W+", "", url)[-6:]


def fetch(url: str) -> str | None:
    CACHE.mkdir(exist_ok=True)
    dest = CACHE / f"pg{gutenberg_id(url)}.txt"
    if not dest.exists() or dest.stat().st_size < 1000:
        print(f"  download {url}")
        r = subprocess.run(
            ["curl", "-sS", "--fail", "--max-time", "90", "-o", str(dest), url],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            print(f"  ! failed ({r.returncode}): {r.stderr.strip()[:120]}")
            return None
    try:
        return dest.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


# --------------------------------------------------------------------------- #
# Strip Project Gutenberg header / footer so offsets are relative to the body
# --------------------------------------------------------------------------- #
START = re.compile(r"\*\*\*\s*START OF (?:THE|THIS) PROJECT GUTENBERG.*?\*\*\*", re.I)
END = re.compile(r"\*\*\*\s*END OF (?:THE|THIS) PROJECT GUTENBERG.*?\*\*\*", re.I)


def strip_boilerplate(text: str) -> str:
    s = START.search(text)
    body = text[s.end():] if s else text
    e = END.search(body)
    if e:
        body = body[: e.start()]
    return body.strip("\n")


# --------------------------------------------------------------------------- #
# Heading heuristics
# --------------------------------------------------------------------------- #
# Explicit structural keyword + a number/word ("Chapter IV", "BOOK 2", "Sura 5")
KEYWORD = re.compile(
    r"^\s*(CHAPTER|CHAP\.?|BOOK|PART|CANTO|SECTION|SECT\.?|PSALM|SURA[H]?|"
    r"HYMN|LECTURE|DISCOURSE|FYTTE|ACT|SCENE|LETTER|EPISTLE)\b"
    r"[\s.:]*([IVXLCDM]+|\d+|[A-Z][A-Za-z]+)?",
    re.I,
)
ROMAN = re.compile(r"^\s*([IVXLCDM]{1,7})\.?\s*$")
NUMBERED = re.compile(r"^\s*(\d{1,3})\.?\s*$")
CONTENTS = re.compile(r"^\s*(CONTENTS|TABLE OF CONTENTS)\s*$", re.I)

ROMAN_OK = re.compile(r"^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$", re.I)


def is_blank(line: str) -> bool:
    return not line.strip()


def is_allcaps_title(line: str) -> bool:
    s = line.strip()
    if not (2 <= len(s) <= 55):
        return False
    letters = [c for c in s if c.isalpha()]
    if len(letters) < 2:
        return False
    if any(c.islower() for c in letters):
        return False
    # a heading, not a shout of prose — no sentence-ending punctuation mid-run
    return not s.endswith((".", ",", ";", ":"))


def isolated(lines: list[str], i: int) -> bool:
    """A heading tends to sit on its own line with blank space above it."""
    before = i == 0 or is_blank(lines[i - 1])
    after = i + 1 >= len(lines) or is_blank(lines[i + 1]) or len(lines[i + 1].strip()) < 60
    return before and after


def preview(lines: list[str], i: int) -> str:
    out = [lines[i].strip()]
    j = i + 1
    while j < len(lines) and len(out) < 3:
        t = lines[j].strip()
        if t:
            out.append(t)
        elif len(out) > 1:
            break
        j += 1
    txt = " · ".join(out)
    return txt[:160] + ("…" if len(txt) > 160 else "")


def line_offsets(body: str) -> list[int]:
    """Char offset at the start of each line."""
    offs, pos = [], 0
    for ln in body.split("\n"):
        offs.append(pos)
        pos += len(ln) + 1
    return offs


def detect(body: str) -> dict:
    lines = body.split("\n")
    offs = line_offsets(body)

    keyword_hits, roman_hits, allcaps_hits, numbered_hits = [], [], [], []
    for i, ln in enumerate(lines):
        s = ln.strip()
        if not s or len(s) > 70:
            continue
        if not isolated(lines, i):
            continue
        km = KEYWORD.match(ln)
        if km and len(s) <= 60:
            keyword_hits.append(i)
            continue
        rm = ROMAN.match(ln)
        if rm and ROMAN_OK.match(rm.group(1)):
            roman_hits.append(i)
            continue
        if is_allcaps_title(ln):
            allcaps_hits.append(i)
            continue
        if NUMBERED.match(ln):
            numbered_hits.append(i)

    contents = detect_contents(lines)

    strategies = {
        "keyword": keyword_hits,
        "contents": contents,
        "roman": roman_hits,
        "allcaps": allcaps_hits,
        "numbered": numbered_hits,
    }
    counts = {k: len(v) for k, v in strategies.items()}

    # Winning strategy: highest-priority one that clears its minimum.
    priority = [("keyword", 2), ("contents", 3), ("roman", 3), ("allcaps", 3), ("numbered", 4)]
    method = "none"
    chosen: list[int] = []
    for name, minimum in priority:
        if counts[name] >= minimum:
            method, chosen = name, strategies[name]
            break

    chapters = [
        {"title": lines[i].strip()[:80], "line": i, "offset": offs[i], "preview": preview(lines, i)}
        for i in sorted(chosen)[:400]
    ]
    return {"method": method, "counts": counts, "chapters": chapters}


def detect_contents(lines: list[str]) -> list[int]:
    """Find a 'Contents' block near the top and locate each entry in the body.

    Returns the line indices in the body where TOC entries first appear."""
    head_limit = min(len(lines), max(60, len(lines) // 6))
    ci = next((i for i in range(head_limit) if CONTENTS.match(lines[i])), None)
    if ci is None:
        return []

    titles, blanks = [], 0
    for ln in lines[ci + 1 : ci + 400]:
        s = ln.strip()
        if not s:
            blanks += 1
            if blanks >= 3 and titles:
                break
            continue
        blanks = 0
        # drop leading numbering and trailing page-number/dot-leaders
        s = re.sub(r"^\s*(\d+[.)]?|[IVXLCDM]+\.)\s+", "", s)
        s = re.sub(r"[\s.]+\d+\s*$", "", s).strip()
        if 2 <= len(s) <= 70:
            titles.append(s)
    if len(titles) < 3:
        return []

    body_after = ci + 1
    found = []
    search_from = body_after
    for t in titles:
        needle = t.lower()
        for i in range(search_from, len(lines)):
            if lines[i].strip().lower().startswith(needle[:40]):
                found.append(i)
                search_from = i + 1
                break
    # only trust it if we located a good share of the listed entries
    return found if len(found) >= max(3, len(titles) // 2) else []


# --------------------------------------------------------------------------- #
def main():
    books = json.loads(CORPUS.read_text(encoding="utf-8"))
    out_books = []
    print(f"corpus: {len(books)} books")

    for b in books:
        text = fetch(b["url"])
        if text is None:
            print(f"[skip] {b['title']}")
            continue
        body = strip_boilerplate(text)
        lines = body.split("\n")
        det = detect(body)

        head = "\n".join(ln[:100] for ln in lines[:45]).strip()
        out_books.append({
            "title": b["title"],
            "tradition": b["tradition"],
            "id": gutenberg_id(b["url"]),
            "url": b["url"],
            "bytes": len(body),
            "lines": len(lines),
            "method": det["method"],
            "counts": det["counts"],
            "chapters": det["chapters"],
            "headPreview": head[:2600],
        })
        print(f"  {det['method']:9s} {len(det['chapters']):4d}  {b['title']}")

    out_books.sort(key=lambda x: (x["tradition"], x["title"]))
    payload = {"books": out_books}
    OUT.write_text("window.DATA = " + json.dumps(payload, ensure_ascii=False) + ";", encoding="utf-8")

    by_method: dict[str, int] = {}
    for b in out_books:
        by_method[b["method"]] = by_method.get(b["method"], 0) + 1
    print(f"\n{len(out_books)} books · methods: " +
          ", ".join(f"{k}={v}" for k, v in sorted(by_method.items())))
    print(f"data.js ~{OUT.stat().st_size // 1024}KB")


if __name__ == "__main__":
    sys.exit(main())
