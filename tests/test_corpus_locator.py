"""Part 1 step 2 — locator normalization + document_id = blake2b(locator) (D1, data-model §5)."""

from corpus.locator import document_id, normalize_locator


class TestNormalizeWeb:
    def test_lowercases_scheme_and_host_only(self):
        assert normalize_locator("HTTP://Example.COM/Path") == "http://example.com/Path"  # path case kept

    def test_drops_default_port(self):
        assert normalize_locator("http://x.com:80/a") == "http://x.com/a"
        assert normalize_locator("https://x.com:443/a") == "https://x.com/a"

    def test_keeps_nondefault_port(self):
        assert normalize_locator("http://x.com:8080/a") == "http://x.com:8080/a"

    def test_drops_fragment(self):
        assert normalize_locator("http://x.com/a#section") == "http://x.com/a"

    def test_decodes_unreserved_only(self):
        # %7E → ~ (unreserved); %2F stays (reserved — could change meaning).
        assert normalize_locator("http://x.com/%7Euser") == "http://x.com/~user"
        assert normalize_locator("http://x.com/a%2Fb") == "http://x.com/a%2Fb"

    def test_collapses_single_trailing_slash(self):
        assert normalize_locator("http://x.com/a/") == "http://x.com/a"

    def test_keeps_query_verbatim(self):
        assert normalize_locator("http://x.com/a?id=5") == "http://x.com/a?id=5"


class TestNormalizeLocal:
    def test_strips_file_scheme_and_normalizes(self):
        assert normalize_locator("file:sub/./epic.pdf") == "sub/epic.pdf"

    def test_preserves_case(self):
        assert normalize_locator("file:Myth.txt") == "Myth.txt"


class TestDocumentId:
    def test_cosmetic_variants_collapse_to_one_id(self):
        # The data-model §5 example: host case, trailing slash, %7E≡~, dropped fragment.
        a = document_id("https://Example.com/~user/Text/")
        b = document_id("https://example.com/%7Euser/Text#intro")
        assert a == b

    def test_query_and_path_case_differences_do_not_collapse(self):
        assert document_id("http://x.com/A") != document_id("http://x.com/a")  # path case
        assert document_id("http://x.com/a?v=1") != document_id("http://x.com/a?v=2")  # query

    def test_distinct_sources_distinct_ids(self):
        assert document_id("http://x.com/iliad") != document_id("http://x.com/odyssey")

    def test_is_32_hex(self):
        did = document_id("http://x.com/a")
        assert len(did) == 32 and all(c in "0123456789abcdef" for c in did)

    def test_stable_across_calls(self):
        assert document_id("file:local.txt") == document_id("file:local.txt")
