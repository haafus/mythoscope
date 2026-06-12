import gc
import hashlib
import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Callable

logger = logging.getLogger(__name__)


class LanguageDetector:
    _fasttext_model = None
    _model_path = os.path.expanduser("~/.cache/fasttext/lid.176.bin")

    @classmethod
    def _load_fasttext(cls):
        if cls._fasttext_model is not None:
            return True

        try:
            import fasttext
        except ImportError:
            logger.warning("FastText is not installed. Install it with: pip install fasttext")
            return False

        if not os.path.exists(cls._model_path):
            logger.warning(
                f"FastText model not found at {cls._model_path}. Run download_fasttext_model() to download it."
            )
            return False

        try:
            cls._fasttext_model = fasttext.load_model(cls._model_path)
            return True
        except Exception as e:
            logger.error(f"FastText model load error: {e}")
            return False

    @classmethod
    def unload_model(cls):
        if cls._fasttext_model is not None:
            del cls._fasttext_model
            cls._fasttext_model = None
            gc.collect()
            logger.info("FastText model unloaded from memory")

    @classmethod
    def detect(cls, text: str) -> str:
        if not text or len(text.strip()) < 3:
            return "unknown"

        clean_text = " ".join(text.split())

        if cls._load_fasttext() and cls._fasttext_model is not None:
            try:
                predictions = cls._fasttext_model.predict(clean_text.lower(), k=1)
                lang_code: str = predictions[0][0].replace("__label__", "")
                return lang_code
            except Exception as e:
                logger.debug(f"FastText error: {e}, switching to langdetect")

        try:
            from langdetect import DetectorFactory, detect

            DetectorFactory.seed = 0
            result: str = detect(clean_text)
            return result
        except ImportError:
            logger.debug("langdetect is not installed, falling back to heuristic detection")
        except Exception as e:
            logger.debug(f"langdetect failed ({e}), falling back to heuristic detection")

        return cls._heuristic_detect(text)

    @classmethod
    def _heuristic_detect(cls, text: str) -> str:
        total_chars = len(text.strip())
        if total_chars == 0:
            return "unknown"

        counts = {
            "ru": len(RegexPatterns.CYRILLIC_PATTERN.findall(text)),
            "en": len(RegexPatterns.LATIN_PATTERN.findall(text)),
            "zh": len(RegexPatterns.CJK_PATTERN.findall(text)),
            "ar": len(RegexPatterns.ARABIC_PATTERN.findall(text)),
            "hi": len(RegexPatterns.DEVANAGARI_PATTERN.findall(text)),
        }

        threshold = total_chars * 0.3
        filtered = {k: v for k, v in counts.items() if v >= threshold}

        if filtered:
            return max(filtered, key=lambda k: filtered[k])

        if counts["en"] > 0:
            return "en"

        return "unknown"


def download_fasttext_model():
    import os
    import urllib.request

    cache_dir = os.path.expanduser("~/.cache/fasttext")
    os.makedirs(cache_dir, exist_ok=True)
    model_path = os.path.join(cache_dir, "lid.176.bin")

    if os.path.exists(model_path):
        print(f"Model already exists: {model_path}")
        return model_path

    url = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"
    print("Downloading FastText model (176 languages, ~130MB)...")
    print(f"URL: {url}")
    print(f"Path: {model_path}")

    try:
        urllib.request.urlretrieve(url, model_path)
        print("Download complete!")
        return model_path
    except Exception as e:
        print(f"Load error: {e}")
        if os.path.exists(model_path):
            os.remove(model_path)
        raise


@dataclass
class ChunkMetadata:
    chunk_id: str
    index: int
    start_pos: int
    end_pos: int
    chunk_type: str
    strategy_used: str
    overlap_with_prev: bool = False
    overlap_with_next: bool = False
    word_count: int = 0
    char_count: int = 0
    language: str | None = None
    has_code: bool = False
    has_markdown: bool = False
    parent_doc_hash: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "index": self.index,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "chunk_type": self.chunk_type,
            "strategy_used": self.strategy_used,
            "overlap_with_prev": self.overlap_with_prev,
            "overlap_with_next": self.overlap_with_next,
            "word_count": self.word_count,
            "char_count": self.char_count,
            "language": self.language,
            "has_code": self.has_code,
            "has_markdown": self.has_markdown,
            "parent_doc_hash": self.parent_doc_hash,
        }


