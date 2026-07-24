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

# ---------------------------------------------------------------------------
# reset — delete DERIVED outputs + fp sidecars for the deterministic stages so a
# plain rebuild (no --force) exercises the regeneration path. Caches are kept, so
# the rebuild re-derives from pinned inputs: no re-fetch, no re-LLM, no re-embed.
#   * corpus      — corpus.json + .txt tree; raw/ kept → re-extract from raw
#   * projections — plot .json + .input-fp; Chroma untouched → refit UMAP (seed 42)
#   * graphs      — graph .json + .fp; extraction_cache.jsonl kept → reassemble from cache
#   * motifs      — output .json; raw/ kept → re-parse cached pages
# embeddings (Chroma) and preprocessed/ are NEVER in the deletable set — the fp
# gate then makes `mytho embeddings` a no-op, so nothing is re-embedded.
_RESET_STAGES = {
    "corpus": dict(root=ROOT / settings.corpus_dir, protected={"raw"},
                   delete=lambda p: p.name == "corpus.json" or p.suffix == ".txt"),
    "projections": dict(root=ROOT / settings.projections_dir, protected=set(),
                        delete=lambda p: p.suffix == ".json" or p.name == ".input-fp"),
    "graphs": dict(root=ROOT / settings.graphs_dir, protected=set(),
                   delete=lambda p: p.suffix == ".json" or p.name == ".fp"),
    "motifs": dict(root=ROOT / settings.motifs_dir, protected={"raw"},
                   delete=lambda p: p.suffix == ".json"),
}
# Hard guards: nothing under these, no raw/ cache, no LLM response cache — ever.
_NEVER_TOUCH = [ROOT / settings.embeddings_dir, ROOT / settings.preprocessed_dir]
_NEVER_DELETE_NAMES = {"extraction_cache.jsonl"}


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# The corpus catalog carries `date_downloaded` (a fetch-time wall-clock stamp — not
# reproducible from the pinned raw) and rows in ThreadPool-completion order (unstable).
# It also carries `source_fp`, the stage's input-fingerprint sidecar (a one-off fp-init).
# Hash only its reproducible *content*: rows sorted by document_id, those fields dropped.
# The `.txt` bodies, the per-row output `fingerprint`, path, and counts stay fully guarded.
_CORPUS_CATALOG = (ROOT / settings.corpus_dir / "corpus.json").resolve()
_CATALOG_DROP = ("date_downloaded", "source_fp")


def _hash_corpus_catalog(path: Path) -> str:
    rows = json.loads(path.read_text(encoding="utf-8"))
    norm = sorted(
        ({k: v for k, v in r.items() if k not in _CATALOG_DROP} for r in rows),
        key=lambda r: r.get("document_id", ""),
    )
    payload = json.dumps(norm, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


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
            digest = _hash_corpus_catalog(p) if p.resolve() == _CORPUS_CATALOG else _hash_file(p)
            manifest[str(p.relative_to(ROOT))] = digest
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


def _reset_targets(stage_keys: list[str]) -> list[tuple[str, Path]]:
    targets: list[tuple[str, Path]] = []
    for key in stage_keys:
        spec = _RESET_STAGES[key]
        root: Path = spec["root"]
        if not root.exists():
            continue
        for p in sorted(root.rglob("*")):
            if not p.is_file():
                continue
            if spec["protected"].intersection(p.relative_to(root).parts):
                continue
            if spec["delete"](p):
                targets.append((key, p))
    return targets


def _assert_reset_safe(targets: list[tuple[str, Path]]) -> None:
    # Defence in depth: even if a spec were mis-edited, never delete a cache or store.
    for _key, p in targets:
        for banned in _NEVER_TOUCH:
            if _under(p, banned):
                raise SystemExit(f"refusing to delete protected store: {p}")
        parts = p.relative_to(ROOT).parts
        if "raw" in parts or p.name in _NEVER_DELETE_NAMES:
            raise SystemExit(f"refusing to delete cache: {p}")


def cmd_reset(args) -> int:
    stage_keys = [s.strip() for s in args.stages.split(",") if s.strip()]
    unknown = [s for s in stage_keys if s not in _RESET_STAGES]
    if unknown:
        print(f"error: unknown stage(s): {', '.join(unknown)}. valid: {', '.join(_RESET_STAGES)}", file=sys.stderr)
        return 2

    targets = _reset_targets(stage_keys)
    _assert_reset_safe(targets)

    by_stage: dict[str, list[Path]] = {}
    for key, p in targets:
        by_stage.setdefault(key, []).append(p)
    for key in stage_keys:
        files = by_stage.get(key, [])
        print(f"{key}: {len(files)} derived file(s)")
        for p in files[:4]:
            print(f"    {p.relative_to(ROOT)}")
        if len(files) > 4:
            print(f"    … +{len(files) - 4} more")

    print(f"\nPRESERVED (never touched): raw/ caches, graphs' extraction_cache.jsonl, "
          f"Chroma ({settings.embeddings_dir}), preprocessed ({settings.preprocessed_dir}).")

    if not args.apply:
        print(f"\nDRY RUN — {len(targets)} file(s) would be deleted. Re-run with --apply to delete.")
        return 0

    for _key, p in targets:
        p.unlink()
    print(f"\nDeleted {len(targets)} derived file(s). Now rebuild WITHOUT --force, then `golden_diff assert`.")
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

    p_reset = sub.add_parser("reset", help="delete derived outputs + fp sidecars (keep caches) to force a deterministic rebuild")
    p_reset.add_argument("--stages", default=",".join(_RESET_STAGES),
                         help=f"comma-separated stages to reset (default: {','.join(_RESET_STAGES)})")
    p_reset.add_argument("--apply", action="store_true", help="actually delete (default: dry run)")
    p_reset.set_defaults(func=cmd_reset)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
