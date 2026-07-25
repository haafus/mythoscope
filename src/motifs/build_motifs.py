"""Orchestrate the motif-database build step.

Reads ``config/motifs.json``, scrapes/downloads each enabled source into the
resumable raw cache, parses them into per-index JSON, derives the cross-walk and
writes a manifest. Re-parses and regenerates every time it runs, reusing the raw
cache (downloading only what's missing); ``force`` re-fetches every raw source.
"""

from __future__ import annotations

import itertools
import json
import logging
import time
from datetime import datetime, timezone

from json_utils import load_json_optional, save_json
from settings import settings

from . import crosswalk, derive, parallels, reasoned_parallels, store
from .sources import (
    ashliman,
    atu_wikidata,
    berezkin,
    berezkin_bibliography,
    bibliography,
    mapsofmyths,
    trilogy,
)

logger = logging.getLogger(__name__)

# Which network enrichments belong to each source — for persisting per-source enrichment summaries
# (skip status + counts) that the future meta aggregator collects. mapsofmyths/berezkin_bibliography
# enrich the Berezkin build; bibliography the TMI build; wikidata/ashliman the ATU build.
_SOURCE_ENRICHMENTS = {
    "berezkin": ["mapsofmyths", "berezkin_bibliography"],
    "tmi": ["bibliography"],
    "atu": ["atu_wikidata", "ashliman"],
}


def _aggregate_enrichment() -> dict:
    """Merge the per-source enrichment sidecars (task 3) into the single summary the degradation
    guard + meta consume — the aggregation the future meta stage runs. Source/key order matches
    the monolith's in-memory build order, so the merged dict is identical."""
    out: dict = {}
    for src in _SOURCE_ENRICHMENTS:
        path = store.enrichment_path(src)
        if path.exists():
            out.update(json.loads(path.read_text(encoding="utf-8")))
    return out


def _load_config() -> dict:
    config_file = settings.config_dir / "motifs.json"
    if not config_file.exists():
        raise FileNotFoundError(f"Motifs config not found: {config_file}")
    return json.loads(config_file.read_text(encoding="utf-8"))


def _applied(records: list[dict], pred) -> int:
    """How many records satisfy ``pred`` — used for the per-step enrichment counts."""
    return sum(1 for r in records if pred(r))


def _flat_metrics(counts: dict, crosswalk_counts: dict) -> dict[str, int]:
    """The named counters whose drop is a degradation signal: index sizes + cross-walk link totals."""
    m = {f"index.{k}": v for k, v in counts.items()}
    m.update({f"crosswalk.{k}": v for k, v in crosswalk_counts.items()})
    return m


def _degradation_check(metrics: dict[str, int], enrichment: dict, prior: dict,
                       built_at: str) -> tuple[dict, list, dict]:
    """Build-time degradation guard. Compare each metric to its all-time **high-water** mark
    (``meta.highwater``) and raise a durable **``yield-drop``** flag while it sits below. The mark
    advances only on a *trusted* build — one where no source was skipped/degraded — so a spurious
    spike can't poison it; a genuine drop persists (``first_seen`` carried forward) and **auto-clears**
    once the metric recovers to the mark. Also records a per-source ``fetch_outcome``. (Per-payload
    ``changed``/``gone``/``degraded`` flags are refresh-time — they need an upstream diff — and land
    with ``refresh``.)"""
    prior_hw = prior.get("highwater", {})
    prior_flags = {(f["kind"], f["key"]): f for f in prior.get("flags", [])}
    trusted = not any(isinstance(e, dict) and e.get("skipped") for e in enrichment.values())
    highwater: dict[str, int] = {}
    flags: list[dict] = []
    # Iterate the union of current metrics and prior marks: a counter present in a prior build but absent
    # now (a source disabled / a count key gone) reads as 0 and still trips its high-water mark.
    for name in sorted(set(metrics) | set(prior_hw)):
        val = metrics.get(name, 0)
        mark = max(prior_hw.get(name, val), val) if trusted else prior_hw.get(name, val)
        highwater[name] = mark
        if val < mark:
            first_seen = prior_flags.get(("yield-drop", name), {}).get("first_seen", built_at)
            flags.append({"source": "build", "key": name, "kind": "yield-drop",
                          "detail": f"{val} < high-water {mark}", "auto_action": "kept-going",
                          "first_seen": first_seen})
            logger.warning("REGRESSION [yield-drop]: %s = %d, below high-water %d", name, val, mark)
    fetch_outcomes = {src: (f"skipped-{e['skipped']}" if isinstance(e, dict) and e.get("skipped") else "ok")
                      for src, e in enrichment.items()}
    return highwater, flags, fetch_outcomes


