"""Field profiles and generation specs."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from test_data_agent.core.distribution import validate_distribution


_TYPED_DISTRIBUTION_KINDS = {
    "synthetic_identifier",
    "masked_patterns",
    "numeric",
    "boolean",
    "date_range",
    "datetime_range",
    "categorical",
    "string_pattern",
}


def _normalize_distribution(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return value
    kind = value.get("kind")
    if kind not in _TYPED_DISTRIBUTION_KINDS:
        return value
    return validate_distribution(value).model_dump(mode="json")


class FieldType(StrEnum):
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    STRING = "string"
    DATE = "date"
    DATETIME = "datetime"


class FieldProfile(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    name: str
    data_type: FieldType
    nullable: bool = False
    null_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    unique_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    sensitive: bool = False
    semantic_type: str | None = None
    is_identifier: bool = False
    distribution: dict[str, Any] = Field(default_factory=dict)

    @field_validator("distribution", mode="before")
    @classmethod
    def validate_distribution_shape(cls, value: Any) -> dict[str, Any]:
        return _normalize_distribution(value)


class FieldSpec(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    name: str
    data_type: FieldType
    nullable: bool = False
    null_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    sensitive: bool = False
    semantic_type: str | None = None
    is_identifier: bool = False
    distribution: dict[str, Any] = Field(default_factory=dict)

    @field_validator("distribution", mode="before")
    @classmethod
    def validate_distribution_shape(cls, value: Any) -> dict[str, Any]:
        return _normalize_distribution(value)
