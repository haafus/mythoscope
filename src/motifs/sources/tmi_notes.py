"""Structured extraction from a TMI motif's free-text ``notes`` field.

A note packs several layers into one string: an optional prose definition, then
a bibliography whose citations are tagged by culture/region labels, plus inline
cross-references to other motifs (``†``) and to ATU tale types (``Type``). This
pulls those into separate fields; the raw ``notes`` is kept as the source of
truth, so anything the heuristics miss is never lost.
"""

from __future__ import annotations

import re

# The bibliography opens at the earliest of these; the prose before it (if any)
# is the definition. Covers the '--' block separator, a motif/type/source ref,
# and a culture label anchored to a group boundary.
# A culture label can carry parenthetical qualifiers before its colon
# (``S. Am. Indian (Paressi):``, ``Indian (Hindu):``) — tolerate any of them so
# the label is still recognised as the bibliography boundary.
_LABEL_HEAD = r"[A-Z][A-Za-z. ]{1,26}?(?:\s*\([^)]*\))*"
_BIB_START = re.compile(
    r"\s--|†|\bTypes?\b|\*[A-Z]|\([Cc]f|(?:^|[;.]|\s--)\s*" + _LABEL_HEAD + r":"
)

# A '†' motif cross-reference, optionally introduced by 'Cf.' ("compare").
_DAGGER = re.compile(r"([Cc]f\.\s*)?†\s*([A-Z]\d[\dA-Za-z.]*)")
# An inline ATU reference, possibly a comma list ("Type 803", "Types 403, 425").
_TYPE = re.compile(r"\bTypes?\s+(\d[\dA-Za-z*]*(?:\s*,\s*\d[\dA-Za-z*]*)*)")
# A culture/region label heading a citation group, anchored to a group boundary
# (start, ';', ' --') so a colon inside a source title isn't taken for a label.
_LABEL = re.compile(r"(?:^|;|\s--)\s*([A-Z][A-Za-z. ]*?(?:\s*\([^)]*\))*)\s*:\s*")
_GROUP_SPLIT = re.compile(r";|\s--")
# A '†' cross-reference, with any leading '(Cf.' and trailing ')'. Stripped from
# the text before parsing the definition/bibliography (it lives in see_also), so
# it can't bleed into a neighbouring culture citation.
_XREF = re.compile(r"\(?\s*(?:[Cc]f\.\s*)?†\s*[A-Z]\d[\dA-Za-z.]*\.?\s*\)?")


def parse_notes(notes: str | None) -> dict:
    """Decompose a ``notes`` string into definition + structured references."""
    notes = (notes or "").strip()
    # A leading '--' is just the bibliography-intro dash (no definition); drop it
    # so the first culture label sits at a boundary the parser recognises.
    cleaned = _strip_xrefs(notes).lstrip("-– ").strip()
    definition, biblio = _split_definition(cleaned)
    return {
        "definition": definition,
        "cultures": _cultures(biblio),
        "references": _references(biblio),
        "see_also": _see_also(notes),
        "atu_inline": _atu_inline(notes),
    }


def _strip_xrefs(notes: str) -> str:
    s = _XREF.sub(" ", notes)
    s = re.sub(r"\(\s*\)", " ", s)         # empty parens left behind
    s = re.sub(r"\s+([.,;])", r"\1", s)    # space pulled before punctuation
    s = re.sub(r"([.,;])\s*\1+", r"\1", s)  # punctuation doubled by the removal
    return re.sub(r"\s+", " ", s).strip()


def _is_prose(head: str) -> bool:
    """True if a leading fragment reads as a definition, not a stray citation."""
    if len(head.split()) < 4 or head[:1] in "*(":
        return False
    if re.match(rf"^{_LABEL_HEAD}:", head):  # 'Greek: …' / 'S. Am. Indian (Paressi): …' is a citation
        return False
    return not head.lower().startswith(("for a ", "for the ", "see "))  # meta-biblio


def _split_definition(notes: str) -> tuple[str, str]:
    m = _BIB_START.search(notes)
    if not m:
        head = notes.strip(" -")
        return (head, "") if _is_prose(head) else ("", notes)
    head = notes[: m.start()].strip(" -")
    return (head, notes[m.start():]) if _is_prose(head) else ("", notes)


def _see_also(notes: str) -> dict:
    cf, ref = [], []
    for is_cf, mid in _DAGGER.findall(notes):
        (cf if is_cf else ref).append(mid.rstrip("."))
    return {"cf": _dedup(cf), "ref": _dedup(ref)}


def _atu_inline(notes: str) -> list[str]:
    out: list[str] = []
    for clause in _TYPE.findall(notes):
        out.extend(p.strip() for p in clause.split(","))
    return _dedup(out)


def _cultures(biblio: str) -> dict[str, list[str]]:
    """``{label: [citation strings]}``; nested sub-areas stay inline."""
    bounds = [(m.end(), m.group(1)) for m in _LABEL.finditer(biblio)]
    starts = [m.start() for m in _LABEL.finditer(biblio)] + [len(biblio)]
    out: dict[str, list[str]] = {}
    for i, (end, label) in enumerate(bounds):
        cite = biblio[end: starts[i + 1]].strip(" .,;-")
        if cite:
            out.setdefault(re.sub(r"\s+", " ", label).strip(), []).append(cite)
    return out


def _references(biblio: str) -> list[str]:
    return [seg for seg in (s.strip(" .,-") for s in _GROUP_SPLIT.split(biblio)) if seg]


def _dedup(items) -> list[str]:
    seen, out = set(), []
    for it in items:
        if it and it not in seen:
            seen.add(it)
            out.append(it)
    return out
