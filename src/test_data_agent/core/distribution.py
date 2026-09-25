"""Typed distribution metadata for domain-agnostic dataset specs."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from typing import Annotated, Any, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_serializer, model_validator

from test_data_agent.core.decimal_units import decimal_to_units


class CategoryWeight(BaseModel):
    value: Any
    count: float = Field(default=1.0, ge=0.0)


class MaskedPattern(BaseModel):
    pattern: str = Field(min_length=1)
    count: int = Field(ge=0)


class SyntheticIdentifierDistribution(BaseModel):
    kind: Literal["synthetic_identifier"] = "synthetic_identifier"
    prefix: str | None = None
    pool_size: int | None = Field(default=None, strict=True, ge=1)

    @model_serializer(mode="wrap")
    def serialize(self, handler: Any) -> dict[str, Any]:
        payload: dict[str, Any] = handler(self)
        if self.pool_size is None:
            payload.pop("pool_size", None)
        return payload


class MaskedPatternsDistribution(BaseModel):
    kind: Literal["masked_patterns"] = "masked_patterns"
    patterns: list[MaskedPattern] = Field(default_factory=list)


class NumericDistribution(BaseModel):
    kind: Literal["numeric"] = "numeric"
    min_value: int | float | None = None
    max_value: int | float | None = None
    p05: int | float | None = None
    p95: int | float | None = None
    scale_factor: float = Field(default=1.0, ge=0.1, le=10.0)

    @model_validator(mode="after")
    def validate_ordered_bounds(self) -> NumericDistribution:
        if self.min_value is not None and self.max_value is not None and self.min_value > self.max_value:
            raise ValueError("numeric min_value must be <= max_value")
        if self.p05 is not None and self.p95 is not None and self.p05 > self.p95:
            raise ValueError("numeric p05 must be <= p95")
        return self


class DecimalRangeDistribution(BaseModel):
    """Exact synthetic bounds; never derived from source rows."""

    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    kind: Literal["decimal_range"] = "decimal_range"
    precision: int = Field(strict=True, ge=1, le=38)
    scale: int = Field(strict=True, ge=0)
    min: str = Field(repr=False)
    max: str = Field(repr=False)

    @model_validator(mode="after")
    def validate_exact_bounds(self) -> DecimalRangeDistribution:
        if decimal_to_units(self.min, precision=self.precision, scale=self.scale) > decimal_to_units(
            self.max, precision=self.precision, scale=self.scale,
        ):
            raise ValueError("invalid decimal range")
        return self


class NumericShapeDistribution(BaseModel):
    kind: Literal["numeric_shape"] = "numeric_shape"
    max_abs_magnitude: int = Field(ge=-308, le=307)
    has_negative: bool = False
    has_positive: bool = False

    @model_validator(mode="after")
    def validate_nonzero_shape(self) -> NumericShapeDistribution:
        if not self.has_negative and not self.has_positive:
            raise ValueError("numeric shape must include a non-zero sign")
        return self


class BooleanDistribution(BaseModel):
    kind: Literal["boolean"] = "boolean"
    true_ratio: float = Field(default=0.5, ge=0.0, le=1.0)


class DateRangeDistribution(BaseModel):
    kind: Literal["date_range"] = "date_range"
    min: str | None = None
    max: str | None = None

    @model_validator(mode="after")
    def validate_ordered_bounds(self) -> DateRangeDistribution:
        validate_optional_date_range(self.min, self.max, "date_range")
        return self


class DateTimeRangeDistribution(BaseModel):
    kind: Literal["datetime_range"] = "datetime_range"
    min: str | None = None
    max: str | None = None

    @model_validator(mode="after")
    def validate_ordered_bounds(self) -> DateTimeRangeDistribution:
        validate_optional_datetime_range(self.min, self.max, "datetime_range")
        return self


class CategoricalDistribution(BaseModel):
    kind: Literal["categorical"] = "categorical"
    categories: list[CategoryWeight] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_positive_weight(self) -> CategoricalDistribution:
        if self.categories and sum(category.count for category in self.categories) <= 0:
            raise ValueError("categorical distribution requires a positive total count")
        return self


class StringPatternDistribution(BaseModel):
    kind: Literal["string_pattern"] = "string_pattern"
    min_length: int = Field(default=1, ge=0)
    max_length: int = Field(default=12, ge=0)

    @model_validator(mode="after")
    def validate_ordered_lengths(self) -> StringPatternDistribution:
        if self.min_length > self.max_length:
            raise ValueError("string_pattern min_length must be <= max_length")
        return self


def validate_optional_date_range(min_value: str | None, max_value: str | None, label: str) -> None:
    start = parse_date_bound(min_value, label)
    end = parse_date_bound(max_value, label)
    if start is not None and end is not None and start > end:
        raise ValueError(f"{label} min must be <= max")


def validate_optional_datetime_range(min_value: str | None, max_value: str | None, label: str) -> None:
    start = parse_datetime_bound(min_value, label)
    end = parse_datetime_bound(max_value, label)
    if start is not None and end is not None:
        try:
            ordered = start <= end
        except TypeError as exc:
            raise ValueError(f"{label} bounds must use compatible timezone awareness") from exc
        if not ordered:
            raise ValueError(f"{label} min must be <= max")


def parse_date_bound(value: str | None, label: str) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError as exc:
        raise ValueError(f"{label} bound must be an ISO date") from exc


def parse_datetime_bound(value: str | None, label: str) -> datetime | None:
    if value is None:
        return None
    try:
        text = value.replace("Z", "+00:00")
        if "T" not in text and " " not in text:
            text = f"{text}T00:00:00"
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{label} bound must be an ISO datetime") from exc


FieldDistribution: TypeAlias = Annotated[
    SyntheticIdentifierDistribution
    | MaskedPatternsDistribution
    | NumericDistribution
    | DecimalRangeDistribution
    | NumericShapeDistribution
    | BooleanDistribution
    | DateRangeDistribution
    | DateTimeRangeDistribution
    | CategoricalDistribution
    | StringPatternDistribution,
    Field(discriminator="kind"),
]


_DISTRIBUTION_ADAPTER: TypeAdapter[FieldDistribution] = TypeAdapter(FieldDistribution)
_TYPED_DISTRIBUTION_KINDS = frozenset(
    {
        "synthetic_identifier",
        "masked_patterns",
        "numeric",
        "decimal_range",
        "numeric_shape",
        "boolean",
        "date_range",
        "datetime_range",
        "categorical",
        "string_pattern",
    }
)


def validate_distribution(data: dict[str, Any]) -> FieldDistribution:
    """Validate raw profile/spec distribution metadata against known shapes."""
    return _DISTRIBUTION_ADAPTER.validate_python(data)


def parse_distribution(data: Mapping[str, Any] | None) -> FieldDistribution | None:
    """Return a typed distribution when metadata declares a supported kind."""
    if data is None:
        return None
    kind = data.get("kind")
    if kind not in _TYPED_DISTRIBUTION_KINDS:
        return None
    return validate_distribution(dict(data))
