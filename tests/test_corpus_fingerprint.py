"""The corpus stage's input fingerprint: stable for identical inputs, sensitive to each one."""

from corpus.fingerprint import source_fingerprint


def test_stable_for_identical_inputs():
    assert source_fingerprint(b"raw text", "START", "END") == source_fingerprint(b"raw text", "START", "END")


def test_sensitive_to_raw_bytes():
    assert source_fingerprint(b"raw text", None, None) != source_fingerprint(b"raw TEXT", None, None)


def test_sensitive_to_trim_bounds():
    base = source_fingerprint(b"raw", None, None)
    assert source_fingerprint(b"raw", "START", None) != base
    assert source_fingerprint(b"raw", None, "END") != base
    assert source_fingerprint(b"raw", "START", "END") != source_fingerprint(b"raw", "START", None)


def test_none_and_empty_trim_are_equivalent():
    # `.get("content_start")` yields None when absent; "" when present-but-empty — same input.
    assert source_fingerprint(b"raw", None, None) == source_fingerprint(b"raw", "", "")
