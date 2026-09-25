"""Field profiles and generation specs."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from test_data_agent.core.distribution import DecimalRangeDistribution, FieldDistribution, parse_distribution


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
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    STRING = "string"
    DATE = "date"
    DATETIME = "datetime"


class FieldProfile(BaseModel):
    model_config = ConfigDict(validate_assignment=True, hide_input_in_errors=True)

    name: str
    data_type: FieldType
    decimal_precision: int | None = Field(default=None, strict=True, exclude_if=lambda value: value is None)
    decimal_scale: int | None = Field(default=None, strict=True, exclude_if=lambda value: value is None)
    nullable: bool = False
    null_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    unique_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    unique_ratio_kind: Literal["unspecified", "exact", "lower_bound"] = "unspecified"
    sensitive: bool = False
    semantic_type: str | None = None
    is_identifier: bool = False
    distribution: dict[str, Any] = Field(default_factory=dict, repr=False)

    @field_validator("distribution", mode="before")
    @classmethod
    def validate_distribution_shape(cls, value: Any) -> dict[str, Any]:
        return _normalize_distribution(value)

    @model_validator(mode="after")
    def validate_decimal_metadata(self) -> FieldProfile:
        precision, scale = self.decimal_precision, self.decimal_scale
        if self.data_type == FieldType.DECIMAL:
            if (precision is None) != (scale is None):
                raise ValueError("decimal profile requires paired precision and scale")
            if precision is not None and scale is not None and (
                not 1 <= precision <= 38 or not 0 <= scale <= precision
            ):
                raise ValueError("decimal profile requires supported precision and scale")
        elif precision is not None or scale is not None:
            raise ValueError("decimal metadata requires decimal field type")
        return self

    @property
    def typed_distribution(self) -> FieldDistribution | None:
        return parse_distribution(self.distribution)


class FieldSpec(BaseModel):
    model_config = ConfigDict(validate_assignment=True, hide_input_in_errors=True)

    name: str
    data_type: FieldType
    nullable: bool = False
    null_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    sensitive: bool = False
    semantic_type: str | None = None
    is_identifier: bool = False
    distribution: dict[str, Any] = Field(default_factory=dict, repr=False)

    @field_validator("distribution", mode="before")
    @classmethod
    def validate_distribution_shape(cls, value: Any) -> dict[str, Any]:
        return _normalize_distribution(value)

    @model_validator(mode="after")
    def validate_decimal_contract(self) -> FieldSpec:
        exact = isinstance(self.typed_distribution, DecimalRangeDistribution)
        if (self.data_type == FieldType.DECIMAL) != exact:
            raise ValueError("decimal fields require an exact decimal_range distribution")
        if exact and self.is_identifier:
            raise ValueError("decimal identifiers are not supported")
        return self

    @property
    def typed_distribution(self) -> FieldDistribution | None:
        return parse_distribution(self.distribution)