def _timed(label: str, fn, *args, **kwargs):
    """Run fn, logging its wall time — so the per-step pauses (even when everything is
    cached, the parse/derive still runs) are visible and attributable."""
    t = time.monotonic()
    result = fn(*args, **kwargs)
    logger.info("      ⏱ %s: %.1fs", label, time.monotonic() - t)
    return result


def _persist_enrichment(source: str, enrichment: dict) -> None:
    """Write a source's enrichment summary sidecar (skip status + counts), the per-source input the
    meta aggregator reads. Restricted to the keys that belong to this source."""
    keys = _SOURCE_ENRICHMENTS.get(source, [])
    save_json(store.enrichment_path(source), {k: enrichment[k] for k in keys if k in enrichment})


def _build_berezkin(config: dict, *, force: bool) -> dict:
    """Build ``berezkin.json`` (+ its enrichment sidecar) from the areal catalogue + mapsofmyths.
    Returns ``{counts, sources}`` for the meta aggregation. The future ``motifs:source:berezkin``."""
    bz_cfg = config.get("berezkin", {})
    if not bz_cfg.get("enabled", True):
        return {"counts": {}, "sources": {}}
    enrichment: dict[str, dict] = {}
    home = bz_cfg.get("homepage", "areasofmyths.com")
    logger.info("[1/5] Berezkin areal catalogue — source: %s (%s + per-motif detail pages for definitions)",
                home, bz_cfg.get("index_page", "index page"))
    # mapsofmyths enrichment refresh (English text, taxonomy, TMI/ATU ids, traditions) — part of
    # building the Berezkin index, so downloaded under this step; credential-gated, a no-op skips it.
    mm = enrichment["mapsofmyths"] = _timed("mapsofmyths.refresh", mapsofmyths.refresh, force=force)
    berezkin_data = _timed("berezkin.build (parse)", berezkin.build, bz_cfg, force=force)
    save_json(store.index_path("berezkin"), berezkin_data)
    berezkin_motifs = berezkin_data["motifs"]
    logger.info("      + base scrape (areasofmyths.com): %d motifs, %d chapters, %d with a definition",
                len(berezkin_motifs), len(berezkin_data.get("chapters", {})),
                _applied(berezkin_motifs, lambda m: m.get("definition") or m.get("definition_rus")))
    if mm.get("skipped"):
        logger.info("      + mapsofmyths.com enrichment SKIPPED (%s) — Russian names/definitions only", mm["skipped"])
    else:
        logger.info("      + mapsofmyths.com enrichment (motifs gaining each field):")
        logger.info("          English name (Russian kept as subtitle): %d",
                    _applied(berezkin_motifs, lambda m: m.get("name_rus")))
        logger.info("          English definition                     : %d",
                    _applied(berezkin_motifs, lambda m: m.get("definition_rus")))
        logger.info("          thematic type/group                    : %d",
                    _applied(berezkin_motifs, lambda m: m.get("motif_type")))
        logger.info("          direct TMI links                       : %d",
                    _applied(berezkin_motifs, lambda m: m.get("tmi_refs")))
        logger.info("          areal tradition sets                   : %d",
                    _applied(berezkin_motifs, lambda m: m.get("traditions")))
        logger.info("          + tradition catalogue: %d areal codes → people name, region & language",
                    len(berezkin_data.get("traditions", {})))

    enrichment["berezkin_bibliography"] = _timed("berezkin_bibliography.refresh", berezkin_bibliography.refresh, berezkin_motifs, force=force)
    bb = enrichment["berezkin_bibliography"]
    if bb.get("skipped"):
        logger.info("      + bibliography (areasofmyths.com) SKIPPED (%s)", bb["skipped"])
    else:
        logger.info("      + bibliography (areasofmyths.com): %d works; citations resolved %d/%d (%d%%), "
                    "ambiguous %d",
                    bb["works"], bb["resolved"], bb["citations"],
                    round(100 * bb["resolved"] / bb["citations"]) if bb["citations"] else 0,
                    bb["ambiguous"])
    _persist_enrichment("berezkin", enrichment)
    return {"counts": {"berezkin": len(berezkin_motifs)},
            "sources": {"berezkin": {"homepage": home, "attribution": bz_cfg.get("attribution", "")}}}


