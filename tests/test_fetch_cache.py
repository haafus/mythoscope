"""Phase 1 — validate-before-commit staging in the shared fetch layer."""

import pytest

import fetch_cache


def _patch_download(monkeypatch, content):
    import corpus.downloader as dl
    monkeypatch.setattr(dl, "download_file", lambda url, auth=None: content)


class TestValidateBeforeCommit:
    def test_valid_commits_atomically(self, tmp_path, monkeypatch):
        _patch_download(monkeypatch, b"good bytes")
        cache = tmp_path / "page"
        out = fetch_cache.fetch_to_cache("http://u", cache, validate=lambda b: True)
        assert out == b"good bytes"
        assert cache.read_bytes() == b"good bytes"
        assert not cache.with_name("page.partial").exists()   # staging consumed by os.replace

    def test_no_validator_still_commits(self, tmp_path, monkeypatch):
        _patch_download(monkeypatch, b"plain")
        cache = tmp_path / "page"
        assert fetch_cache.fetch_to_cache("http://u", cache) == b"plain"
        assert cache.read_bytes() == b"plain"
        assert not cache.with_name("page.partial").exists()

    def test_invalid_rejects_and_keeps_pinned(self, tmp_path, monkeypatch):
        cache = tmp_path / "page"
        cache.write_bytes(b"pinned good")
        _patch_download(monkeypatch, b"degraded bad")
        with pytest.raises(fetch_cache.FetchRejected):
            fetch_cache.fetch_to_cache("http://u", cache, force=True, validate=lambda b: False)
        assert cache.read_bytes() == b"pinned good"           # live copy untouched
        assert not cache.with_name("page.partial").exists()   # no staging left behind

    def test_invalid_no_cache_raises_and_writes_nothing(self, tmp_path, monkeypatch):
        cache = tmp_path / "page"
        _patch_download(monkeypatch, b"bad")
        with pytest.raises(fetch_cache.FetchRejected):
            fetch_cache.fetch_to_cache("http://u", cache, validate=lambda b: False)
        assert not cache.exists()
        assert not cache.with_name("page.partial").exists()

    def test_transport_failure_propagates_and_keeps_pinned(self, tmp_path, monkeypatch):
        cache = tmp_path / "page"
        cache.write_bytes(b"pinned good")

        def boom(url, auth=None):
            raise RuntimeError("network down")

        import corpus.downloader as dl
        monkeypatch.setattr(dl, "download_file", boom)
        with pytest.raises(RuntimeError):                     # transport error propagates unchanged
            fetch_cache.fetch_to_cache("http://u", cache, force=True, validate=lambda b: True)
        assert cache.read_bytes() == b"pinned good"           # never touched (raised before any write)


class TestOfflineMode:
    """MYTHO_OFFLINE: the fetch layer serves pinned-only, never the network — a frozen rebuild."""

    def _no_network(self, monkeypatch):
        import corpus.downloader as dl
        monkeypatch.setattr(dl, "download_file",
                            lambda *a, **k: pytest.fail("offline mode hit the network"))

    def test_serves_pinned_without_network(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MYTHO_OFFLINE", "1")
        self._no_network(monkeypatch)
        cache = tmp_path / "page"
        cache.write_bytes(b"pinned")
        assert fetch_cache.fetch_to_cache("http://u", cache) == b"pinned"

    def test_force_still_serves_pinned_never_refetches(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MYTHO_OFFLINE", "1")
        self._no_network(monkeypatch)
        cache = tmp_path / "page"
        cache.write_bytes(b"pinned")
        assert fetch_cache.fetch_to_cache("http://u", cache, force=True) == b"pinned"  # force ignored offline

    def test_miss_raises_and_writes_nothing(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MYTHO_OFFLINE", "1")
        self._no_network(monkeypatch)
        cache = tmp_path / "page"                             # not pinned
        with pytest.raises(fetch_cache.FetchRejected):
            fetch_cache.fetch_to_cache("http://u", cache)
        assert not cache.exists() and not cache.with_name("page.partial").exists()

    def test_disabled_by_default(self, tmp_path, monkeypatch):
        monkeypatch.delenv("MYTHO_OFFLINE", raising=False)
        assert not fetch_cache.offline()
        _patch_download(monkeypatch, b"downloaded")
        assert fetch_cache.fetch_to_cache("http://u", tmp_path / "p") == b"downloaded"  # network used
