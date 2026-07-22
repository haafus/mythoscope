"""Corpus serve layer (Part 1 §5 steps 4–5).

Two projections over the committed sources of truth: the **region → tradition tree**
(`config/traditions.json`, served as-is — §2.9) and the **documents** (the built catalog,
trimmed to the tradition reference + per-doc fields — no region/colour, which the front
resolves from the tree). Text is fetched by `document_id`. Nothing here writes a colour or
denormalizes a region onto a record (B1/§2.6).
"""

import json
import logging
from pathlib import Path

from corpus.traditions_config import flat_traditions, load_traditions_tree
from settings import settings

logger = logging.getLogger(__name__)

# Per-document fields the /documents list exposes (the tradition is the only reference;
# region + colour are resolved on the front from the tree — §2.10).
_DOCUMENT_FIELDS = (
    "document_id", "title", "tradition", "url", "source",
    "description", "dating", "word_count", "sentence_count", "char_count",
)


def _load_catalog() -> list[dict]:
    path = settings.corpus_dir / "corpus.json"
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_traditions_tree() -> dict:
    """The region → tradition tree, served straight from the config (§2.9). Empty on a
    missing/broken config rather than 500 (the front degrades to no grouping)."""
    try:
        return load_traditions_tree(settings.config_dir)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Could not read traditions config: %s", exc)
        return {}


def get_documents() -> list[dict]:
    """The documents list: the tradition reference + per-doc fields only (no region/colour).
    Sorted by region (via the tree) → tradition → title so the browser's grouping is stable."""
    tree = get_traditions_tree()
    trad_region = flat_traditions(tree)
    documents = [{k: row[k] for k in _DOCUMENT_FIELDS if k in row} for row in _load_catalog()]
    documents.sort(key=lambda d: (
        trad_region.get(d.get("tradition", ""), "~"),  # unknown traditions sort last
        d.get("tradition", ""),
        d.get("title", ""),
    ))
    return documents


def get_document_text(document_id: str) -> str | None:
    """The raw text of one document, addressed by `document_id` (§3). Confined under
    corpus_dir (path traversal guard); None when the id or its file is unknown."""
    root = Path(settings.corpus_dir).resolve()
    for row in _load_catalog():
        if row.get("document_id") == document_id and row.get("path"):
            target = (root / row["path"]).resolve()
            if not target.is_relative_to(root) or not target.exists():
                return None
            return target.read_text(encoding="utf-8")
    return None


def document_ids_for_tradition(tradition: str) -> set[str]:
    """The document_ids of one tradition — the set the cross-tradition search excludes
    (`where document_id $nin`, §5 step 4), since tradition is no longer on the chunk."""
    return {
        row["document_id"]
        for row in _load_catalog()
        if row.get("tradition") == tradition and row.get("document_id")
    }


def tradition_of_document(document_id: str) -> str | None:
    for row in _load_catalog():
        if row.get("document_id") == document_id:
            return row.get("tradition")
    return None
