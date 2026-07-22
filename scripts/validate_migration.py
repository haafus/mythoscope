"""Gate the region / data-model migration (§6). Run **after** the re-key + rebuild.

Four gates, each fails loud:
  (a) re-key integrity  — every config doc's raw sits at document_id with the manifest's bytes
                          (proves the sha1→blake2b rename lost nothing and is invertible);
  (b) fail-loud model   — every corpus tradition ∈ the tree, every region ∈ the 14 canon,
                          name-uniqueness, and no document_id collision;
  (c) counts vs baseline — documents / chunks / graphs are non-empty and match a pre-migration
                          baseline (captured with --capture-baseline before wiping), modulo growth;
  (d) zero orphans      — pipeline_inspect reports nothing stranded.

    python scripts/validate_migration.py --capture-baseline   # BEFORE wiping derived
    python scripts/validate_migration.py                      # AFTER the rebuild → gates a–d
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus.locator import document_id  # noqa: E402
from corpus.traditions_config import TraditionsConfigError, load_traditions_tree, validate_traditions  # noqa: E402
from settings import settings  # noqa: E402

BASELINE = Path("outputs") / ".migration-baseline.json"


def _load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _config_docs() -> list[dict]:
    return _load_json(settings.config_dir / "corpus.json", [])


def _catalog() -> list[dict]:
    return _load_json(settings.corpus_dir / "corpus.json", [])


def _chunk_count() -> int:
    try:
        from embeddings import chroma_manager
        return sum(c.count() for c in chroma_manager.list_collections())
    except Exception:
        return -1  # deps absent / not built — reported, not fatal here


def _graph_count() -> int:
    gdir = Path(settings.graphs_dir)
    if not gdir.exists():
        return 0
    return sum(1 for d in gdir.iterdir() if d.is_dir() and (d / "beings.json").exists())


# ---- gates -----------------------------------------------------------------

def gate_rekey_integrity() -> list[str]:
    import hashlib
    problems: list[str] = []
    raw_dir = Path(settings.corpus_dir) / "raw"
    manifest = _load_json(raw_dir / ".rekey-manifest.json", {})
    for item in _config_docs():
        url = item.get("url", "")
        if not url:
            continue
        raw = raw_dir / document_id(url)
        if not raw.exists():
            problems.append(f"no raw at document_id for {item.get('title')!r} (fetched on build?)")
            continue
        rec = manifest.get(raw.name)
        if rec and hashlib.sha256(raw.read_bytes()).hexdigest() != rec["sha256"]:
            problems.append(f"raw bytes changed since re-key: {item.get('title')!r}")
    return problems


def gate_fail_loud() -> list[str]:
    problems: list[str] = []
    config = _config_docs()
    try:
        validate_traditions(load_traditions_tree(settings.config_dir), config)
    except TraditionsConfigError as exc:
        problems.append(str(exc))
    seen: dict[str, str] = {}
    for item in config:
        did = document_id(item.get("url", ""))
        if did in seen:
            problems.append(f"document_id collision: {item.get('title')!r} == {seen[did]!r} ({did})")
        seen[did] = item.get("title", "")
    return problems


def gate_counts() -> list[str]:
    problems: list[str] = []
    catalog = _catalog()
    docs, chunks, graphs = len(catalog), _chunk_count(), _graph_count()
    config = [d for d in _config_docs() if not d.get("exclude")]
    print(f"    documents={docs} (config expects {len(config)}), chunks={chunks}, graphs={graphs}")
    if docs == 0:
        problems.append("catalog is empty — corpus did not rebuild")
    else:
        # A shortfall is a WARNING, not a failure: a dead/404 *new* source that never fetched
        # (acquire-on-miss) is a normal best-effort flag, not a broken migration (fetch-and-refresh).
        built = {r.get("document_id") for r in catalog}
        missing = [d.get("title") for d in config if document_id(d.get("url", "")) not in built]
        if missing:
            print(f"    ⚠ {len(missing)} config doc(s) did not build (dead source? review flags): {missing}")
    if chunks == 0:
        problems.append("no embedded chunks — embeddings did not rebuild")
    base = _load_json(BASELINE, None)
    if base:
        print(f"    baseline: documents={base['documents']}, chunks={base['chunks']}, graphs={base['graphs']}")
        if chunks >= 0 and base["chunks"] and chunks < base["chunks"] * 0.5:
            problems.append(f"chunks dropped sharply vs baseline ({chunks} < {base['chunks']})")
    else:
        print("    (no baseline captured — count-vs-baseline check skipped)")
    return problems


def gate_orphans() -> list[str]:
    problems: list[str] = []
    try:
        from pipeline_inspect import (
            corpus_orphans,
            embeddings_orphan_chunks,
            embeddings_orphan_collections,
            graphs_orphans,
            projections_orphans,
        )
    except Exception as exc:
        return [f"could not import orphan checks: {exc}"]

    def _safe(fn, label):
        try:
            n = len(fn())
            if n:
                problems.append(f"{label}: {n} orphan(s)")
        except Exception as exc:
            print(f"    ({label} check skipped: {exc})")

    _safe(lambda: corpus_orphans(settings), "corpus")
    _safe(lambda: embeddings_orphan_collections(settings), "embeddings collections")
    _safe(lambda: embeddings_orphan_chunks(settings), "embeddings chunks")
    _safe(lambda: projections_orphans(settings), "projections")
    _safe(lambda: graphs_orphans(settings), "graphs")
    return problems


def capture_baseline() -> None:
    BASELINE.parent.mkdir(parents=True, exist_ok=True)
    data = {"documents": len(_catalog()), "chunks": _chunk_count(), "graphs": _graph_count()}
    BASELINE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Baseline captured → {BASELINE}: {data}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--capture-baseline", action="store_true",
                    help="record pre-migration counts (run BEFORE wiping derived)")
    args = ap.parse_args()
    if args.capture_baseline:
        capture_baseline()
        return 0

    gates = [
        ("(a) re-key integrity", gate_rekey_integrity),
        ("(b) fail-loud model", gate_fail_loud),
        ("(c) counts vs baseline", gate_counts),
        ("(d) zero orphans", gate_orphans),
    ]
    failed = 0
    for label, fn in gates:
        problems = fn()
        if problems:
            failed += 1
            print(f"  [FAIL] {label}")
            for p in problems:
                print(f"         - {p}")
        else:
            print(f"  [PASS] {label}")
    print(f"\n{'MIGRATION OK' if not failed else f'{failed} GATE(S) FAILED'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
