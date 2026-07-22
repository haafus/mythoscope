import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Generator

from .utils import UNASSIGNED, content_fingerprint, normalize_catalog_id

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CorpusFileInfo:
    _path: Path
    text_id: str
    major_tradition: str
    tradition: str
    url: str
    # The stable document identity (D1) from the catalog — the embeddings chunk anchor
    # and the single reference stored on each chunk after B1.
    document_id: str = ""
    # Per-doc content fingerprint (blake2b of the cleaned text) from the catalog; the
    # embeddings staleness gate folds it into each chunk's key (pipeline §4).
    fingerprint: str = ""

    @property
    def filename(self) -> str:
        return self._path.name

    def read_text(self) -> str:
        return self._path.read_text(encoding="utf-8")

    def content_fingerprint(self) -> str:
        """The stored doc fingerprint, or recomputed from disk for a pre-fingerprint
        catalog (older builds stored no `fingerprint`) so the gate still works."""
        return self.fingerprint or content_fingerprint(self.read_text().encode("utf-8"))


def iter_files(corpus_dir: Path) -> Generator[CorpusFileInfo, None, None]:
    metadata_file = corpus_dir / "corpus.json"

    if not metadata_file.exists():
        raise FileNotFoundError(
            f"{metadata_file} not found. Run 'mytho corpus build' first."
        )

    with open(metadata_file, encoding="utf-8") as f:
        items = json.load(f)

    for item in items:
        title = item.get("title")
        if not title:
            continue

        path = item.get("path")
        if not path:
            logger.warning("Skipping entry '%s': no path", title)
            continue

        txt_file = corpus_dir / path
        if not txt_file.exists():
            logger.warning("Skipping entry '%s': file not found at %s", title, txt_file)
            continue

        yield CorpusFileInfo(
            _path=txt_file,
            text_id=normalize_catalog_id(title),
            major_tradition=item.get("major_tradition", UNASSIGNED),
            tradition=item.get("tradition", UNASSIGNED),
            url=item.get("url", ""),
            document_id=item.get("document_id", ""),
            fingerprint=item.get("fingerprint", ""),
        )
