import pytest

from corpus.sources import (
    is_file_source,
    read_local,
    resolve_local_path,
    source_scheme,
)


class TestSourceScheme:
    def test_https(self):
        assert source_scheme("https://example.com/x") == "https"

    def test_file(self):
        assert source_scheme("file:foo.txt") == "file"

    def test_bare_path_has_no_scheme(self):
        assert source_scheme("sub/foo.txt") == ""

    def test_empty(self):
        assert source_scheme("") == ""


class TestIsFileSource:
    @pytest.mark.parametrize("url", ["file:foo.txt", "file:sub/foo.pdf", "sources/x.txt"])
    def test_true_for_local(self, url):
        assert is_file_source(url) is True

    @pytest.mark.parametrize("url", ["http://x/y", "https://x/y"])
    def test_false_for_web(self, url):
        assert is_file_source(url) is False

    def test_false_for_empty(self):
        # A missing/empty url is NOT a file source (keeps web-cached skip behavior).
        assert is_file_source("") is False


class TestResolveLocalPath:
    def test_file_scheme_relative(self, tmp_path):
        (tmp_path / "foo.txt").write_text("x")
        assert resolve_local_path("file:foo.txt", tmp_path) == (tmp_path / "foo.txt").resolve()

    def test_bare_relative_path(self, tmp_path):
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "foo.txt").write_text("x")
        assert resolve_local_path("sub/foo.txt", tmp_path) == (tmp_path / "sub" / "foo.txt").resolve()

    def test_percent_encoding_decoded(self, tmp_path):
        (tmp_path / "a b.txt").write_text("x")
        assert resolve_local_path("file:a%20b.txt", tmp_path) == (tmp_path / "a b.txt").resolve()

    def test_traversal_rejected(self, tmp_path):
        with pytest.raises(ValueError, match="escapes"):
            resolve_local_path("file:../secret.txt", tmp_path)

    def test_absolute_rejected(self, tmp_path):
        with pytest.raises(ValueError, match="Absolute"):
            resolve_local_path("file:///etc/passwd", tmp_path)

    def test_remote_host_rejected(self, tmp_path):
        with pytest.raises(ValueError, match="Remote"):
            resolve_local_path("file://evil.example/x.txt", tmp_path)

    def test_non_file_scheme_rejected(self, tmp_path):
        with pytest.raises(ValueError, match="Not a local"):
            resolve_local_path("https://example.com/x", tmp_path)


class TestReadLocal:
    def test_reads_bytes(self, tmp_path):
        (tmp_path / "foo.txt").write_bytes(b"hello")
        assert read_local("file:foo.txt", tmp_path) == b"hello"

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            read_local("file:missing.txt", tmp_path)
