"""Typed distribution metadata for domain-agnostic dataset specs."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from typing import Annotated, Any, Literal, TypeAlias

from pydantic import BaseModel, Field, TypeAdapter, model_validator


class CategoryWeight(BaseModel):
    value: Any
    count: float = Field(default=1.0, ge=0.0)


class MaskedPattern(BaseModel):
    pattern: str = Field(min_length=1)
    count: int = Field(ge=0)


class SyntheticIdentifierDistribution(BaseModel):
    kind: Literal["synthetic_identifier"] = "synthetic_identifier"
    prefix: str | None = None


class MaskedPatternsDistribution(BaseModel):
    kind: Literal["masked_patterns"] = "masked_patterns"
    patterns: list[MaskedPattern] = Field(default_factory=list)


class NumericDistribution(BaseModel):
    kind: Literal["numeric"] = "numeric"
    min_value: int | float | None = None
    max_value: int | float | None = None
    p05: int | float | None = None
    p95: int | float | None = None

    @model_validator(mode="after")
    def validate_ordered_bounds(self) -> NumericDistribution:
        if self.min_value is not None and self.max_value is not None and self.min_value > self.max_value:
            raise ValueError("numeric min_value must be <= max_value")
        if self.p05 is not None and self.p95 is not None and self.p05 > self.p95:
            raise ValueError("numeric p05 must be <= p95")
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
    | BooleanDistribution
    | DateRangeDistribution
    | DateTimeRangeDistribution
    | CategoricalDistribution
    | StringPatternDistribution,
    Field(discriminator="kind"),
]


_DISTRIBUTION_ADAPTER = TypeAdapter(FieldDistribution)
_TYPED_DISTRIBUTION_KINDS = frozenset(
    {
        "synthetic_identifier",
        "masked_patterns",
        "numeric",
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