def _build_tmi(config: dict, *, force: bool) -> dict:
    """Build ``tmi.json`` (+ enrichment sidecar) from the trilogy TMI CSV (+ Mellmann headings +
    folkmasa bibliography). Returns ``{counts, sources}``. The future ``motifs:source:tmi``."""
    tr_cfg = config.get("trilogy", {})
    if not tr_cfg.get("enabled", True):
        return {"counts": {}, "sources": {}}
    enrichment: dict[str, dict] = {}
    sources = {"trilogy": {"homepage": tr_cfg.get("homepage", ""), "attribution": tr_cfg.get("attribution", "")}}
    files = tr_cfg.get("files", {})
    logger.info("[2/5] Thompson Motif-Index (TMI) — source: %s (%s)",
                tr_cfg.get("homepage", "trilogy"), files.get("tmi", "tmi.csv"))
    mel_cfg = config.get("mellmann", {})
    mel_on = mel_cfg.get("enabled", False)
    tmi_index = _timed("trilogy.build_tmi (parse)", trilogy.build_tmi, tr_cfg, force=force,
                       divisions_config=mel_cfg if mel_on else None)
    if mel_on:
        sources["mellmann"] = {"homepage": mel_cfg.get("homepage", ""),
                               "attribution": mel_cfg.get("attribution", "")}
        logger.info("      classification headings — source: Mellmann TMI_as_CSV")
        logger.info("      %d divisions, %d sub-divisions, %d sub-sub-divisions, %d sections",
                    len(tmi_index.get("divisions", [])), len(tmi_index.get("subdivisions", [])),
                    len(tmi_index.get("subdivisions3", [])), len(tmi_index.get("sections", [])))
    save_json(store.index_path("tmi"), tmi_index)
    tmi_motifs = tmi_index["motifs"]
    logger.info("      %d motifs; notes parsed → definition ×%d, cultures ×%d, ATU refs ×%d",
                len(tmi_motifs),
                _applied(tmi_motifs, lambda m: m.get("definition")),
                _applied(tmi_motifs, lambda m: m.get("cultures")),
                _applied(tmi_motifs, lambda m: m.get("atu_inline")))
    enrichment["bibliography"] = _timed("bibliography.refresh", bibliography.refresh, tmi_motifs, force=force)
    bib = enrichment["bibliography"]
    logger.info("      citation key — source: %s + curated supplement: %d entries (%d with a book link)",
                "folkmasa.org", bib.get("entries", 0), bib.get("linked", 0))
    _persist_enrichment("tmi", enrichment)
    return {"counts": {"tmi": len(tmi_motifs)}, "sources": sources}


def _build_atu(config: dict, *, force: bool) -> dict:
    """Build ``atu.json`` (+ enrichment sidecar) from the trilogy ATU CSVs (+ Wikidata + Ashliman).
    Returns ``{counts, sources}``. The future ``motifs:source:atu``."""
    tr_cfg = config.get("trilogy", {})
    if not tr_cfg.get("enabled", True):
        return {"counts": {}, "sources": {}}
    enrichment: dict[str, dict] = {}
    files = tr_cfg.get("files", {})
    logger.info("[3/5] Aarne-Thompson-Uther (ATU) tale types — source: %s", tr_cfg.get("homepage", "trilogy"))
    logger.info("      files: %s", ", ".join(v for k, v in files.items() if k != "tmi") or "atu CSVs")
    atu_index, _ = _timed("trilogy.build_atu (parse)", trilogy.build_atu, tr_cfg, force=force)
    enrichment["atu_wikidata"] = _timed("atu_wikidata.refresh", atu_wikidata.refresh, atu_index["types"], force=force)
    enrichment["ashliman"] = _timed("ashliman.refresh", ashliman.refresh, atu_index["types"], force=force)
    save_json(store.index_path("atu"), atu_index)
    atu_types = atu_index["types"]
    logger.info("      %d tale types", len(atu_types))
    wd = enrichment["atu_wikidata"]
    if wd.get("skipped"):
        logger.info("      + Wikidata enrichment SKIPPED (%s)", wd["skipped"])
    else:
        logger.info("      + Wikidata: %d types with multilingual names, %d with Wikipedia links",
                    wd["types_with_names"], wd["types_with_wikipedia"])
    ash = enrichment["ashliman"]
    if ash.get("skipped"):
        logger.info("      + Ashliman example tales SKIPPED (%s)", ash["skipped"])
    else:
        logger.info("      + Ashliman: %d types carry %d tale variants (from %d pages, %d orphan site types dropped)",
                    ash["types_with_tales"], ash["variants"], ash["pages"], ash["orphans_dropped"])
    _persist_enrichment("atu", enrichment)
    return {"counts": {"atu": len(atu_types)}, "sources": {}}


