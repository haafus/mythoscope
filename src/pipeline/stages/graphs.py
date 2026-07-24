"""The graphs stage — one knowledge-graph set per document. Key = ``document_id``.

fp-native already: each book carries ``graphs/<document_id>/.fp`` = the doc content fingerprint
folded with the prompts, LLM and limits. Per-document (``store = None``) — its orphans (a
removed book) are ordinary level-1 keys. The internal per-chunk LLM cache
(``extraction_cache.jsonl``) is a resumable tier, not a driver key, so a rebuild reassembles
from it without the network.
"""

from __future__ import annotations

import json
import shutil

from graphs.build_graphs import _graph_fingerprint, build_graphs
from graphs.store import GRAPH_TYPES, graph_dir
from settings import settings

from ..stage import Stage
from .corpus import CorpusStage


class GraphsStage(Stage):
    name = "graphs"
    store = None  # per-document

    def __init__(self, corpus: CorpusStage):
        self._corpus = corpus

    def inputs(self) -> list[Stage]:
        return [self._corpus]

    def desired(self) -> dict[str, str]:
        prompts = self._prompts()
        cfg = settings.graphs
        return {
            doc: _graph_fingerprint(content_fp, prompts, cfg)
            for doc, content_fp in self._corpus.doc_fingerprints().items()
        }

    def actual(self) -> dict[str, str]:
        """Built books: a ``graphs/<document_id>/`` with its ``.fp`` and all three graphs.

        The directory name is the document_id (blake2b hex → sanitize-stable), matching
        ``graph_dir``; so a book removed from the corpus surfaces here but not in ``desired``."""
        root = settings.graphs_dir
        out: dict[str, str] = {}
        if not root.exists():
            return out
        for d in root.iterdir():
            fp_path = d / ".fp"
            if d.is_dir() and fp_path.exists() and all((d / f"{n}.json").exists() for n in GRAPH_TYPES):
                out[d.name] = fp_path.read_text(encoding="utf-8").strip()
        return out

    def build(self, keys: set[str]) -> None:
        build_graphs(rebuild=set(keys))

    def delete(self, keys: set[str]) -> None:
        """Level-1: drop these books' whole graph directories."""
        for did in keys:
            shutil.rmtree(graph_dir(did), ignore_errors=True)

    @staticmethod
    def _prompts() -> dict:
        return json.loads((settings.config_dir / "prompts.json").read_text(encoding="utf-8"))
