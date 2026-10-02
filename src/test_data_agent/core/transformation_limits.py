"""Private transformation input budgets and value-free recovery diagnostics."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictInt
from test_data_agent.core.limits import InputLimitError

PositiveLimit = Annotated[StrictInt, Field(gt=0, le=2**63 - 1)]


class InputDimension(StrEnum):
    ROWS = "max_input_rows"
    COLUMNS = "max_input_columns"
    CELLS = "max_input_cells"
    BYTES = "max_input_file_bytes"
    TOTAL_BYTES = "max_total_input_bytes"
    CELL_CHARS = "max_input_cell_chars"
    EXPANDED_BYTES = "max_parquet_expanded_bytes"
    OUTPUT_BYTES = "max_output_bytes"


class TransformationInputLimits(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, revalidate_instances="always")
    max_input_rows: PositiveLimit = 1_000_000
    max_input_columns: PositiveLimit = 1_000
    max_input_cells: PositiveLimit = 100_000_000
    max_input_file_bytes: PositiveLimit = 128 * 1024 * 1024
    max_total_input_bytes: PositiveLimit = 512 * 1024 * 1024
    max_input_cell_chars: PositiveLimit = 1_000_000
    max_parquet_expanded_bytes: PositiveLimit = 512 * 1024 * 1024
    max_output_bytes: PositiveLimit = 512 * 1024 * 1024


class TransformationLimitError(InputLimitError):
    """Only fixed identifiers and nonnegative counters; never backend text."""

    def __init__(self, dimension: InputDimension, amount: int, limit: int,
                 origin: str, *, requested: bool = False):
        if (type(dimension) is not InputDimension or type(amount) is not int
                or type(limit) is not int or not 0 <= amount <= 2**63 - 1
                or not 0 < limit <= 2**63 - 1
                or origin not in {"default", "profile", "session", "legacy_session", "snapshot_run", "trace_run", "replacement_trace_run", "output_run", "bundle_run", "sql_output_run", "parquet_output_run", "query_rows_run", "query_bytes_run"}
                or origin == "snapshot_run" and dimension is not InputDimension.TOTAL_BYTES
                or origin == "query_rows_run" and dimension is not InputDimension.ROWS
                or origin == "query_bytes_run" and dimension is not InputDimension.BYTES
                or origin in {"trace_run", "replacement_trace_run"} and dimension is not InputDimension.CELLS
                or origin in {"output_run", "bundle_run", "sql_output_run", "parquet_output_run"} and dimension is not InputDimension.OUTPUT_BYTES
                or type(requested) is not bool):
            raise ValueError("invalid limit diagnostic")
        self.dimension, self.amount, self.limit, self.origin = dimension, amount, limit, origin
        self.code = "requested_above_limit" if requested else "limit_exceeded"
        self.unit = ("bytes" if dimension in {InputDimension.BYTES, InputDimension.TOTAL_BYTES, InputDimension.EXPANDED_BYTES, InputDimension.OUTPUT_BYTES}
                     else "characters" if dimension is InputDimension.CELL_CHARS
                     else dimension.value.removeprefix("max_input_"))
        self.session_setting = "TEST_DATA_AGENT_TRANSFORM_" + dimension.value.upper()
        self.profile_key = "resource_limits." + dimension.value
        self.run_setting = {"trace_run": "trace_csv_review_request(max_cells=...)",
                            "snapshot_run": "prepare_csv_review_from_paths(max_total_bytes=...)",
                            "query_rows_run": "_capture_authorized_result(max_rows=...)",
                            "query_bytes_run": "_capture_authorized_result(max_bytes=...)",
                            "replacement_trace_run": "trace_csv_replacements(max_cells=...)",
                            "output_run": "replace_csv_snapshot(max_output_bytes=...)",
                            "bundle_run": "temporary_csv_publication(max_output_bytes=...)",
                            "sql_output_run": "render_transformation_sql(max_bytes=...)",
                            "parquet_output_run": "render_transformation_parquet(max_bytes=...)"}.get(origin)
        recovery = (f"Run: increase {self.run_setting} within the session/profile ceiling. "
                    if self.run_setting else "")
        super().__init__(f"{self.code}: {dimension.value} {amount} > {limit} {self.unit} "
            f"(origin={origin}). {recovery}Session: set {self.session_setting} to a sufficient positive integer; "
            f"saved behavior profile: set {self.profile_key}. No automatic increase or truncation.")


@dataclass(frozen=True)
class EffectiveInputLimit:
    dimension: InputDimension
    value: int
    origin: str

    def check(self, amount: int, *, requested: bool = False) -> None:
        if amount > self.value:
            try:
                raise TransformationLimitError(self.dimension, amount, self.value, self.origin,
                    requested=requested)
            except TransformationLimitError as error:
                error.__context__ = None
                raise


def resolve_input_limit(dimension: InputDimension, profile: TransformationInputLimits | None,
                        session: Mapping[str, str]) -> EffectiveInputLimit:
    """Explicit transformation env > saved field > legacy env > default."""
    key = dimension.value
    setting = "TEST_DATA_AGENT_TRANSFORM_" + key.upper()
    legacy = "TEST_DATA_AGENT_" + key.upper()
    if setting in session:
        value, origin = session[setting], "session"
    elif profile is not None and key in profile.model_fields_set:
        return EffectiveInputLimit(dimension, getattr(profile, key), "profile")
    elif legacy in session:
        value, origin = session[legacy], "legacy_session"
    else:
        return EffectiveInputLimit(dimension, getattr(TransformationInputLimits(), key), "default")
    if (type(value) is str and 0 < len(value) <= 19 and value.isascii() and value.isdecimal()
            and 0 < int(value) <= 2**63 - 1):
        return EffectiveInputLimit(dimension, int(value), origin)
    raise ValueError(f"invalid resource setting: {setting if origin == 'session' else legacy}; "
        f"use a positive integer <= {2**63 - 1}; profile key resource_limits.{key}")
