import dataclasses
import logging
import time
from typing import Any

import numpy as np
from tqdm import tqdm

from corpus.iterator import CorpusFileInfo, iter_files
from corpus.utils import chunk_id
from model_registry import embedding_config, embedding_variants
from settings import settings

from . import chroma_manager
from .chunking import chunk_text
from .model_manager import EmbeddingEncoder
from .preprocess import preprocess_texts

logger = logging.getLogger(__name__)


def build_embeddings(
    model_name: str | None = None,
    models: list | None = None,
    force: bool = False,
) -> None:
    if model_name:
        keys = [embedding_config(model_name)["key"]]
    else:
        keys = models or embedding_variants()

    encoder = EmbeddingEncoder()

    logger.info("Starting embedding generation...")
    logger.info(f"   Source: {settings.corpus_dir}")
    logger.info(f"   Embeddings: {settings.embeddings_dir}")

    try:
        for key in keys:
            if force:
                chroma_manager.delete_collection(key)
            encoder.load(key)
            logger.info(f"   Variant: {key} (model {encoder.model_name})")
            _save_corpus_to_chroma(encoder)
    finally:
        encoder.unload()

    logger.info("All embeddings saved to Chroma.")


def _save_corpus_to_chroma(encoder: EmbeddingEncoder) -> None:
    cfg = encoder.config
    key = cfg["key"]
    preprocess_prompt = cfg["preprocess_prompt"]
    emb = settings.embedding
    corpus_dir = settings.corpus_dir
    batch_size = emb.batch_size

    files_info = list(iter_files(corpus_dir))

    if not files_info:
        logger.warning("No files found in corpus/. Check the folder structure.")
        return

    collection = chroma_manager.get_or_create_collection(
        key,
        metadata={"key": key, "model": encoder.model_name, "hnsw:space": "cosine"},
    )

    existing_ids = collection.existing_ids()
    if existing_ids:
        logger.info(f"Collection '{collection.name}' has {len(existing_ids)} existing chunks, resuming")

    added_total = 0
    skipped_total = 0
    total_chunks = 0
    encode_seconds = 0.0

    logger.info(f"Embedding {len(files_info)} files to collection '{collection.name}'")

    total = 0
    initial = 0
    for fi in files_info:
        n = sum(1 for c in chunk_text(fi.read_text(), emb.chunk_size, emb.chunk_overlap) if c.strip())
        total += n
        initial += sum(1 for i in range(n) if chunk_id(fi.text_id, i) in existing_ids)

    t0 = time.monotonic()
    with tqdm(total=total, initial=initial, desc="Embedding", unit="chunk") as pbar:
        for file_info in files_info:
            content = file_info.read_text()
            chunks = [c for c in chunk_text(content, emb.chunk_size, emb.chunk_overlap) if c.strip()]
            if not chunks:
                continue
            n_chunks = len(chunks)
            total_chunks += n_chunks
            try:
                ids, metadatas = _build_chroma_entries(chunks, file_info)

                missing = [
                    (i, chunk) for i, (cid, chunk) in enumerate(zip(ids, chunks, strict=True))
                    if cid not in existing_ids
                ]
                skipped_total += n_chunks - len(missing)
                if not missing:
                    continue

                # For a preprocessing variant, embed the transformed text (and store it as the
                # document); a chunk whose preprocessing failed is skipped and retried next run.
                if preprocess_prompt:
                    transformed = preprocess_texts([c for _, c in missing], preprocess_prompt)
                    kept = [(i, out) for (i, _), out in zip(missing, transformed, strict=True) if out.strip()]
                else:
                    kept = missing
                if not kept:
                    continue

                kept_idx = [i for i, _ in kept]
                kept_texts = [t for _, t in kept]
                kept_ids = [ids[i] for i in kept_idx]
                kept_metas = [metadatas[i] for i in kept_idx]

                for b_start in range(0, len(kept_texts), batch_size):
                    b_end = min(b_start + batch_size, len(kept_texts))
                    b_texts = kept_texts[b_start:b_end]

                    t_enc = time.monotonic()
                    b_embs = encoder.encode(
                        b_texts,
                        batch_size=batch_size,
                        show_progress_bar=False,
                        normalize_embeddings=True,
                    )
                    encode_seconds += time.monotonic() - t_enc
                    b_embs = np.asarray(b_embs, dtype=np.float32)

                    collection.upsert(
                        ids=kept_ids[b_start:b_end],
                        embeddings=b_embs,
                        metadatas=kept_metas[b_start:b_end],
                        documents=b_texts,
                    )

                    pbar.update(len(b_texts))

                added_total += len(kept_texts)

            except Exception:
                logger.exception("Error processing %s", file_info.filename)

            encoder.release_cache()

    collection.modify(metadata={
        "key": key,
        "model": encoder.model_name,
        "chunk_size": emb.chunk_size,
        "total_chunks": total_chunks,
    })

    elapsed = time.monotonic() - t0
    logger.info(f"Done: {added_total} added, {skipped_total} skipped, {total_chunks} total in '{collection.name}' ({elapsed:.1f}s)")
    if encode_seconds > 0 and added_total > 0:
        speed = added_total / encode_seconds
        logger.info(f"Encode speed: {speed:,.1f} chunks/sec ({added_total} chunks in {encode_seconds:.1f}s)")


def _build_chroma_entries(
    chunks: list[str], info: CorpusFileInfo,
) -> tuple[list[str], list[dict[str, Any]]]:
    ids = [chunk_id(info.text_id, i) for i in range(len(chunks))]
    base = {k: v for k, v in dataclasses.asdict(info).items() if not k.startswith("_")}
    metadatas = [{**base, "chunk_index": i} for i in range(len(chunks))]
    return ids, metadatas
