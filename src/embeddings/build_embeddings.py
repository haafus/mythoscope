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
from .preprocess import preprocess_texts
from .transform import chunk_fingerprint, embed_plan, orphan_chunk_ids, transform_version

# NB: EmbeddingEncoder (and through it torch/sentence-transformers) is imported lazily,
# inside _save_corpus_to_chroma, so a run with nothing to embed never loads the ML stack.

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

    logger.info("Starting embedding generation...")
    logger.info(f"   Source: {settings.corpus_dir}")
    logger.info(f"   Embeddings: {settings.embeddings_dir}")

    encoder = None  # built lazily, only for a variant that actually has chunks to encode
    try:
        for key in keys:
            if force:
                chroma_manager.delete_collection(key)
            encoder = _save_corpus_to_chroma(key, encoder)
    finally:
        if encoder is not None:
            encoder.unload()

    logger.info("All embeddings saved to Chroma.")


def _save_corpus_to_chroma(key: str, encoder):
    """Sync one variant's collection. Returns the encoder (loading it lazily the first time
    a variant needs encoding); returns it unchanged when the collection is already current."""
    cfg = embedding_config(key)
    preprocess_prompt = cfg["preprocess_prompt"]
    document_prefix = cfg["document_prefix"]
    emb = settings.embedding
    corpus_dir = settings.corpus_dir
    batch_size = emb.batch_size

    files_info = list(iter_files(corpus_dir))

    if not files_info:
        logger.warning("No files found in corpus/. Check the folder structure.")
        return encoder

    collection = chroma_manager.get_or_create_collection(
        key,
        metadata={"key": key, "model": cfg["model"], "hnsw:space": "cosine"},  # hf id, no model load
    )

    transform_v = transform_version(cfg, emb.chunk_size, emb.chunk_overlap)

    # Stored chunk fingerprints from the last build: {chunk_id -> fingerprint}. A chunk is
    # up-to-date iff it is present AND its stored fp equals the one its document hashes to
    # now — so a text edit (new doc fp) re-embeds, a pure rename does not (pipeline §4).
    prev = collection.get(include=["metadatas"])
    existing_fp = {
        cid: (meta or {}).get("fingerprint")
        for cid, meta in zip(prev["ids"], prev["metadatas"], strict=True)
    }
    if existing_fp:
        logger.info(f"Collection '{collection.name}' has {len(existing_fp)} existing chunks, resuming")

    # Prune chunks whose document left the corpus (removed book, or every doc after a re-key
    # migration) — the positional gate below only trims within a surviving document_id, so
    # otherwise they linger and surface in search with an unresolvable document_id.
    current_ids = {fi.document_id for fi in files_info}
    orphan_ids = orphan_chunk_ids(prev["ids"], prev["metadatas"], current_ids)
    if orphan_ids:
        collection.delete(ids=orphan_ids)
        for cid in orphan_ids:
            existing_fp.pop(cid, None)
        logger.info(f"Pruned {len(orphan_ids)} orphaned chunk(s) from documents no longer in the corpus")

    added_total = 0
    skipped_total = 0
    total_chunks = 0
    stale_removed = len(orphan_ids)
    encode_seconds = 0.0

    # Cheap pre-pass (no model): count what needs encoding and prune stale chunks in place
    # (deletion needs no model). If nothing needs encoding, return before loading the ML stack.
    total = 0
    to_embed_total = 0
    for fi in files_info:
        chunks = [c for c in chunk_text(fi.read_text(), emb.chunk_size, emb.chunk_overlap) if c.strip()]
        expected = chunk_fingerprint(fi.content_fingerprint(), transform_v)
        to_embed, stale = embed_plan(fi.document_id, len(chunks), expected, existing_fp)
        if stale:
            collection.delete(ids=stale)
            for cid in stale:
                existing_fp.pop(cid, None)
            stale_removed += len(stale)
        total += len(chunks)
        to_embed_total += len(to_embed)
    initial = total - to_embed_total

    if to_embed_total == 0:
        collection.modify(metadata={
            "key": key, "model": cfg["model"], "chunk_size": emb.chunk_size,
            "total_chunks": total, "transform_version": transform_v,
        })
        removed = f", {stale_removed} stale removed" if stale_removed else ""
        logger.info(f"'{collection.name}' already current — {total} chunks, model not loaded{removed}")
        return encoder

    if encoder is None:
        from .model_manager import EmbeddingEncoder  # defer torch/sentence-transformers to here
        encoder = EmbeddingEncoder()
    encoder.load(key)
    logger.info(f"   Variant: {key} (model {encoder.model_name})")
    logger.info(f"Embedding {len(files_info)} files to collection '{collection.name}'")

    t0 = time.monotonic()
    with tqdm(total=total, initial=initial, desc="Embedding", unit="chunk") as pbar:
        for file_info in files_info:
            content = file_info.read_text()
            chunks = [c for c in chunk_text(content, emb.chunk_size, emb.chunk_overlap) if c.strip()]
            n_chunks = len(chunks)
            expected = chunk_fingerprint(file_info.content_fingerprint(), transform_v)
            try:
                to_embed, stale = embed_plan(file_info.document_id, n_chunks, expected, existing_fp)
                # Drop chunks a shorter (or now-empty) document no longer has — the only
                # deletion case; positional ids upsert-overwrite the rest, never orphan (§4).
                # Runs before the empty-doc skip so a doc edited down to zero chunks does
                # not strand its old vectors.
                if stale:
                    collection.delete(ids=stale)
                    stale_removed += len(stale)
                if not chunks:
                    continue
                total_chunks += n_chunks

                ids, metadatas = _build_chroma_entries(chunks, file_info, expected)
                missing = [(i, chunks[i]) for i in to_embed]
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

                # For a preprocessing variant the embedded document is the transformed
                # text, so keep the original chunk in metadata for the UI to reveal.
                if preprocess_prompt:
                    for i, meta in zip(kept_idx, kept_metas, strict=True):
                        meta["source_text"] = chunks[i]

                for b_start in range(0, len(kept_texts), batch_size):
                    b_end = min(b_start + batch_size, len(kept_texts))
                    b_texts = kept_texts[b_start:b_end]
                    # The prefix is the model's input formatting, not content: encode
                    # prefix+text, store the clean text as the document.
                    enc_input = [document_prefix + t for t in b_texts] if document_prefix else b_texts

                    t_enc = time.monotonic()
                    b_embs = encoder.encode(
                        enc_input,
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
        "model": cfg["model"],
        "chunk_size": emb.chunk_size,
        "total_chunks": total_chunks,
        "transform_version": transform_v,
    })

    elapsed = time.monotonic() - t0
    removed = f", {stale_removed} stale removed" if stale_removed else ""
    logger.info(f"Done: {added_total} added, {skipped_total} skipped{removed}, {total_chunks} total in '{collection.name}' ({elapsed:.1f}s)")
    if encode_seconds > 0 and added_total > 0:
        speed = added_total / encode_seconds
        logger.info(f"Encode speed: {speed:,.1f} chunks/sec ({added_total} chunks in {encode_seconds:.1f}s)")
    return encoder


def _build_chroma_entries(
    chunks: list[str], info: CorpusFileInfo, fingerprint: str,
) -> tuple[list[str], list[dict[str, Any]]]:
    # B1: a chunk carries exactly one document reference `{document_id, chunk_index}` plus
    # its staleness `fingerprint` (the hash of the doc fp + transform version, compared by
    # the next build's gate). tradition/region/url/colour are resolved from document_id at
    # query time (data-model §2.13) — never denormalized onto the chunk.
    ids = [chunk_id(info.document_id, i) for i in range(len(chunks))]
    metadatas = [
        {"document_id": info.document_id, "chunk_index": i, "fingerprint": fingerprint}
        for i in range(len(chunks))
    ]
    return ids, metadatas
