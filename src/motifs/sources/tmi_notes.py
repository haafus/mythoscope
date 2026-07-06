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
# Latin letters incl. Latin-1 diacritics, so a label like ``Guarayú`` or
# ``Métis`` is recognised. A culture label can also carry parenthetical
# qualifiers before its colon (``S. Am. Indian (Paressi):``, ``Indian (Hindu):``)
# — tolerate any of them so the label is still seen as the bibliography boundary.
_UC = r"A-ZÀ-ÖØ-Þ"          # uppercase, incl. accented
_LC = r"A-Za-zÀ-ÖØ-öø-ÿ"    # any Latin letter, incl. accented
# A culture label is an uppercase-initial run of letters, dots, spaces, commas and
# hyphens — so a multi-culture list (``Mono-Alu, Fauru, Buin``) or a hyphenated
# name (``Finno-Ugric``) reads as one label. The length cap is what keeps a label
# from swallowing its neighbours: a sentence boundary, a run-on, or the ``--``
# separator all sit beyond ~26 chars from the colon, so the (lazy, capped) match
# stops before reaching across them and the prose before stays the definition.
_LBL = rf"{_LC},. \-"
_LABEL_HEAD = rf"[{_UC}][{_LBL}]{{1,26}}?(?:\s*\([^)]*\))*"
_BIB_START = re.compile(
    r"\s--|†|\bTypes?\b|\*[A-Z]|\([Cc]f|(?:^|[;.]|\s--)\s*" + _LABEL_HEAD + r":"
)

# A '†' motif cross-reference, optionally introduced by 'Cf.' ("compare"); the
# 'Cf.' may carry a footnote-style '[b]' marker before the dagger.
_DAGGER = re.compile(r"([Cc]f\.\s*(?:\[[a-z]\]\s*)?)?†\s*([A-Z]\d[\dA-Za-z.]*)")
# An inline ATU reference, possibly a comma list ("Type 803", "Types 403, 425").
_TYPE = re.compile(r"\bTypes?\s+(\d[\dA-Za-z*]*(?:\s*,\s*\d[\dA-Za-z*]*)*)")
# A culture/region label heading a citation group, anchored to a group boundary
# (start, ';', ' --') so a colon inside a source title isn't taken for a label.
_LABEL = re.compile(rf"(?:^|;|\s--)\s*([{_UC}][{_LBL}]*?(?:\s*\([^)]*\))*)\s*:\s*")
_GROUP_SPLIT = re.compile(r";|\s--")
# A '†' cross-reference, with any leading '(Cf.' and trailing ')'. Stripped from
# the text before parsing the definition/bibliography (it lives in see_also), so
# it can't bleed into a neighbouring culture citation.
_XREF = re.compile(r"\(?\s*(?:[Cc]f\.\s*)?†\s*[A-Z]\d[\dA-Za-z.]*\.?\s*\)?")


# Hand-curated overrides for notes whose leading citation the heuristic cannot tell
# from prose: an English-titled citation that opens the bibliography with no culture
# label ('Krappe The Review of Religion (1941)'), whose title words ('The', 'of')
# read like a sentence. Each listed motif has its whole note treated as bibliography
# — the definition is dropped and the citation kept in ``references``. This is an
# extensible escape hatch: add an id here when a citation still shows as a definition.
FORCE_BIBLIOGRAPHY: frozenset[str] = frozenset({
    "A112.1", "A475", "A475.1", "A728", "A751.1.3", "A992.2",
    "B11.6.1", "B53.2", "B121.1", "B142.3", "B331.2.1", "B469.4", "B563.1",
    "B713.1", "B732", "B751.2", "B771.3",
    "C321", "C915.1.1",
    "D2191",
    "E0", "E631.3", "E748", "E755.2",
    "F252.2", "F574.1.2", "F709.1",
    "G86", "G261.1", "G303.3.3.1.3", "G303.16.3.4",
})


def parse_notes(notes: str | None, motif_id: str | None = None) -> dict:
    """Decompose a ``notes`` string into definition + structured references. ``motif_id``
    lets the curated ``FORCE_BIBLIOGRAPHY`` overrides drop a citation the heuristic
    would otherwise keep as a definition."""
    notes = (notes or "").strip()
    # A leading '--' is just the bibliography-intro dash (no definition); drop it
    # so the first culture label sits at a boundary the parser recognises.
    cleaned = _strip_xrefs(notes).lstrip("-– ").strip()
    if motif_id in FORCE_BIBLIOGRAPHY:
        definition, biblio = "", cleaned          # override: the whole note is bibliography
    else:
        definition, biblio = _split_definition(cleaned)
    # The definition split can land on a '.' boundary (e.g. after a leading
    # '(Cf. †…)' xref was removed, or a 'definition. Culture:' sentence break),
    # leaving the bibliography with a stray leading '.'. _LABEL treats ';' and
    # ' --' as group boundaries but not '.', so the first culture would be missed
    # — drop the leading dot(s) so it is recognised. (' --' has no leading dot.)
    biblio = biblio.lstrip(".")
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


