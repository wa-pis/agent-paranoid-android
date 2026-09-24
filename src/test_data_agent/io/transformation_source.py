"""Private fixed CSV source snapshots; not transformation authorization."""

import csv
import os
from pathlib import Path

from test_data_agent.adapters.csv_file import csv_profile_to_dataset_profile
from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.limits import DEFAULT_MAX_INPUT_FILE_BYTES, GenerationBudget
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.csv_profiler import profile_csv_bytes
from test_data_agent.io.path_policy import open_regular_file


class TransformationSourceError(ValueError):
    """Invalid source snapshot or stale profile; never echo source values."""


def load_csv_source_snapshot(
    path: Path, table_name: str, *, budget: GenerationBudget,
    max_bytes: int = DEFAULT_MAX_INPUT_FILE_BYTES,
) -> SnapshotPart:
    """Read one regular file once; callers must reuse returned bytes."""
    try:
        budget.check("transformation source snapshot")
        if type(table_name) is not str or not table_name or type(max_bytes) is not int or max_bytes < 1:
            raise ValueError
        with open_regular_file(path) as handle:
            if os.fstat(handle.fileno()).st_size > max_bytes:
                raise ValueError
            payload = handle.read(max_bytes + 1)
        if len(payload) > max_bytes:
            raise ValueError
        budget.check("transformation source snapshot")
        return SnapshotPart("source", table_name, payload)
    except (OSError, ValueError, TypeError, AttributeError):
        raise TransformationSourceError("invalid transformation source") from None


def revalidate_csv_evidence(
    source: SnapshotPart, evidence_json: bytes, *, budget: GenerationBudget,
    max_bytes: int = DEFAULT_MAX_INPUT_FILE_BYTES,
) -> DatasetProfile:
    """Reprofile fixed bytes and reject changed classification/evidence."""
    try:
        budget.check("transformation source evidence")
        if not isinstance(source, SnapshotPart) or source.kind != "source" or type(evidence_json) is not bytes:
            raise ValueError
        reviewed = DatasetProfile.model_validate_json(evidence_json)
        observed = csv_profile_to_dataset_profile(
            profile_csv_bytes(source.payload, source.name, budget=budget, max_bytes=max_bytes)
        )
        if reviewed.model_dump(mode="json") != observed.model_dump(mode="json"):
            raise ValueError
        budget.check("transformation source evidence")
        return observed
    except (OSError, ValueError, TypeError, AttributeError, csv.Error):
        raise TransformationSourceError("invalid transformation source evidence") from None
