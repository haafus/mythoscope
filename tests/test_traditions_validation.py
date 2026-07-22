"""Part 1 step 1 — fail-loud validation of the region → tradition tree (§2.12)."""

import pytest

from corpus.traditions_config import (
    CANON_REGIONS,
    TraditionsConfigError,
    flat_traditions,
    validate_traditions,
)


def _tree(**regions):
    return {r: {"traditions": {t: {} for t in trads}} for r, trads in regions.items()}


class TestValidateTraditions:
    def test_valid_passes(self):
        tree = _tree(Europe=["Greek", "Norse"])
        validate_traditions(tree, [{"tradition": "Greek"}, {"tradition": "Norse"}])

    def test_non_canon_region_fails(self):
        tree = _tree(Atlantis=["Greek"])
        with pytest.raises(TraditionsConfigError, match="non-canon"):
            validate_traditions(tree, [{"tradition": "Greek"}])

    def test_duplicate_tradition_across_regions_fails(self):
        tree = _tree(Europe=["Greek"], **{"East Asia": ["Greek"]})
        with pytest.raises(TraditionsConfigError, match="both"):
            validate_traditions(tree, [])

    def test_region_tradition_name_clash_fails(self):
        # "Europe" used as both a region key and a tradition name.
        tree = _tree(Europe=["Greek"], **{"East Asia": ["Europe"]})
        with pytest.raises(TraditionsConfigError, match="both a region and a tradition"):
            validate_traditions(tree, [])

    def test_book_tradition_missing_from_tree_fails(self):
        tree = _tree(Europe=["Greek"])
        with pytest.raises(TraditionsConfigError, match="not in the tree"):
            validate_traditions(tree, [{"tradition": "Klingon"}])

    def test_empty_tree_with_a_book_fails(self):
        # The old silent-degradation case: a book tradition with no tree entry.
        with pytest.raises(TraditionsConfigError):
            validate_traditions({}, [{"tradition": "Greek"}])


class TestCanonAndFlat:
    def test_canon_is_14_unique(self):
        assert len(CANON_REGIONS) == 14
        assert len(set(CANON_REGIONS)) == 14

    def test_flat_traditions_maps_to_region(self):
        tree = _tree(Europe=["Greek", "Norse"], **{"East Asia": ["Chinese"]})
        assert flat_traditions(tree) == {"Greek": "Europe", "Norse": "Europe", "Chinese": "East Asia"}
