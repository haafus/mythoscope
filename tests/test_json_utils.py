import os

import pytest

from json_utils import load_json_optional, save_json


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "x.json"
    save_json(path, {"a": 1})
    assert load_json_optional(path) == {"a": 1}


def test_missing_file_returns_none(tmp_path):
    assert load_json_optional(tmp_path / "nope.json") is None


def test_interrupted_write_keeps_old_file(tmp_path):
    path = tmp_path / "x.json"
    save_json(path, {"a": 1})

    # A non-serializable value makes json.dump fail partway through the write.
    with pytest.raises(TypeError):
        save_json(path, {"bad": object()})

    assert load_json_optional(path) == {"a": 1}  # previous content untouched
    assert not [f for f in os.listdir(tmp_path) if f.endswith(".tmp")]  # temp cleaned up
