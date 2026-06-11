import csv
import io
import json
import re
import zipfile
from pathlib import Path

from ui_server.config import paths

CATALOG_SOURCES = {
    "corpus": paths.corpus_dir,
    "chunked": paths.corpus_chunked_dir,
}


def to_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def sanitize_path_part(value: str) -> str:
    value = (value or "").replace("/", "_").replace(" ", "_")
    return re.sub(r'[\\/*?:"<>|]', "_", value).strip()


def source_root(source: str = "corpus") -> Path:
    return CATALOG_SOURCES.get(source, paths.corpus_dir)


def get_catalog_documents(source: str = "corpus") -> list[dict]:
    root = source_root(source)
    metadata_path = root / "corpus_metadata.json"
    catalog_path = root / "corpus_catalog.csv"

    catalog_by_key = {}
    if catalog_path.exists():
        with catalog_path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                key = (
                    row.get("id", ""),
                    row.get("major_tradition", ""),
                    row.get("tradition", ""),
                )
                catalog_by_key[key] = row

    metadata_rows = []
    if metadata_path.exists():
        with metadata_path.open("r", encoding="utf-8") as handle:
            metadata_rows = json.load(handle)

    source_rows = metadata_rows or list(catalog_by_key.values()) or scan_document_rows(root)
    documents = []
    traditions_info = load_traditions_info(source)

    for row in source_rows:
        key = (
            row.get("id", ""),
            row.get("major_tradition", ""),
            row.get("tradition", ""),
        )
        catalog_row = catalog_by_key.get(key, {})
        tradition_info = traditions_info.get(row.get("tradition", ""), {})
        documents.append(
            {
                "id": row.get("id", ""),
                "major_tradition": row.get("major_tradition", ""),
                "tradition": row.get("tradition", ""),
                "language": row.get("language", ""),
                "type": row.get("type", ""),
                "url": row.get("url", ""),
                "word_count": to_int(row.get("word_count", catalog_row.get("word_count"))),
                "sentence_count": to_int(row.get("sentence_count", catalog_row.get("sentence_count"))),
                "char_count": to_int(row.get("char_count")),
                "color": row.get("color") or catalog_row.get("color") or tradition_info.get("color") or "#6b7280",
                "description": catalog_row.get("description")
                or row.get("description")
                or tradition_info.get("description", ""),
                "source": source,
            }
        )

    documents.sort(
        key=lambda item: (
            item.get("major_tradition", ""),
            item.get("tradition", ""),
            item.get("id", ""),
        )
    )
    return documents


def scan_document_rows(root: Path) -> list[dict]:
    rows: list[dict] = []
    if not root.exists():
        return rows

    for file_path in root.glob("*/*/*/*.txt"):
        try:
            major, tradition, title_dir, _ = file_path.relative_to(root).parts
        except ValueError:
            continue

        text = file_path.read_text(encoding="utf-8", errors="ignore")
        title = title_dir.replace("_", " ")
        rows.append(
            {
                "id": title,
                "major_tradition": major.replace("_", " "),
                "tradition": tradition.replace("_", " "),
                "path": str(file_path.relative_to(root)),
                "char_count": len(text),
                "word_count": len(re.findall(r"\S+", text)),
                "sentence_count": len(re.findall(r"[.!?]+", text)),
            }
        )

    return rows


def resolve_document_path(
    doc_id: str, major_tradition: str, tradition: str, source: str = "corpus"
) -> tuple[Path, Path | None, str]:
    corpus_root = source_root(source).resolve()
    major_path = sanitize_path_part(major_tradition)
    tradition_path = sanitize_path_part(tradition)
    title_path = sanitize_path_part(doc_id)
    file_path = (corpus_root / major_path / tradition_path / title_path / f"{title_path}.txt").resolve()

    try:
        file_path.relative_to(corpus_root)
    except ValueError:
        return corpus_root, None, title_path

    if source == "chunked" and not file_path.exists():
        file_path = next(
            (
                candidate.resolve()
                for candidate in corpus_root.glob("*/*/*/*.txt")
                if candidate.stem.replace("_", " ").casefold() == doc_id.casefold()
                and candidate.parent.name.replace("_", " ").casefold() == doc_id.casefold()
                and candidate.parents[1].name.replace("_", " ").casefold() == tradition.casefold()
                and candidate.parents[2].name.replace("_", " ").casefold() == major_tradition.casefold()
            ),
            file_path,
        )

    return corpus_root, file_path, title_path


def read_document(doc_id: str, major_tradition: str, tradition: str, source: str = "corpus") -> tuple[str, str]:
    _, file_path, title_path = resolve_document_path(doc_id, major_tradition, tradition, source)
    if not file_path:
        raise PermissionError("Access denied")
    if not file_path.exists():
        raise FileNotFoundError(str(file_path))

    return file_path.read_text(encoding="utf-8"), title_path


def build_corpus_archive() -> bytes:
    documents = get_catalog_documents()
    archive_buffer = io.BytesIO()

    with zipfile.ZipFile(archive_buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for doc in documents:
            _, file_path, title_path = resolve_document_path(
                doc.get("id", ""),
                doc.get("major_tradition", ""),
                doc.get("tradition", ""),
                doc.get("source", "corpus"),
            )

            if not file_path or not file_path.exists():
                continue

            archive_name = (
                Path(sanitize_path_part(doc.get("major_tradition", "Unknown")))
                / sanitize_path_part(doc.get("tradition", "Unknown"))
                / f"{title_path}.txt"
            ).as_posix()
            archive.write(file_path, archive_name)

    return archive_buffer.getvalue()


def load_traditions_info(source: str = "chunked") -> dict:
    path = source_root(source) / "traditions_info.json"
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}

    return {}


def get_traditions_info() -> dict:
    for path in (
        paths.corpus_chunked_dir / "traditions_info.json",
        paths.corpus_dir / "traditions_info.json",
    ):
        if path.exists():
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            return data if isinstance(data, dict) else {}

    return {}
