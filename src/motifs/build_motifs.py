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
from .sources import berezkin, trilogy

logger = logging.getLogger(__name__)


def _load_config() -> dict:
    config_file = settings.config_dir / "motifs.json"
    if not config_file.exists():
        raise FileNotFoundError(f"Motifs config not found: {config_file}")
    return json.loads(config_file.read_text(encoding="utf-8"))


def build_motifs(*, force: bool = False) -> None:
    """Build the motif database, always re-parsing/regenerating from the raw cache.

    Missing raw files are fetched on demand; ``force`` additionally re-fetches
    everything that is already cached.
    """
    config = _load_config()
    store.motifs_dir().mkdir(parents=True, exist_ok=True)

    sources: dict[str, dict] = {}
    counts: dict[str, int] = {}

    # --- Berezkin (areal catalogue) ---
    berezkin_motifs: list[dict] = []
    bz_cfg = config.get("berezkin", {})
    if bz_cfg.get("enabled", True):
        berezkin_data = berezkin.build(bz_cfg, force=force)
        save_json(store.index_path("berezkin"), berezkin_data)
        berezkin_motifs = berezkin_data["motifs"]
        counts["berezkin"] = len(berezkin_motifs)
        sources["berezkin"] = {"homepage": bz_cfg.get("homepage", ""), "attribution": bz_cfg.get("attribution", "")}

    # --- Trilogy (TMI + ATU) ---
    tmi_ids: set[str] = set()
    atu_ids: set[str] = set()
    atu_seq: dict[str, list[str]] = {}
    tr_cfg = config.get("trilogy", {})
    if tr_cfg.get("enabled", True):
        trilogy_data = trilogy.build(tr_cfg, force=force)
        save_json(store.index_path("tmi"), trilogy_data["tmi"])
        save_json(store.index_path("atu"), trilogy_data["atu"])
        counts["tmi"] = len(trilogy_data["tmi"]["motifs"])
        counts["atu"] = len(trilogy_data["atu"]["types"])
        tmi_ids = {m["id"] for m in trilogy_data["tmi"]["motifs"]}
        atu_ids = {t["id"] for t in trilogy_data["atu"]["types"]}
        atu_seq = trilogy_data["atu_seq"]
        sources["trilogy"] = {"homepage": tr_cfg.get("homepage", ""), "attribution": tr_cfg.get("attribution", "")}

    # --- Cross-walk (ATU <-> TMI, Berezkin -> ATU) ---
    links = crosswalk.build(atu_seq, tmi_ids, berezkin_motifs, atu_ids)
    save_json(store.crosswalk_path(), links)

    meta = {
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "counts": counts,
        "crosswalk": {
            "atu_to_tmi": len(links["atu_to_tmi"]),
            "tmi_to_atu": len(links["tmi_to_atu"]),
            "berezkin_to_atu": len(links["berezkin_to_atu"]),
            "atu_to_berezkin": len(links["atu_to_berezkin"]),
            "linked_tmi_count": links["linked_tmi_count"],
        },
        "sources": sources,
    }
    save_json(store.meta_path(), meta)
    store.clear_cache()

    logger.info(
        "Motif database built: %s motifs/types, %d ATU->TMI links",
        ", ".join(f"{k}={v}" for k, v in counts.items()) or "none",
        len(links["atu_to_tmi"]),
    )