class ChunkWithMetadata:
    def __init__(self, text: str, metadata: ChunkMetadata):
        self.text = text
        self.metadata = metadata


class RegexPatterns:
    CODE_PATTERN = re.compile(
        r"```[\s\S]*?```|"
        r"^\s*(def|class|import|from|return|if|else|for|while)\s|"
        r"^\s*(function|const|let|var|if|else|for|while|switch)\s|"
        r"^\s*(public|private|protected|static|void|int|string)\s|"
        r"^\s*(#include|#define|int main|printf|scanf)\s",
        re.MULTILINE,
    )
    MARKDOWN_PATTERN = re.compile(r"[#*`\[\]\(\)]|^>", re.MULTILINE)
    CODE_BLOCK_PATTERN = re.compile(r"```[\s\S]*?```")
    HEADER_PATTERN = re.compile(r"^#{1,6}\s", re.MULTILINE)
    LIST_PATTERN = re.compile(r"^\s*[-*+]\s", re.MULTILINE)

    SENTENCE_SPLITTER = re.compile(r"(?<=[.!?])\s+|(?<=[。！？।])\s*")
    PARAGRAPH_SPLITTER = re.compile(r"\n\s*\n")

    CYRILLIC_PATTERN = re.compile(r"[\u0400-\u04FF]")
    LATIN_PATTERN = re.compile(r"[a-zA-Z]")
    CJK_PATTERN = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]")
    ARABIC_PATTERN = re.compile(r"[\u0600-\u06FF\u0750-\u077F]")
    DEVANAGARI_PATTERN = re.compile(r"[\u0900-\u097F]")


def character_based_chunking(
    text: str, chunk_size: int = 512, chunk_overlap: int = 64, separators: list[str] | None = None
) -> list[str]:
    if chunk_size < 10:
        raise ValueError("chunk_size must be at least 10 characters")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap cannot be greater than or equal to chunk_size")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative")

    if separators is None:
        separators = ["\n\n", "\n", ". ", "! ", "? ", "。", "！", "？", "।", "; ", ", ", "、", " ", ""]

    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    def _extract_tail(chunk: str, overlap_size: int) -> str:
        if overlap_size <= 0 or len(chunk) <= overlap_size:
            return ""
        tail_start = len(chunk) - overlap_size
        priority_seps = ["\n\n", "\n", ". ", "! ", "? ", "。", "！", "？", "।", "; ", ", ", "、", " ", ""]
        for sep in priority_seps:
            if not sep:
                continue
            search_start = max(0, tail_start - 50)
            last_sep_pos = chunk.rfind(sep, search_start, len(chunk))
            if last_sep_pos != -1 and last_sep_pos >= tail_start - 100:
                return chunk[last_sep_pos + len(sep) :]
        return chunk[-overlap_size:]

    def _split_recursive(text_to_split: str, seps: list[str], tail: str = "", depth: int = 0) -> list[str]:
        MAX_DEPTH = 10
        if depth > MAX_DEPTH:
            step = chunk_size - chunk_overlap
            if step <= 0:
                step = chunk_size // 2
            return [text_to_split[i : i + chunk_size] for i in range(0, len(text_to_split), step)]

        if not seps:
            full_text = tail + text_to_split
            if len(full_text) <= chunk_size:
                return [full_text]
            chunks = []
            step = chunk_size - chunk_overlap
            if step <= 0:
                step = chunk_size // 2
            for i in range(0, len(full_text), step):
                chunk = full_text[i : i + chunk_size]
                if chunk:
                    chunks.append(chunk)
            return chunks

        separator = seps[0]
        remaining_seps = seps[1:]
        if separator:
            splits = text_to_split.split(separator)
            splits = [s + (separator if i < len(splits) - 1 else "") for i, s in enumerate(splits) if s]
        else:
            splits = [text_to_split] if text_to_split else []

        if tail and splits:
            splits[0] = tail + splits[0]
            tail = ""
        chunks, current_chunk, current_tail = [], "", ""

        for split in splits:
            if len(current_chunk) + len(split) <= chunk_size:
                current_chunk += split
            else:
                if current_chunk:
                    current_tail = _extract_tail(current_chunk, chunk_overlap)
                    chunks.append(current_chunk)
                if len(split) > chunk_size:
                    sub_chunks = _split_recursive(split, remaining_seps, current_tail, depth + 1)
                    if sub_chunks:
                        chunks.extend(sub_chunks)
                        current_tail = _extract_tail(sub_chunks[-1], chunk_overlap)
                        current_chunk = ""
                    else:
                        current_chunk = current_tail
                else:
                    current_chunk = current_tail + split
                    current_tail = ""
        if current_chunk:
            chunks.append(current_chunk)
        return _merge_small_chunks(chunks, chunk_size)

    def _merge_small_chunks(chunks: list[str], min_size: int) -> list[str]:
        if not chunks:
            return []
        merged, current = [], chunks[0]
        for i in range(1, len(chunks)):
            next_chunk = chunks[i]
            if len(current) + len(next_chunk) <= min_size * 1.2:
                current += next_chunk
            else:
                merged.append(current)
                current = next_chunk
        merged.append(current)
        return merged

    return _split_recursive(text, separators)


