from __future__ import annotations

import hashlib
import re
from pathlib import Path
import unicodedata
from io import BytesIO
import logging
from typing import Optional
import pymupdf

logger = logging.getLogger(__name__)

PYMUPDF_AVAILABLE = True


def md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def _detect_encoding(content: bytes) -> tuple[str, float]:
    encodings_to_try = ['utf-8', 'windows-1252', 'iso-8859-1', 'cp1251', 'gb2312']

    for enc in encodings_to_try:
        try:
            content.decode(enc)
            return enc, 0.8
        except UnicodeDecodeError:
            continue

    return 'utf-8', 0.0


def _decode_bytes(content: bytes, min_confidence: float = 0.7) -> str:
    encoding, confidence = _detect_encoding(content)

    if confidence > min_confidence:
        try:
            return content.decode(encoding, errors='replace')
        except (UnicodeDecodeError, LookupError):
            pass

    encodings = ['utf-8', 'utf-8-sig', 'windows-1252', 'iso-8859-1', 'cp1251', 'gb2312']
    for enc in encodings:
        try:
            return content.decode(enc, errors='strict')
        except UnicodeDecodeError:
            continue

    return content.decode('utf-8', errors='replace')


def html_to_text(html_content: bytes, include_comments: bool = False,
                 include_tables: bool = True, target_language: Optional[str] = None) -> str:
    if not html_content:
        return ""

    try:
        decoded = _decode_bytes(html_content)
    except Exception as e:
        logger.error(f"Ошибка декодирования HTML: {e}")
        return ""

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(decoded, "html.parser")

        for element in soup(["script", "style", "nav", "footer", "header",
                             "aside", "iframe", "noscript"]):
            element.decompose()

        main_content = (
                soup.find("main") or
                soup.find("article") or
                soup.find(role="main") or
                soup.find("div", class_=re.compile(r"content|main|article", re.I))
        )

        if main_content:
            text = main_content.get_text(separator='\n')
        else:
            text = soup.get_text(separator='\n')

        logger.debug("HTML обработан с помощью BeautifulSoup")
        return _normalize_text(text)

    except Exception as e:
        logger.error(f"Ошибка извлечения через BeautifulSoup: {e}")
        return decoded[:10000]


def pdf_to_text(pdf_content: bytes, extract_tables: bool = False,
                preserve_layout: bool = True, ocr_fallback: bool = False) -> str:
    if not pdf_content:
        return ""

    if not PYMUPDF_AVAILABLE:
        logger.error("PyMuPDF не установлен. Установите: pip install pymupdf")
        return ""

    text_parts = []

    try:
        doc = pymupdf.open(stream=pdf_content, filetype="pdf")

        if doc.is_encrypted:
            try:
                if not doc.authenticate(""):
                    logger.warning("Зашифрованный PDF, не удалось расшифровать")
                    doc.close()
                    return ""
            except Exception as e:
                logger.warning(f"Ошибка при расшифровке PDF: {e}")
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
                            table_texts.append(f"[ТАБЛИЦА]\n{table_str}\n[/ТАБЛИЦА]")

                    if table_texts:
                        if page_text:
                            page_text += "\n\n" + "\n\n".join(table_texts)
                        else:
                            page_text = "\n\n".join(table_texts)

            if page_text:
                text_parts.append(unicodedata.normalize('NFC', page_text))

        doc.close()

        if text_parts:
            logger.debug(f"PDF обработан с помощью PyMuPDF ({len(text_parts)} стр.)")
            return _normalize_text("\n\n".join(text_parts))
        else:
            logger.warning("Не удалось извлечь текст из PDF")
            return ""

    except Exception as e:
        logger.error(f"Ошибка при обработке PDF через PyMuPDF: {e}")
        return ""


def _normalize_text(text: str) -> str:
    if not text:
        return ""

    text = unicodedata.normalize('NFC', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = ''.join(char for char in text if char in ('\n', '\t') or ord(char) >= 32)

    return text.strip()


def normalize_text(text: str) -> str:
    return _normalize_text(text)


def count_words(text: str) -> int:
    if not text:
        return 0
    return len(re.findall(r'\b\w+\b', text, re.UNICODE))


def count_sentences(text: str) -> int:
    if not text:
        return 0
    sentences = re.split(r'[.!?…]+[\s\n]+', text)
    return len([s for s in sentences if s.strip()])


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def extract_text_from_file(file_path: Path | str, **kwargs) -> str:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")

    content = path.read_bytes()
    suffix = path.suffix.lower()

    if suffix in ('.pdf',):
        return pdf_to_text(content, **kwargs)
    elif suffix in ('.html', '.htm', '.xhtml'):
        return html_to_text(content, **kwargs)
    elif suffix in ('.txt', '.md', '.rst'):
        return _normalize_text(_decode_bytes(content))
    else:
        if content[:4] == b'%PDF':
            return pdf_to_text(content, **kwargs)
        elif b'<html' in content[:1000].lower() or b'<!doctype html' in content[:1000].lower():
            return html_to_text(content, **kwargs)
        else:
            return _normalize_text(_decode_bytes(content))