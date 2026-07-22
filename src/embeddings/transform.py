"""Transform version + chunk staleness fingerprint for the embeddings stage.

The staleness gate (pipeline §4) re-embeds a document's chunks iff their stored
fingerprint diverges from ``chunk_fingerprint(doc_fingerprint, transform_version)``.
``transform_version`` is the hybrid of D4 (§2.5): a hash of the output-affecting
parameters plus one manual ``algo_version`` for pure-logic/library changes.
"""

import hashlib

from corpus.utils import chunk_id, content_fingerprint

# Bump on a behavioural change the parameters below do NOT capture — the chunking
# logic, prefix handling, or a sentence-transformers/torch upgrade that shifts the
# vectors (D4, §2.5). A forgotten bump is caught by `--force`.
EMBED_ALGO_VERSION = 1


def transform_version(cfg: dict, chunk_size: int, chunk_overlap: int) -> str:
    """Short hash of everything that, on change, must re-embed a document's chunks:
    the model, the chunk params, the document prefix, the preprocess prompt, and the
    manual algo version. Data params are precise (no false triggers); the manual
    version is the thin net for logic/library edits."""
    parts = [
        str(EMBED_ALGO_VERSION),
        cfg.get("model", "") or "",
        str(chunk_size),
        str(chunk_overlap),
        cfg.get("document_prefix", "") or "",
        cfg.get("preprocess_prompt", "") or "",
    ]
    return hashlib.blake2b("\x00".join(parts).encode("utf-8"), digest_size=8).hexdigest()


def chunk_fingerprint(doc_fingerprint: str, transform_v: str) -> str:
    """The staleness key stored in every chunk's Chroma metadata. Per-document (all of
    a doc's chunks share it): a text edit changes ``doc_fingerprint`` → re-embed; a
    pure rename leaves it (and the ``document_id`` anchor) unchanged → skip (§4)."""
    return content_fingerprint(f"{doc_fingerprint}|{transform_v}".encode("utf-8"))


def embed_plan(
    text_id: str, n_chunks: int, expected_fp: str, existing_fp: dict[str, str | None],
) -> tuple[list[int], list[str]]:
    """Decide, from the collection's stored ``{chunk_id: fingerprint}``, what to (re)embed
    and what to delete for one document (pipeline §4):

    - **to_embed** — the chunk indices whose stored fp is absent or ≠ ``expected_fp``
      (a new doc, a text edit, or a transform-version bump); the up-to-date rest are skipped.
    - **stale** — trailing chunk-ids ``text_id::i`` for ``i >= n_chunks`` (the document
      shrank); the only deletion case, since positional ids upsert-overwrite in place.
    """
    to_embed = [i for i in range(n_chunks) if existing_fp.get(chunk_id(text_id, i)) != expected_fp]
    stale: list[str] = []
    for cid in existing_fp:
        did, sep, idx = cid.rpartition("::")
        if sep and did == text_id and idx.isdigit() and int(idx) >= n_chunks:
            stale.append(cid)
    return to_embed, stale
