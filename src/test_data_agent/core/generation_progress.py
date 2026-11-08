"""Value-free, informational progress; never an approval or completion receipt."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class GenerationProgress(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)
    spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    phase: Literal['generating', 'completed']
    rows_completed: int = Field(ge=0)
    rows_total: int = Field(ge=0)
    elapsed_seconds: float = Field(ge=0, allow_inf_nan=False)
    remaining_seconds_low: float = Field(ge=0, allow_inf_nan=False)
    remaining_seconds_high: float = Field(ge=0, allow_inf_nan=False)
