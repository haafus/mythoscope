import hashlib
import logging
import zlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from json_utils import load_json, save_json

logger = logging.getLogger(__name__)


class CacheValidator:
    def __init__(self, cache_dir: Path, validation_method: str = "crc32", ttl_days: int = 30):
        self.cache_dir = Path(cache_dir)
        self.validation_method = validation_method
        self.ttl_days = ttl_days
        self._checksums: dict[str, str] = {}
        self._load_checksums()

    def _get_checksum_file(self) -> Path:
        return self.cache_dir / ".checksums.json"

    def _load_checksums(self) -> None:
        self._checksums = load_json(self._get_checksum_file(), default={})

    def _save_checksums(self) -> None:
        save_json(self._get_checksum_file(), self._checksums, indent=2)

    _CHUNK_SIZE = 1024 * 1024

    def compute_checksum_for_file(self, file_path: Path) -> str | None:
        """Streams the file in chunks so large .npy files are never fully loaded into RAM."""
        if not file_path.exists():
            return None
        try:
            if self.validation_method == "crc32":
                crc = 0
                with open(file_path, "rb") as f:
                    while chunk := f.read(self._CHUNK_SIZE):
                        crc = zlib.crc32(chunk, crc)
                return format(crc & 0xFFFFFFFF, "08x")
            elif self.validation_method == "md5":
                h = hashlib.md5()
                with open(file_path, "rb") as f:
                    while chunk := f.read(self._CHUNK_SIZE):
                        h.update(chunk)
                return h.hexdigest()
            return ""
        except OSError:
            logger.exception("Failed to compute checksum for %s", file_path)
            return None

    def validate_file(self, file_path: Path) -> tuple[bool, str | None]:
        if not file_path.exists():
            return False, None

        if self.ttl_days > 0:
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if datetime.now() - mtime > timedelta(days=self.ttl_days):
                logger.debug(f"Cache file expired: {file_path}")
                return False, None

        stored_checksum = self._checksums.get(file_path.name)
        if not stored_checksum and self.validation_method != "none":
            computed = self.compute_checksum_for_file(file_path)
            if computed:
                self._checksums[file_path.name] = computed
                self._save_checksums()
            return True, computed

        if self.validation_method != "none" and stored_checksum:
            current_checksum = self.compute_checksum_for_file(file_path)
            if current_checksum and current_checksum != stored_checksum:
                logger.warning(f"Cache file corrupted: {file_path}")
                return False, current_checksum

        return True, stored_checksum

    def validate_all(self) -> dict[str, Any]:
        results: dict[str, Any] = {
            "total": 0,
            "valid": 0,
            "corrupted": 0,
            "expired": 0,
            "corrupted_files": [],
            "size_mb": 0.0,
            "size_bytes": 0,
        }

        if not self.cache_dir.exists():
            return results

        for cache_file in self.cache_dir.glob("*.npy"):
            if cache_file.name.startswith("."):
                continue

            results["total"] += 1
            results["size_bytes"] += cache_file.stat().st_size

            json_file = cache_file.with_suffix(".json")
            if json_file.exists():
                results["size_bytes"] += json_file.stat().st_size

            is_valid, checksum = self.validate_file(cache_file)

            if is_valid:
                results["valid"] += 1
            else:
                results["corrupted"] += 1
                results["corrupted_files"].append(str(cache_file))

        results["size_mb"] = results["size_bytes"] / 1024 / 1024
        return results