def sentence_based_chunking(text: str, chunk_size: int = 512, chunk_overlap: int = 64) -> list[str]:
    if chunk_size < 10:
        raise ValueError("chunk_size must be at least 10 characters")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap cannot be greater than or equal to chunk_size")

    if not text:
        return []
    sentences = RegexPatterns.SENTENCE_SPLITTER.split(text)
    sentences = [s for s in sentences if s.strip()]
    if not sentences:
        return [text] if text else []

    chunks: list[str] = []
    current_sentences: list[str] = []
    current_length = 0
    overlap_sentences_count = max(1, chunk_overlap // 100) if chunk_overlap > 0 else 0

    for sent in sentences:
        sent_len = len(sent)
        if sent_len > chunk_size:
            if current_sentences:
                chunks.append(" ".join(current_sentences))
            chunks.extend(character_based_chunking(sent, chunk_size, chunk_overlap))
            current_sentences, current_length = [], 0
            continue

        if current_length + sent_len > chunk_size and current_sentences:
            chunks.append(" ".join(current_sentences))
            if overlap_sentences_count > 0 and len(current_sentences) >= overlap_sentences_count:
                current_sentences = current_sentences[-overlap_sentences_count:]
                current_length = sum(len(s) for s in current_sentences) + len(current_sentences) - 1
            else:
                current_sentences, current_length = [], 0

        current_sentences.append(sent)
        current_length += sent_len + 1

    if current_sentences:
        chunks.append(" ".join(current_sentences))
    return chunks


def paragraph_based_chunking(text: str, chunk_size: int = 1024, chunk_overlap: int = 128) -> list[str]:
    if chunk_size < 10:
        raise ValueError("chunk_size must be at least 10 characters")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap cannot be greater than or equal to chunk_size")

    if not text:
        return []
    paragraphs = RegexPatterns.PARAGRAPH_SPLITTER.split(text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    if not paragraphs:
        return [text[:chunk_size]] if text else []

    chunks: list[str] = []
    current_paragraphs: list[str] = []
    current_length = 0
    overlap_para_count = max(1, chunk_overlap // 200) if chunk_overlap > 0 else 0

    for para in paragraphs:
        para_len = len(para)
        if para_len > chunk_size:
            if current_paragraphs:
                chunks.append("\n\n".join(current_paragraphs))
            chunks.extend(character_based_chunking(para, chunk_size, chunk_overlap))
            current_paragraphs, current_length = [], 0
            continue

        if current_length + para_len > chunk_size and current_paragraphs:
            chunks.append("\n\n".join(current_paragraphs))
            if overlap_para_count > 0 and len(current_paragraphs) >= overlap_para_count:
                current_paragraphs = current_paragraphs[-overlap_para_count:]
                current_length = sum(len(p) for p in current_paragraphs) + (len(current_paragraphs) - 1) * 2
            else:
                current_paragraphs, current_length = [], 0

        current_paragraphs.append(para)
        current_length += para_len + (2 if len(current_paragraphs) > 1 else 0)

    if current_paragraphs:
        chunks.append("\n\n".join(current_paragraphs))
    return chunks


class ChunkingStrategy:
    def __init__(
        self,
        name: str,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        chunking_func: Callable | None = None,
        return_metadata: bool = False,
        language: str = "auto",
    ):
        if chunk_size < 10:
            raise ValueError("chunk_size must be at least 10 characters")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap cannot be greater than or equal to chunk_size")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")

        self.name = name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunking_func = chunking_func or character_based_chunking
        self.return_metadata = return_metadata
        self.language = language

    def __call__(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        return self.chunking_func(text, self.chunk_size, self.chunk_overlap)

    def call_with_metadata(self, text: str, doc_hash: str | None = None) -> list[ChunkWithMetadata]:
        if not text or not text.strip():
            return []
        if doc_hash is None:
            doc_hash = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]

        chunks = self.chunking_func(text, self.chunk_size, self.chunk_overlap)
        chunks_with_metadata = []
        position_tracker = 0

        for i, chunk_text in enumerate(chunks):
            start_pos = text.find(chunk_text, position_tracker)
            if start_pos == -1:
                start_pos = text.find(chunk_text)
            if start_pos == -1:
                start_pos = position_tracker

            end_pos = start_pos + len(chunk_text)

            if i < len(chunks) - 1:
                position_tracker = max(position_tracker + 1, end_pos - self.chunk_overlap)
            else:
                position_tracker = end_pos

            chunk_id = hashlib.md5(f"{doc_hash}_{i}_{start_pos}".encode()).hexdigest()[:12]
            has_code = bool(RegexPatterns.CODE_PATTERN.search(chunk_text))
            has_markdown = bool(RegexPatterns.MARKDOWN_PATTERN.search(chunk_text))

            detected_language = LanguageDetector.detect(chunk_text) if self.language == "auto" else self.language

            metadata = ChunkMetadata(
                chunk_id=chunk_id,
                index=i,
                start_pos=start_pos,
                end_pos=end_pos,
                chunk_type=self._determine_chunk_type(chunk_text),
                strategy_used=self.name,
                overlap_with_prev=(i > 0 and self.chunk_overlap > 0),
                overlap_with_next=(i < len(chunks) - 1 and self.chunk_overlap > 0),
                word_count=len(chunk_text.split()),
                char_count=len(chunk_text),
                language=detected_language,
                has_code=has_code,
                has_markdown=has_markdown,
                parent_doc_hash=doc_hash,
            )
            chunks_with_metadata.append(ChunkWithMetadata(chunk_text, metadata))
        return chunks_with_metadata

    def _determine_chunk_type(self, text: str) -> str:
        if RegexPatterns.CODE_BLOCK_PATTERN.search(text):
            return "code_block"
        elif RegexPatterns.HEADER_PATTERN.search(text):
            return "markdown_with_headers"
        elif RegexPatterns.LIST_PATTERN.search(text):
            return "list"
        elif "\n\n" in text:
            return "multi_paragraph"
        elif ". " in text and len(text.split(". ")) > 2:
            return "multi_sentence"
        else:
            return "text"


def create_chunking_strategies() -> dict[str, ChunkingStrategy]:
    return {
        "character": ChunkingStrategy(
            name="character", chunk_size=512, chunk_overlap=64, chunking_func=character_based_chunking
        ),
        "sentence": ChunkingStrategy(
            name="sentence", chunk_size=512, chunk_overlap=64, chunking_func=sentence_based_chunking
        ),
        "paragraph": ChunkingStrategy(
            name="paragraph", chunk_size=1024, chunk_overlap=128, chunking_func=paragraph_based_chunking
        ),
    }
