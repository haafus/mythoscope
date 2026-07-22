import hashlib
import re
import unicodedata
from pathlib import Path
from typing import Any


def sanitize_filename(name: str) -> str:
    # Make any name that lands in a file path filesystem- and URL-safe (§2.11): trim,
    # whitespace-runs → one `_`, replace unsafe/control chars (now incl. & % # ' — region
    # names carry &), forbid `..`, collapse repeats, strip edge `_`/`.`. Case is preserved.
    name = (name or "").strip()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r'[\\/*?:"<>|&%#\'\x00-\x1f]', "_", name)
    name = name.replace("..", "_")
    name = re.sub(r"_+", "_", name)
    return name.strip("_.")


def md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


# Change-detection fingerprint (non-adversarial): blake2b, digest_size=16 (32 hex).
# One algorithm everywhere (pipeline §2.4) — fast, stdlib, ample collision margin.
def content_fingerprint(data: bytes) -> str:
    return hashlib.blake2b(data, digest_size=16).hexdigest()


def normalize_catalog_id(value: Any) -> str:
    return re.sub(r"\s+", "_", str(value or "").strip())


def chunk_id(text_id: str, chunk_index: int) -> str:
    return f"{text_id}::{chunk_index}"


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


def text_path(corpus_dir: Path, major_tradition: str, tradition: str, title: str) -> Path:
    major = sanitize_filename(major_tradition)
    trad = sanitize_filename(tradition)
    title = sanitize_filename(title)
    return corpus_dir / major / trad / f"{title}.txt"


