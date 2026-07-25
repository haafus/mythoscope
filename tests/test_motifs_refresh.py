"""The staged motif-refresh engine: fresh-vs-pinned diff → §9 status/action, keep-pinned by
default, adopt only on apply, and never a blind overwrite of a bad/absent upstream."""

import pytest

from motifs.refresh import (
    CHANGED,
    DEGRADED,
    GONE,
    NEW,
    NOT_CHANGED,
    Fetchable,
    refresh_fetchables,
)


def _pin(tmp_path, name, data: bytes):
    p = tmp_path / name
    p.write_bytes(data)
    return p


def _stub(mapping):
    """A downloader returning bytes per-url, or raising the mapped exception."""
    def download(url, auth=None):
        v = mapping[url]
        if isinstance(v, Exception):
            raise v
        return v
    return download


def _resp_error(status):
    exc = RuntimeError(f"http {status}")
    exc.response = type("R", (), {"status_code": status})()
    return exc


def test_not_changed_keeps_pinned(tmp_path):
    cache = _pin(tmp_path, "a", b"same")
    f = Fetchable("A", "http://x/a", cache)
    r = refresh_fetchables([f], apply=True, download=_stub({"http://x/a": b"same"}))
    assert [(o.title, o.status, o.action) for o in r.outcomes] == [("A", NOT_CHANGED, "keep cached")]
    assert r.adopted == []
    assert cache.read_bytes() == b"same"


def test_changed_previews_then_adopts(tmp_path):
    cache = _pin(tmp_path, "a", b"old")
    f = Fetchable("A", "http://x/a", cache)
    dl = _stub({"http://x/a": b"new"})

    preview = refresh_fetchables([f], apply=False, download=dl)
    assert preview.outcomes[0].status == CHANGED
    assert preview.outcomes[0].action == "adopt on apply"
    assert preview.adopted == []
    assert cache.read_bytes() == b"old"                 # kept pinned on preview

    applied = refresh_fetchables([f], apply=True, download=dl)
    assert applied.adopted == ["A"]
    assert cache.read_bytes() == b"new"                 # os.replace adopted


def test_new_acquires_only_on_apply(tmp_path):
    cache = tmp_path / "a"                               # no pinned copy
    f = Fetchable("A", "http://x/a", cache)
    dl = _stub({"http://x/a": b"fresh"})

    preview = refresh_fetchables([f], apply=False, download=dl)
    assert preview.outcomes[0].status == NEW
    assert preview.outcomes[0].action == "acquire on apply"
    assert not cache.exists()

    refresh_fetchables([f], apply=True, download=dl)
    assert cache.read_bytes() == b"fresh"


def test_degraded_body_never_overwrites(tmp_path):
    cache = _pin(tmp_path, "a", b"good")
    f = Fetchable("A", "http://x/a", cache)
    r = refresh_fetchables([f], apply=True, download=_stub({"http://x/a": b"   "}))  # empty/whitespace
    assert r.outcomes[0].status == DEGRADED
    assert r.outcomes[0].action == "keep cached"
    assert r.adopted == [] and cache.read_bytes() == b"good"


def test_validate_failure_is_degraded(tmp_path):
    cache = _pin(tmp_path, "a", b"good")
    f = Fetchable("A", "http://x/a", cache, validate=lambda b: b"<ok>" in b)
    r = refresh_fetchables([f], apply=True, download=_stub({"http://x/a": b"<bad>"}))
    assert r.outcomes[0].status == DEGRADED and cache.read_bytes() == b"good"


def test_404_is_gone_transport_error_is_degraded(tmp_path):
    ca = _pin(tmp_path, "a", b"a")
    cb = _pin(tmp_path, "b", b"b")
    fs = [Fetchable("A", "http://x/a", ca), Fetchable("B", "http://x/b", cb)]
    r = refresh_fetchables(fs, apply=True, download=_stub(
        {"http://x/a": _resp_error(404), "http://x/b": ConnectionError("boom")}))
    by = {o.title: o.status for o in r.outcomes}
    assert by == {"A": GONE, "B": DEGRADED}
    assert r.kept_pinned == 2                            # both surfaced as unhealthy
    assert ca.read_bytes() == b"a" and cb.read_bytes() == b"b"


def test_tally_counts_by_status(tmp_path):
    fs = [Fetchable("A", "u1", _pin(tmp_path, "a", b"x")),
          Fetchable("B", "u2", _pin(tmp_path, "b", b"y")),
          Fetchable("C", "u3", _pin(tmp_path, "c", b"z"))]
    r = refresh_fetchables(fs, download=_stub({"u1": b"x", "u2": b"y2", "u3": b"z"}))
    assert r.tally() == {NOT_CHANGED: 2, CHANGED: 1}


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