# A bibliographic locus token — a page/volume/No./year/footnote marker that only
# ever sits inside a citation, never in a prose definition. Used to spot a
# *culture-less* citation (one with no 'Label:' prefix, so _BIB_START skips it and
# the splitter would otherwise read it as the definition — e.g. J21.22's leading
# "Nouvelles de Sens No. 7").
_LOCUS = re.compile(
    r"\bNos?\.\s*\*?\d|\bpp?\.\s*\d|\b[IVXLC]{2,}\s+\d|\b\d+\s*ff\b\.?"
    r"|\(\s*\d{4}\s*\)|\bvol\.?\s*\d|\bibid\b|\bn\.\s*\d", re.I)
# English function/verb/pronoun words: present in a real (English) definition,
# absent from a name-only or foreign-language ("Jahrb. d. kaiserlichen deutschen
# …") citation. Used only to tell a prose clause apart from a citation, so a
# trailing citation glued to a real definition is not mistaken for a leading one.
_PROSE_WORD = re.compile(
    r"\b(?:the|an?|and|or|but|of|in|on|to|with|for|as|at|from|is|are|was|were|be|been|being"
    r"|has|have|had|do|does|did|he|she|it|they|we|him|her|them|his|its|their|our|who|whom"
    r"|which|that|this|these|those|when|where|why|how|what|while|because|so|then|comes?|came"
    r"|becomes?|became|makes?|made|gives?|gave|given|falls?|fell|creates?|created|goes?|went"
    r"|sees?|saw|takes?|took|tells?|told|says?|said|kills?|killed|brings?|brought|finds?|found"
    r"|lives?|lived|puts?|sends?|sent|wants?|tries|cannot|will|would|must|should)\b", re.I)
_CAP_INIT = re.compile(r"^[\"'(*.,;\-\s]*[A-ZÀ-ÖØ-Þ]")


def _is_leading_citation(head: str) -> bool:
    """True if the candidate definition is really a culture-less citation that opens
    the bibliography (so it should be dropped, not shown as a definition). A citation
    either carries a bibliographic locus with no prose clause before it, or is a short
    ``Author Work Page`` run whose numbers no lowercase word precedes."""
    m = _LOCUS.search(head)
    if m:
        region = head[: m.start()]           # what sits before the first locus
        if len(region.split()) <= 12 and not _PROSE_WORD.search(region):
            return True                      # citation leads the field (no prose ahead of it)
    if _CAP_INIT.match(head) and len(head.split()) <= 9 and not _PROSE_WORD.search(head):
        d = re.search(r"\d", head)
        if d and not re.search(r"\b[a-zà-öø-ÿ]{2,}\b", head[: d.start()]):
            return True                      # 'Gaster Thespis 211, 389, 397.'
    return False


def _sentence_ends(s: str):
    """Yield the index just past each sentence terminator at bracket/paren depth 0 (so
    ``s[:i]`` keeps the punctuation). Decimal points and terminators nested in
    ``(…)``/``[…]`` are skipped; a ``.`` counts only when it ends the string or is
    followed by whitespace then a capital / opening quote or bracket."""
    depth = 0
    for i, ch in enumerate(s):
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(0, depth - 1)
        elif depth == 0 and ch in ".!?":
            if ch == "." and i and s[i - 1].isdigit() and i + 1 < len(s) and s[i + 1].isdigit():
                continue
            j = i + 1
            while j < len(s) and s[j] == " ":
                j += 1
            if j >= len(s) or s[j].isupper() or s[j] in "([\"'":
                yield i + 1


def _is_citation_sentence(seg: str) -> bool:
    """True if a single sentence is a bibliographic citation (a locus, or an
    ``Author Work Page`` run whose numbers no lowercase word precedes) rather than
    prose — so a bare noun list ('Stone, cedar, iron…') is *not* taken for one."""
    seg = seg.strip()
    if not seg:
        return True
    if _PROSE_WORD.search(seg):     # any English function/verb word => prose, not a pure citation
        return False
    if _LOCUS.search(seg):
        return True
    d = re.search(r"\d", seg)       # 'Gaster Thespis 211' — proper-noun-led, no word before the number
    return bool(d and _CAP_INIT.match(seg)
                and not re.search(r"\b[a-zà-öø-ÿ]{2,}\b", seg[: d.start()]))


