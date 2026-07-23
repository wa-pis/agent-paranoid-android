"""Field profiles and generation specs."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from test_data_agent.core.distribution import FieldDistribution, parse_distribution


def _normalize_distribution(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("distribution must be an object")
    distribution = parse_distribution(value)
    if distribution is None:
        return value
    return distribution.model_dump(mode="json")


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

    @property
    def typed_distribution(self) -> FieldDistribution | None:
        return parse_distribution(self.distribution)


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

    @property
    def typed_distribution(self) -> FieldDistribution | None:
        return parse_distribution(self.distribution)
