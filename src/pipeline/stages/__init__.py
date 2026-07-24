"""Concrete stages — one adapter per build module, exposing the :class:`~pipeline.stage.Stage`
protocol over the existing builders. Wired together by ``build_pipeline()``."""

from .corpus import CorpusStage
from .embeddings import EmbeddingsStage
from .graphs import GraphsStage

__all__ = ["CorpusStage", "EmbeddingsStage", "GraphsStage"]