def _trim_trailing_citation(head: str) -> tuple[str, str]:
    """Split a citation glued onto the end of a prose definition ('…eating him. Wienert
    FFC LVI 52…; Halm Aesop No. 231') into ``(definition, trailing)``. Cut at the
    earliest sentence end after which *every* sentence is itself a citation and the
    kept part still reads as prose — so real multi-sentence prose (even a bare noun
    list) is never trimmed."""
    for cut in _sentence_ends(head):
        tail = head[cut:].strip()
        if not (tail and _LOCUS.search(tail) and _PROSE_WORD.search(head[:cut])):
            continue
        segs, prev = [], 0
        for e in [*_sentence_ends(tail), len(tail)]:
            segs.append(tail[prev:e]); prev = e
        if all(_is_citation_sentence(s) for s in segs):
            return head[:cut].strip(), tail
    return head, ""


def _split_definition(notes: str) -> tuple[str, str]:
    m = _BIB_START.search(notes)
    head = (notes[: m.start()] if m else notes).strip(" -")
    biblio = notes[m.start():] if m else ""
    if _is_prose(head) and not _is_leading_citation(head):
        head, trailing = _trim_trailing_citation(head)
        if trailing:                          # move the peeled citation into the bibliography
            biblio = f"{trailing}; {biblio.lstrip(' ;-')}" if biblio.strip(" ;-") else trailing
        return head, biblio
    return "", notes


# The connector between two †refs of one open 'Cf. †A, †B and †C / †A--†D' list:
# commas, 'and', a range dash — anything else breaks the list.
_CF_CONT = re.compile(r"(?:[\s,]|and|[-–])*")
# A '†X' glued to a citation as '… Smith (†X)' is a bibliographic tag, not a
# cross-reference — the '(' sits right after a word char.
_CITE_TAG = re.compile(r"[A-Za-z0-9]\s*\(\s*$")


def _see_also(notes: str) -> dict:
    cf, ref = [], []
    carry = False        # inside an open 'Cf. †A, †B, …' list?
    prev_end = None
    for m in _DAGGER.finditer(notes):
        mid = m.group(2).rstrip(".")
        if not m.group(1) and _CITE_TAG.search(notes[:m.start()]):
            carry = False                     # '… (†X)' citation tag — skip entirely
            prev_end = m.end()
            continue
        if m.group(1):                        # explicit 'Cf.' introduces (or re-opens) the list
            is_cf = carry = True
        elif carry and prev_end is not None and _CF_CONT.fullmatch(notes[prev_end:m.start()]):
            is_cf = True                      # continuation of the open 'Cf.' list
        else:                                 # a bare '†X' (see also), or a break in the list
            is_cf = carry = False
        (cf if is_cf else ref).append(mid)
        prev_end = m.end()
    return {"cf": _dedup(cf), "ref": _dedup(ref)}


def _atu_inline(notes: str) -> list[str]:
    out: list[str] = []
    for clause in _TYPE.findall(notes):
        out.extend(p.strip() for p in clause.split(","))
    return _dedup(out)


# Genre/structural words that head a genuine citation block but are not cultures
# ("Fable: Aesop …", "Answer: he-goat. *Type 812 …"). The source-like test cannot
# catch these (their citations are real), so they are listed explicitly.
_NONCULTURE = {"Fable", "Answer", "Countertask"}


def _sourcelike(cite: str) -> bool:
    """True if a citation carries a source token — a page/volume/year digit, an
    author surname or index marker (capital / ``*``), or an ``ibid.``/``cf.`` back-
    reference. A "citation" that is none of these is prose that a stray capitalised
    word (``Answer:``, ``Decision:``) dragged in as a false culture label.
    """
    c = cite.strip()
    if not c:
        return False
    if any(ch.isdigit() for ch in c) or c[0] == "*" or c[0].isupper():
        return True
    return bool(re.match(r"(?:ibid|cf)\b", c, re.I))


def _cultures(biblio: str) -> dict[str, list[str]]:
    """``{label: [citation strings]}``; nested sub-areas stay inline.

    A label is kept only if at least one of its citations looks like a real
    source — this drops prose fragments (``Answer:``, ``Tabu: …``) that a
    capitalised word before a colon leaked in as a spurious culture.
    """
    bounds = [(m.end(), m.group(1)) for m in _LABEL.finditer(biblio)]
    starts = [m.start() for m in _LABEL.finditer(biblio)] + [len(biblio)]
    out: dict[str, list[str]] = {}
    for i, (end, label) in enumerate(bounds):
        cite = biblio[end: starts[i + 1]].strip(" .,;-")
        if cite:
            out.setdefault(re.sub(r"\s+", " ", label).strip(), []).append(cite)
    return {lbl: cs for lbl, cs in out.items()
            if lbl not in _NONCULTURE and any(_sourcelike(c) for c in cs)}


def _references(biblio: str) -> list[str]:
    return [seg for seg in (s.strip(" .,-") for s in _GROUP_SPLIT.split(biblio)) if seg]


def _dedup(items) -> list[str]:
    seen, out = set(), []
    for it in items:
        if it and it not in seen:
            seen.add(it)
            out.append(it)
    return out
