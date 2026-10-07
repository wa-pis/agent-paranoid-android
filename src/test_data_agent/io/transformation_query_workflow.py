"""Closed SQL/common workflow composition; no registration or dataset approval.

Only fictional development may materialize captured rows into this owned
workspace. Existing CLI/MCP candidate consumers subsequently read the frozen
snapshot and never reconnect during review, receipt consumption or execution.
"""
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import math
import os
from typing import cast

from test_data_agent.core.limits import GenerationBudget, GenerationLimitError
from test_data_agent.core.transformation_limits import EffectiveInputLimit, InputDimension, TransformationLimitError, resolve_input_limit
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.core.transformation_yaml import load_behavior_policy_yaml
from test_data_agent.io.mapping_snapshot import read_mapping_snapshot
from test_data_agent.io.transformation_batch import TransformationBatch, TransformationBatchError
from test_data_agent.io.transformation_batch_profile import BatchProfile, temporary_batch_profile
from test_data_agent.postgres_config import PostgresConfig
from test_data_agent.sql_query_source import SqlQueryAdapter, SqlQueryProfileRequest
from test_data_agent.trino_config import TrinoConfig
from test_data_agent.trino_work_budget import QueryWorkBudgetExceeded


@dataclass(frozen=True, repr=False)
class _QueryBatchInput:
    request: SqlQueryProfileRequest
    config: PostgresConfig | TrinoConfig
    max_rows: int
    max_bytes: int
    max_seconds: float


@contextmanager
def _temporary_query_batch_profile(root: Path, profile: BatchProfile, *,
        queries: Mapping[str, _QueryBatchInput], max_total_bytes: int,
        max_review_bytes: int, budget: GenerationBudget,
        ) -> Iterator[tuple[Path, TransformationBatch]]:
    """Trusted configuration only; adapters and factories cannot be caller code."""
    captured: dict[str, SnapshotPart] = {}
    try:
        profile = BatchProfile.model_validate(profile.model_dump(mode="json", exclude_unset=True, warnings=False))
        if type(max_total_bytes) is not int or max_total_bytes < 1:
            raise ValueError
        resolve_input_limit(InputDimension.TOTAL_BYTES, profile.resource_limits, os.environ).check(
            max_total_bytes, requested=True)
        if (not queries or set(queries) - {item.source for item in profile.inputs}
                or len({item.source for item in profile.inputs}) != len(profile.inputs)):
            raise ValueError
        # Freeze every policy before any driver connection. The temporary common
        # loader checks these same bytes again after capture before publication.
        policies = {}
        policy_snapshots: dict[str, bytes] = {}
        forbidden = {profile.validation, *(item.policy for item in profile.inputs),
                     *(path for item in profile.inputs for path in (*item.mappings, *item.generation_policies))}
        if set(queries) & forbidden:
            raise ValueError
        for item in profile.inputs:
            if item.source not in queries:
                continue
            binding = queries[item.source]
            if (type(binding) is not _QueryBatchInput
                    or type(binding.max_bytes) is not int or not 0 < binding.max_bytes <= max_total_bytes
                    or type(binding.max_rows) is not int or not 0 < binding.max_rows < 2**63 - 1
                    or type(binding.max_seconds) not in {int, float}
                    or not math.isfinite(binding.max_seconds) or not 0.1 <= binding.max_seconds <= 3600):
                raise ValueError
            binding.request.validate()
            source_path = Path(item.source)
            if (source_path.is_absolute() or ".." in source_path.parts
                    or not source_path.parts or source_path.parts[0] == "batch.yaml"
                    or item.entity != binding.request.entity_name):
                raise ValueError
            policy_bytes = read_mapping_snapshot(root, item.policy,
                max_bytes=max_total_bytes, budget=budget,
                total_limit=EffectiveInputLimit(InputDimension.TOTAL_BYTES, max_total_bytes, "batch_input_run"),
                consumed_bytes=sum(len(data) for data in policy_snapshots.values())).payload
            if sum(len(data) for data in policy_snapshots.values()) + len(policy_bytes) > max_total_bytes:
                raise ValueError
            policy = load_behavior_policy_yaml(policy_bytes, max_bytes=max_total_bytes, budget=budget)
            if (policy.input_format != f"{binding.request.adapter.value}_query"
                    or {field.entity for field in policy.fields} != {item.entity}):
                raise ValueError
            if ((binding.request.adapter is SqlQueryAdapter.POSTGRES
                    and type(binding.config) is not PostgresConfig)
                    or (binding.request.adapter is SqlQueryAdapter.TRINO
                        and type(binding.config) is not TrinoConfig)):
                raise ValueError
            if isinstance(binding.config, PostgresConfig):
                binding.config.validate()
            else:
                binding.config.validate_security()
            for dimension, amount in ((InputDimension.BYTES, binding.max_bytes),
                                      (InputDimension.ROWS, binding.max_rows)):
                resolve_input_limit(dimension, policy.resource_limits, os.environ).check(amount, requested=True)
            policies[item.source] = policy
            policy_snapshots[item.source] = policy_bytes
        for item in profile.inputs:
            if item.source not in queries:
                continue
            binding = queries[item.source]
            if (type(binding.max_bytes) is not int or binding.max_bytes <= 0
                    or binding.max_bytes > max_total_bytes - sum(len(part.payload) for part in captured.values())
                    - sum(len(data) for data in policy_snapshots.values())):
                raise ValueError
            seconds = min(binding.max_seconds, budget.remaining_seconds())
            if binding.request.adapter is SqlQueryAdapter.POSTGRES:
                from test_data_agent.io.transformation_postgres_capture import (
                    _PostgresCapture, _capture_configured_postgres,
                )
                source = _capture_configured_postgres(_PostgresCapture(
                    binding.request, cast(PostgresConfig, binding.config), (), None, policies[item.source],
                    binding.max_rows, binding.max_bytes), max_seconds=seconds)
            else:
                from test_data_agent.io.transformation_trino_stream import (
                    _TrinoCapture, _capture_configured_trino,
                )
                source = _capture_configured_trino(_TrinoCapture(
                    binding.request, cast(TrinoConfig, binding.config), binding.request.source_id,
                    policies[item.source], binding.max_rows, binding.max_bytes),
                    max_seconds=seconds)
            budget.check("common SQL capture")
            if sum(len(part.payload) for part in captured.values()) + len(source.payload) > max_total_bytes:
                raise ValueError
            captured[item.source] = source
    except (GenerationLimitError, TransformationLimitError, QueryWorkBudgetExceeded):
        raise
    except Exception:
        raise TransformationBatchError("invalid common SQL capture") from None
    with temporary_batch_profile(root, profile, max_total_bytes=max_total_bytes,
            max_review_bytes=max_review_bytes, budget=budget,
            _captured_query_sources=captured,
            _captured_query_policies=policy_snapshots) as materialized:
        yield materialized
