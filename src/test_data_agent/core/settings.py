"""Generation and validation settings for DatasetSpec."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class GenerationMode(StrEnum):
    VALID = "valid"
    MIXED = "mixed"
    NEGATIVE = "negative"
    EDGE = "edge"
    LOAD_TEST = "load_test"


class OutputFormat(StrEnum):
    CSV = "csv"
    JSON = "json"
    PARQUET = "parquet"


class GenerationSettings(BaseModel):
    seed: int | None = Field(default=None, ge=0)
    mode: GenerationMode = GenerationMode.VALID
    invalid_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    output_format: OutputFormat = OutputFormat.JSON
    locale: str | None = None


class ValidationSettings(BaseModel):
    validate_schema: bool = True
    validate_relationships: bool = True
    validate_constraints: bool = True
    validate_privacy: bool = True
    fail_fast: bool = False

