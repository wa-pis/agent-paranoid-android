"""Safe profile cache helpers.

The cache stores only profile metadata. It must never store source rows.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.limits import read_limited_text
from test_data_agent.core.serialization import load_limited_json
from test_data_agent.io.path_policy import atomic_write_bytes


DEFAULT_PROFILE_CACHE_DIR = Path(".test_data_agent_cache") / "profiles"
DEFAULT_RULE_SAMPLE_ROWS = 50_000
PROFILE_CACHE_FORMAT_VERSION = 2


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
    path = cache_path(cache_dir, csv_folder_fingerprint(input_folder, rule_sample_rows))
    payload = {
        "format_version": PROFILE_CACHE_FORMAT_VERSION,
        "fingerprint": csv_folder_fingerprint(input_folder, rule_sample_rows),
        "profile": profile.model_dump(mode="json"),
    }
    atomic_write_bytes(
        path,
        json.dumps(payload, indent=2, sort_keys=True).encode("utf-8"),
    )
    return path


def read_profile_cache_file(path: Path, expected_fingerprint: str | None = None) -> DatasetProfile:
    payload = load_limited_json(read_limited_text(path), label="profile cache")
    if not isinstance(payload, dict) or payload.get("format_version") != PROFILE_CACHE_FORMAT_VERSION:
        raise ValueError("unsupported profile cache format")
    cached_fingerprint = payload.get("fingerprint")
    if expected_fingerprint is not None and cached_fingerprint != expected_fingerprint:
        raise ValueError("profile cache fingerprint mismatch")
    return DatasetProfile.model_validate(payload.get("profile"))
