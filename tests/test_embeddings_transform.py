"""Part 2 — the embeddings staleness gate (content fingerprints + transform version).

These pure-function tests ARE the acceptance gate for item 1 (roadmap Stage II): a text
edit re-embeds, an unchanged doc is skipped, a transform-version bump re-embeds, a rename
does not, and a shrunk document drops its trailing chunks.
"""

from embeddings.transform import (
    chunk_fingerprint,
    embed_plan,
    transform_version,
)

_CFG = {"model": "bge-m3", "document_prefix": "", "preprocess_prompt": None}


def _tv(**over):
    cfg = {**_CFG, **over.pop("cfg", {})}
    return transform_version(cfg, over.get("chunk_size", 1024), over.get("chunk_overlap", 128))


class TestTransformVersion:
    def test_deterministic(self):
        assert _tv() == _tv()

    def test_model_change_bumps(self):
        assert _tv() != _tv(cfg={"model": "other"})

    def test_chunk_params_bump(self):
        assert _tv() != _tv(chunk_size=512)
        assert _tv() != _tv(chunk_overlap=0)

    def test_preprocess_prompt_bumps(self):
        assert _tv() != _tv(cfg={"preprocess_prompt": "summarize"})

    def test_none_and_empty_prefix_equivalent(self):
        # A missing key and an empty string must hash the same (no spurious re-embed).
        a = transform_version({"model": "m"}, 1024, 128)
        b = transform_version({"model": "m", "document_prefix": "", "preprocess_prompt": None}, 1024, 128)
        assert a == b


class TestChunkFingerprint:
    def test_rename_stable(self):
        # Same content + same transform → same fp (a pure rename must NOT re-embed, flaw 1).
        tv = _tv()
        assert chunk_fingerprint("doc-fp", tv) == chunk_fingerprint("doc-fp", tv)

    def test_text_edit_changes(self):
        # New doc fingerprint (edited text) → new key → re-embed (flaw 2).
        tv = _tv()
        assert chunk_fingerprint("doc-fp-v1", tv) != chunk_fingerprint("doc-fp-v2", tv)

    def test_transform_bump_changes(self):
        assert chunk_fingerprint("doc-fp", _tv()) != chunk_fingerprint("doc-fp", _tv(chunk_size=512))


class TestEmbedPlan:
    def setup_method(self):
        self.tv = _tv()
        self.fp = chunk_fingerprint("docA-v1", self.tv)
        self.fp2 = chunk_fingerprint("docA-v2", self.tv)

    def test_fresh_doc_embeds_all(self):
        assert embed_plan("A", 3, self.fp, {}) == ([0, 1, 2], [])

    def test_unchanged_doc_skips_all(self):
        existing = {"A::0": self.fp, "A::1": self.fp, "A::2": self.fp}
        assert embed_plan("A", 3, self.fp, existing) == ([], [])

    def test_edited_doc_reembeds_all(self):
        existing = {"A::0": self.fp, "A::1": self.fp, "A::2": self.fp}
        assert embed_plan("A", 3, self.fp2, existing) == ([0, 1, 2], [])

    def test_partial_build_resumes_only_missing(self):
        # Crash after the first two chunks: only the absent third is embedded.
        existing = {"A::0": self.fp, "A::1": self.fp}
        assert embed_plan("A", 3, self.fp, existing) == ([2], [])

    def test_shrunk_doc_drops_trailing(self):
        existing = {"A::0": self.fp, "A::1": self.fp, "A::2": self.fp}
        to_embed, stale = embed_plan("A", 2, self.fp, existing)
        assert to_embed == []
        assert stale == ["A::2"]

    def test_shrunk_to_zero_drops_all(self):
        # A doc edited down to no chunks must drop ALL its old chunks (review finding 3).
        existing = {"A::0": self.fp, "A::1": self.fp}
        to_embed, stale = embed_plan("A", 0, self.fp, existing)
        assert to_embed == []
        assert sorted(stale) == ["A::0", "A::1"]

    def test_other_documents_untouched(self):
        # A doc whose id is a prefix of another's must not steal its chunks.
        existing = {"A::0": self.fp, "AB::0": self.fp, "AB::1": self.fp}
        to_embed, stale = embed_plan("A", 1, self.fp, existing)
        assert to_embed == []
        assert stale == []  # AB::* belong to a different document

    def test_id_containing_separator(self):
        # A text_id that itself contains '::' is matched on the LAST separator only.
        existing = {"A::B::0": self.fp, "A::B::1": self.fp}
        to_embed, stale = embed_plan("A::B", 1, self.fp, existing)
        assert to_embed == []
        assert stale == ["A::B::1"]
