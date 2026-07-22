"""Where one document's graphs live on disk.

The directory is keyed by the document's stable ``document_id`` (D1) and derived here — by
both the build (`build_graphs`) and the serve layer (`server.services.graphs`) — so the two
can never drift (they used to each re-derive it from the title, a latent divergence) and a
rename never moves the dir. The id is sanitised and the result confined under ``graphs_dir``,
so a hostile serve-time id like ``../../etc`` can neither escape the tree nor read outside it.
"""

from pathlib import Path

from corpus.utils import normalize_catalog_id, sanitize_filename
from settings import settings

# The three graph JSONs a document's directory holds.
GRAPH_TYPES = ("beings", "realms", "ages")


def graph_dir(document_id: str) -> Path:
    """The directory holding ``document_id``'s graph JSONs, or raise ``ValueError`` for an id
    that sanitises to nothing or would escape ``graphs_dir`` (the traversal guard)."""
    root = Path(settings.graphs_dir).resolve()
    name = sanitize_filename(normalize_catalog_id(document_id))
    if not name:
        raise ValueError(f"invalid graph id: {document_id!r}")
    path = (root / name).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"invalid graph id: {document_id!r}")
    return path
