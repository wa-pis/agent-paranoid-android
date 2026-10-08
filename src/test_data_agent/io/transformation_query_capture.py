"""Closed fictional query-result capture; no database client or public wiring.

An injected stream must enforce backend read-only/scan/statement deadlines.
Local result checks cannot interrupt a blocking driver or bound its allocations.
"""

from test_data_agent.trino_work_budget import QueryWorkBudgetExceeded

import io
import json
import os
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from typing import Any

from test_data_agent.core.limits import (
    DEFAULT_MAX_INPUT_COLUMNS, GenerationBudget,
)
from test_data_agent.core.transformation_limits import (
    EffectiveInputLimit, InputDimension, TransformationLimitError, resolve_input_limit,
)
from test_data_agent.core.privacy import infer_sensitive_from_name
from test_data_agent.core.transformation_policy import BehaviorPolicy, parse_behavior_policy
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.io.transformation_input import source_reader
from test_data_agent.io.transformation_query_snapshot import _capture_query_result
from test_data_agent.sql_query_source import (
    QUERY_SOURCE_POLICY_VERSION, QuerySourceColumn, SqlQueryProfileRequest,
    authorize_query_source, inspect_query_source,
)


@dataclass(frozen=True, repr=False)
class _ResultQuery:
    sql: str = field(repr=False)
    max_rows: int
    adapter: str
    source_id: str
    table: str
    columns: tuple[str, ...]
    cell_chars: EffectiveInputLimit


def _capture_authorized_result(
    request: SqlQueryProfileRequest, *, allowed_tables: frozenset[str],
    source_columns: tuple[QuerySourceColumn, ...], schema: Any,
    stream: Callable[[_ResultQuery], AbstractContextManager[Iterator[Any]]],
    policy: BehaviorPolicy, max_rows: int, max_bytes: int, budget: GenerationBudget,
    expected_query_sha256: str | None = None,
) -> SnapshotPart:
    """Authorize before callback; bind context/schema/ordered batches exactly.

    Source columns must be the frozen allowlisted metadata, never unrestricted
    discovery. This private development boundary accepts fictional streams only.
    """
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq

        budget.check("query capture preflight")
        if (type(max_rows) is not int or not 0 < max_rows < 2**63 - 1
                or type(max_bytes) is not int or not 0 < max_bytes <= 2**63 - 1
                or not isinstance(schema, pa.Schema) or schema.metadata
                or not len(schema)
                or type(source_columns) is not tuple
                or not 0 < len(source_columns) <= DEFAULT_MAX_INPUT_COLUMNS
                or type(allowed_tables) is not frozenset
                or not 0 < len(allowed_tables) <= DEFAULT_MAX_INPUT_COLUMNS
                or any(type(name) is not str or not name or len(name) > 256 for name in allowed_tables)):
            raise ValueError
        policy = parse_behavior_policy(policy)
        limits = {dimension: resolve_input_limit(dimension, policy.resource_limits, os.environ)
                  for dimension in InputDimension}
        limits[InputDimension.ROWS].check(max_rows, requested=True)
        limits[InputDimension.BYTES].check(max_bytes, requested=True)
        limits[InputDimension.COLUMNS].check(len(schema), requested=True)
        row_limit = EffectiveInputLimit(InputDimension.ROWS, max_rows, "query_rows_run")
        byte_limit = EffectiveInputLimit(InputDimension.BYTES, max_bytes, "query_bytes_run")
        draft = inspect_query_source(request)
        if draft.table_name not in allowed_tables:
            raise ValueError
        plan = authorize_query_source(draft, source_columns)
        if expected_query_sha256 is not None and expected_query_sha256 != plan.fingerprint:
            raise ValueError
        if (policy.input_format != f"{plan.adapter.value}_query"
                or tuple(schema.names) != plan.output_fields
                or any(item.entity != plan.entity_name for item in policy.fields)
                or any(infer_sensitive_from_name(item.name) for item in source_columns)):
            raise ValueError
        context = json.dumps({"policy": QUERY_SOURCE_POLICY_VERSION,
            "query": plan.fingerprint, "source": plan.source_id, "entity": plan.entity_name,
            "tables": sorted(allowed_tables), "columns": [
                [item.name, item.data_type, item.nullable] for item in source_columns],
            "max_rows": max_rows, "max_bytes": max_bytes,
            "limits": {dimension.value: [limit.value, limit.origin]
                       for dimension, limit in limits.items()}}, sort_keys=True, separators=(",", ":")).encode()
        byte_limit.check(len(context))
        bound_schema = schema.with_metadata({b"apa.capture": context})
        envelope_bytes = len(b"APA-QUERY-1\n") + len(policy.input_format.encode("ascii")) + 1 + 64 + 1

        class BoundedBuffer(io.BytesIO):
            def write(self, data: Any) -> int:
                budget.check("query capture encoding")
                # Include the fixed envelope, not just the Parquet payload.
                byte_limit.check(self.tell() + len(data) + envelope_bytes)
                return super().write(data)

        # Reuse native type/format checks before the stream can be opened.
        with BoundedBuffer() as preflight:
            pq.write_table(pa.Table.from_batches([], schema=bound_schema), preflight)
            empty = _capture_query_result(preflight.getvalue(), adapter=policy.input_format,
                query_sha256=plan.fingerprint, entity=plan.entity_name, byte_limit=byte_limit)
            source_reader(empty, policy, budget=budget)
        fields = ", ".join(f'"{name}"' for name in plan.output_fields)
        query = _ResultQuery(
            f'SELECT {fields} FROM ({plan.sql}) AS "__apa_capture" LIMIT {max_rows + 1}',
            max_rows + 1, plan.adapter.value, plan.source_id, draft.table_name,
            tuple(item.name for item in source_columns),
            limits[InputDimension.CELL_CHARS],
        )
        rows = decoded = 0
        with BoundedBuffer() as buffer:
            with pq.ParquetWriter(buffer, bound_schema) as writer:
                budget.check("query capture open")
                with stream(query) as batches:
                    for batch in batches:
                        budget.check("query capture batch")
                        if (not isinstance(batch, pa.RecordBatch)
                                or not batch.schema.equals(schema, check_metadata=True)):
                            raise ValueError
                        rows += batch.num_rows
                        decoded += batch.nbytes
                        row_limit.check(rows)
                        limits[InputDimension.CELLS].check(rows * len(schema))
                        limits[InputDimension.EXPANDED_BYTES].check(decoded)
                        if (any(not item.nullable and batch.column(i).null_count
                                       for i, item in enumerate(schema))):
                            raise ValueError
                        writer.write_batch(batch.replace_schema_metadata(bound_schema.metadata))
                    budget.check("query capture stream complete")
            source = _capture_query_result(buffer.getvalue(), adapter=policy.input_format,
                query_sha256=plan.fingerprint, entity=plan.entity_name, byte_limit=byte_limit)
        source_reader(source, policy, budget=budget)
        return source
    except (TransformationLimitError, QueryWorkBudgetExceeded):
        raise
    except Exception:
        pass
    raise ValueError("invalid bounded query capture")