def _build_crosswalk() -> dict:
    """Build ``crosswalk.json`` from the three source indexes (reloaded + re-derived via
    motifs.derive). Returns the links map. The future ``motifs:crosswalk`` stage."""
    logger.info("[4/5] Cross-walk — deriving id links across the three indexes")
    d = derive.load_indexes()
    links = _timed("crosswalk.build", crosswalk.build, d["atu_seq"], d["tmi_ids"], d["berezkin_motifs"],
                   d["atu_ids"], d["atu_defining"], d["atu_aliases"], d["tmi_notes"], d["aath_to_atu"],
                   d["atu_summaries"], d["tmi_aliases"])
    save_json(store.crosswalk_path(), links)
    logger.info("      ATU<->TMI %d/%d (+%d defining motifs → %d TMI; %d TMI motifs reachable from a tale type)",
                len(links["atu_to_tmi"]), len(links["tmi_to_atu"]),
                len(links["atu_to_tmi_defining"]), len(links["tmi_to_atu_defining"]),
                links["linked_tmi_count"])
    logger.info("      Berezkin<->ATU %d/%d", len(links["berezkin_to_atu"]), len(links["atu_to_berezkin"]))
    logger.info("      Berezkin<->TMI (direct) %d/%d", len(links["berezkin_to_tmi"]), len(links["tmi_to_berezkin"]))
    logger.info("      + inline relations (each stored both ways): TMI notes → %d ATU types, "
                "ATU summaries → %d TMI motifs", len(links["atu_to_tmi_note"]), len(links["tmi_to_atu_summary"]))
    logger.info("      + inferred (transitive closure via low-fan-out pivots): %d edges",
                links.get("inferred_count", 0))
    return links


def _build_parallels(links: dict) -> dict:
    """Build ``parallels.json`` (heuristic look-alikes with no recorded cross-walk link) from the
    source indexes + the cross-walk. Returns the per-tier counts. The future ``motifs:parallels``."""
    logger.info("[5/5] Textual parallels — lexical look-alikes with no recorded link")
    d = derive.load_indexes()
    par = _timed("parallels.build (TF-IDF + NN)", parallels.build,
                 d["berezkin_motifs"], d["tmi_motifs"], d["atu_types"], links)
    if par is None:
        logger.info("      SKIPPED (no TMI/ATU, or scikit-learn unavailable)")
        return {}
    save_json(store.parallels_path(), par)
    par_counts = par["counts"]
    logger.info("      candidates (unlinked look-alikes) — tier A / tier B; near-identical is the "
                "strongest subset of tier A:")
    for key, name in (("atu_tmi", "ATU~TMI     "), ("berezkin_tmi", "Berezkin~TMI"),
                      ("berezkin_atu", "Berezkin~ATU")):
        logger.info("        %s  %d / %d  (%d near-identical)", name,
                    par_counts.get(f"{key}_A", 0), par_counts.get(f"{key}_B", 0),
                    par_counts.get(f"{key}_near", 0))
    logger.info("        three-way parallels: %d", par_counts.get("triangles", 0))
    return par_counts


def _build_semantic() -> None:
    """Copy the committed, precomputed BGE-M3 semantic-parallels file into outputs. The future
    ``motifs:semantic`` stage (copy-in mode)."""
    sem = store.copy_semantic_parallels()
    if sem is not None:
        logger.info("      + semantic parallels (BGE-M3): %d pairs — precomputed, committed file copied into outputs",
                    sem.get("counts", {}).get("pairs", 0))
    else:
        logger.info("      + semantic parallels (BGE-M3): none (run scripts/build_semantic_parallels.py)")


