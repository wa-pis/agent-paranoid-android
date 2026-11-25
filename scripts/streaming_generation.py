"""Benchmark-only streaming sinks for the flat fictional tiled-v1 fixture."""

from __future__ import annotations

from collections.abc import Callable
import csv
import hashlib
import io
from math import ceil
from pathlib import Path
import resource
import sys
import tempfile
import time
from typing import Any

from test_data_agent.adapters.parallel_generation import (
    ParallelGenerationPolicy,
    _visit_generated_tiles,
)
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.limits import (
    GenerationBudget,
    GenerationLimitError,
    enforce_output_capacity,
    enforce_output_payload_size,
)
from test_data_agent.core.settings import GenerationMode
from test_data_agent.generation.constraint_solver import solve_constraints
from test_data_agent.generation.tiled_generator import TILE_ROWS
from test_data_agent.io.path_policy import atomic_binary_writer
from test_data_agent.io.writers import neutralize_csv_cell
from test_data_agent.safety import assert_spec_safe
from test_data_agent.validation.reconciliation import assert_generated_dataset_valid


class StreamingBenchmarkError(ValueError):
    """Value-free failure of this experimental, local-only comparison."""


def _check_supported(spec: DatasetSpec) -> None:
    assert_spec_safe(spec)
    # shortcut: only the flat valid fixture; global rule execution needs another experiment.
    if (len(spec.entities) != 1 or spec.relationships or spec.constraints
            or spec.generation_settings.mode != GenerationMode.VALID
            or not spec.entities[0].primary_key
            or any(field.data_type.value not in {"integer", "float", "boolean", "date", "string"}
                   for field in spec.entities[0].fields)):
        raise StreamingBenchmarkError("streaming benchmark requires a flat valid specification")


