#!/usr/bin/env python3
"""Golden-diff guard for the Part 3 / Stage IV stage-protocol refactor.

An orchestration refactor MUST NOT change data. This script hashes every build
artifact into a manifest, so you can snapshot the state *before* the refactor and
assert *after* that nothing drifted — the whole-corpus guarantee the per-key
``mytho status`` cannot give.

What it covers:
  * file-hash (streamed sha256) — every file under ``corpus/``, ``projections/``,
    ``graphs/`` and ``motifs/``: build outputs AND the pinned ``raw/`` caches, so an
    accidental touch of the fetched inputs is caught too.
  * logical-hash — each Chroma collection's records + vectors, ordered
    deterministically. The on-disk Chroma files carry non-deterministic internal
    state (sqlite bookkeeping), so we hash the logical content the pipeline reads
    back, which is the actual invariant.
  * excluded — ``logs/`` (timestamped every run), ``__pycache__``, ``.DS_Store``
    and the manifest itself.

Usage (from the repo root, project installed, outputs built + region-migrated):
    python scripts/golden_diff.py snapshot [--out PATH]
    python scripts/golden_diff.py assert  [--before PATH] [--allow-added]

``assert`` exits non-zero on any *changed* or *removed* artifact (that is drift).
*Added* artifacts also fail — UNLESS they are fingerprint sidecars (``.fp`` /
``.input-fp``) or ``--allow-added`` is passed: the roadmap permits the refactor's
one-off fp-init (projection refit / motif reassembly, no re-fetch, no re-LLM).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from settings import settings  # noqa: E402

# Directories hashed file-by-file, anchored on ROOT (settings paths are relative).
# Chroma (embeddings_dir) is handled logically below; logs_dir is deliberately
# absent (it changes every run).
HASH_DIRS = [
    ROOT / settings.corpus_dir,
    ROOT / settings.projections_dir,
    ROOT / settings.graphs_dir,
    ROOT / settings.motifs_dir,
]

_SKIP_NAMES = {"__pycache__", ".DS_Store", ".golden"}
# Added files allowed through `assert` without --allow-added (the intended fp-init).
_FP_SUFFIXES = (".fp", ".input-fp")

DEFAULT_MANIFEST = ROOT / settings.corpus_dir.parent / ".golden" / "manifest.json"


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _iter_files(root: Path):
    for p in sorted(root.rglob("*")):
        if p.is_file() and not _SKIP_NAMES.intersection(p.parts) and p.name not in _SKIP_NAMES:
            yield p


def _canon(record: dict) -> str:
    # Stable, content-defining serialisation of one chunk's metadata + text.
    return json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


def _hash_chroma() -> dict[str, str]:
    """Logical hash per collection: records + vectors in a stable (id, chunk) order."""
    from embeddings import chroma_manager as cm

    out: dict[str, str] = {}
    for key in cm.get_available_models():
        records, embeddings = cm.get_collection(key).load_data()
        order = sorted(
            range(len(records)),
            key=lambda i: (str(records[i].get("id", "")), str(records[i].get("chunk_index", "")), _canon(records[i])),
        )
        h = hashlib.sha256()
        for i in order:
            h.update(_canon(records[i]).encode("utf-8"))
            if embeddings.size:
                h.update(embeddings[i].tobytes())
        out[f"chroma:{key}"] = h.hexdigest()
    return out


def build_manifest(out_path: Path) -> dict[str, str]:
    manifest: dict[str, str] = {}
    for d in HASH_DIRS:
        if not d.exists():
            continue
        for p in _iter_files(d):
            manifest[str(p.relative_to(ROOT))] = _hash_file(p)
    manifest.update(_hash_chroma())
    if _under(out_path, ROOT):  # never hash the manifest into itself
        manifest.pop(str(out_path.resolve().relative_to(ROOT.resolve())), None)
    return dict(sorted(manifest.items()))


def _under(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def cmd_snapshot(args) -> int:
    out_path = Path(args.out)
    manifest = build_manifest(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    n_files = sum(1 for k in manifest if not k.startswith("chroma:"))
    n_chroma = sum(1 for k in manifest if k.startswith("chroma:"))
    print(f"snapshot → {out_path}  ({n_files} files + {n_chroma} chroma collections)")
    return 0


def cmd_assert(args) -> int:
    before_path = Path(args.before)
    if not before_path.exists():
        print(f"error: baseline manifest not found: {before_path}", file=sys.stderr)
        print("  run `python scripts/golden_diff.py snapshot` BEFORE the refactor.", file=sys.stderr)
        return 2

    before = json.loads(before_path.read_text(encoding="utf-8"))
    now = build_manifest(before_path)

    changed = sorted(k for k in before.keys() & now.keys() if before[k] != now[k])
    removed = sorted(before.keys() - now.keys())
    added = sorted(now.keys() - before.keys())

    for k in changed:
        print(f"CHANGED  {k}")
    for k in removed:
        print(f"REMOVED  {k}")
    allowed_added = [k for k in added if k.endswith(_FP_SUFFIXES) or args.allow_added]
    flagged_added = [k for k in added if k not in set(allowed_added)]
    for k in flagged_added:
        print(f"ADDED    {k}")
    for k in allowed_added:
        print(f"added (allowed: fp-init)  {k}")

    drift = bool(changed or removed or flagged_added)
    if drift:
        print(f"\nDRIFT: {len(changed)} changed, {len(removed)} removed, {len(flagged_added)} unexpected added.")
        print("An orchestration refactor must not change data — investigate before trusting the state.")
        return 1
    print(f"\nOK: byte-identical ({len(allowed_added)} fp-init additions allowed).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Golden-diff guard for the stage-protocol refactor.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_snap = sub.add_parser("snapshot", help="hash all artifacts into a baseline manifest")
    p_snap.add_argument("--out", default=str(DEFAULT_MANIFEST), help=f"manifest path (default: {DEFAULT_MANIFEST})")
    p_snap.set_defaults(func=cmd_snapshot)

    p_assert = sub.add_parser("assert", help="recompute and compare against a baseline manifest")
    p_assert.add_argument("--before", default=str(DEFAULT_MANIFEST), help=f"baseline manifest (default: {DEFAULT_MANIFEST})")
    p_assert.add_argument("--allow-added", action="store_true", help="permit any new file, not just fp sidecars")
    p_assert.set_defaults(func=cmd_assert)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
