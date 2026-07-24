"""The projections stage — one per embeddings model (a global reduce over all its points).

Singleton per model: key = the model. fp-native already via the ``projections/<model>/.input-fp``
sidecar = ``_fingerprint_from_metas`` over that model's chunk metadata (so an embeddings change
flips it). The whole model dir is one ``FileStore`` id for L2 GC when a model is dropped.
"""

from __future__ import annotations

import shutil

from embeddings import chroma_manager
from projections import PROJECTION_METHODS
from projections.build_projections import _fingerprint_from_metas, build_projections
from settings import settings

from ..stage import Stage, Store
from .embeddings import EmbeddingsStage


class ProjectionsStage(Stage):
    def __init__(self, model: str, embeddings: EmbeddingsStage, store: Store):
        self.model = model
        self.name = f"projections:{model}"
        self.store = store
        self.id = model  # its subdir in the projections FileStore
        self._embeddings = embeddings

    def inputs(self) -> list[Stage]:
        return [self._embeddings]

    def desired(self) -> dict[str, str]:
        """The reduce's input identity, from this model's chunk metadata (vectors not loaded)."""
        return {self.model: _fingerprint_from_metas(self._metas())}

    def actual(self) -> dict[str, str]:
        """Built iff the model dir has its ``.input-fp`` AND every plot JSON (the completeness
        check ``build_projections`` itself uses)."""
        d = settings.projections_dir / self.model
        fp_path = d / ".input-fp"
        if fp_path.exists() and all((d / f"{m['key']}.json").exists() for m in PROJECTION_METHODS):
            return {self.model: fp_path.read_text(encoding="utf-8").strip()}
        return {}

    def build(self, keys: set[str]) -> None:
        build_projections(model_name=self.model, force=True)

    def delete(self, keys: set[str]) -> None:
        shutil.rmtree(settings.projections_dir / self.model, ignore_errors=True)

    def _metas(self) -> list[dict]:
        try:
            col = chroma_manager.get_collection(self.model)
        except Exception:
            return []  # no collection → nothing to reduce
        return col.get(include=["metadatas"]).get("metadatas") or []