def _stream(
    spec: DatasetSpec, backend: str, *, seed: int, policy: ParallelGenerationPolicy,
    budget: GenerationBudget, scratch: Path,
) -> dict[str, Any]:
    """Write only validated synthetic batches; publish inside private scratch after all checks."""
    import pyarrow as pa

    _check_supported(spec)
    if backend not in {"arrow", "duckdb"}:
        raise StreamingBenchmarkError("unknown streaming benchmark backend")
    started = time.perf_counter()
    stages = dict.fromkeys(("generation_ipc_pool", "validation", "arrow_conversion", "backend_ingest",
                           "global_check", "backend_readback", "csv_write_hash", "setup_cleanup"), 0.0)

    def timed(stage: str, operation: Callable[[], Any]) -> Any:
        before = time.perf_counter()
        result = operation()
        stages[stage] += time.perf_counter() - before
        return result

    entity = spec.entities[0]
    names = [field.name for field in entity.fields]
    types = {"integer": pa.int64(), "float": pa.float64(), "boolean": pa.bool_(),
             "string": pa.string(), "date": pa.string()}
    schema = pa.schema([("ordinal", pa.int64())] + [
        (f"c{index}", types[field.data_type.value]) for index, field in enumerate(entity.fields)
    ])
    assert entity.primary_key is not None
    pk_index = names.index(entity.primary_key)
    seen: set[Any] = set()
    count = size = scratch_peak = spill_peak = 0
    digest = hashlib.sha256()
    connection: Any = None
    reader: Any = None
    deadline = time.perf_counter() + budget.max_seconds

    def query(sql: str) -> Any:
        budget.check("streaming SQL")
        connection.execute("SET max_execution_time = ?", [max(1, ceil(
            (deadline - time.perf_counter()) * 1000))])
        return connection.execute(sql)

    def observe_scratch() -> None:
        nonlocal scratch_peak, spill_peak
        total = spill = 0
        for path in scratch.rglob("*"):
            try:
                size_on_disk = path.stat().st_size if path.is_file() else 0
            except FileNotFoundError:
                continue
            total += size_on_disk
            if scratch / "spill" in path.parents:
                spill += size_on_disk
        scratch_peak = max(scratch_peak, total)
        spill_peak = max(spill_peak, spill)

    try:
        enforce_output_capacity(scratch)
        if backend == "duckdb":
            import duckdb

            connection = duckdb.connect(":memory:", config={
                "memory_limit": "128MiB", "threads": "1", "async_threads": "1",
                "temp_directory": str(scratch / "spill"),
                "autoinstall_known_extensions": "false", "autoload_known_extensions": "false",
                "python_enable_replacements": "false",
            })
            connection.execute("SET enable_external_access = false")
            connection.execute("SET enable_logging = false")
            connection.execute("SET max_temp_directory_size = '2GiB'")
            connection.execute("SET preserve_insertion_order = false")
            empty = pa.RecordBatch.from_arrays([pa.array([], type=field.type) for field in schema],
                                               schema=schema)
            connection.register("incoming", empty)
            query("CREATE TABLE generated AS SELECT * FROM incoming")
            connection.unregister("incoming")
        stages["setup_cleanup"] += time.perf_counter() - started
        with atomic_binary_writer(scratch / "synthetic.csv") as handle:
            def write(batch: Any) -> None:
                nonlocal size
                columns = timed("backend_readback", batch.to_pydict)

                def encode_write() -> None:
                    nonlocal size
                    text = io.StringIO(newline="")
                    writer = csv.writer(text)
                    if size == 0:
                        writer.writerow([neutralize_csv_cell(name) for name in names])
                    for row in zip(*(columns[f"c{index}"] for index in range(len(names))), strict=True):
                        writer.writerow([neutralize_csv_cell(value) for value in row])
                    encoded = text.getvalue().encode("utf-8")
                    enforce_output_payload_size(size + len(encoded), label="benchmark CSV")
                    budget.check("streaming CSV")
                    handle.write(encoded)
                    digest.update(encoded)
                    size += len(encoded)

                timed("csv_write_hash", encode_write)

            def consume(entity_index: int, start: int, rows: list[dict[str, Any]]) -> None:
                nonlocal count
                budget.check("streaming batch")

                def validate() -> None:
                    batch_spec = spec.model_copy(deep=True)
                    batch_spec.entities[0].row_count = len(rows)
                    data = {entity.name: rows}
                    solve_constraints(data, batch_spec, seed=seed)
                    assert_generated_dataset_valid(data, batch_spec)
                    if entity_index != 0 or start != count:
                        raise StreamingBenchmarkError("streaming row order differs")

                timed("validation", validate)

                def convert() -> Any:
                    return pa.RecordBatch.from_arrays([
                        pa.array(range(start, start + len(rows)), type=pa.int64()),
                        *(pa.array([row[name] for row in rows], type=schema.field(index + 1).type)
                          for index, name in enumerate(names)),
                    ], schema=schema)

                batch = timed("arrow_conversion", convert)
                if connection is None:
                    def check_keys() -> None:
                        for key in batch.column(pk_index + 1).to_pylist():
                            if key is None or key in seen:
                                raise StreamingBenchmarkError("streaming primary key validation failed")
                            seen.add(key)

                    timed("global_check", check_keys)
                    write(batch)
                else:
                    def ingest() -> None:
                        connection.register("incoming", batch)
                        try:
                            query("INSERT INTO generated SELECT * FROM incoming")
                        finally:
                            connection.unregister("incoming")

                    timed("backend_ingest", ingest)
                count += len(rows)
                observe_scratch()
                budget.check("streaming batch")

            before = time.perf_counter()
            callback_before = sum(stages.values())
            _visit_generated_tiles(spec, seed, policy=policy, budget=budget, consume=consume)
            stages["generation_ipc_pool"] += (time.perf_counter() - before
                                               - (sum(stages.values()) - callback_before))

            def final_check() -> None:
                if count != entity.row_count:
                    raise StreamingBenchmarkError("streaming row count differs")
                if connection is None:
                    unique = len(seen)
                else:
                    actual, unique = query(
                        f"SELECT count(*), count(DISTINCT c{pk_index}) FROM generated"
                    ).fetchall()[0]
                    if actual != count:
                        raise StreamingBenchmarkError("streaming stored row count differs")
                if unique != count:
                    raise StreamingBenchmarkError("streaming primary key validation failed")

            timed("global_check", final_check)
            if connection is not None:
                budget.check("streaming readback")
                query("SELECT 1").fetchall()  # Refresh the native deadline before the relation.
                reader = timed("backend_readback", lambda: connection.sql(
                    "SELECT * FROM generated ORDER BY ordinal"
                ).to_arrow_reader(batch_size=TILE_ROWS))
                exported = 0
                while True:
                    before = time.perf_counter()
                    try:
                        batch = reader.read_next_batch()
                    except StopIteration:
                        batch = None
                    stages["backend_readback"] += time.perf_counter() - before
                    if batch is None:
                        break
                    write(batch)
                    exported += batch.num_rows
                    observe_scratch()
                    budget.check("streaming export")
                if exported != count:
                    raise StreamingBenchmarkError("streaming exported row count differs")
            budget.check("streaming final validation")
            observe_scratch()
        result: dict[str, Any] = {"stage_seconds": stages,
                "csv_bytes": size, "csv_sha256": digest.hexdigest(), "unique_primary_keys": True,
                "rows_validated": count, "scratch_observed_peak_bytes": scratch_peak,
                "spill_observed_peak_bytes": spill_peak,
                "scratch_private": scratch.stat().st_mode & 0o777 == 0o700,
                "output_private": (scratch / "synthetic.csv").stat().st_mode & 0o777 == 0o600}
    finally:
        before = time.perf_counter()
        try:
            if reader is not None:
                reader.close()
        finally:
            if connection is not None:
                connection.close()
        stages["setup_cleanup"] += time.perf_counter() - before
    result["total_seconds"] = time.perf_counter() - started
    stages["setup_cleanup"] += result["total_seconds"] - sum(stages.values())
    return result


def run_streaming_benchmark(rows: int, backend: str) -> dict[str, Any]:
    from benchmark_parallel_generation import fictional_spec

    started = time.perf_counter()
    failed = False
    result: dict[str, Any] = {}
    try:
        with tempfile.TemporaryDirectory(prefix="test-data-agent-stream-benchmark-") as directory:
            scratch = Path(directory).resolve()
            result = _stream(fictional_spec(rows), backend, seed=42, scratch=scratch,
                             policy=ParallelGenerationPolicy(workers=4, max_rows=rows, max_cells=rows * 25),
                             budget=GenerationBudget(600))
        if scratch.exists():
            raise StreamingBenchmarkError("streaming scratch cleanup failed")
    except GenerationLimitError:
        raise
    except Exception:
        failed = True
    if failed:
        raise StreamingBenchmarkError("streaming benchmark generation, export or cleanup failed")
    elapsed = time.perf_counter() - started
    result["stage_seconds"]["setup_cleanup"] += elapsed - result["total_seconds"]
    result["total_seconds"] = elapsed
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result["coordinator_peak_rss_bytes"] = peak if sys.platform == "darwin" else peak * 1024
    result["scratch_removed"] = True
    return result
