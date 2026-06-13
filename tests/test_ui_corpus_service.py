from corpus.utils import sanitize_filename
from server.services.corpus import to_int


class TestToInt:
    def test_integer_input(self):
        assert to_int(42) == 42

    def test_string_number(self):
        assert to_int("123") == 123

    def test_invalid_string(self):
        assert to_int("abc") == 0

    def test_none_returns_default(self):
        assert to_int(None) == 0

    def test_custom_default(self):
        assert to_int("bad", default=99) == 99

    def test_float_string(self):
        assert to_int("3.14") == 0

    def test_empty_string(self):
        assert to_int("") == 0


class TestSanitizeFilename:
    def test_replaces_slashes(self):
        assert "/" not in sanitize_filename("a/b/c")
        assert "\\" not in sanitize_filename("a\\b\\c")

    def test_replaces_spaces(self):
        result = sanitize_filename("hello world")
        assert " " not in result

    def test_preserves_normal_text(self):
        assert sanitize_filename("simple") == "simple"

    def test_empty_string(self):
        result = sanitize_filename("")
        assert isinstance(result, str)
