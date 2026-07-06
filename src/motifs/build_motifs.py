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
from datetime import datetime, timezone

from json_utils import save_json
from settings import settings

from . import crosswalk, parallels, reasoned_parallels, store
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


def _load_config() -> dict:
    config_file = settings.config_dir / "motifs.json"
    if not config_file.exists():
        raise FileNotFoundError(f"Motifs config not found: {config_file}")
    return json.loads(config_file.read_text(encoding="utf-8"))


def _applied(records: list[dict], pred) -> int:
    """How many records satisfy ``pred`` — used for the per-step enrichment counts."""
    return sum(1 for r in records if pred(r))


def build_motifs(*, force: bool = False) -> None:
    """Build the motif database, always re-parsing/regenerating from the raw cache.

    Missing raw files are fetched on demand; ``force`` additionally re-fetches
    everything that is already cached.
    """
    config = _load_config()
    store.motifs_dir().mkdir(parents=True, exist_ok=True)

    sources: dict[str, dict] = {}
    counts: dict[str, int] = {}
    enrichment: dict[str, dict] = {}
    logger.info("=== Building the motif database: 3 indexes (Berezkin, TMI, ATU) + cross-walk ===")

    # --- [1/3] Berezkin (areal catalogue; folds in the mapsofmyths enrichment) ---
    berezkin_motifs: list[dict] = []
    mm: dict = {}
    bz_cfg = config.get("berezkin", {})
    if bz_cfg.get("enabled", True):
        home = bz_cfg.get("homepage", "areasofmyths.com")
        logger.info("[1/5] Berezkin areal catalogue — source: %s (%s + per-motif detail pages for definitions)",
                    home, bz_cfg.get("index_page", "index page"))
        # mapsofmyths enrichment refresh (English text, taxonomy, TMI/ATU ids,
        # traditions) — part of building the Berezkin index, so downloaded under
        # this step; credential-gated, a no-op skips the enrichment.
        mm = enrichment["mapsofmyths"] = mapsofmyths.refresh(force=force)
        berezkin_data = berezkin.build(bz_cfg, force=force)
        save_json(store.index_path("berezkin"), berezkin_data)
        berezkin_motifs = berezkin_data["motifs"]
        counts["berezkin"] = len(berezkin_motifs)
        sources["berezkin"] = {"homepage": home, "attribution": bz_cfg.get("attribution", "")}
        # Base scrape (areasofmyths.com), before any enrichment. "with a definition"
        # counts a definition from the detail page whether or not English later
        # replaced it (the original is kept as definition_rus).
        logger.info("      + base scrape (areasofmyths.com): %d motifs, %d chapters, %d with a definition",
                    len(berezkin_motifs), len(berezkin_data.get("chapters", {})),
                    _applied(berezkin_motifs, lambda m: m.get("definition") or m.get("definition_rus")))
        if mm.get("skipped"):
            logger.info("      + mapsofmyths.com enrichment SKIPPED (%s) — Russian names/definitions only", mm["skipped"])
        else:
            # Each line = how many of the 3488 motifs gained this from mapsofmyths.
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
            logger.info("          (+ shared name catalogue: %d traditions — each areal code → people name + region, resolves the sets above)",
                        len(berezkin_data.get("traditions", {})))

        # Bibliography (areasofmyths.com biblio.html) + citation → region/ethnos
        # linkage, resolved from the already-cached detail pages.
        enrichment["berezkin_bibliography"] = berezkin_bibliography.refresh(berezkin_motifs, force=force)
        bb = enrichment["berezkin_bibliography"]
        if bb.get("skipped"):
            logger.info("      + bibliography (areasofmyths.com) SKIPPED (%s)", bb["skipped"])
        else:
            logger.info("      + bibliography (areasofmyths.com): %d works; citations resolved %d/%d (%d%%), "
                        "ambiguous %d",
                        bb["works"], bb["resolved"], bb["citations"],
                        round(100 * bb["resolved"] / bb["citations"]) if bb["citations"] else 0,
                        bb["ambiguous"])

    # --- [2/3] TMI + [3/3] ATU (from the j-hagedorn/trilogy dataset) ---
    tmi_ids: set[str] = set()
    atu_ids: set[str] = set()
    tmi_motifs: list[dict] = []
    atu_types: list[dict] = []
    atu_seq: dict[str, list[str]] = {}
    atu_defining: dict[str, list[str]] = {}
    atu_aliases: dict[str, str] = {}
    tmi_notes: dict[str, list[str]] = {}
    atu_summaries: dict[str, str] = {}
    aath_to_atu: dict[str, list[str]] = {}
    tr_cfg = config.get("trilogy", {})
    if tr_cfg.get("enabled", True):
        files = tr_cfg.get("files", {})
        sources["trilogy"] = {"homepage": tr_cfg.get("homepage", ""), "attribution": tr_cfg.get("attribution", "")}

        # --- [2/5] TMI: header first, so its parse warnings sit under it. ---
        logger.info("[2/5] Thompson Motif-Index (TMI) — source: %s (%s)",
                    tr_cfg.get("homepage", "trilogy"), files.get("tmi", "tmi.csv"))
        mel_cfg = config.get("mellmann", {})
        mel_on = mel_cfg.get("enabled", False)
        tmi_index = trilogy.build_tmi(tr_cfg, force=force,
                                      divisions_config=mel_cfg if mel_on else None)
        if mel_on:
            sources["mellmann"] = {"homepage": mel_cfg.get("homepage", ""),
                                   "attribution": mel_cfg.get("attribution", "")}
            logger.info("      classification headings — source: Mellmann TMI_as_CSV → "
                        "%d divisions, %d sub-divisions",
                        len(tmi_index.get("divisions", [])), len(tmi_index.get("subdivisions", [])))
        save_json(store.index_path("tmi"), tmi_index)
        tmi_motifs = tmi_index["motifs"]
        counts["tmi"] = len(tmi_motifs)
        tmi_ids = {m["id"] for m in tmi_motifs}
        # Inline "Type N" citations in TMI notes → feed the (inverse) note cross-walk.
        tmi_notes = {m["id"]: m["atu_inline"] for m in tmi_motifs if m.get("atu_inline")}
        logger.info("      %d motifs; notes parsed → definition ×%d, cultures ×%d, ATU refs ×%d",
                    len(tmi_motifs),
                    _applied(tmi_motifs, lambda m: m.get("definition")),
                    _applied(tmi_motifs, lambda m: m.get("cultures")),
                    _applied(tmi_motifs, lambda m: m.get("atu_inline")))
        # TMI citation-key (folkmasa bibliography + curated), annotated with the
        # per-source usage counts from the just-built TMI notes.
        enrichment["bibliography"] = bibliography.refresh(tmi_motifs, force=force)
        bib = enrichment["bibliography"]
        logger.info("      citation key — source: %s + curated supplement: %d entries (%d with a book link)",
                    "folkmasa.org", bib.get("entries", 0), bib.get("linked", 0))

        # --- [3/5] ATU: header before the ATU parse, on par with the other steps. ---
        logger.info("[3/5] Aarne-Thompson-Uther (ATU) tale types — source: %s",
                    tr_cfg.get("homepage", "trilogy"))
        logger.info("      files: %s",
                    ", ".join(v for k, v in files.items() if k != "tmi") or "atu CSVs")
        atu_index, atu_seq = trilogy.build_atu(tr_cfg, force=force)
        # Multilingual names + Wikipedia links from Wikidata (open, best-effort).
        enrichment["atu_wikidata"] = atu_wikidata.refresh(atu_index["types"], force=force)
        # Example tales sourced straight from Ashliman's Folktexts (best-effort).
        enrichment["ashliman"] = ashliman.refresh(atu_index["types"], force=force)
        save_json(store.index_path("atu"), atu_index)
        atu_types = atu_index["types"]
        counts["atu"] = len(atu_types)
        atu_ids = {t["id"] for t in atu_types}
        atu_defining = {t["id"]: t["defining_motifs"] for t in atu_types if t.get("defining_motifs")}
        atu_aliases = atu_index.get("aliases", {})
        atu_summaries = {t["id"]: t["summary"] for t in atu_types if t.get("summary")}
        # AaTh tale-type number → ATU 2004 id(s), from the Wikidata concordance each
        # type carries; resolves the pre-2004 numbers TMI notes cite.
        for t in atu_types:
            for code in (t.get("concordances") or {}).get("AaTh", []):
                aath_to_atu.setdefault(code, [])
                if t["id"] not in aath_to_atu[code]:
                    aath_to_atu[code].append(t["id"])
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

    # --- [4/5] Cross-walk (ATU <-> TMI via tale-type numbers, Berezkin -> ATU via
    #     title refs, Berezkin <-> TMI via curated Thompson ids) ---
    logger.info("[4/5] Cross-walk — deriving id links across the three indexes")
    links = crosswalk.build(atu_seq, tmi_ids, berezkin_motifs, atu_ids, atu_defining,
                            atu_aliases, tmi_notes, aath_to_atu, atu_summaries)
    save_json(store.crosswalk_path(), links)
    logger.info("      ATU<->TMI %d/%d (+%d defining motifs → %d TMI; %d TMI motifs reachable from a tale type)",
                len(links["atu_to_tmi"]), len(links["tmi_to_atu"]),
                len(links["atu_to_tmi_defining"]), len(links["tmi_to_atu_defining"]),
                links["linked_tmi_count"])
    logger.info("      Berezkin<->ATU %d/%d",
                len(links["berezkin_to_atu"]), len(links["atu_to_berezkin"]))
    logger.info("      Berezkin<->TMI (direct) %d/%d",
                len(links["berezkin_to_tmi"]), len(links["tmi_to_berezkin"]))
    logger.info("      + inline relations (each stored both ways): TMI notes → %d ATU types, "
                "ATU summaries → %d TMI motifs",
                len(links["atu_to_tmi_note"]), len(links["tmi_to_atu_summary"]))
    logger.info("      + inferred (transitive closure via low-fan-out pivots): %d edges",
                links.get("inferred_count", 0))

    # --- [5/5] Textual parallels: a heuristic suggestion layer (lexical title +
    #     description matching) surfacing look-alike motifs with *no* recorded
    #     cross-walk link — hints for review, kept apart from the curated links. ---
    logger.info("[5/5] Textual parallels — lexical look-alikes with no recorded link")
    par = parallels.build(berezkin_motifs, tmi_motifs, atu_types, links)
    if par is None:
        logger.info("      SKIPPED (no TMI/ATU, or scikit-learn unavailable)")
        par_counts = {}
    else:
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

    # Semantic parallels (BGE-M3) are precomputed offline (scripts/build_semantic_parallels.py)
    # and shipped as a committed file; copy it into outputs so this build serves it.
    sem = store.copy_semantic_parallels()
    if sem is not None:
        logger.info("      + semantic parallels (BGE-M3): %d pairs — precomputed, committed file copied into outputs",
                    sem.get("counts", {}).get("pairs", 0))
    else:
        logger.info("      + semantic parallels (BGE-M3): none (run scripts/build_semantic_parallels.py)")

    meta = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "counts": counts,
        "enrichment": enrichment,  # per-source enrichment counts (what was added)
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
    save_json(store.meta_path(), meta)
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
