import io
import json
import logging
import zipfile
from pathlib import Path

from corpus.utils import read_traditions, sanitize_filename, text_path
from settings import settings

logger = logging.getLogger(__name__)


def get_catalog_documents() -> list[dict]:
    metadata_path = settings.corpus_dir / "corpus.json"
    if not metadata_path.exists():
        return []

    with metadata_path.open("r", encoding="utf-8") as handle:
        metadata_rows = json.load(handle)

    documents = []
    traditions_info = read_traditions(settings.corpus_dir)

    for row in metadata_rows:
        # A corpus row may reference a tradition missing from traditions.json (or lack
        # the key entirely); fall back to the default colour rather than 500 the whole
        # catalog (which also feeds /traditions and /archive).
        tradition = traditions_info.get(row.get("tradition", ""), {})
        documents.append({**row, "color": tradition.get("color", "#6b7280")})

    documents.sort(
        key=lambda item: (
            item.get("major_tradition", ""),
            item.get("tradition", ""),
            item.get("title", ""),
        )
    )

    return documents


def traditions_with_books() -> dict:
    """Tradition metadata (from traditions.json) with each tradition's book titles attached."""
    data = read_traditions(settings.corpus_dir)
    books_by_tradition: dict[str, list[str]] = {}
    for doc in get_catalog_documents():
        trad = doc.get("tradition", "")
        if trad:
            books_by_tradition.setdefault(trad, []).append(doc.get("title", ""))
    for trad, info in data.items():
        info["books"] = sorted(books_by_tradition.get(trad, []))
    return data


def build_corpus_archive() -> io.BytesIO:
    documents = get_catalog_documents()
    buf = io.BytesIO()

    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for doc in documents:
            file_path = text_path(
                settings.corpus_dir,
                doc.get("major_tradition", ""),
                doc.get("tradition", ""),
                doc.get("title", ""),
            )

            if not file_path.exists():
                continue

            archive_name = (
                Path(sanitize_filename(doc.get("major_tradition", "Unknown")))
                / sanitize_filename(doc.get("tradition", "Unknown"))
                / file_path.name
            ).as_posix()
            archive.write(file_path, archive_name)

    buf.seek(0)
    return buf
