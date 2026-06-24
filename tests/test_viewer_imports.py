"""Guard: the viewer profile must import and serve without torch or scraping libs.

Runs in a subprocess so blocking is hermetic — in-process, torch is already
imported by other tests.
"""

import os
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]

# chromadb is deliberately NOT blocked (it is part of the viewer profile).
_BLOCKED = [
    "torch",
    "sentence_transformers",
    "transformers",
    "requests",
    "bs4",
    "trafilatura",
    "fitz",
    "pymupdf",
    "fake_useragent",
]

_SCRIPT = """
import sys
for _name in {blocked!r}:
    sys.modules[_name] = None  # makes `import _name` raise ImportError

from server.run_server import create_app
from fastapi.testclient import TestClient

client = TestClient(create_app())
for _path in ("/api/corpus/catalog", "/api/corpus/traditions"):
    _status = client.get(_path).status_code
    assert _status == 200, (_path, _status)

_leaked = [n for n in {blocked!r} if sys.modules.get(n) is not None]
assert not _leaked, "server pulled heavy deps at import time: " + ", ".join(_leaked)
print("OK")
"""


def test_server_imports_without_heavy_deps():
    env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(_ROOT), str(_ROOT / "src")])}
    result = subprocess.run(
        [sys.executable, "-c", _SCRIPT.format(blocked=_BLOCKED)],
        cwd=str(_ROOT),
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert "OK" in result.stdout
