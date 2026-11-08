"""Value-free capacity forecasts; these are not resource-limit guarantees."""
from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.field import FieldSpec, FieldType
from test_data_agent.core.fingerprints import model_fingerprint


class EstimateRange(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    low: float = Field(ge=0, allow_inf_nan=False)
    expected: float = Field(ge=0, allow_inf_nan=False)
    high: float = Field(ge=0, allow_inf_nan=False)

    @model_validator(mode='after')
    def ordered(self) -> EstimateRange:
        if not self.low <= self.expected <= self.high:
            raise ValueError('forecast bounds must be ordered')
        return self


class EntityCapacity(BaseModel):
    entity: str
    rows: int
    cells: int
    file_bytes: EstimateRange
    logical_database_bytes: EstimateRange
    postgres_table_bytes: EstimateRange | None = None


class CapacityEstimate(BaseModel):
    schema_version: Literal["1"] = "1"
    estimator_version: Literal["1"] = "1"
    spec_sha256: str
    output_format: str
    method: Literal["metadata", "synthetic_calibration"] = "metadata"
    confidence: Literal["low", "medium"] = "low"
    entities: list[EntityCapacity]
    file_bytes: EstimateRange
    control_artifact_bytes: EstimateRange
    logical_database_bytes: EstimateRange
    postgres_table_bytes: EstimateRange | None = None
    duration_seconds: EstimateRange | None = None
    calibration_seconds: float | None = None
    duration_stages_seconds: dict[str, EstimateRange] = Field(default_factory=dict)
    assumptions: list[str]
    budget_findings: list[str] = Field(default_factory=list)
    duration_unknown_reason: str | None = "No matching local calibration; request bounded calibration."
    calibration: dict[str, float | str | int] | None = None


def spread(expected: float, low: float = .5, high: float = 2.) -> EstimateRange:
    return EstimateRange(low=expected*low, expected=expected, high=expected*high)


def total(ranges: list[EstimateRange]) -> EstimateRange:
    return EstimateRange(**{key: sum(getattr(item, key) for item in ranges)
                            for key in ("low", "expected", "high")})


def field_width(field: FieldSpec, rows: int) -> tuple[float, float]:
    """Expected text and typed logical payload bytes; never returns field values."""
    kind = field.data_type
    distribution = field.distribution
    non_null = 1-field.null_ratio if field.nullable else 1.
    if field.is_identifier:
        # Seed range is unknown here; include room for signed 64-bit seed expansion.
        text = 24. if kind == FieldType.INTEGER else 34.
        logical = 8. if kind == FieldType.INTEGER else text
    elif kind == FieldType.BOOLEAN:
        text, logical = 4.5, 1.
    elif kind in {FieldType.INTEGER, FieldType.FLOAT}:
        bound = max(abs(distribution.get("min_value") or 0),
                    abs(distribution.get("max_value") or 1000))
        text = len(str(int(bound))) + (7 if kind == FieldType.FLOAT else 0)
        logical = 8.
    elif kind == FieldType.DECIMAL:
        text = float(distribution["precision"]+2)
        logical = 8+2*math.ceil(distribution["precision"]/4)
    elif kind in {FieldType.DATE, FieldType.DATETIME}:
        text, logical = (10., 4.) if kind == FieldType.DATE else (25., 8.)
    else:
        categories = distribution.get("categories") or []
        if categories:
            weight = sum(item.get("count", 1) for item in categories) or 1
            text = sum(len(str(item["value"]).encode("utf-8"))*item.get("count", 1)
                       for item in categories)/weight
        elif field.sensitive:
            text = 48.
        else:
            text = (distribution.get("min_length", 6)+distribution.get("max_length", 12))/2
        logical = text
    return text*non_null, logical*non_null


def estimate_capacity(spec: DatasetSpec, *, database: Literal["logical", "postgresql"] = "logical") -> CapacityEstimate:
    if database not in {'logical', 'postgresql'}:
        raise ValueError('supported database models are logical and postgresql; other physical layouts are unknown')
    fmt = spec.generation_settings.output_format.value
    if fmt not in {"csv", "json", "parquet"}:
        raise ValueError("capacity forecasts support csv, json and parquet")
    if not spec.entities:
        raise ValueError("capacity estimation requires entities")
    multiplier = (spec.generation_settings.load_multiplier
                  if spec.generation_settings.mode == "load_test" else 1)
    identifier_domains = max(1, sum(field.is_identifier for entity in spec.entities for field in entity.fields))
    reference_rows: dict[tuple[str, str], int] = {}
    policy = spec.generation_settings.execution_policy
    if policy is not None and policy.engine == 'scalable-relational-v1':
        parents = {entity.name: entity.row_count*multiplier for entity in spec.entities}
        reference_rows = {(r.child_entity, r.child_field): parents[r.parent_entity]
            for r in spec.relationships if r.status != 'rejected' and r.parent_entity in parents}
    entities = []
    for entity in spec.entities:
        rows = entity.row_count*multiplier
        widths = [field_width(field.model_copy(update={'is_identifier': True})
            if (entity.name, field.name) in reference_rows else field, rows) for field in entity.fields]
        logical = sum(item[1] for item in widths)
        text = sum(item[0] for item in widths)
        headers = sum(len(field.name.encode("utf-8"))+1 for field in entity.fields)+2
        if fmt == "json":
            per_row = text+sum(len(field.name.encode("utf-8"))+10 for field in entity.fields)+8
            size = rows*per_row+2
        elif fmt == "csv":
            size = headers+rows*(text+len(entity.fields)+2)
        else:
            size = 2048+rows*logical*.65
        # PostgreSQL estimate: approximate MAXALIGN'd tuple plus line pointer;
        # page occupancy varies with types, nulls and wide-value externalization.
        tuple_bytes = math.ceil((24+math.ceil(len(entity.fields)/8)+logical
                                 +4*sum(field.data_type == FieldType.STRING for field in entity.fields))/8)*8+4
        wide_values = any(field.data_type == FieldType.STRING and (
            int(field.distribution.get("max_length", 128))*4 > 1800
            or any(len(str(item.get("value", "")).encode("utf-8")) > 1800
                   for item in field.distribution.get("categories", []))) for field in entity.fields)
        outside_int64 = any(field.data_type == FieldType.INTEGER and (
            ((field.is_identifier or (entity.name, field.name) in reference_rows)
                and ((spec.generation_settings.seed or 0)*1_000_000
                     +reference_rows.get((entity.name, field.name), rows)+1)*identifier_domains > 2**63-1)
            or (field.distribution.get('kind') == 'numeric_shape' and field.distribution['max_abs_magnitude'] >= 18)
            or any(abs(field.distribution.get(key) or 0)*field.distribution.get('scale_factor', 1) > 2**63-1
                   for key in ('min_value', 'max_value', 'p05', 'p95'))
        ) for field in entity.fields)
        pg = (spread(math.ceil(rows*tuple_bytes/8168)*8192, .8, 1.5)
              if database == "postgresql" and not wide_values and not outside_int64 else None)
        entities.append(EntityCapacity(entity=entity.name, rows=rows, cells=rows*len(entity.fields),
            file_bytes=spread(size, .35 if fmt == "parquet" else .5, 3. if fmt == "parquet" else 2.),
            logical_database_bytes=spread(rows*logical, .7, 1.4), postgres_table_bytes=pg))
    assumptions = [
        "Forecast ranges are uncertain, not hard safety bounds; values are bytes.",
        "UTF-8; existing CSV quoting/null encoding or indented JSON; Parquet defaults to Snappy.",
        "Database logical payload uses int64/float64, boolean, date/timestamp, decimal and UTF-8 values.",
        "Database excludes indexes, WAL, replicas, backups and auxiliary storage.",
        "Metadata forecasts have low confidence; use representative synthetic calibration for files/time.",
        "Temporary disk and process memory are governed by execution policy, not predicted by file size.",
        "Duration covers standalone source-free bundle generation; attached-source profiling/reuse scans and human review add uncalibrated time.",
    ]
    if database == "postgresql":
        assumptions.append("Approximate PostgreSQL 8KiB pages, 24-byte tuple header, null bitmap, 8-byte alignment and line pointers; no TOAST prediction, externalized values or integers outside int64 make physical size unknown.")
    artifact_size = len(spec.model_dump_json().encode("utf-8"))*2+65536
    return CapacityEstimate(spec_sha256=model_fingerprint(spec), output_format=fmt,
        entities=entities, file_bytes=total([e.file_bytes for e in entities]),
        control_artifact_bytes=spread(artifact_size),
        logical_database_bytes=total([e.logical_database_bytes for e in entities]),
        postgres_table_bytes=total([e.postgres_table_bytes for e in entities if e.postgres_table_bytes is not None]) if database == "postgresql" and all(e.postgres_table_bytes is not None for e in entities) else None,
        assumptions=assumptions)
