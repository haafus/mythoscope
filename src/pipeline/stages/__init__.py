"""Concrete stages — one adapter per build module, exposing the :class:`~pipeline.stage.Stage`
protocol over the existing builders. Wired together by ``build_pipeline()``."""

from .corpus import CorpusStage
from .embeddings import EmbeddingsStage
from .graphs import GraphsStage
from .motifs import motifs_stages
from .projections import ProjectionsStage

__all__ = ["CorpusStage", "EmbeddingsStage", "GraphsStage", "ProjectionsStage", "motifs_stages"]
