import json
import logging
from pathlib import Path
from typing import Any, NamedTuple

import numpy as np

from corpus.utils import UNASSIGNED
from embeddings import chroma_manager
from settings import settings

logger = logging.getLogger(__name__)


def _attach_tradition(records: list[dict[str, Any]]) -> None:
    """Join each chunk's tradition from the catalog by `document_id` (B1: tradition is no
    longer on the chunk). The projection build reads `item["tradition"]` for its residual /
    distribution / colour groupings, so it is resolved here once, not stored on the vector."""
    catalog = settings.corpus_dir / "corpus.json"
    id_to_tradition: dict[str, str] = {}
    if catalog.exists():
        try:
            for row in json.loads(catalog.read_text(encoding="utf-8")):
                if row.get("document_id"):
                    id_to_tradition[row["document_id"]] = row.get("tradition", UNASSIGNED)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Could not read catalog for tradition join: %s", exc)
    for record in records:
        record["tradition"] = id_to_tradition.get(record.get("id"), UNASSIGNED)


class ModelData(NamedTuple):
    model_name: str
    data: list[dict[str, Any]]
    embeddings: np.ndarray
    output_dir: Path


def load_model_data(key: str) -> ModelData | None:
    output_dir = settings.projections_dir / key
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading data for variant: {key}...")
    data, embeddings = chroma_manager.get_collection(key).load_data()

    if not data:
        logger.warning(f"No data found for variant '{key}'")
        return None

    _attach_tradition(data)  # B1: resolve tradition from document_id for the projections
    logger.info(f"Chunks loaded: {len(data)}")
    return ModelData(model_name=key, data=data, embeddings=embeddings, output_dir=output_dir)