def _meta_counts_sources(config: dict) -> tuple[dict, dict]:
    """Re-derive meta's ``counts`` (index sizes) and ``sources`` (provenance) from the stored
    indexes + config, in the monolith's build order — so the meta aggregator needs no in-memory
    handoff from the source builds. Only enabled sources contribute, matching ``_build_*``."""
    counts: dict[str, int] = {}
    sources: dict[str, dict] = {}
    bz = config.get("berezkin", {})
    if bz.get("enabled", True):
        counts["berezkin"] = len((store.load_index("berezkin") or {}).get("motifs", []))
        sources["berezkin"] = {"homepage": bz.get("homepage", "areasofmyths.com"),
                               "attribution": bz.get("attribution", "")}
    tr = config.get("trilogy", {})
    if tr.get("enabled", True):
        counts["tmi"] = len((store.load_index("tmi") or {}).get("motifs", []))
        sources["trilogy"] = {"homepage": tr.get("homepage", ""), "attribution": tr.get("attribution", "")}
        mel = config.get("mellmann", {})
        if mel.get("enabled", False):
            sources["mellmann"] = {"homepage": mel.get("homepage", ""), "attribution": mel.get("attribution", "")}
        counts["atu"] = len((store.load_index("atu") or {}).get("types", []))
    return counts, sources


def _build_meta(config: dict) -> None:
    """Assemble ``meta.json``: counts, per-source enrichment (from the sidecars), cross-walk +
    parallels tallies, provenance, and the degradation guard. The future ``motifs:meta`` stage —
    reads everything it aggregates from disk (indexes, sidecars, crosswalk/parallels JSON)."""
    counts, sources = _meta_counts_sources(config)
    links = load_json_optional(store.crosswalk_path()) or {}
    par_counts = (load_json_optional(store.parallels_path()) or {}).get("counts", {})
    enrichment_agg = _aggregate_enrichment()
    meta = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "counts": counts,
        "enrichment": enrichment_agg,  # per-source enrichment counts (what was added)
        "crosswalk": {
            "atu_to_tmi": len(links["atu_to_tmi"]),
            "tmi_to_atu": len(links["tmi_to_atu"]),
            "berezkin_to_atu": len(links["berezkin_to_atu"]),
            "atu_to_berezkin": len(links["atu_to_berezkin"]),
            "berezkin_to_tmi": len(links["berezkin_to_tmi"]),
            "tmi_to_berezkin": len(links["tmi_to_berezkin"]),
            "linked_tmi_count": links["linked_tmi_count"],
        },
        "parallels": par_counts,  # heuristic look-alikes with no recorded link
        "sources": sources,
    }
    # Degradation guard: load the prior meta, carry forward the high-water marks + flags, and flag any
    # metric now below its mark. Written into meta so it is durable and self-clearing across builds.
    meta["highwater"], meta["flags"], meta["fetch_outcomes"] = _degradation_check(
        _flat_metrics(counts, meta["crosswalk"]), enrichment_agg, store.load_meta(), meta["built_at"])
    if meta["flags"]:
        logger.warning("motif build: %d yield-drop flag(s) raised — see meta.flags", len(meta["flags"]))
    save_json(store.meta_path(), meta)


def build_motifs(*, force: bool = False) -> None:
    """Build the whole motif database in one pass, re-parsing/regenerating from the raw cache —
    the wholesale re-fetch helper behind ``scripts/fetch_motifs_raw.py``. The incremental pipeline
    path is the atomised ``motifs:*`` stages (which call the same ``_build_*`` helpers per-stage);
    this is the one-shot equivalent, not a driver node, so it stamps no fp gate.

    Missing raw files are fetched on demand; ``force`` additionally re-fetches everything cached.
    """
    config = _load_config()
    store.motifs_dir().mkdir(parents=True, exist_ok=True)

    sources: dict[str, dict] = {}
    counts: dict[str, int] = {}
    logger.info("=== Building the motif database: 3 indexes (Berezkin, TMI, ATU) + cross-walk ===")

    # Build the three source indexes — each writes its JSON + enrichment sidecar; crosswalk/parallels
    # then reload them via motifs.derive. These are the future motifs:source:* stages.
    for build_source in (_build_berezkin, _build_tmi, _build_atu):
        r = build_source(config, force=force)
        counts.update(r["counts"])
        sources.update(r["sources"])

    links = _build_crosswalk()
    par_counts = _build_parallels(links)
    _build_semantic()
    _build_meta(config)
    store.clear_cache()

    _log_summary(counts, links, par_counts)


