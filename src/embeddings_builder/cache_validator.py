import hashlib
import logging
import zlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

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
        checksum_file = self._get_checksum_file()
        if checksum_file.exists():
            try:
                import json

                with open(checksum_file, encoding="utf-8") as f:
                    self._checksums = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load checksums: {e}")

    def _save_checksums(self) -> None:
        try:
            import json

            checksum_file = self._get_checksum_file()
            checksum_file.parent.mkdir(parents=True, exist_ok=True)
            with open(checksum_file, "w", encoding="utf-8") as f:
                json.dump(self._checksums, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save checksums: {e}")

    def _calculate_crc32(self, data: bytes) -> str:
        return format(zlib.crc32(data) & 0xFFFFFFFF, "08x")

    def _calculate_md5(self, data: bytes) -> str:
        return hashlib.md5(data).hexdigest()

    def _calculate_checksum(self, data: bytes) -> str:
        if self.validation_method == "crc32":
            return self._calculate_crc32(data)
        elif self.validation_method == "md5":
            return self._calculate_md5(data)
        return ""

    def compute_checksum_for_file(self, file_path: Path) -> str | None:
        if not file_path.exists():
            return None
        try:
            with open(file_path, "rb") as f:
                data = f.read()
            return self._calculate_checksum(data)
        except Exception as e:
            logger.error(f"Failed to compute checksum for {file_path}: {e}")
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

    def cleanup_corrupted(self) -> int:
        results = self.validate_all()
        removed = 0

        for file_path in results["corrupted_files"]:
            try:
                base_path = Path(file_path)
                base_path.unlink(missing_ok=True)

                json_path = base_path.with_suffix(".json")
                json_path.unlink(missing_ok=True)

                self._checksums.pop(base_path.name, None)
                removed += 1
                logger.info(f"Removed corrupted cache file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to remove {file_path}: {e}")

        if removed > 0:
            self._save_checksums()

        return removed
