"""``build_pipeline()`` — the one registry. Constructs every stage and wires each to its
upstream by held reference, so ``inputs()`` returns real objects and the driver's topological
sort reproduces the historical order: Corpus → Embeddings → Projections → Graphs → Motifs.

Fan-out is a plain loop over config: one embeddings + one projections stage per model in
``models.json``. Adding a model here makes it appear in status/build/clean for free.
"""

from __future__ import annotations

from model_registry import embedding_variants
from settings import settings

from .stage import Stage
from .stages import CorpusStage, EmbeddingsStage, GraphsStage, ProjectionsStage, motifs_stages
from .stores import ChromaStore, FileStore


def build_pipeline() -> list[Stage]:
    corpus = CorpusStage()
    chroma = ChromaStore()
    proj_store = FileStore(settings.projections_dir)

    emb = {variant: EmbeddingsStage(variant, corpus, chroma) for variant in embedding_variants()}

    # Declaration order is the topological tie-break, so it must mirror the historical order.
    stages: list[Stage] = [corpus, *emb.values()]
    stages += [ProjectionsStage(model, emb[model], proj_store) for model in emb]
    stages += [GraphsStage(corpus), *motifs_stages()]
    return stages
