"""Part 2 item 4 — `refresh documents`: staged, diffed, keep-pinned-by-default."""

import pytest

from corpus import refresh as refresh_mod
from corpus.locator import corpus_raw_path
from corpus.refresh import refresh_corpus


@pytest.fixture
def env(tmp_path, monkeypatch):
    from settings import settings

    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    monkeypatch.setattr(settings, "corpus_dir", corpus_dir)
    return corpus_dir


def _items(monkeypatch, items):
    monkeypatch.setattr(refresh_mod, "load_download_list", lambda: [dict(i) for i in items])


def _download(monkeypatch, mapping):
    import corpus.downloader as dl

    def fake(url, auth=None):
        val = mapping[url]
        if isinstance(val, Exception):
            raise val
        return val

    monkeypatch.setattr(dl, "download_file", fake)


def _pin(corpus_dir, url, content):
    raw = corpus_raw_path(corpus_dir / "raw", url)
    raw.parent.mkdir(parents=True, exist_ok=True)
    raw.write_bytes(content)
    return raw


class TestRefreshCorpus:
    def test_unchanged_is_noop(self, env, monkeypatch):
        url = "https://x/a"
        _items(monkeypatch, [{"title": "A", "url": url}])
        _pin(env, url, b"same")
        _download(monkeypatch, {url: b"same"})

        r = refresh_corpus(apply=False)
        assert r.unchanged == 1
        assert r.changed == [] and r.adopted == []

    def test_changed_preview_keeps_pinned(self, env, monkeypatch):
        url = "https://x/a"
        _items(monkeypatch, [{"title": "A", "url": url}])
        raw = _pin(env, url, b"old")
        _download(monkeypatch, {url: b"new"})

        r = refresh_corpus(apply=False)
        assert r.changed == ["A"]
        assert r.adopted == []
        assert raw.read_bytes() == b"old"  # pinned copy untouched on preview

    def test_changed_apply_adopts(self, env, monkeypatch):
        url = "https://x/a"
        _items(monkeypatch, [{"title": "A", "url": url}])
        raw = _pin(env, url, b"old")
        _download(monkeypatch, {url: b"new"})

        r = refresh_corpus(apply=True)
        assert r.adopted == ["A"]
        assert raw.read_bytes() == b"new"  # adopted via os.replace
        assert not raw.with_name(raw.name + ".partial").exists()

    def test_new_source_acquired_only_on_apply(self, env, monkeypatch):
        url = "https://x/new"
        _items(monkeypatch, [{"title": "N", "url": url}])
        _download(monkeypatch, {url: b"fresh"})
        raw = corpus_raw_path(env / "raw", url)

        preview = refresh_corpus(apply=False)
        assert preview.new == ["N"] and not raw.exists()

        applied = refresh_corpus(apply=True)
        assert applied.adopted == ["N"] and raw.read_bytes() == b"fresh"

    def test_unreachable_keeps_pinned(self, env, monkeypatch):
        url = "https://x/a"
        _items(monkeypatch, [{"title": "A", "url": url}])
        raw = _pin(env, url, b"good")
        _download(monkeypatch, {url: RuntimeError("network down")})

        r = refresh_corpus(apply=True)
        assert r.unreachable and r.unreachable[0][0] == "A"
        assert raw.read_bytes() == b"good"  # never overwritten on failure

    def test_empty_body_kept_pinned(self, env, monkeypatch):
        # A 200 with an empty/whitespace body is degraded — never overwrite the pinned copy.
        url = "https://x/a"
        _items(monkeypatch, [{"title": "A", "url": url}])
        raw = _pin(env, url, b"good")
        _download(monkeypatch, {url: b"   \n  "})

        r = refresh_corpus(apply=True)
        assert r.degraded and r.degraded[0][0] == "A"
        assert r.adopted == []
        assert raw.read_bytes() == b"good"  # degraded reply rejected, last-good kept

    def test_adopt_invalidates_derived_output(self, env, monkeypatch):
        # After adopting new raw, the stale .txt is removed so a plain `build` re-derives it.
        import json

        url = "https://x/a"
        _items(monkeypatch, [{"title": "A", "url": url}])
        raw = _pin(env, url, b"old")
        _download(monkeypatch, {url: b"new"})
        (env / "A.txt").write_text("derived-from-old")
        (env / "corpus.json").write_text(json.dumps([{"title": "A", "url": url, "path": "A.txt"}]))

        r = refresh_corpus(apply=True)
        assert r.adopted == ["A"]
        assert raw.read_bytes() == b"new"
        assert not (env / "A.txt").exists()  # invalidated → next plain build re-derives

    def test_local_sources_skipped(self, env, monkeypatch):
        _items(monkeypatch, [{"title": "L", "url": "file:local.txt"}])
        r = refresh_corpus(apply=False)
        assert r.skipped_local == 1
        assert r.changed == [] and r.new == []
