"""The corpus stage — one artifact (a cleaned ``.txt`` + catalog row) per document.

Key = ``document_id``. Its own staleness turns on the **input** fingerprint ``source_fp``
(raw + trim + clean_version, decided offline). What it exposes *downstream* is the **output**
``fingerprint`` (blake2b of the cleaned text) that embeddings/graphs fold — see
:meth:`CorpusStage.doc_fingerprints`.
"""

from __future__ import annotations

import json
from pathlib import Path

from corpus.builder import build_corpus
from corpus.downloader import load_download_list
from corpus.fingerprint import source_fingerprint
from corpus.locator import corpus_raw_path, document_id
from json_utils import save_json
from settings import settings

from ..stage import Stage

_UNFETCHED = "unfetched"  # a document whose raw is not yet in the archive → build acquires it


class CorpusStage(Stage):
    name = "corpus"
    store = None  # per-document: owns its whole tree, relies on the per-key diff (level 1)
    sampleable = True  # `--sample N` caps this stage to N docs; embeddings/graphs follow via their fps

    def inputs(self) -> list[Stage]:
        return []

    def desired(self) -> dict[str, str]:
        """Per config entry, the offline input fingerprint of its pinned raw (or a sentinel
        when the raw has never been fetched — that document is simply ``missing`` until built)."""
        raw_root = Path(settings.corpus_dir) / "raw"
        out: dict[str, str] = {}
        for item in load_download_list():
            url = item.get("url", "")
            raw = corpus_raw_path(raw_root, url)
            out[document_id(url)] = (
                source_fingerprint(raw.read_bytes(), item.get("content_start"), item.get("content_end"))
                if raw.exists()
                else _UNFETCHED
            )
        return out

    def actual(self) -> dict[str, str]:
        """Built documents: a row whose ``.txt`` exists and whose ``source_fp`` was recorded."""
        root = Path(settings.corpus_dir).resolve()
        out: dict[str, str] = {}
        for row in self._catalog():
            did, fp = row.get("document_id"), row.get("source_fp")
            if did and fp and (root / row.get("path", "")).exists():
                out[did] = fp
        return out

    def build(self, keys: set[str]) -> None:
        build_corpus(rebuild=set(keys))

    def delete(self, keys: set[str]) -> None:
        """Level-1: drop these documents' ``.txt`` and catalog rows (orphans of a config edit)."""
        root = Path(settings.corpus_dir).resolve()
        kept = []
        for row in self._catalog():
            if row.get("document_id") in keys:
                (root / row.get("path", "")).unlink(missing_ok=True)
            else:
                kept.append(row)
        save_json(settings.corpus_dir / "corpus.json", kept, indent=2)

    def doc_fingerprints(self) -> dict[str, str]:
        """``{document_id: output content fingerprint}`` — what embeddings/graphs fold as *their*
        input fp. Read from the catalog after this stage has built (topological order)."""
        root = Path(settings.corpus_dir).resolve()
        return {
            row["document_id"]: row["fingerprint"]
            for row in self._catalog()
            if row.get("document_id") and row.get("fingerprint") and (root / row.get("path", "")).exists()
        }

    @staticmethod
    def _catalog() -> list[dict]:
        path = settings.corpus_dir / "corpus.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
