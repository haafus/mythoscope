import re
from typing import List, Callable


class ChunkingStrategy:
    def __init__(self, name: str, chunk_size: int = 512, chunk_overlap: int = 64,
                 func: Callable[[str], List[str]] = None):
        self.name = name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.func = func

    def __call__(self, text: str) -> List[str]:
        if not isinstance(text, str):
            raise TypeError("Текст должен быть строкой")
        return self.func(text)


def create_chunking_strategies() -> dict:
    def fixed_size_chunking(text: str, chunk_size: int = 512, chunk_overlap: int = 64) -> List[str]:
        if not text:
            return []
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start = end - chunk_overlap
        return chunks

    def sentence_based_chunking(text: str, chunk_size: int = 512, chunk_overlap: int = 64) -> List[str]:
        if not text:
            return []
        sentences = re.split(r'([.!?]+(?:\s+|$))', text)
        sentences = [sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else '')
                     for i in range(0, len(sentences), 2) if i + 1 < len(sentences) or sentences[i].strip()]
        if len(sentences) % 2 == 1:
            sentences.append(sentences.pop() if sentences else '')

        chunks = []
        current_chunk = ""
        for sent in sentences:
            if len(current_chunk) + len(sent) > chunk_size and current_chunk.strip():
                chunks.append(current_chunk.strip())
                overlap_start = max(0, len(current_chunk) - chunk_overlap)
                current_chunk = current_chunk[overlap_start:]
            current_chunk += sent
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        return chunks

    def paragraph_based_chunking(text: str, chunk_size: int = 512, chunk_overlap: int = 64) -> List[str]:
        if not text:
            return []
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        current_chunk = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(current_chunk) + len(para) + 2 > chunk_size and current_chunk.strip():
                chunks.append(current_chunk.strip())
                overlap_start = max(0, len(current_chunk) - chunk_overlap)
                current_chunk = current_chunk[overlap_start:] + "\n\n" + para
            else:
                current_chunk += ("\n\n" + para if current_chunk else para)
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        return chunks

    return {
        "fixed_size": ChunkingStrategy(
            name="fixed_size",
            chunk_size=512,
            chunk_overlap=64,
            func=fixed_size_chunking
        ),
        "sentence_based": ChunkingStrategy(
            name="sentence_based",
            chunk_size=512,
            chunk_overlap=64,
            func=sentence_based_chunking
        ),
        "paragraph_based": ChunkingStrategy(
            name="paragraph_based",
            chunk_size=512,
            chunk_overlap=64,
            func=paragraph_based_chunking
        ),
    }
