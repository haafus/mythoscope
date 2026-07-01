"""Orchestrate the motif-database build step.

Reads ``config/motifs.json``, scrapes/downloads each enabled source into the
resumable raw cache, parses them into per-index JSON, derives the cross-walk and
writes a manifest. Re-parses and regenerates every time it runs, reusing the raw
cache (downloading only what's missing); ``force`` re-fetches every raw source.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from json_utils import save_json
from settings import settings

from . import crosswalk, store
from .sources import berezkin, bibliography, mapsofmyths, trilogy

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
    logger.info("=== Building the motif database: 3 indexes + cross-walk (Berezkin, TMI, ATU) ===")

    # --- mapsofmyths enrichment refresh (English text, taxonomy, TMI/ATU ids,
    #     traditions) — credential-gated; a no-op skips the enrichment. ---
    mm = enrichment["mapsofmyths"] = mapsofmyths.refresh(force=force)

    # --- [1/3] Berezkin (areal catalogue; folds in the mapsofmyths enrichment) ---
    berezkin_motifs: list[dict] = []
    bz_cfg = config.get("berezkin", {})
    if bz_cfg.get("enabled", True):
        home = bz_cfg.get("homepage", "areasofmyths.com")
        logger.info("[1/4] Berezkin areal catalogue — source: %s (%s + per-motif detail pages for definitions)",
                    home, bz_cfg.get("index_page", "index page"))
        berezkin_data = berezkin.build(bz_cfg, force=force)
        save_json(store.index_path("berezkin"), berezkin_data)
        berezkin_motifs = berezkin_data["motifs"]
        counts["berezkin"] = len(berezkin_motifs)
        sources["berezkin"] = {"homepage": home, "attribution": bz_cfg.get("attribution", "")}
        logger.info("      %d motifs across %d chapters; %d Russian definitions from detail pages",
                    len(berezkin_motifs), len([c for c in berezkin_data.get("chapters", {})]),
                    _applied(berezkin_motifs, lambda m: m.get("definition") and not m.get("definition_rus")))
        if mm.get("skipped"):
            logger.info("      enrichment from mapsofmyths.com SKIPPED (%s) — Russian names/definitions only", mm["skipped"])
        else:
            logger.info("      enriched from mapsofmyths.com: English name ×%d, English definition ×%d, "
                        "type/group ×%d, direct TMI links ×%d, tradition sets ×%d; tradition catalogue: %d entries",
                        _applied(berezkin_motifs, lambda m: m.get("name_rus")),
                        _applied(berezkin_motifs, lambda m: m.get("definition_rus")),
                        _applied(berezkin_motifs, lambda m: m.get("motif_type")),
                        _applied(berezkin_motifs, lambda m: m.get("tmi_refs")),
                        _applied(berezkin_motifs, lambda m: m.get("traditions")),
                        len(berezkin_data.get("traditions", {})))

    # --- [2/3] TMI + [3/3] ATU (from the j-hagedorn/trilogy dataset) ---
    tmi_ids: set[str] = set()
    atu_ids: set[str] = set()
    atu_seq: dict[str, list[str]] = {}
    tr_cfg = config.get("trilogy", {})
    if tr_cfg.get("enabled", True):
        files = tr_cfg.get("files", {})
        # Header before the build so any TMI parse warnings appear under it, not
        # ahead of it (mirrors the [1/3] Berezkin step).
        logger.info("[2/4] Thompson Motif-Index (TMI) — source: %s (%s)",
                    tr_cfg.get("homepage", "trilogy"), files.get("tmi", "tmi.csv"))
        trilogy_data = trilogy.build(tr_cfg, force=force)
        save_json(store.index_path("tmi"), trilogy_data["tmi"])
        save_json(store.index_path("atu"), trilogy_data["atu"])
        tmi_motifs = trilogy_data["tmi"]["motifs"]
        atu_types = trilogy_data["atu"]["types"]
        counts["tmi"] = len(tmi_motifs)
        counts["atu"] = len(atu_types)
        tmi_ids = {m["id"] for m in tmi_motifs}
        atu_ids = {t["id"] for t in atu_types}
        atu_seq = trilogy_data["atu_seq"]
        sources["trilogy"] = {"homepage": tr_cfg.get("homepage", ""), "attribution": tr_cfg.get("attribution", "")}
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
        logger.info("[3/4] Aarne-Thompson-Uther (ATU) tale types — source: %s (%s)",
                    tr_cfg.get("homepage", "trilogy"),
                    ", ".join(v for k, v in files.items() if k != "tmi") or "atu CSVs")
        logger.info("      %d tale types", len(atu_types))

    # --- [4/4] Cross-walk (ATU <-> TMI via tale-type numbers, Berezkin -> ATU via
    #     title refs, Berezkin <-> TMI via curated Thompson ids) ---
    logger.info("[4/4] Cross-walk — deriving id links across the three indexes")
    links = crosswalk.build(atu_seq, tmi_ids, berezkin_motifs, atu_ids)
    save_json(store.crosswalk_path(), links)
    logger.info("      ATU<->TMI %d/%d, Berezkin<->ATU %d/%d, Berezkin<->TMI (direct) %d/%d "
                "(%d TMI motifs reachable from a tale type)",
                len(links["atu_to_tmi"]), len(links["tmi_to_atu"]),
                len(links["berezkin_to_atu"]), len(links["atu_to_berezkin"]),
                len(links["berezkin_to_tmi"]), len(links["tmi_to_berezkin"]), links["linked_tmi_count"])

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
        "sources": sources,
    }
    save_json(store.meta_path(), meta)
    store.clear_cache()

    logger.info("=== Motif database built: %s ===",
                ", ".join(f"{k}={v}" for k, v in counts.items()) or "none")
