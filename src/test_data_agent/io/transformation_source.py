"""Private fixed CSV source snapshots; not transformation authorization."""

import csv
import os
from collections.abc import Sequence
from pathlib import Path

from test_data_agent.adapters.csv_file import csv_profile_to_dataset_profile
from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.limits import (
    DEFAULT_MAX_INPUT_COLUMNS, DEFAULT_MAX_INPUT_FILE_BYTES, GenerationBudget,
)
from test_data_agent.core.transformation_approval import ApprovalRequest, prepare_approval_request
from test_data_agent.core.transformation_mapping import CsvMapping
from test_data_agent.core.transformation_policy import SubstituteAction, SynthesizeAction
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.core.transformation_yaml import load_behavior_policy_yaml
from test_data_agent.csv_profiler import profile_csv_bytes
from test_data_agent.io.mapping_snapshot import read_mapping_snapshot
from test_data_agent.io.path_policy import open_regular_file


class TransformationSourceError(ValueError):
    """Invalid source snapshot or stale profile; never echo source values."""


def prepare_csv_review_request(
    policy_yaml: bytes, source: SnapshotPart, referenced_parts: Sequence[SnapshotPart], *,
    max_total_bytes: int, max_review_bytes: int, budget: GenerationBudget,
) -> ApprovalRequest:
    """Derive review evidence from the same fixed CSV bytes bound to approval."""
    try:
        budget.check("transformation source review")
        if (not isinstance(source, SnapshotPart) or source.kind != "source"
                or type(source.name) is not str or not source.name
                or type(source.payload) is not bytes
                or len(referenced_parts) > 3 * DEFAULT_MAX_INPUT_COLUMNS
                or any(not isinstance(part, SnapshotPart)
                       or part.kind not in {"mapping", "generation_policy"}
                       for part in referenced_parts)):
            raise ValueError
        profile = csv_profile_to_dataset_profile(profile_csv_bytes(
            source.payload, source.name, budget=budget,
            max_bytes=min(DEFAULT_MAX_INPUT_FILE_BYTES, max_total_bytes),
        ))
        evidence_json = profile.model_dump_json().encode("utf-8")
        return prepare_approval_request(
            policy_yaml, evidence_json, (source, *referenced_parts),
            max_total_bytes=max_total_bytes, max_review_bytes=max_review_bytes, budget=budget,
        )
    except (OSError, ValueError, TypeError, AttributeError, csv.Error):
        raise TransformationSourceError("invalid transformation source review") from None


def prepare_csv_review_from_paths(
    source_path: Path, table_name: str, policy_root: Path, policy_path: str, *,
    max_total_bytes: int, max_review_bytes: int, budget: GenerationBudget,
) -> ApprovalRequest:
    """Read private inputs once and prepare a value-free local CSV review."""
    try:
        policy_yaml = read_mapping_snapshot(
            policy_root, policy_path, max_bytes=max_total_bytes, budget=budget,
        ).payload
        policy = load_behavior_policy_yaml(policy_yaml, max_bytes=max_total_bytes, budget=budget)
        mapping_paths = {domain.mapping.path for domain in policy.domains
                         if isinstance(domain.mapping, CsvMapping)}
        generation_paths: set[str] = set()
        for decision in policy.fields:
            action = decision.behavior
            if isinstance(action, SynthesizeAction):
                generation_paths.add(action.generation_policy_ref)
            elif isinstance(action, SubstituteAction):
                if isinstance(action.mapping, CsvMapping):
                    mapping_paths.add(action.mapping.path)
                if isinstance(action.unmatched, SynthesizeAction):
                    generation_paths.add(action.unmatched.generation_policy_ref)
        if len(mapping_paths) + len(generation_paths) > 3 * DEFAULT_MAX_INPUT_COLUMNS:
            raise ValueError
        referenced = tuple(
            SnapshotPart(kind, path, read_mapping_snapshot(
                policy_root, path, max_bytes=max_total_bytes, budget=budget,
            ).payload)
            for kind, paths in (("mapping", mapping_paths), ("generation_policy", generation_paths))
            for path in sorted(paths)
        )
        source = load_csv_source_snapshot(
            source_path, table_name, budget=budget,
            max_bytes=min(DEFAULT_MAX_INPUT_FILE_BYTES, max_total_bytes),
        )
        return prepare_csv_review_request(
            policy_yaml, source, referenced, max_total_bytes=max_total_bytes,
            max_review_bytes=max_review_bytes, budget=budget,
        )
    except (OSError, ValueError, TypeError, AttributeError):
        raise TransformationSourceError("invalid transformation source review") from None


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
