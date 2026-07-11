from corpus.clean_gutenberg import (
    _normalize_gutenberg_whitespace,
    _remove_gutenberg_footer_notes_with_count,
    _remove_header_metadata,
    clean_gutenberg_text,
    is_gutenberg_text,
    trim_to_content,
)


class TestTrimToContent:
    def test_start_marker_trims_front(self):
        text = "Translator's preface, all editorial.\n\nBOOK I\nSing, O Muse, the tale."
        out = trim_to_content(text, content_start="Sing, O Muse")
        assert out == "Sing, O Muse, the tale."

    def test_end_marker_trims_back(self):
        text = "The story ends here.\n\nGLOSSARY\nword: meaning"
        out = trim_to_content(text, content_end="GLOSSARY")
        assert out == "The story ends here."

    def test_start_and_end_together(self):
        text = "preface\n\nOm! the body begins\nmiddle\n\nAPPENDIX\nback matter"
        out = trim_to_content(text, content_start="Om! the body begins", content_end="APPENDIX")
        assert out == "Om! the body begins\nmiddle"

    def test_whitespace_tolerant_match(self):
        # marker words separated differently (newline vs space) still match
        text = "front\n\nTell me,\nO   Muse, of the hero"
        out = trim_to_content(text, content_start="Tell me, O Muse")
        assert out.startswith("Tell me,")

    def test_end_uses_last_occurrence(self):
        # a marker word also in a front table of contents must not cut early
        text = "CONTENTS NOTES\n\nreal body text\n\nNOTES\n1. a note"
        out = trim_to_content(text, content_end="NOTES")
        assert "real body text" in out
        assert "1. a note" not in out

    def test_missing_marker_keeps_text(self):
        text = "some body without the marker"
        out = trim_to_content(text, content_start="NONEXISTENT", content_end="ALSO MISSING")
        assert out == text

    def test_no_markers_is_noop(self):
        text = "unchanged body"
        assert trim_to_content(text) == text


class TestIsGutenbergText:
    def test_detects_start_marker(self):
        text = "*** START OF THE PROJECT GUTENBERG EBOOK BIBLE ***\nActual content."
        assert is_gutenberg_text(text) is True

    def test_detects_end_marker(self):
        text = "Some text.\nEnd of the Project Gutenberg EBook of something"
        assert is_gutenberg_text(text) is True

    def test_detects_url(self):
        text = "Visit www.gutenberg.org for more."
        assert is_gutenberg_text(text) is True

    def test_rejects_plain_text(self):
        text = "In the beginning God created the heaven and the earth."
        assert is_gutenberg_text(text) is False

    def test_empty_string(self):
        assert is_gutenberg_text("") is False


class TestCleanGutenbergText:
    def test_strips_header_and_footer(self):
        text = (
            "Header stuff\n"
            "*** START OF THE PROJECT GUTENBERG EBOOK TEST ***\n"
            "\n"
            "Actual book content here.\n"
            "More content.\n"
            "\n"
            "*** END OF THE PROJECT GUTENBERG EBOOK TEST ***\n"
            "Footer license stuff"
        )
        result = clean_gutenberg_text(text)
        assert "Actual book content here." in result
        assert "More content." in result
        assert "Header stuff" not in result
        assert "Footer license stuff" not in result
        assert "PROJECT GUTENBERG" not in result

    def test_strips_this_project_variant(self):
        text = (
            "Preamble\n"
            "*** START OF THIS PROJECT GUTENBERG EBOOK FOO ***\n\n"
            "The real text.\n\n"
            "*** END OF THIS PROJECT GUTENBERG EBOOK FOO ***\n"
            "Postamble"
        )
        result = clean_gutenberg_text(text)
        assert "The real text." in result
        assert "Preamble" not in result

    def test_returns_original_if_no_markers(self):
        text = "Just plain text with no gutenberg markers."
        result = clean_gutenberg_text(text)
        assert result == text

    def test_empty_input(self):
        assert clean_gutenberg_text("") == ""
        assert clean_gutenberg_text(None) is None  # type: ignore[arg-type]

    def test_preserves_content_between_markers(self):
        content_lines = [f"Line {i} of the book." for i in range(50)]
        content = "\n".join(content_lines)
        text = (
            "*** START OF THE PROJECT GUTENBERG EBOOK X ***\n\n"
            f"{content}\n\n"
            "*** END OF THE PROJECT GUTENBERG EBOOK X ***"
        )
        result = clean_gutenberg_text(text)
        for line in content_lines:
            assert line in result

    def test_only_start_marker(self):
        text = "License header\n*** START OF THE PROJECT GUTENBERG EBOOK Y ***\n\nContent without end marker."
        result = clean_gutenberg_text(text)
        assert "Content without end marker." in result
        assert "License header" not in result

    def test_only_end_marker(self):
        text = "Content before end marker.\n\n*** END OF THE PROJECT GUTENBERG EBOOK Z ***\nLicense footer"
        result = clean_gutenberg_text(text)
        assert "Content before end marker." in result
        assert "License footer" not in result


class TestRemoveFootnotes:
    def test_strips_trailing_numbered_footnotes(self):
        text = "Body one.\n\nBody two.\n\n[1] First note.\n\n[2] Second note,\nwrapped line."
        cleaned, count = _remove_gutenberg_footer_notes_with_count(text)
        assert "Body one." in cleaned
        assert "Body two." in cleaned
        assert "[1]" not in cleaned and "[2]" not in cleaned
        assert count == 1

    def test_inline_footnote_reference_does_not_truncate_body(self):
        # Regression: a lone "[1] …" mid-body must NOT delete the rest of the text.
        text = "Chapter 1.\n\n[1] is a marker but the tale continues.\n\nThe hero set out.\n\nThe end."
        cleaned, count = _remove_gutenberg_footer_notes_with_count(text)
        assert "The hero set out." in cleaned
        assert "The end." in cleaned
        assert count == 0


class TestNormalizeWhitespace:
    def test_removes_decorative_lines(self):
        text = "Before.\n**********\nAfter."
        result = _normalize_gutenberg_whitespace(text)
        assert "****" not in result
        assert "Before." in result
        assert "After." in result

    def test_strips_trailing_whitespace(self):
        text = "Line with trailing spaces   \nNext line"
        result = _normalize_gutenberg_whitespace(text)
        assert "   \n" not in result


class TestRemoveHeaderMetadata:
    def test_removes_translated_by(self):
        text = "Translated by John Smith\n\nActual content."
        result = _remove_header_metadata(text)
        assert "Translated by" not in result
        assert "Actual content." in result

    def test_removes_copyright(self):
        text = "Copyright 1922\n\nThe story begins."
        result = _remove_header_metadata(text)
        assert "Copyright" not in result
        assert "The story begins." in result

    def test_preserves_normal_text(self):
        text = "In the beginning was the Word.\nAnd the Word was with God."
        result = _remove_header_metadata(text)
        assert "In the beginning" in result
