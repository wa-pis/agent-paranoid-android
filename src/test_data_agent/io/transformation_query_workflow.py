"""Owned configured-SQL capture composition for CLI and MCP workflows.

Configured read authority and shared limits govern captured rows in this temporary
workspace. Consumers reuse the frozen snapshot without reconnecting during review,
local receipt consumption, validation or execution.
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


@dataclass(frozen=True, repr=False)
class _ConfiguredQueryReference:
    """Value-free local reference; no endpoint, credentials or driver callback."""
    adapter: SqlQueryAdapter
    source_id: str
    entity: str
    query_file: str
    max_rows: int
    max_bytes: int
    max_seconds: float


@contextmanager
def _temporary_configured_query_profile(root: Path, profile: BatchProfile, *,
        references: Mapping[str, _ConfiguredQueryReference], max_total_bytes: int,
        max_review_bytes: int, budget: GenerationBudget,
        ) -> Iterator[tuple[Path, TransformationBatch]]:
    """Closed CLI/MCP preparation; one capture, then frozen local consumers.

    Connections come exclusively from existing administrator environment config.
    Query files are bounded workspace snapshots, never arbitrary caller paths.
    The returned root lives only for this context; do not persist row snapshots.
    """
    from tempfile import TemporaryDirectory
    from test_data_agent.io.path_policy import atomic_write_bytes
    from test_data_agent.sql_query_source import SqlQueryProfileLimits

    with TemporaryDirectory(prefix="apa-owned-query-references-") as temporary:
        bindings: dict[str, _QueryBatchInput] = {}
        consumed = 0
        try:
            if not references or set(references) - {item.source for item in profile.inputs}:
                raise ValueError
            for index, (source, reference) in enumerate(references.items()):
                if type(reference) is not _ConfiguredQueryReference or type(reference.adapter) is not SqlQueryAdapter:
                    raise ValueError
                limits = SqlQueryProfileLimits.from_env()
                query = read_mapping_snapshot(root, reference.query_file,
                    max_bytes=min(limits.max_query_bytes, max_total_bytes), budget=budget,
                    total_limit=EffectiveInputLimit(InputDimension.TOTAL_BYTES, max_total_bytes, "batch_input_run"),
                    consumed_bytes=consumed).payload
                consumed += len(query)
                query_path = Path(temporary).resolve() / f"query-{index}.sql"
                atomic_write_bytes(query_path, query)
                request = SqlQueryProfileRequest(reference.adapter, reference.source_id,
                    reference.entity, query_path, limits)
                request.validate()
                config: PostgresConfig | TrinoConfig
                if reference.adapter is SqlQueryAdapter.POSTGRES:
                    config = PostgresConfig.from_env()
                    if reference.source_id != config.source_id:
                        raise ValueError
                else:
                    config = TrinoConfig.from_env()
                    if reference.source_id != "trino":
                        raise ValueError
                bindings[source] = _QueryBatchInput(request, config, reference.max_rows,
                    reference.max_bytes, reference.max_seconds)
        except (GenerationLimitError, TransformationLimitError, QueryWorkBudgetExceeded):
            raise
        except Exception:
            raise TransformationBatchError("invalid configured SQL reference") from None
        with _temporary_query_batch_profile(root, profile, queries=bindings,
                max_total_bytes=max_total_bytes, max_review_bytes=max_review_bytes,
                budget=budget) as captured:
            yield captured



def _load_configured_query_references(root: Path, path: str, *, max_bytes: int,
        budget: GenerationBudget) -> Mapping[str, _ConfiguredQueryReference]:
    """Strict bounded reference-file schema; never connection configuration."""
    from typing import Literal
    from pydantic import BaseModel, ConfigDict, Field
    from test_data_agent.core.transformation_yaml import _load_private_yaml

    class Reference(BaseModel):
        model_config = ConfigDict(extra="forbid", strict=True)
        adapter: Literal["postgres", "trino"]
        source_id: str = Field(min_length=1, max_length=256)
        entity: str = Field(min_length=1, max_length=256)
        query_file: str = Field(min_length=1, max_length=4096)
        max_rows: int = Field(gt=0, lt=2**63 - 1)
        max_bytes: int = Field(gt=0, le=2**63 - 1)
        max_seconds: float = Field(ge=0.1, le=3600, allow_inf_nan=False)

    class References(BaseModel):
        model_config = ConfigDict(extra="forbid", strict=True)
        schema_version: Literal["0.1"]
        queries: dict[str, Reference] = Field(min_length=1, max_length=1000)

    try:
        data = read_mapping_snapshot(root, path, max_bytes=max_bytes, budget=budget).payload
        parsed = References.model_validate(_load_private_yaml(data, max_bytes))
        return {source: _ConfiguredQueryReference(SqlQueryAdapter(item.adapter), item.source_id,
            item.entity, item.query_file, item.max_rows, item.max_bytes, item.max_seconds)
            for source, item in parsed.queries.items()}
    except (GenerationLimitError, TransformationLimitError):
        raise
    except Exception:
        raise TransformationBatchError("invalid configured SQL reference file") from None
