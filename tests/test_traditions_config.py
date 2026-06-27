import json
from pathlib import Path

_CONFIG = Path(__file__).resolve().parents[1] / "config"


def _load(name: str):
    return json.loads((_CONFIG / name).read_text(encoding="utf-8"))


def test_traditions_config_is_a_tree():
    tree = _load("traditions.json")
    for major, node in tree.items():
        assert isinstance(node, dict) and "traditions" in node, major
        assert isinstance(node["traditions"], dict)


def test_every_book_tradition_is_in_the_tree_under_one_major():
    tree = _load("traditions.json")
    trad_to_majors: dict[str, list[str]] = {}
    for major, node in tree.items():
        for trad in node.get("traditions", {}):
            trad_to_majors.setdefault(trad, []).append(major)

    dupes = {t: m for t, m in trad_to_majors.items() if len(m) > 1}
    assert not dupes, f"traditions under multiple majors: {dupes}"

    books = _load("corpus.json")
    missing = sorted({b["tradition"] for b in books if b.get("tradition")} - set(trad_to_majors))
    assert not missing, f"book traditions missing from the tree: {missing}"


def test_books_do_not_carry_major_tradition():
    books = _load("corpus.json")
    offenders = [b.get("title") for b in books if "major_tradition" in b]
    assert not offenders, f"books still carry major_tradition: {offenders}"
