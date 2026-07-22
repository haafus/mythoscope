"""Orchestrate the region / data-model migration (region-implementation.md §6).

Runs the **offline, reversible** prep in order, then hands off the heavy rebuild:

  1. pre-flight   — the new config passes fail-loud validation, the raw archive is present;
  2. baseline     — record pre-migration counts (for validate gate c);
  3. wipe derived — delete the .txt tree, corpus.json, the generated traditions.json,
                    embeddings/, graphs/, projections/, preprocessed/ — but KEEP corpus/raw/;
  4. re-key raw   — sha1(url) → blake2b(locator), in place, no network (rekey_raw.py --apply).

Then it prints the two remaining commands (they are yours to run, so the multi-hour GPU/LLM
rebuild is never triggered silently):

    mytho build                              # rebuild everything off the re-keyed raw (offline)
    python scripts/validate_migration.py     # gate a–d, expect zero orphans

**Dry-run by default** — shows exactly what it would delete/rename. Add --apply to do it.
Nothing here re-fetches; raw is preserved, so the step is reversible (rename back / git for
config+code). Consider copying outputs/ elsewhere first if you want to skip re-paying the rebuild.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus.traditions_config import TraditionsConfigError, load_traditions_tree, validate_traditions  # noqa: E402
from settings import settings  # noqa: E402

SCRIPTS = Path(__file__).resolve().parent


def _config_docs() -> list[dict]:
    import json
    return json.loads((settings.config_dir / "corpus.json").read_text(encoding="utf-8"))


def preflight() -> bool:
    raw = Path(settings.corpus_dir) / "raw"
    if not raw.exists() or not any(raw.iterdir()):
        print(f"ERROR: raw archive {raw} is missing/empty — cannot migrate offline.", file=sys.stderr)
        return False
    try:
        validate_traditions(load_traditions_tree(settings.config_dir), _config_docs())
    except (TraditionsConfigError, OSError) as exc:
        print(f"ERROR: config fails validation — fix it before migrating:\n  {exc}", file=sys.stderr)
        return False
    print("  pre-flight OK: raw present, config valid.")
    return True


def wipe_targets() -> list[Path]:
    corpus = Path(settings.corpus_dir)
    raw = corpus / "raw"
    targets: list[Path] = []
    if corpus.exists():
        targets += [p for p in corpus.iterdir() if p != raw]  # keep raw/, drop the rest
    for d in (settings.embeddings_dir, settings.graphs_dir, settings.projections_dir, settings.preprocessed_dir):
        p = Path(d)
        if p.exists():
            targets.append(p)
    return targets


def wipe(apply: bool) -> None:
    for t in wipe_targets():
        print(f"  {'wiping' if apply else 'would wipe'}: {t}")
        if apply:
            shutil.rmtree(t) if t.is_dir() else t.unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="actually wipe derived + re-key (default: preview)")
    args = ap.parse_args()

    print("1. Pre-flight")
    if not preflight():
        return 2

    print("\n2. Baseline (pre-migration counts)")
    if args.apply:
        subprocess.run([sys.executable, str(SCRIPTS / "validate_migration.py"), "--capture-baseline"], check=False)
    else:
        print("  would capture baseline counts")

    print("\n3. Wipe derived (raw/ is preserved)")
    wipe(args.apply)

    print("\n4. Re-key raw (sha1 → blake2b, in place)")
    subprocess.run([sys.executable, str(SCRIPTS / "rekey_raw.py")] + (["--apply"] if args.apply else []), check=False)

    if args.apply:
        print("\nOffline prep done. Now run the rebuild + validation yourself:")
        print("    mytho build")
        print("    python scripts/validate_migration.py")
        print("    mytho status        # expect zero orphans")
    else:
        print("\nDry run. Re-run with --apply to capture the baseline, wipe derived, and re-key.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