def _edge_set(fwd: dict) -> set:
    """Undirected edges (frozenset id-pairs) of a ``{a: [b]}`` cross-walk map."""
    return {frozenset((a, b)) for a, bs in (fwd or {}).items() for b in bs}


def _log_summary(counts: dict, links: dict, par_counts: dict) -> None:
    """Final summary: confirmed cross-index links per pair (union of every
    relation, deduplicated) and the grand total, plus the suggestion layers."""
    at = (_edge_set(links.get("atu_to_tmi")) | _edge_set(links.get("atu_to_tmi_defining"))
          | _edge_set(links.get("atu_to_tmi_note")) | _edge_set(links.get("atu_to_tmi_summary")))
    ba = _edge_set(links.get("berezkin_to_atu"))
    bt = _edge_set(links.get("berezkin_to_tmi"))
    # fold the inferred edges into their pair (dedup the bidirectional entries)
    inf = {"at": 0, "ba": 0, "bt": 0}
    seen: set = set()
    for side, byid in (links.get("inferred") or {}).items():
        for mid, lst in byid.items():
            for e in lst:
                key = frozenset(((side, mid), (e["index"], e["id"])))
                if key in seen:
                    continue
                seen.add(key)
                pair = frozenset((side, e["index"]))
                edge = frozenset((mid, e["id"]))
                if pair == frozenset(("atu", "tmi")):
                    at.add(edge); inf["at"] += 1
                elif pair == frozenset(("berezkin", "atu")):
                    ba.add(edge); inf["ba"] += 1
                else:
                    bt.add(edge); inf["bt"] += 1
    grand = len(at) + len(ba) + len(bt)
    inferred_total = inf["at"] + inf["ba"] + inf["bt"]
    lex_a = sum(par_counts.get(f"{k}_A", 0) for k in ("atu_tmi", "berezkin_tmi", "berezkin_atu"))
    lex_b = sum(par_counts.get(f"{k}_B", 0) for k in ("atu_tmi", "berezkin_tmi", "berezkin_atu"))
    lex_near = sum(par_counts.get(f"{k}_near", 0) for k in ("atu_tmi", "berezkin_tmi", "berezkin_atu"))
    triangles = par_counts.get("triangles", 0)
    sem = store.load_semantic_parallels().get("counts", {})
    reasoned_pairs = {frozenset((a, b))
                      for g in reasoned_parallels.GROUPS
                      for a, b in itertools.combinations(g["members"], 2) if a[0] != b[0]}

    logger.info("=== SUMMARY: motif database built ===")
    logger.info("  indexes: %s", ", ".join(f"{k}={v}" for k, v in counts.items()) or "none")
    logger.info("  confirmed cross-index links (union per pair, incl. %d inferred):", inferred_total)
    logger.info("      ATU <-> TMI      %5d  (+%d inferred)", len(at), inf["at"])
    logger.info("      Berezkin <-> ATU %5d  (+%d inferred)", len(ba), inf["ba"])
    logger.info("      Berezkin <-> TMI %5d  (+%d inferred)", len(bt), inf["bt"])
    logger.info("      TOTAL confirmed  %5d", grand)
    logger.info("  hypothesis / suggestion layers (NOT confirmed, shown apart on the page):")
    logger.info("      reasoned parallels (curated) : %d groups / %d pairs",
                len(reasoned_parallels.GROUPS), len(reasoned_pairs))
    logger.info("      lexical parallels (heuristic): %d tier-A (%d near-identical) + %d tier-B, %d three-way",
                lex_a, lex_near, lex_b, triangles)
    if sem:
        logger.info("      semantic parallels (BGE-M3)  : %d pairs (%d new beyond lexical) [precomputed]",
                    sem.get("pairs", 0), sem.get("novel_only", 0))
    else:
        logger.info("      semantic parallels (BGE-M3)  : none — run scripts/build_semantic_parallels.py")
