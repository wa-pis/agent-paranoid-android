"""Explicit, finite policy for the opt-in scalable synthetic engine."""
from pydantic import BaseModel, ConfigDict, Field

MAX_SCALABLE_JSON_ROW_CHARS = 4*1024**2


class GenerationExecutionPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)
    engine: str = Field(default="scalable-v1", pattern=r"^scalable-v1$")
    max_rows: int = Field(default=1_000_000, strict=True, ge=1, le=10_000_000)
    max_cells: int = Field(default=25_000_000, strict=True, ge=1, le=100_000_000)
    max_memory_bytes: int = Field(default=1024**3, strict=True, ge=256*1024**2, le=8*1024**3)
    max_output_bytes: int = Field(default=512*1024**2, strict=True, ge=1, le=8*1024**3)
    max_temporary_bytes: int = Field(default=512*1024**2, strict=True, ge=1, le=8*1024**3)
    max_seconds: float = Field(default=600, gt=0, le=3600, allow_inf_nan=False)
    workers: int = Field(default=1, strict=True, ge=1, le=4)
    batch_size: int = Field(default=2000, strict=True, ge=1, le=10000)
    require_distinct_rows: bool = True
