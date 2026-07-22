"""One-off migration: re-key the corpus raw archive ``sha1(url) → blake2b(locator)`` (D1, §6).

Config-driven and **offline**: for each document in ``config/corpus.json`` compute the old key
(``sha1`` of the raw config url, the pre-migration `fetch_cache.cache_path` scheme) and the new
key (``document_id`` = ``blake2b(normalized locator)``), then rename the raw file **in place**.
Same bytes, new name, no network — a dead/404 source cannot lose data because nothing is
re-fetched. A doc with no raw yet is left for the build's ordinary acquire-on-miss. Idempotent;
**dry-run by default**.

    python scripts/rekey_raw.py            # preview the plan
    python scripts/rekey_raw.py --apply    # rename in place + write a manifest

The manifest (``corpus/raw/.rekey-manifest.json``: ``{new_key: {title, sha256}}``) lets
``validate_migration.py`` confirm the re-key preserved every file's bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from corpus.locator import document_id  # noqa: E402
from settings import settings  # noqa: E402


def _old_key(url: str) -> str:
    # The pre-migration raw key: fetch_cache.cache_path = sha1 over the raw config url.
    return hashlib.sha1(url.encode("utf-8")).hexdigest()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plan_rekey(config: list[dict], raw_dir: Path) -> list[dict]:
    plan = []
    for item in config:
        url = item.get("url", "")
        if not url:
            continue
        old = raw_dir / _old_key(url)
        new = raw_dir / document_id(url)
        if new.exists() and new.stat().st_size > 0:
            status = "already-rekeyed"
        elif old.exists():
            status = "collision" if new.exists() else "rename"
        else:
            status = "missing-raw"
        plan.append({"title": item.get("title", url), "old": old, "new": new, "status": status})
    return plan


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="rename in place (default: preview only)")
    args = ap.parse_args()

    raw_dir = Path(settings.corpus_dir) / "raw"
    config_path = settings.config_dir / "corpus.json"
    if not config_path.exists():
        print(f"ERROR: {config_path} not found", file=sys.stderr)
        return 2
    if not raw_dir.exists():
        print(f"ERROR: raw archive {raw_dir} not found — nothing to re-key", file=sys.stderr)
        return 2

    config = json.loads(config_path.read_text(encoding="utf-8"))
    plan = plan_rekey(config, raw_dir)

    counts: dict[str, int] = {}
    manifest: dict[str, dict] = {}
    for entry in plan:
        counts[entry["status"]] = counts.get(entry["status"], 0) + 1
        print(f"  [{entry['status']:15}] {entry['title'][:44]:44} "
              f"{entry['old'].name[:10]} → {entry['new'].name[:10]}")
        if entry["status"] == "rename" and args.apply:
            entry["old"].rename(entry["new"])
        if entry["status"] in ("rename", "already-rekeyed"):
            f = entry["new"] if entry["new"].exists() else entry["old"]
            if f.exists():
                manifest[entry["new"].name] = {"title": entry["title"], "sha256": _sha256(f)}

    print(f"\n{len(plan)} documents: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    if counts.get("collision"):
        print("  ⚠ collision: an existing new-key file blocks a rename — two locators may "
              "normalize to one id; resolve before proceeding.", file=sys.stderr)
    if counts.get("missing-raw"):
        print("  missing raw is fine: the build fetches those (acquire-on-miss); nothing is lost.")

    if args.apply:
        (raw_dir / ".rekey-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"Applied. Manifest → {raw_dir / '.rekey-manifest.json'}")
        return 1 if counts.get("collision") else 0
    print("Dry run. Re-run with --apply to rename in place.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
