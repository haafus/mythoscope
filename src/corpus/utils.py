from __future__ import annotations

import hashlib
import logging
import random
import re
import threading
import unicodedata
from pathlib import Path

import pymupdf
import trafilatura
from bs4 import BeautifulSoup

_color_lock = threading.Lock()
_used_colors: set[str] = set()
_tradition_colors: dict[str, str] = {}
logger = logging.getLogger(__name__)

PYMUPDF_AVAILABLE = True


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[\\/*?:"<>|]', "_", name).strip()
    name = name.replace("..", "_")
    return name


def md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def _decode_bytes(content: bytes) -> str:
    encodings_to_try = ["utf-8", "windows-1251", "iso-8859-1", "cp1251", "gb2312"]
    for enc in encodings_to_try:
        try:
            return content.decode(enc)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


def html_to_text(
    html_content: bytes, include_comments: bool = False, include_tables: bool = True, target_language: str | None = None
) -> str:
    if not html_content:
        return ""

    try:
        text = trafilatura.extract(
            html_content,
            include_comments=include_comments,
            include_tables=include_tables,
            target_language=target_language,
            favor_precision=True,
        )
        if text:
            logger.debug("HTML processed with Trafilatura")
            return normalize_text(text)
    except Exception as e:
        logger.warning(f"Trafilatura failed, falling back to BeautifulSoup: {e}")

    try:
        decoded = _decode_bytes(html_content)
        soup = BeautifulSoup(decoded, "html.parser")

        for element in soup(
            ["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript", "form", "button"]
        ):
            element.decompose()

        main_content = (
            soup.find("main")
            or soup.find("article")
            or soup.find(role="main")
            or soup.find("div", class_=re.compile(r"content|main|article", re.I))
        )

        text = main_content.get_text(separator="\n") if main_content else soup.get_text(separator="\n")
        logger.debug("HTML processed with BeautifulSoup")
        return normalize_text(text)

    except Exception as e:
        logger.error(f"Critical HTML extraction error: {e}")
        return ""


def pdf_to_text(
    pdf_content: bytes, extract_tables: bool = False, preserve_layout: bool = True, ocr_fallback: bool = False
) -> str:
    if not pdf_content:
        return ""

    if not PYMUPDF_AVAILABLE:
        logger.error("PyMuPDF is not installed.")
        return ""

    text_parts = []
    try:
        doc = pymupdf.open(stream=pdf_content, filetype="pdf")

        if doc.is_encrypted:
            if not doc.authenticate(""):
                logger.warning("Encrypted PDF could not be decrypted")
                doc.close()
                return ""

        for page_num in range(len(doc)):
            page = doc[page_num]
            if preserve_layout:
                blocks = page.get_text("blocks")
                page_text = "\n".join(block[4] for block in blocks if block[4].strip())
            else:
                page_text = page.get_text()

            if extract_tables:
                tables = page.find_tables()
                if tables and tables.tables:
                    table_texts = []
                    for table in tables.tables:
                        table_str = table.to_text()
                        if table_str:
                            table_texts.append(f"[TABLE]\n{table_str}\n[/TABLE]")
                    if table_texts:
                        page_text = (page_text + "\n\n" if page_text else "") + "\n\n".join(table_texts)

            if page_text:
                text_parts.append(page_text)

        doc.close()

        if text_parts:
            logger.debug(f"PDF processed with PyMuPDF ({len(text_parts)} pages)")
            return normalize_text("\n\n".join(text_parts))
        else:
            logger.warning("Failed to extract text from PDF")
            return ""

    except Exception as e:
        logger.error(f"Error processing PDF with PyMuPDF: {e}")
        return ""


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = "".join(char for char in text if char in ("\n", "\t") or ord(char) >= 32)
    return text.strip()


def count_words(text: str) -> int:
    if not text:
        return 0
    return len(re.findall(r"\b\w+\b", text, re.UNICODE))


def count_sentences(text: str) -> int:
    if not text:
        return 0
    sentences = re.split(r"[.!?…]+[\s\n]+", text)
    return len([s for s in sentences if s.strip()])


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def extract_text_from_file(file_path: Path | str, **kwargs) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    content = path.read_bytes()
    suffix = path.suffix.lower()

    if suffix in (".pdf",):
        return pdf_to_text(content, **kwargs)
    elif suffix in (".html", ".htm", ".xhtml"):
        return html_to_text(content, **kwargs)
    elif suffix in (".txt", ".md", ".rst"):
        return normalize_text(_decode_bytes(content))
    else:
        if content[:4] == b"%PDF":
            return pdf_to_text(content, **kwargs)
        elif b"<html" in content[:1000].lower() or b"<!doctype html" in content[:1000].lower():
            return html_to_text(content, **kwargs)
        else:
            return normalize_text(_decode_bytes(content))


def get_tradition_color(tradition: str) -> str:
    with _color_lock:
        if tradition in _tradition_colors:
            return _tradition_colors[tradition]

        while True:
            color = f"#{random.randint(0, 0xFFFFFF):06X}"
            if color not in _used_colors:
                _used_colors.add(color)
                _tradition_colors[tradition] = color
                return color
