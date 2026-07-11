"""Safe profile cache helpers.

The cache stores only profile metadata. It must never store source rows.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile

from test_data_agent.core.dataset import DatasetProfile


DEFAULT_PROFILE_CACHE_DIR = Path(".test_data_agent_cache") / "profiles"
DEFAULT_RULE_SAMPLE_ROWS = 50_000


def csv_folder_fingerprint(
    input_folder: Path,
    rule_sample_rows: int = DEFAULT_RULE_SAMPLE_ROWS,
) -> str:
    digest = hashlib.sha256()
    digest.update(str(rule_sample_rows).encode())
    for path in sorted(input_folder.glob("*.csv")):
        stat = path.stat()
        digest.update(path.name.encode())
        digest.update(str(stat.st_size).encode())
        digest.update(str(stat.st_mtime_ns).encode())
    return digest.hexdigest()


def cache_path(cache_dir: Path, fingerprint: str) -> Path:
    return cache_dir / f"{fingerprint}.json"


def load_cached_profile(
    input_folder: Path,
    cache_dir: Path = DEFAULT_PROFILE_CACHE_DIR,
    rule_sample_rows: int = DEFAULT_RULE_SAMPLE_ROWS,
) -> DatasetProfile | None:
    fingerprint = csv_folder_fingerprint(input_folder, rule_sample_rows)
    path = cache_path(cache_dir, fingerprint)
    if not path.exists():
        return None
    try:
        return read_profile_cache_file(path, expected_fingerprint=fingerprint)
    except (OSError, ValueError):
        return None


def write_cached_profile(
    input_folder: Path,
    profile: DatasetProfile,
    cache_dir: Path = DEFAULT_PROFILE_CACHE_DIR,
    rule_sample_rows: int = DEFAULT_RULE_SAMPLE_ROWS,
) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_path(cache_dir, csv_folder_fingerprint(input_folder, rule_sample_rows))
    payload = {
        "fingerprint": csv_folder_fingerprint(input_folder, rule_sample_rows),
        "profile": profile.model_dump(mode="json"),
    }
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=cache_dir,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        temporary_path = Path(handle.name)
        json.dump(payload, handle, indent=2, sort_keys=True)
    temporary_path.replace(path)
    return path


def read_profile_cache_file(path: Path, expected_fingerprint: str | None = None) -> DatasetProfile:
    payload = json.loads(path.read_text())
    cached_fingerprint = payload.get("fingerprint") if isinstance(payload, dict) else None
    if expected_fingerprint is not None and cached_fingerprint != expected_fingerprint:
        raise ValueError("profile cache fingerprint mismatch")
    return DatasetProfile.model_validate(payload.get("profile", payload))
