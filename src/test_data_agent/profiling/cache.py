"""Safe profile cache helpers.

The cache stores only profile metadata. It must never store source rows.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from test_data_agent.core.dataset import DatasetProfile


DEFAULT_PROFILE_CACHE_DIR = Path(".test_data_agent_cache") / "profiles"


def csv_folder_fingerprint(input_folder: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(input_folder.glob("*.csv")):
        stat = path.stat()
        digest.update(path.name.encode())
        digest.update(str(stat.st_size).encode())
        digest.update(str(stat.st_mtime_ns).encode())
    return digest.hexdigest()


def cache_path(cache_dir: Path, fingerprint: str) -> Path:
    return cache_dir / f"{fingerprint}.json"


def load_cached_profile(input_folder: Path, cache_dir: Path = DEFAULT_PROFILE_CACHE_DIR) -> DatasetProfile | None:
    path = cache_path(cache_dir, csv_folder_fingerprint(input_folder))
    if not path.exists():
        return None
    return read_profile_cache_file(path)


def write_cached_profile(input_folder: Path, profile: DatasetProfile, cache_dir: Path = DEFAULT_PROFILE_CACHE_DIR) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_path(cache_dir, csv_folder_fingerprint(input_folder))
    payload = {
        "fingerprint": csv_folder_fingerprint(input_folder),
        "profile": profile.model_dump(mode="json"),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return path


def read_profile_cache_file(path: Path) -> DatasetProfile:
    payload = json.loads(path.read_text())
    return DatasetProfile.model_validate(payload.get("profile", payload))
