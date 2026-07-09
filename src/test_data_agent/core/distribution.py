"""Typed distribution metadata for domain-agnostic dataset specs."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, Any, Literal, TypeAlias

from pydantic import BaseModel, Field, TypeAdapter


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


class BooleanDistribution(BaseModel):
    kind: Literal["boolean"] = "boolean"
    true_ratio: float = Field(default=0.5, ge=0.0, le=1.0)


class DateRangeDistribution(BaseModel):
    kind: Literal["date_range"] = "date_range"
    min: str | None = None
    max: str | None = None


class DateTimeRangeDistribution(BaseModel):
    kind: Literal["datetime_range"] = "datetime_range"
    min: str | None = None
    max: str | None = None


class CategoricalDistribution(BaseModel):
    kind: Literal["categorical"] = "categorical"
    categories: list[CategoryWeight] = Field(default_factory=list)


class StringPatternDistribution(BaseModel):
    kind: Literal["string_pattern"] = "string_pattern"
    min_length: int = Field(default=1, ge=0)
    max_length: int = Field(default=12, ge=0)


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
