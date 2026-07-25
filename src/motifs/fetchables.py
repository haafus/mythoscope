"""What each motif source stage would re-fetch — the ``Fetchable`` enumeration ``refresh`` walks.

A stage's refresh re-checks every raw file the source has pinned, so the enumeration is derived
*from the pinned raw tree itself*: each cached file maps back to its upstream URL by the source's
own naming rule (base + relative name for the scraped sites; a fixed URL for the single-shot
endpoints). This is exactly the "present raw" refresh re-checks — new upstream resources appear
only after a build first acquires them, at which point they too are pinned and enumerated.

Enrichment sources fold into the stage that owns them (motifs-atomisation): mapsofmyths +
berezkin_bibliography → berezkin; folkmasa bibliography + mellmann → tmi; wikidata + ashliman → atu.
mapsofmyths (a POST endpoint + parse-discovered node pages) is enumerated separately (7-b2).
"""

from __future__ import annotations

import json
from pathlib import Path

from settings import settings

from .refresh import Fetchable
from .sources import berezkin_bibliography, bibliography

_MAPS_TODO = "mapsofmyths"  # enumerated in a follow-up (POST markers + parse-discovered node pages)


def _config() -> dict:
    return json.loads((settings.config_dir / "motifs.json").read_text(encoding="utf-8"))


def _raw() -> Path:
    return Path(settings.motifs_dir) / "raw"


def _walk(subdir: str, base: str, *, suffix: str = "", exclude: set[str] = frozenset()) -> list[Fetchable]:
    """Every pinned file under ``raw/<subdir>`` → a Fetchable at ``base/<relative-name>`` (the tail
    rule the scraped sites share). ``suffix`` filters by extension; ``.absent`` markers and
    ``exclude`` names are skipped."""
    root = _raw() / subdir
    if not root.exists():
        return []
    out = []
    for f in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = f.relative_to(root).as_posix()
        if rel in exclude or f.name.endswith(".absent") or (suffix and not rel.endswith(suffix)):
            continue
        out.append(Fetchable(title=f"{subdir}/{rel}", url=f"{base.rstrip('/')}/{rel}", cache_file=f))
    return out


def _berezkin(config: dict) -> list[Fetchable]:
    base = config["berezkin"]["base_url"]
    # areasofmyths.com serves the index + every per-motif detail page under one base; biblio.html
    # is berezkin_bibliography's, enumerated just below.
    scrape = _walk("berezkin", base, exclude={"biblio.html"})
    biblio = _raw() / "berezkin" / "biblio.html"
    if biblio.exists():
        scrape.append(Fetchable("berezkin/biblio.html", f"{berezkin_bibliography.BASE}/biblio.html", biblio))
    return scrape


def _tmi(config: dict) -> list[Fetchable]:
    tr, mel = config["trilogy"], config.get("mellmann", {})
    out = _walk("trilogy", tr["base_url"], exclude={"atu_df.csv", "atu_seq.csv", "atu_combos.csv"})
    if mel.get("base_url"):
        out += _walk("mellmann", mel["base_url"])
    folkmasa = _raw() / "folkmasa_bibliography.html"
    if folkmasa.exists():
        out.append(Fetchable("folkmasa_bibliography.html", bibliography.SOURCE_URL, folkmasa))
    return out


def _atu(config: dict) -> list[Fetchable]:
    from .sources import ashliman, atu_wikidata

    tr = config["trilogy"]
    out = [f for f in _walk("trilogy", tr["base_url"])
           if Path(f.cache_file).name in {"atu_df.csv", "atu_seq.csv", "atu_combos.csv"}]
    out += _walk("ashliman", ashliman.BASE)
    wd = _raw() / "wikidata" / "atu.json"
    if wd.exists():
        out.append(Fetchable("wikidata/atu.json", atu_wikidata.query_url(), wd))
    return out


_BUILDERS = {"berezkin": _berezkin, "tmi": _tmi, "atu": _atu}


def source_fetchables(source: str) -> list[Fetchable]:
    """The resources ``motifs:source:<source>`` would re-check on refresh."""
    return _BUILDERS[source](_config())
